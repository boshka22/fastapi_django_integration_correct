from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('delete-document/', views.delete_document_view, name='delete_document'),
    path('analyze/', views.analyze_document_view, name='analyze_document'),
    path('get-text/', views.get_document_text_view, name='get_document_text'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)