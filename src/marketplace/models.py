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
    bio = models.TextField(blank=True)

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
    # STRUCTURED ALLERGEN LIST - STORES ZERO OR MORE OF THE UK MAJOR ALLERGEN KEYS
    allergens = models.JSONField(default=list, blank=True)
    
    CATEGORY_CHOICES = [
        ('VEG', 'Vegetables'),
        ('FRUIT', 'Fruit'),
        ('MEAT', 'Meat & Poultry'),
        ('DAIRY', 'Dairy'),
        ('BAKERY', 'Bakery'),
    ]

    # UK MAJOR ALLERGEN CHOICES USED FOR PRODUCER CHECKBOX INPUTS AND CUSTOMER FILTERING
    ALLERGEN_CHOICES = [
        ('CELERY', 'Celery'),
        ('GLUTEN', 'Cereals containing gluten'),
        ('CRUSTACEANS', 'Crustaceans'),
        ('EGGS', 'Eggs'),
        ('FISH', 'Fish'),
        ('LUPIN', 'Lupin'),
        ('MILK', 'Milk'),
        ('MOLLUSCS', 'Molluscs'),
        ('NUTS', 'Nuts'),
        ('MUSTARD', 'Mustard'),
        ('PEANUTS', 'Peanuts'),
        ('SESAME', 'Sesame'),
        ('SOYBEANS', 'Soybeans'),
        ('SULPHITES', 'Sulphur dioxide and sulphites'),
    ]

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.name} - {self.producer.business_name}"

    def get_allergen_labels(self):
        # MAP STORED ALLERGEN KEYS TO DISPLAY LABELS FOR TEMPLATE OUTPUT
        label_map = dict(self.ALLERGEN_CHOICES)
        return [label_map[key] for key in self.allergens if key in label_map]


# BASKET ITEM MODEL - REPRESENTS A SINGLE PRODUCT SITTING IN A CUSTOMER'S BASKET BEFORE CHECKOUT
class BasketItem(models.Model):
    # LINK TO THE CUSTOMER WHO OWNS THIS BASKET ENTRY
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='basket_items')
    # LINK TO THE PRODUCT BEING HELD IN THE BASKET
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='basket_items')
    # HOW MANY UNITS OF THE PRODUCT THE CUSTOMER WANTS
    quantity = models.PositiveIntegerField(default=1)
    # TIMESTAMP FOR WHEN THE ITEM WAS ADDED
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # PREVENT DUPLICATE ENTRIES - ONE ROW PER CUSTOMER+PRODUCT PAIR
        unique_together = ('customer', 'product')

    def get_subtotal(self):
        # CALCULATE THE LINE TOTAL FOR THIS BASKET ITEM
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.customer.name}'s basket"


# CUSTOMER ORDER MODEL - REPRESENTS A CONFIRMED ORDER STORED IN THE DATABASE
class CustomerOrder(models.Model):
    # LINK TO THE CUSTOMER WHO PLACED THE ORDER
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    # TIMESTAMP AUTOMATICALLY SET WHEN THE ORDER IS CREATED
    created_at = models.DateTimeField(auto_now_add=True)
    # DELIVERY DETAILS ENTERED BY THE CUSTOMER AT CHECKOUT
    delivery_address = models.CharField(max_length=300)
    preferred_delivery_date = models.DateField()
    # CARD HOLDER NAME FOR REFERENCE
    card_holder_name = models.CharField(max_length=100)
    # ONLY THE LAST 4 DIGITS ARE STORED - FULL CARD NUMBERS ARE NEVER PERSISTED
    card_number_last4 = models.CharField(max_length=4)
    # TOTAL VALUE OF THE ORDER CALCULATED AT CHECKOUT
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # ORDER STATUS CHOICES
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('READY', 'Ready for Delivery'),
        ('DELIVERED', 'Delivered'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name} on {self.created_at.date()}"


# ORDER ITEM MODEL - REPRESENTS A SINGLE PRODUCT LINE WITHIN A CONFIRMED ORDER
class OrderItem(models.Model):
    # LINK BACK TO THE PARENT ORDER
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items')
    # LINK TO THE PRODUCT THAT WAS ORDERED
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    # QUANTITY ORDERED
    quantity = models.PositiveIntegerField()
    # SNAPSHOT THE PRICE AT TIME OF PURCHASE SO PRICE CHANGES DON'T AFFECT HISTORICAL ORDERS
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal(self):
        # CALCULATE THE SUBTOTAL FOR THIS ORDER LINE
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.id})"