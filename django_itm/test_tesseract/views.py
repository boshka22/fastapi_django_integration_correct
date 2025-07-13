from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from .models import Docs, UserToDocs, Price, Cart
from .forms import UploadFileForm, LoginForm, AnalyzeForm, DocumentDeleteForm
from django.conf import settings
import requests
import os
from django.contrib import messages
import logging
logger = logging.getLogger(__name__)
# Create your views here.



def home(request):
    docs = Docs.objects.exclude(file__isnull=True).exclude(file='').all()
    return render(request, 'home.html', {'docs': docs})
@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Сохраняем в Django
                doc = form.save(commit=False)
                doc.save()  # Это автоматически вызовет метод save() модели

                # Отправляем в FastAPI
                with doc.file.open('rb') as f:
                    response = requests.post(
                        f'{settings.FASTAPI_URL}/upload_doc',
                        files={'file': (doc.file.name, f)},
                        timeout=10
                    )
                    response.raise_for_status()
                    response_data = response.json()

                    # Обновляем документ данными из FastAPI
                    doc.fastapi_id = response_data.get('doc_id')
                    doc.fastapi_filepath = response_data.get('file_path')
                    doc.save()

                # Создаем связь с пользователем
                UserToDocs.objects.create(
                    username=request.user.username,
                    doc=doc
                )

                messages.success(request, "Файл успешно загружен")
                return redirect('home')

            except requests.RequestException as e:
                error_msg = f"Ошибка FastAPI: {str(e)}"
                if hasattr(e, 'response'):
                    try:
                        error_msg = e.response.json().get('detail', error_msg)
                    except:
                        pass
                messages.error(request, error_msg)
                if 'doc' in locals():
                    doc.delete()

            except Exception as e:
                messages.error(request, f"Ошибка загрузки: {str(e)}")
                if 'doc' in locals():
                    doc.delete()

    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})

def login_view(request):
    """Авторизация пользователя"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Неверные имя пользователя или пароль")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('home')


@login_required
def analyse_doc(request):
    #потом допишу
    return render(request, 'analyse.html')


@login_required
@permission_required('auth.delete_document', raise_exception=True)
def delete_document_view(request):
    if request.method == 'POST':
        form = DocumentDeleteForm(request.POST)
        if form.is_valid():
            doc_id = form.cleaned_data['doc_id']
        if not doc_id:
            messages.error(request, "Неверный ID документа")
            return redirect('delete_document')

        try:
            doc = Docs.objects.get(id=int(doc_id))

            # Удаление из FastAPI (по имени файла)
            try:
                file_name = os.path.basename(doc.file.name)
                resp = requests.delete(
                    f"{settings.FASTAPI_URL}/delete_doc",
                    json={"file_name": file_name},
                    timeout=10
                )
                if resp.status_code == 404:
                    messages.warning(request, "Документ не найден в FastAPI (продолжаем удаление)")
                elif resp.status_code not in (200, 204):
                    raise Exception(f"Ошибка FastAPI: {resp.text}")
            except Exception as e:
                messages.error(request, f"Ошибка при удалении из FastAPI: {str(e)}")
                return redirect('delete_document')

            # Удаление из Django
            doc.delete()

            messages.success(request, f"Документ {doc_id} успешно удалён")
            return redirect('home')

        except Docs.DoesNotExist:
            messages.error(request, f"Документ с ID {doc_id} не найден")
        except Exception as e:
            messages.error(request, f"Ошибка при удалении: {str(e)}")

    # GET запрос
    docs = Docs.objects.all().order_by('-uploaded_at')
    return render(request, 'delete_document.html', {'docs': docs})