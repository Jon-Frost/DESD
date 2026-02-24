from django import forms
from django.contrib.auth.models import User
from .models import Producer

class ProducerSignupForm(forms.ModelForm):
    # Standard User fields
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Producer
        fields = ['business_name', 'contact_name', 'email', 'phone_number', 'business_address', 'postcode']

    def save(self, commit=True):
        # Create the user first
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