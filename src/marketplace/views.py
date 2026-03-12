from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Producer, Customer, Product, BasketItem, CustomerOrder, OrderItem
from .forms import CustomerSignupForm, ProducerSignupForm, ProductForm, ProducerBioForm, CheckoutForm

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


@login_required
def producer_bio(request):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    if request.method == 'POST':
        form = ProducerBioForm(request.POST, instance=producer_profile)
        if form.is_valid():
            form.save()
            return redirect('producer_bio')
    else:
        form = ProducerBioForm(instance=producer_profile)

    return render(
        request,
        'marketplace/producer_bio.html',
        {
            'form': form,
            'producer': producer_profile,
        }
    )


@login_required
def producer_bio_public(request, producer_id):
    producer = get_object_or_404(Producer, id=producer_id)
    return render(
        request,
        'marketplace/producer_bio_public.html',
        {'producer': producer}
    )


# ADD TO BASKET VIEW - HANDLES A POST REQUEST TO ADD A PRODUCT TO THE CUSTOMER'S BASKET
@login_required
def add_to_basket(request, product_id):
    # VERIFY THE LOGGED-IN USER IS A CUSTOMER
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    # FETCH THE PRODUCT OR RETURN 404 IF IT DOES NOT EXIST
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # READ THE REQUESTED QUANTITY FROM THE FORM, DEFAULTING TO 1
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        # REJECT QUANTITIES OF ZERO OR LESS
        if quantity < 1:
            messages.error(request, 'Quantity must be at least 1.')
            return redirect('customer_market')

        # GET THE EXISTING BASKET ITEM IF PRESENT, OR PREPARE A NEW ONE
        basket_item, created = BasketItem.objects.get_or_create(
            customer=customer_profile,
            product=product,
            defaults={'quantity': 0},
        )

        # CALCULATE THE NEW TOTAL QUANTITY AFTER ADDING THE REQUESTED AMOUNT
        new_quantity = basket_item.quantity + quantity

        # PREVENT ADDING MORE ITEMS THAN ARE CURRENTLY IN STOCK
        if new_quantity > product.stock_quantity:
            available = product.stock_quantity - basket_item.quantity
            if available <= 0:
                messages.error(request, f'No more stock available for "{product.name}".')
            else:
                messages.error(
                    request,
                    f'Only {available} more unit(s) of "{product.name}" available.'
                )
            return redirect('customer_market')

        # SAVE THE UPDATED QUANTITY TO THE DATABASE
        basket_item.quantity = new_quantity
        basket_item.save()
        messages.success(request, f'Added {quantity}x "{product.name}" to your basket.')

    return redirect('customer_market')


# VIEW BASKET VIEW - DISPLAYS ALL ITEMS IN THE CUSTOMER'S BASKET AND THE CHECKOUT FORM
@login_required
def view_basket(request):
    # VERIFY THE LOGGED-IN USER IS A CUSTOMER
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    # FETCH ALL BASKET ITEMS FOR THIS CUSTOMER WITH THEIR RELATED PRODUCT DATA
    basket_items = BasketItem.objects.filter(customer=customer_profile).select_related('product')

    # CALCULATE THE GRAND TOTAL ACROSS ALL BASKET ITEMS
    total = sum(item.get_subtotal() for item in basket_items)

    # INITIALISE A BLANK CHECKOUT FORM FOR THE CUSTOMER TO FILL IN
    form = CheckoutForm()

    return render(
        request,
        'marketplace/basket.html',
        {
            'basket_items': basket_items,
            'total': total,
            'form': form,
        }
    )


# REMOVE FROM BASKET VIEW - DELETES A SINGLE ITEM FROM THE CUSTOMER'S BASKET
@login_required
def remove_from_basket(request, item_id):
    # VERIFY THE LOGGED-IN USER IS A CUSTOMER
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    # FETCH THE BASKET ITEM, ENSURING IT BELONGS TO THIS CUSTOMER
    basket_item = get_object_or_404(BasketItem, id=item_id, customer=customer_profile)

    if request.method == 'POST':
        # DELETE THE ITEM FROM THE BASKET
        basket_item.delete()
        messages.success(request, f'Removed "{basket_item.product.name}" from your basket.')

    return redirect('view_basket')


# CHECKOUT VIEW - PROCESSES THE CHECKOUT FORM AND CREATES A CONFIRMED ORDER
@login_required
def checkout(request):
    # VERIFY THE LOGGED-IN USER IS A CUSTOMER
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    # FETCH ALL CURRENT BASKET ITEMS FOR THIS CUSTOMER
    basket_items = BasketItem.objects.filter(customer=customer_profile).select_related('product')

    # REDIRECT BACK TO BASKET IF IT IS EMPTY
    if not basket_items.exists():
        messages.error(request, 'Your basket is empty.')
        return redirect('view_basket')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # RE-CHECK STOCK AVAILABILITY FOR ALL ITEMS BEFORE CONFIRMING THE ORDER
            for item in basket_items:
                if item.quantity > item.product.stock_quantity:
                    messages.error(
                        request,
                        f'Sorry, "{item.product.name}" now only has {item.product.stock_quantity} unit(s) in stock. '
                        f'Please update your basket.'
                    )
                    return redirect('view_basket')

            # CALCULATE THE TOTAL ORDER VALUE USING THE CURRENT PRODUCT PRICES
            total = sum(item.product.price * item.quantity for item in basket_items)

            # CREATE THE PARENT ORDER RECORD IN THE CUSTOMER_ORDERS TABLE
            order = CustomerOrder.objects.create(
                customer=customer_profile,
                delivery_address=form.cleaned_data['delivery_address'],
                preferred_delivery_date=form.cleaned_data['preferred_delivery_date'],
                card_holder_name=form.cleaned_data['card_holder_name'],
                # ONLY STORE THE LAST 4 DIGITS OF THE CARD NUMBER FOR SECURITY
                card_number_last4=form.cleaned_data['card_number'][-4:],
                total_price=total,
            )

            # CREATE AN ORDER ITEM RECORD FOR EACH PRODUCT AND REDUCE THE STOCK
            for item in basket_items:
                # SAVE A SNAPSHOT OF THE UNIT PRICE AT THE TIME OF PURCHASE
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                )
                # DEDUCT THE ORDERED QUANTITY FROM THE PRODUCT'S REMAINING STOCK
                item.product.stock_quantity -= item.quantity
                item.product.save()

            # CLEAR THE CUSTOMER'S BASKET NOW THAT THE ORDER HAS BEEN CONFIRMED
            basket_items.delete()

            # REDIRECT TO THE ORDER CONFIRMATION PAGE
            return redirect('order_confirmation', order_id=order.id)

        else:
            # FORM IS INVALID - RE-RENDER THE BASKET PAGE WITH ERRORS
            basket_items_list = BasketItem.objects.filter(customer=customer_profile).select_related('product')
            total = sum(item.get_subtotal() for item in basket_items_list)
            return render(
                request,
                'marketplace/basket.html',
                {
                    'basket_items': basket_items_list,
                    'total': total,
                    'form': form,
                }
            )

    return redirect('view_basket')


# ORDER CONFIRMATION VIEW - DISPLAYS A SUMMARY OF THE COMPLETED ORDER
@login_required
def order_confirmation(request, order_id):
    # VERIFY THE LOGGED-IN USER IS A CUSTOMER
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    # FETCH THE ORDER, ENSURING IT BELONGS TO THIS CUSTOMER
    order = get_object_or_404(CustomerOrder, id=order_id, customer=customer_profile)

    # FETCH ALL ITEMS ASSOCIATED WITH THIS ORDER
    order_items = order.items.select_related('product').all()

    return render(
        request,
        'marketplace/order_confirmation.html',
        {
            'order': order,
            'order_items': order_items,
        }
    )