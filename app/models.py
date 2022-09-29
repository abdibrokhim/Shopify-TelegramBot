from django.db import models


class TGClient(models.Model):
    tg_id = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tg_id


class Product(models.Model):
    tg_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    price = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='media')
    ship = models.CharField(max_length=255)
    payment = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category


class Tariff(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    price = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Order(models.Model):
    tg_id = models.CharField(max_length=255)
    tariff = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    quantity = models.CharField(max_length=255)
    left_qty = models.CharField(max_length=255)
    price = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now=True)
    left_days = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tg_id
