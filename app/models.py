from django.db import models


class TGClient(models.Model):
    tg_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tg_id


class Product(models.Model):
    owner = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    price = models.FloatField()
    photo = models.ImageField(upload_to='products')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

