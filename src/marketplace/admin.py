from django.contrib import admin

from .models import Product
from .models import Producer
from .models import Customer


# Register your models here.

# Poduct model
admin.site.register(Product)
admin.site.register(Producer)
admin.site.register(Customer)