from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Producer, Customer, Product
from .forms import CustomerSignupForm, ProducerSignupForm, ProductForm

def home(request):
    return render(request, 'marketplace/home.html')

def signup_choice(request):
    return render(request, 'marketplace/signup_choice.html')

def signup_producer(request):
    if request.method == 'POST':
        form = ProducerSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
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

@login_required
def add_product(request):
    try:
        producer_profile = request.user.producer
    except Producer.DoesNotExist:
        return redirect('home')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.producer = producer_profile
            product.save()
            return redirect('home')
    else:
        form = ProductForm()
    
    return render(request, 'marketplace/producer_add_product.html', {'form': form})