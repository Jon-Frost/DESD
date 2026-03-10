from django.shortcuts import get_object_or_404, render, redirect
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

    producer_products = producer_profile.products.order_by('name')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.producer = producer_profile
            product.save()
            return redirect('add_product')
    else:
        form = ProductForm()
    
    return render(
        request,
        'marketplace/producer_add_product.html',
        {
            'form': form,
            'producer_products': producer_products,
        }
    )


def _get_logged_in_producer(user):
    try:
        return user.producer
    except Producer.DoesNotExist:
        return None


def _get_logged_in_customer(user):
    try:
        return user.customer
    except Customer.DoesNotExist:
        return None


@login_required
def producer_product_actions(request, product_id):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    product = get_object_or_404(Product, id=product_id, producer=producer_profile)
    return render(
        request,
        'marketplace/producer_product_actions.html',
        {'product': product}
    )


@login_required
def edit_product(request, product_id):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    product = get_object_or_404(Product, id=product_id, producer=producer_profile)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('add_product')
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        'marketplace/producer_edit_product.html',
        {
            'form': form,
            'product': product,
        }
    )


@login_required
def delete_product(request, product_id):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    product = get_object_or_404(Product, id=product_id, producer=producer_profile)

    if request.method == 'POST':
        product.delete()

    return redirect('add_product')


@login_required
def customer_market(request):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    products = Product.objects.select_related('producer').order_by('name')
    return render(
        request,
        'marketplace/customer_market.html',
        {'products': products}
    )