from django.db import models

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