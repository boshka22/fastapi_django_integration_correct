from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Docs(models.Model):
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    fastapi_id = models.IntegerField(unique=True, verbose_name='ID в FastAPI')
    fastapi_filepath = models.CharField(max_length=255, verbose_name='Путь в FastAPI')
    size = models.FloatField(verbose_name='Размер (КБ)')
    uploaded_at = models.DateTimeField(default=timezone.now, verbose_name='Дата загрузки')
    file_type = models.CharField(max_length=10, blank=True, verbose_name='Тип файла')

    def __str__(self):
        return f"{self.id} — {self.fastapi_filepath}"

    def delete(self, *args, **kwargs):
        if self.file:
            storage, path = self.file.storage, self.file.path
            super().delete(*args, **kwargs)
            storage.delete(path)
        else:
            super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-uploaded_at']


class UserToDocs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    doc = models.ForeignKey(Docs, on_delete=models.CASCADE, verbose_name='Документ')

    def __str__(self):
        return f"{self.user.username} - {self.doc}"

    class Meta:
        verbose_name = 'Связь пользователь-документ'
        verbose_name_plural = 'Связи пользователь-документ'


class Price(models.Model):
    file_type = models.CharField(max_length=10, verbose_name='Тип файла')
    price = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='Цена за КБ')

    def __str__(self):
        return f"{self.file_type} - {self.price} за КБ"

    class Meta:
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    doc = models.ForeignKey(Docs, on_delete=models.CASCADE, verbose_name='Документ')
    order_price = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='Стоимость заказа')
    payment = models.BooleanField(default=False, verbose_name='Оплачено')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"Заказ {self.id} - {self.user.username}"

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'