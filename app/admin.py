from django.contrib import admin

from .models import TGClient, Product


class TGClientAdmin(admin.ModelAdmin):
    list_display = ('tg_id', 'username', 'phone_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('tg_id', 'username', 'phone_number')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('owner', 'category', 'title', 'description', 'price', 'photo', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('owner', 'category', 'title', 'description', 'price')


admin.site.register(TGClient, TGClientAdmin)
admin.site.register(Product, ProductAdmin)
