from django.db import models

# Create your models here.

class Docs(models.Model):
    file_path = models.CharField(max_length=255, verbose_name='Путь к документу', null=True, blank=True)
    size = models.FloatField(null=True, verbose_name='Размер файла (кб')

class UserToDocs(models.Model):
    username = models.CharField(max_length=255, verbose_name='Имя пользователя', null=True, blank=True)
    docs_id = models.ForeignKey(Docs, on_delete=models.CASCADE)
