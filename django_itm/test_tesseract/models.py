
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Docs(models.Model):
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    file_path = models.CharField(max_length=255, blank=True, null=True)
    size = models.FloatField(blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.id} — {self.file.name}"

    def delete(self, *args, **kwargs):
        # Удаляем физический файл при удалении модели
        if self.file:
            storage, path = self.file.storage, self.file.path
            super().delete(*args, **kwargs)
            storage.delete(path)
        else:
            super().delete(*args, **kwargs)
    class Meta:
        ordering = ['-uploaded_at']
class UserToDocs(models.Model):
    username = models.CharField(max_length=255, verbose_name='Имя пользователя', null=True, blank=True)
    doc = models.ForeignKey(Docs, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.username} - {self.doc}"

class Price(models.Model):
    file_type = models.CharField(max_length=10, verbose_name='Тип файла')
    price = models.DecimalField(max_digits=10,decimal_places=4, verbose_name='Цена за кб')

    def __str__(self):
        return f"{self.file_type} - {self.price} за КБ"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    doc = models.ForeignKey(Docs, on_delete=models.CASCADE, verbose_name='Документ')
    order_price = models.DecimalField(max_digits=10,decimal_places=4, verbose_name='Стоимость заказа')
    payment = models.BooleanField(default=False, verbose_name='Оплачено')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Корзина {self.id} - Пользователь {self.user.username}"