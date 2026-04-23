from django import forms
from django.contrib.auth.models import User
from .models import Producer, Customer, Product, Recipe
import datetime


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data if item]
        cleaned_file = single_file_clean(data, initial)
        return [cleaned_file] if cleaned_file else []

class ProducerSignupForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Producer
        fields = ['business_name', 'contact_name', 'email', 'phone_number', 'business_address', 'postcode']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        producer = super().save(commit=False)
        producer.user = user
        if commit:
            producer.save()
        return producer

class CustomerSignupForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'address', 'postcode']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        customer = super().save(commit=False)
        customer.user = user
        if commit:
            customer.save()
        return customer

class ProducerBioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].widget.attrs.update({'class': 'auth-field', 'rows': 6})
        self.fields['bio'].label = 'About your business'

    class Meta:
        model = Producer
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 6}),
        }


class ProductForm(forms.ModelForm):
    # ALLERGEN FIELD - STORES ZERO, ONE, OR MANY
    allergens = forms.MultipleChoiceField(
        choices=Product.ALLERGEN_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'producer-allergen-select', 'size': 8}),
    )

    def clean(self):
        cleaned_data = super().clean()
        is_surplus = cleaned_data.get('is_surplus')
        discount_percent = cleaned_data.get('discount_percent') or 0

        if not is_surplus and discount_percent > 0:
            self.add_error('discount_percent', 'Discount can only be applied to surplus produce.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # PRE-POPULATE THE ALLERGEN LIST WHEN EDITING AN EXISTING PRODUCT
        if self.instance and self.instance.pk:
            self.fields['allergens'].initial = self.instance.allergens

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                # PRESERVE EXISTING CLASSES WHILE ADDING THE STANDARD AUTH FIELD CLASS
                existing_classes = field.widget.attrs.get('class', '')
                combined_classes = f"{existing_classes} auth-field".strip()
                field.widget.attrs.update({'class': combined_classes})

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'description',
            'price',
            'unit',
            'stock_quantity',
            'seasonal_from',
            'seasonal_to',
            'is_organic',
            'allergens',
            'is_surplus',
            'discount_percent',
            'image',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'discount_percent': forms.NumberInput(attrs={'min': 0, 'max': 100}),

        }

    def clean_allergens(self):
        # VALIDATE THAT ONLY SUPPORTED ALLERGEN KEYS ARE SUBMITTED
        selected_allergens = self.cleaned_data.get('allergens', [])
        valid_allergens = {choice[0] for choice in Product.ALLERGEN_CHOICES}
        return [allergen for allergen in selected_allergens if allergen in valid_allergens]

    def save(self, commit=True):
        # SAVE THE PRODUCT WITH THE SELECTED ALLERGEN LIST IN THE JSON FIELD
        product = super().save(commit=False)
        product.allergens = self.cleaned_data.get('allergens', [])
        if commit:
            product.save()
        return product


# CHECKOUT FORM - COLLECTS DELIVERY AND PAYMENT DETAILS FROM THE CUSTOMER AT CHECKOUT
class CheckoutForm(forms.Form):
    # DELIVERY ADDRESS WHERE THE ORDER SHOULD BE SENT
    delivery_address = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': 'Enter full delivery address'}),
        label='Delivery Address',
    )

    # PREFERRED DATE THE CUSTOMER WOULD LIKE TO RECEIVE THEIR ORDER
    preferred_delivery_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'auth-field', 'type': 'date'}),
        label='Preferred Delivery Date',
    )

    # CARD HOLDER NAME AS IT APPEARS ON THE CARD
    card_holder_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': 'Name on card'}),
        label='Card Holder Name',
    )

    # FULL CARD NUMBER - ONLY THE LAST 4 DIGITS WILL BE SAVED TO THE DATABASE
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': '1234 5678 9012 3456', 'autocomplete': 'off'}),
        label='Card Number',
    )

    # CARD EXPIRY DATE IN MM/YY FORMAT
    card_expiry = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': 'MM/YY'}),
        label='Expiry Date',
    )

    # CVV SECURITY CODE - NEVER STORED, ONLY USED FOR VALIDATION DISPLAY
    card_cvv = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': '123', 'autocomplete': 'off'}),
        label='CVV',
    )

    def clean_card_number(self):
        # STRIP SPACES AND VALIDATE THAT THE CARD NUMBER IS NUMERIC AND 16 DIGITS
        number = self.cleaned_data.get('card_number', '').replace(' ', '').replace('-', '')
        if not number:
            return ''
        if not number.isdigit() or len(number) != 16:
            raise forms.ValidationError('Please enter a valid 16-digit card number.')
        return number

    def clean_preferred_delivery_date(self):
        # ENSURE THE PREFERRED DELIVERY DATE IS NOT IN THE PAST
        date = self.cleaned_data['preferred_delivery_date']
        if date < datetime.date.today():
            raise forms.ValidationError('Preferred delivery date cannot be in the past.')
        return date

    def clean_card_expiry(self):
        # VALIDATE EXPIRY FORMAT IS MM/YY
        expiry = self.cleaned_data.get('card_expiry', '')
        if not expiry:
            return ''
        if len(expiry) != 5 or expiry[2] != '/' or not expiry[:2].isdigit() or not expiry[3:].isdigit():
            raise forms.ValidationError('Please enter expiry in MM/YY format.')
        return expiry
    
class RecipeForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={'class': 'auth-field', 'accept': 'image/*'}),
        label='Recipe Images (upload one or more)'
    )

    linked_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Link to your products'
    )

    def __init__(self, producer=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if producer:
            self.fields['linked_products'].queryset = Product.objects.filter(producer=producer)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs.update({'class': 'auth-field'})


    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'seasonal_tag', 'linked_products']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'ingredients': forms.Textarea(attrs={'rows': 5}),
            'instructions': forms.Textarea(attrs={'rows': 6}),
        }