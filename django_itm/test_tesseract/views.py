from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib import messages
from .models import Docs, UserToDocs
from .forms import UploadFileForm, LoginForm, DocumentDeleteForm
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging
logger = logging.getLogger(__name__)
# Create your views here.



def home(request):
    docs = Docs.objects.exclude(file__isnull=True).exclude(file='').all()
    return render(request, 'home.html', {'docs': docs})




MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            if uploaded_file.size > MAX_FILE_SIZE:
                messages.error(request,
                               f'Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024 * 1024)}MB')
                return render(request, 'upload.html', {'form': form})

            try:
                if isinstance(uploaded_file, InMemoryUploadedFile):
                    response = requests.post(
                        f'{settings.FASTAPI_URL}/upload_doc',
                        files={'file': (uploaded_file.name, uploaded_file)},
                        timeout=10
                    )


            except requests.RequestException as e:
                error = f"Ошибка FastAPI: {str(e)}"
                if hasattr(e, 'response'):
                    try:
                        error = e.response.json().get('detail', error)
                    except:
                        pass
                messages.error(request, error)
                return render(request, 'upload.html', {'form': form})

            try:
                response.raise_for_status()
                response_data = response.json()

                doc = Docs(
                    file=uploaded_file,
                    fastapi_id=response_data['id'],
                    fastapi_filepath=response_data['file_path'],
                    size=response_data['size'],
                    file_type=response_data.get('file_type', '')
                )
                doc.save()

                UserToDocs.objects.create(
                    user=request.user,
                    doc=doc
                )

                messages.success(request, 'Файл успешно загружен')
                return redirect('home')

            except Exception as e:
                messages.error(request, f'Ошибка обработки файла: {str(e)}')
                return render(request, 'upload.html', {'form': form})

            finally:
                pass
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
@permission_required('auth.delete_document', raise_exception=True)
def delete_document_view(request):
    if request.method == 'POST':
        form = DocumentDeleteForm(request.POST)
        if form.is_valid():
            doc_id = form.cleaned_data['doc_id']

            try:
                doc = Docs.objects.get(id=doc_id)

                try:
                    response = requests.delete(
                        f"{settings.FASTAPI_URL}/doc_delete/{doc.fastapi_id}",
                        timeout=10
                    )
                    if response.status_code == 404:
                        messages.warning(request, "Документ не найден в FastAPI (продолжаем удаление)")
                    elif response.status_code not in (200, 204):
                        raise Exception(f"Ошибка FastAPI: {response.text}")
                except Exception as e:
                    messages.error(request, f"Ошибка при удалении из FastAPI: {str(e)}")
                    return redirect('delete_document')


                doc.delete()

                messages.success(request, f"Документ {doc_id} успешно удалён")
                return redirect('home')

            except Docs.DoesNotExist:
                messages.error(request, f"Документ с ID {doc_id} не найден")
            except Exception as e:
                messages.error(request, f"Ошибка при удалении: {str(e)}")

    docs = Docs.objects.all().order_by('-uploaded_at')
    return render(request, 'delete_document.html', {'docs': docs})


def analyze_form(request):
    return render(request, 'analyze_form.html')


def get_text_form(request):
    return render(request, 'get_text_form.html')


@login_required
def analyze_document_view(request):
    if request.method == 'POST':
        doc_id = request.POST.get('doc_id')

        try:
            doc = Docs.objects.get(id=doc_id)

            try:
                response = requests.post(
                    f"{settings.FASTAPI_URL}/doc_analyse/{doc.fastapi_id}",
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                messages.success(
                    request,
                    f"Анализ документа #{doc.fastapi_id} (Django ID: {doc.id}) запущен. Task ID: {data.get('task_id')}"
                )
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Ошибка при анализе документа: {str(e)}")

            return redirect('analyze_document')

        except Docs.DoesNotExist:
            messages.error(request, f"Документ с ID {doc_id} не найден")
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")

    docs = Docs.objects.all().order_by('-uploaded_at')
    return render(request, 'analyze_document.html', {'docs': docs})


@login_required
def get_document_text_view(request):
    if request.method == 'POST':
        doc_id = request.POST.get('doc_id')

        try:
            doc = Docs.objects.get(id=doc_id)

            try:
                response = requests.get(
                    f"{settings.FASTAPI_URL}/get_text/{doc.fastapi_id}",
                    timeout=10
                )

                if response.status_code == 404:
                    messages.warning(request, f"Текст для документа #{doc.fastapi_id} не найден")
                    return redirect('get_document_text')

                response.raise_for_status()
                data = response.json()

                return render(request, 'text_result.html', {
                    'django_id': doc.id,
                    'fastapi_id': doc.fastapi_id,
                    'text': data.get('text', 'Текст не найден')
                })

            except requests.exceptions.RequestException as e:
                messages.error(request, f"Ошибка при получении текста: {str(e)}")

            return redirect('get_document_text')

        except Docs.DoesNotExist:
            messages.error(request, f"Документ с ID {doc_id} не найден")
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")

    docs = Docs.objects.all().order_by('-uploaded_at')
    return render(request, 'get_text_document.html', {'docs': docs})