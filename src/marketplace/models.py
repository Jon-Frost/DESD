from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User # Built-in security
from django.core.validators import MinLengthValidator


# Create your models here.
class Product(models.Model):
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Sustainability & Traceability features
    harvest_date = models.DateField(null=True, blank=True)
    organic_certified = models.BooleanField(default=False)
    
    # Seasonal Availability requirements
    is_available = models.BooleanField(default=True)
    
    # For easier searching
    CATEGORY_CHOICES = [
        ('VEG', 'Vegetables'),
        ('DAIRY', 'Dairy'),
        ('BAKERY', 'Bakery'),
        ('PRESERVE', 'Preserves'),
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name
    
class Producer(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    email = models.EmailField(max_length = 254)
    phone_number = PhoneNumberField(null=True, blank = True)
    business_address = models.CharField(max_length=300)
    postcode = models.CharField(max_length=7, validators=[MinLengthValidator(5)]) # Fit UK postcodes
    
class Customer(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_number = PhoneNumberField(null=True, blank = True)
    address = models.CharField(max_length=100)
    postcode = models.CharField(max_length=7, validators=[MinLengthValidator(5)]) # Fit UK postcodes
    