from django import forms
from django.contrib.auth.models import User
from .models import Producer
from .models import Customer


class ProducerSignupForm(forms.ModelForm):
    # STANDARD USER FIELDS FOR USER AUTHENTICATION AUTOMATICALLY CREATED BY DJANGO
    
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Producer
        fields = ['business_name', 'contact_name', 'email', 'phone_number', 'business_address', 'postcode']

    def save(self, commit=True):
        # LINKS THE PRODUCER SIGNUP TO THE SECURE DJANGO USER MODEL
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


# src/marketplace/forms.py


class CustomerSignupForm(forms.ModelForm):
    # STANDARD USER FIELDS FOR USER AUTHENTICATION AUTOMATICALLY CREATED BY DJANGO
    
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Customer
        
        fields = ['name', 'email', 'phone_number', 'address', 'postcode']

    def save(self, commit=True):
        # LINKS THE CUSOMTER SIGNUP TO THE SECURE DJANGO USER MODEL
        user = User.objects.create_user( # AUTOMATIC HASHING
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        # customer fields linked to the user fields
        customer = super().save(commit=False)
        customer.user = user
        if commit:
            customer.save()
        return customer