from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator

class Producer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone_number = PhoneNumberField(null=True, blank=True)
    business_address = models.CharField(max_length=300)
    postcode = models.CharField(max_length=7, validators=[MinLengthValidator(5)])

    def __str__(self):
        return self.business_name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_number = PhoneNumberField(null=True, blank=True)
    address = models.CharField(max_length=100)
    postcode = models.CharField(max_length=7, validators=[MinLengthValidator(5)])

    def __str__(self):
        return self.name

class Product(models.Model): 
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=50, help_text="e.g., per kg, per bunch")
    stock_quantity = models.PositiveIntegerField(default=0)
    is_organic = models.BooleanField(default=False)
    allergen_information = models.TextField(blank=True, null=True)
    
    CATEGORY_CHOICES = [
        ('VEG', 'Vegetables'),
        ('FRUIT', 'Fruit'),
        ('MEAT', 'Meat & Poultry'),
        ('DAIRY', 'Dairy'),
        ('BAKERY', 'Bakery'),
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.name} - {self.producer.business_name}"