from celery import Celery
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from datetime import date
import os
from sqlalchemy.orm import Session, selectinload
import shutil
import uuid
from app.database import SessionLocal, engine, Base
from app.models import Document, DocumentText
import pytesseract
from PIL import Image
from app.config import settings
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)




celery = Celery(
    'tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_document_text(doc_id: int, text: str, db: Session = Depends(get_db)) -> dict:
    try:
        doc_text = DocumentText(id_doc=doc_id, text=text)
        db.add(doc_text)
        db.commit()
        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        db.rollback()
        raise e

@celery.task
def process_document(doc_id: int, image_path: str):
    db = SessionLocal()
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        doc_text = DocumentText(id_doc=doc_id, text=text)
        db.add(doc_text)
        db.commit()
        db.close()
        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


app = FastAPI(
    title="Document Processor API",
    description="API for document processing with OCR",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.post("/upload_doc", summary="Загрузите документ", response_model=dict)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Создаем папку для документов, если ее нет
        os.makedirs("documents", exist_ok=True)

        # Генерируем уникальное имя файла
        file_ext = os.path.splitext(file.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join("documents", file_name)

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Получаем размер файла в КБ
        file_size = os.path.getsize(file_path) / 1024

        # Определяем тип файла
        file_type = file_ext[1:].lower() if file_ext else 'unknown'

        # Сохраняем в базу данных
        doc = Document(path=file_path, date=date.today())
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Возвращаем данные для Django
        return {
            "id": doc.id,
            "file_path": file_path,
            "size": file_size,
            "file_type": file_type,
            "date": doc.date.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/doc_delete/{doc_id}", summary="Удалите документ")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    try:
        # Находим документ
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Удаляем файл
        if os.path.exists(doc.path):
            os.remove(doc.path)

        # Удаляем запись из базы
        db.delete(doc)
        db.commit()

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/doc_analyse/{doc_id}", summary="Analyze document")
def analyze_document(doc_id: int, db: Session = Depends(get_db)):
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        task = process_document.delay(doc_id, doc.path)
        return {"message": "Analysis started", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_text/{doc_id}", summary="Get extracted text")
def get_text(doc_id: int, db: Session = Depends(get_db)):
    try:
        doc_text = db.query(DocumentText).filter(DocumentText.id_doc == doc_id).first()
        if not doc_text:
            raise HTTPException(status_code=404, detail="Text not found")

        return {"text": doc_text.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

