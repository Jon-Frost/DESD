from django import forms
from django.contrib.auth.models import User
from .models import Producer, Customer, Product
import datetime

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'auth-field'})

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'unit', 'stock_quantity', 'is_organic', 'allergen_information']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'allergen_information': forms.Textarea(attrs={'rows': 2}),
        }


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
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': 'Name on card'}),
        label='Card Holder Name',
    )

    # FULL CARD NUMBER - ONLY THE LAST 4 DIGITS WILL BE SAVED TO THE DATABASE
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': '1234 5678 9012 3456', 'autocomplete': 'off'}),
        label='Card Number',
    )

    # CARD EXPIRY DATE IN MM/YY FORMAT
    card_expiry = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': 'MM/YY'}),
        label='Expiry Date',
    )

    # CVV SECURITY CODE - NEVER STORED, ONLY USED FOR VALIDATION DISPLAY
    card_cvv = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={'class': 'auth-field', 'placeholder': '123', 'autocomplete': 'off'}),
        label='CVV',
    )

    def clean_card_number(self):
        # STRIP SPACES AND VALIDATE THAT THE CARD NUMBER IS NUMERIC AND 16 DIGITS
        number = self.cleaned_data['card_number'].replace(' ', '').replace('-', '')
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
        expiry = self.cleaned_data['card_expiry']
        if len(expiry) != 5 or expiry[2] != '/' or not expiry[:2].isdigit() or not expiry[3:].isdigit():
            raise forms.ValidationError('Please enter expiry in MM/YY format.')
        return expiry