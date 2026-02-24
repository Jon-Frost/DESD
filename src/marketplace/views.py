from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .models import Producer, Customer
from .forms import CustomerSignupForm
# Create your views here.
def home(request):
    return render(request, 'marketplace/home.html')



def signup_choice(request):
    return render(request, 'marketplace/signup_choice.html')

from .forms import ProducerSignupForm

def signup_producer(request):
    if request.method == 'POST':
        form = ProducerSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home') # Ensure you have a login URL named 'login'
    else:
        form = ProducerSignupForm()
    return render(request, 'marketplace/signup_producer.html', {'form': form})


def signup_customer(request):
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home') 
    else:
        form = CustomerSignupForm()
    return render(request, 'marketplace/signup_customer.html', {'form': form})