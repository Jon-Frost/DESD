from django.contrib import admin

from .models import Product
from .models import Producer
from .models import Customer

#admin.site.register(Product) # PRODUCT MODEL NOT YET FINISHED
admin.site.register(Producer)
admin.site.register(Customer)