
from django.contrib import admin
from .models import Product, CustomerProfile, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount', 'stock')


admin.site.register(CustomerProfile)
admin.site.register(Order)