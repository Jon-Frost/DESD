from django import forms
from django.contrib.auth.models import User
from .models import Producer, Customer, Product

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