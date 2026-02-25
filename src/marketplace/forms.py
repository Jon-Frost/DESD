from django import forms
from django.contrib.auth.models import User
from .models import Producer
from .models import Customer


class ProducerSignupForm(forms.ModelForm):
    # Standard User fields
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
        # Link the producer profile to that user
        producer = super().save(commit=False)
        producer.user = user
        if commit:
            producer.save()
        return producer


# src/marketplace/forms.py


class CustomerSignupForm(forms.ModelForm):
    # Credentials
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Customer
        
        fields = ['name', 'email', 'phone_number', 'address', 'postcode']

    def save(self, commit=True):
        # Auth User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        # Customer Profile
        customer = super().save(commit=False)
        customer.user = user
        if commit:
            customer.save()
        return customer