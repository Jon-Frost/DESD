from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from .models import Producer, Customer, Product, BasketItem, CustomerOrder, OrderItem, RecurringOrder, RecurringOrderItem, Notification, ProductReview
from .forms import CustomerSignupForm, ProducerSignupForm, ProductForm, ProducerBioForm, CheckoutForm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from datetime import date, timedelta

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

    # MARKET FILTER INPUTS FROM QUERY STRING
    min_price_input = request.GET.get('min_price', '').strip()
    max_price_input = request.GET.get('max_price', '').strip()
    organic_input = request.GET.get('organic', 'all').strip().lower()
    category_input = request.GET.get('category', '').strip()
    allergen_inputs = request.GET.getlist('allergens')

    products = Product.objects.select_related('producer').order_by('name')

    # APPLY MIN/MAX PRICE FILTERS WHEN VALUES ARE VALID DECIMALS
    if min_price_input:
        try:
            min_price = Decimal(min_price_input)
            products = products.filter(price__gte=min_price)
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid minimum price filter value.')

    if max_price_input:
        try:
            max_price = Decimal(max_price_input)
            products = products.filter(price__lte=max_price)
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid maximum price filter value.')

    # APPLY ORGANIC STATUS FILTER
    if organic_input == 'true':
        products = products.filter(is_organic=True)
    elif organic_input == 'false':
        products = products.filter(is_organic=False)

    # APPLY CATEGORY FILTER ONLY WHEN IT MATCHES A VALID CATEGORY KEY
    valid_categories = {choice[0] for choice in Product.CATEGORY_CHOICES}
    if category_input in valid_categories:
        products = products.filter(category=category_input)

    # APPLY ALLERGEN FILTER IN REVERSE - REMOVE PRODUCTS CONTAINING ANY SELECTED ALLERGEN
    valid_allergens = {choice[0] for choice in Product.ALLERGEN_CHOICES}
    selected_allergens = [allergen for allergen in allergen_inputs if allergen in valid_allergens]
    if selected_allergens:
        allergen_query = Q()
        for allergen in selected_allergens:
            allergen_query |= Q(allergens__contains=[allergen])
        products = products.exclude(allergen_query)

    return render(
        request,
        'marketplace/customer_market.html',
        {
            'products': products,
            'category_choices': Product.CATEGORY_CHOICES,
            'allergen_choices': Product.ALLERGEN_CHOICES,
            'selected_filters': {
                'min_price': min_price_input,
                'max_price': max_price_input,
                'organic': organic_input,
                'category': category_input,
                'allergens': selected_allergens,
            },
        }
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

                # NOTIFY THE PRODUCER OF THE NEW ORDER
                Notification.objects.create(
                    user=item.product.producer.user,
                    message=f'New order #{order.id} received for {item.quantity}x {item.product.name} from {order.customer.name}. Delivery: {order.preferred_delivery_date}.'
                )

                # NOTIFY PRODUCER IF STOCK IS NOW LOW
                if item.product.stock_quantity <= item.product.low_stock_threshold:
                    Notification.objects.create(
                        user=item.product.producer.user,
                        message=f'Low stock alert: {item.product.name} only has {item.product.stock_quantity} units remaining.'
                    )

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


# ORDER HISTORY VIEW - DISPLAYS ALL PAST ORDERS FOR THE CUSTOMER
@login_required
def order_history(request):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    orders = CustomerOrder.objects.filter(
        customer=customer_profile
    ).prefetch_related('items__product__producer').order_by('-created_at')

    # ATTACH REVIEW OBJECTS TO EACH ORDER ITEM FOR TEMPLATE RENDERING
    order_item_ids = [item.id for order in orders for item in order.items.all()]
    reviews_by_order_item_id = {
        review.order_item_id: review
        for review in ProductReview.objects.filter(order_item_id__in=order_item_ids)
    }

    for order in orders:
        for item in order.items.all():
            item.customer_review = reviews_by_order_item_id.get(item.id)

    return render(
        request,
        'marketplace/order_history.html',
        {'orders': orders}
    )


# SUBMIT PRODUCT REVIEW VIEW - ALLOWS REVIEW ONLY FOR PRODUCTS THE CUSTOMER HAS PURCHASED
@login_required
def submit_product_review(request, order_item_id):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    # ENSURE THE TARGET ORDER ITEM BELONGS TO THE LOGGED-IN CUSTOMER'S ORDER HISTORY
    order_item = get_object_or_404(
        OrderItem.objects.select_related('order', 'product'),
        id=order_item_id,
        order__customer=customer_profile,
    )

    if request.method == 'POST':
        # READ AND VALIDATE RATING INPUT
        rating_raw = request.POST.get('rating', '').strip()
        comment = request.POST.get('comment', '').strip()

        try:
            rating = int(rating_raw)
        except (TypeError, ValueError):
            rating = None

        if rating not in {1, 2, 3, 4, 5}:
            messages.error(request, 'Please select a valid rating between 1 and 5.')
            return redirect('order_history')

        # CREATE OR UPDATE A REVIEW FOR THIS PURCHASED ORDER ITEM
        review, created = ProductReview.objects.get_or_create(
            order_item=order_item,
            defaults={
                'customer': customer_profile,
                'product': order_item.product,
                'rating': rating,
                'comment': comment,
            },
        )

        if review.customer_id != customer_profile.id:
            messages.error(request, 'You are not allowed to update this review.')
            return redirect('order_history')

        # SAVE UPDATED REVIEW VALUES
        review.product = order_item.product
        review.rating = rating
        review.comment = comment
        review.save()

        # CREATE A PRODUCER NOTIFICATION SO REVIEWS APPEAR IN THE NOTIFICATIONS PAGE
        if created:
            notification_message = (
                f'Review received: {customer_profile.name} rated "{order_item.product.name}" '
                f'{rating}/5 on order #{order_item.order.id}.'
            )
        else:
            notification_message = (
                f'Review updated: {customer_profile.name} changed review for "{order_item.product.name}" '
                f'to {rating}/5 on order #{order_item.order.id}.'
            )

        Notification.objects.create(
            user=order_item.product.producer.user,
            message=notification_message,
        )

        messages.success(request, f'Review saved for "{order_item.product.name}".')

    return redirect('order_history')


# PRODUCER REVIEWS VIEW - SHOWS ALL REVIEWS LEFT BY CUSTOMERS FOR THIS PRODUCER'S PRODUCTS
@login_required
def producer_reviews(request):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    # FETCH ALL REVIEWS FOR PRODUCTS OWNED BY THIS PRODUCER
    reviews = ProductReview.objects.filter(
        product__producer=producer_profile
    ).select_related(
        'customer__user',
        'product',
        'order_item__order'
    ).order_by('-created_at')

    return render(
        request,
        'marketplace/producer_reviews.html',
        {'reviews': reviews}
    )


# REORDER VIEW - ADDS ALL ITEMS FROM A PREVIOUS ORDER BACK INTO THE BASKET
@login_required
def reorder(request, order_id):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    order = get_object_or_404(CustomerOrder, id=order_id, customer=customer_profile)

    unavailable = []
    for item in order.items.select_related('product'):
        product = item.product
        if product.stock_quantity >= item.quantity:
            basket_item, created = BasketItem.objects.get_or_create(
                customer=customer_profile,
                product=product,
                defaults={'quantity': 0}
            )
            basket_item.quantity += item.quantity
            basket_item.save()
        else:
            unavailable.append(product.name)

    if unavailable:
        messages.warning(
            request,
            f'Some items were unavailable and skipped: {", ".join(unavailable)}'
        )
    else:
        messages.success(request, 'All items added to your basket.')

    return redirect('view_basket')


# DOWNLOAD RECEIPT VIEW - GENERATES A PDF RECEIPT FOR A SPECIFIC ORDER
@login_required
def download_receipt(request, order_id):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    order = get_object_or_404(CustomerOrder, id=order_id, customer=customer_profile)
    order_items = order.items.select_related('product').all()

    # CREATE PDF RESPONSE
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_order_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 50

    # HEADER
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, "Bristol Regional Food Network")
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Order Receipt")
    y -= 30

    # ORDER DETAILS
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, f"Order #: {order.id}")
    y -= 18
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Date Placed: {order.created_at.strftime('%d %B %Y')}")
    y -= 18
    p.drawString(50, y, f"Delivery Date: {order.preferred_delivery_date.strftime('%d %B %Y')}")
    y -= 18
    p.drawString(50, y, f"Delivery Address: {order.delivery_address}")
    y -= 18
    p.drawString(50, y, f"Status: {order.get_status_display()}")
    y -= 18
    p.drawString(50, y, f"Card: **** **** **** {order.card_number_last4}")
    y -= 30

    # ITEMS TABLE HEADER
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Product")
    p.drawString(250, y, "Producer")
    p.drawString(400, y, "Qty")
    p.drawString(450, y, "Unit Price")
    p.drawString(530, y, "Subtotal")
    y -= 5
    p.line(50, y, 580, y)
    y -= 18

    # ITEMS
    p.setFont("Helvetica", 10)
    for item in order_items:
        p.drawString(50, y, item.product.name[:25])
        p.drawString(250, y, item.product.producer.business_name[:20])
        p.drawString(400, y, str(item.quantity))
        p.drawString(450, y, f"£{item.unit_price}")
        p.drawString(530, y, f"£{item.get_subtotal()}")
        y -= 18

    # TOTAL
    y -= 10
    p.line(50, y, 580, y)
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(450, y, f"Total: £{order.total_price}")

    p.showPage()
    p.save()
    return response


# PRODUCER ORDERS VIEW - DISPLAYS ALL INCOMING ORDERS FOR THE PRODUCER
@login_required
def producer_orders(request):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    # GET ALL ORDER ITEMS FOR THIS PRODUCER'S PRODUCTS
    order_items = OrderItem.objects.filter(
        product__producer=producer_profile
    ).select_related(
        'order__customer', 'product'
    ).order_by('order__preferred_delivery_date')

    # GROUP ORDER ITEMS BY ORDER
    orders_dict = {}
    for item in order_items:
        order = item.order
        if order.id not in orders_dict:
            orders_dict[order.id] = {
                'order': order,
                'items': []
            }
        orders_dict[order.id]['items'].append(item)

    orders = list(orders_dict.values())

    return render(
        request,
        'marketplace/producer_orders.html',
        {'orders': orders}
    )


# UPDATE ORDER STATUS VIEW - ALLOWS PRODUCERS TO UPDATE THE STATUS OF AN ORDER
@login_required
def update_order_status(request, order_id):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    order = get_object_or_404(CustomerOrder, id=order_id)
    is_producers_order = order.items.filter(
        product__producer=producer_profile
    ).exists()

    if not is_producers_order:
        return redirect('producer_orders')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [choice[0] for choice in CustomerOrder.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            order.save()

            # NOTIFY THE CUSTOMER OF THE STATUS CHANGE
            Notification.objects.create(
                user=order.customer.user,
                message=f'Your order #{order.id} from {producer_profile.business_name} is now {order.get_status_display()}.'
            )

            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}.')

    return redirect('producer_orders')


# PAYMENT SETTLEMENTS VIEW - DISPLAYS WEEKLY PAYMENT SUMMARIES FOR THE PRODUCER
@login_required
def payment_settlements(request):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    # GET ALL DELIVERED ORDERS FOR THIS PRODUCER
    order_items = OrderItem.objects.filter(
        product__producer=producer_profile,
        order__status='DELIVERED'
    ).select_related('order', 'product').order_by('-order__created_at')

    # GROUP BY WEEK
    weeks = {}
    for item in order_items:
        order_date = item.order.created_at.date()
        week_start = order_date - timedelta(days=order_date.weekday())
        week_end = week_start + timedelta(days=6)
        week_key = week_start

        if week_key not in weeks:
            weeks[week_key] = {
                'week_start': week_start,
                'week_end': week_end,
                'items': [],
                'gross_total': 0,
                'commission': 0,
                'producer_payment': 0,
            }

        subtotal = item.get_subtotal()
        commission = round(subtotal * Decimal('0.05'), 2)
        producer_payment = round(subtotal * Decimal('0.95'), 2)

        weeks[week_key]['items'].append({
            'item': item,
            'subtotal': subtotal,
            'commission': commission,
            'producer_payment': producer_payment,
        })
        weeks[week_key]['gross_total'] += subtotal
        weeks[week_key]['commission'] += commission
        weeks[week_key]['producer_payment'] += producer_payment

    # SORT WEEKS MOST RECENT FIRST
    sorted_weeks = sorted(weeks.values(), key=lambda w: w['week_start'], reverse=True)

    # CALCULATE YEAR TO DATE TOTALS
    ytd_gross = sum(w['gross_total'] for w in sorted_weeks)
    ytd_commission = sum(w['commission'] for w in sorted_weeks)
    ytd_producer_payment = sum(w['producer_payment'] for w in sorted_weeks)

    return render(
        request,
        'marketplace/payment_settlements.html',
        {
            'weeks': sorted_weeks,
            'ytd_gross': ytd_gross,
            'ytd_commission': ytd_commission,
            'ytd_producer_payment': ytd_producer_payment,
        }
    )


# DOWNLOAD SETTLEMENT PDF VIEW - GENERATES A PDF REPORT FOR A SPECIFIC WEEK
@login_required
def download_settlement_pdf(request, week_start_str):
    producer_profile = _get_logged_in_producer(request.user)
    if producer_profile is None:
        return redirect('home')

    try:
        week_start = date.fromisoformat(week_start_str)
    except ValueError:
        return redirect('payment_settlements')

    week_end = week_start + timedelta(days=6)

    order_items = OrderItem.objects.filter(
        product__producer=producer_profile,
        order__status='DELIVERED',
        order__created_at__date__gte=week_start,
        order__created_at__date__lte=week_end,
    ).select_related('order__customer', 'product')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="settlement_{week_start_str}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, "Bristol Regional Food Network")
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Weekly Payment Settlement Report")
    y -= 18
    p.drawString(50, y, f"Producer: {producer_profile.business_name}")
    y -= 18
    p.drawString(50, y, f"Week: {week_start.strftime('%d %b %Y')} - {week_end.strftime('%d %b %Y')}")
    y -= 30

    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Order #")
    p.drawString(110, y, "Date")
    p.drawString(190, y, "Product")
    p.drawString(340, y, "Qty")
    p.drawString(380, y, "Subtotal")
    p.drawString(450, y, "Commission")
    p.drawString(530, y, "You Receive")
    y -= 5
    p.line(50, y, 580, y)
    y -= 18

    gross_total = Decimal('0.00')
    total_commission = Decimal('0.00')
    total_producer = Decimal('0.00')

    p.setFont("Helvetica", 9)
    for item in order_items:
        subtotal = item.get_subtotal()
        commission = round(subtotal * Decimal('0.05'), 2)
        producer_payment = round(subtotal * Decimal('0.95'), 2)

        gross_total += subtotal
        total_commission += commission
        total_producer += producer_payment

        p.drawString(50, y, f"#{item.order.id}")
        p.drawString(110, y, item.order.created_at.strftime('%d %b'))
        p.drawString(190, y, item.product.name[:20])
        p.drawString(340, y, str(item.quantity))
        p.drawString(380, y, f"£{subtotal}")
        p.drawString(450, y, f"£{commission}")
        p.drawString(530, y, f"£{producer_payment}")
        y -= 16

        if y < 80:
            p.showPage()
            y = height - 50

    y -= 10
    p.line(50, y, 580, y)
    y -= 20
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, f"Gross Total: £{gross_total}")
    y -= 18
    p.drawString(50, y, f"Network Commission (5%): £{total_commission}")
    y -= 18
    p.drawString(50, y, f"Your Payment (95%): £{total_producer}")

    p.showPage()
    p.save()
    return response


# SETUP RECURRING ORDER VIEW - CREATES A RECURRING ORDER FROM THE CUSTOMER'S BASKET
@login_required
def setup_recurring_order(request):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    basket_items = BasketItem.objects.filter(
        customer=customer_profile
    ).select_related('product')

    if not basket_items.exists():
        messages.error(request, 'Your basket is empty.')
        return redirect('view_basket')

    if request.method == 'POST':
        frequency = request.POST.get('frequency')
        delivery_address = request.POST.get('delivery_address')
        next_order_date = request.POST.get('next_order_date')

        valid_frequencies = [choice[0] for choice in RecurringOrder.FREQUENCY_CHOICES]
        if frequency not in valid_frequencies:
            messages.error(request, 'Invalid frequency selected.')
            return redirect('setup_recurring_order')

        try:
            next_order_date = date.fromisoformat(next_order_date)
        except ValueError:
            messages.error(request, 'Invalid date selected.')
            return redirect('setup_recurring_order')

        if next_order_date < date.today() + timedelta(days=2):
            messages.error(request, 'First delivery must be at least 48 hours from now.')
            return redirect('setup_recurring_order')

        recurring_order = RecurringOrder.objects.create(
            customer=customer_profile,
            frequency=frequency,
            delivery_address=delivery_address,
            next_order_date=next_order_date,
        )

        for item in basket_items:
            RecurringOrderItem.objects.create(
                recurring_order=recurring_order,
                product=item.product,
                quantity=item.quantity,
            )

        messages.success(
            request,
            f'Recurring {frequency.lower()} order set up successfully!'
        )
        return redirect('manage_recurring_orders')

    return render(
        request,
        'marketplace/setup_recurring_order.html',
        {
            'basket_items': basket_items,
            'frequency_choices': RecurringOrder.FREQUENCY_CHOICES,
            'delivery_address': customer_profile.address,
            'min_date': (date.today() + timedelta(days=2)).isoformat(),
        }
    )


# MANAGE RECURRING ORDERS VIEW - DISPLAYS ALL RECURRING ORDERS FOR THE CUSTOMER
@login_required
def manage_recurring_orders(request):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    recurring_orders = RecurringOrder.objects.filter(
        customer=customer_profile
    ).prefetch_related('items__product').order_by('-created_at')

    return render(
        request,
        'marketplace/manage_recurring_orders.html',
        {'recurring_orders': recurring_orders}
    )


# UPDATE RECURRING ORDER STATUS VIEW - ALLOWS CUSTOMERS TO PAUSE OR CANCEL RECURRING ORDERS
@login_required
def update_recurring_order_status(request, recurring_order_id):
    customer_profile = _get_logged_in_customer(request.user)
    if customer_profile is None:
        return redirect('home')

    recurring_order = get_object_or_404(
        RecurringOrder,
        id=recurring_order_id,
        customer=customer_profile
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [choice[0] for choice in RecurringOrder.STATUS_CHOICES]
        if new_status in valid_statuses:
            recurring_order.status = new_status
            recurring_order.save()
            messages.success(request, f'Recurring order {new_status.lower()} successfully.')

    return redirect('manage_recurring_orders')


# NOTIFICATIONS VIEW - DISPLAYS ALL NOTIFICATIONS FOR THE LOGGED-IN USER
@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # MARK ALL AS READ WHEN VIEWED
    user_notifications.filter(is_read=False).update(is_read=True)

    return render(
        request,
        'marketplace/notifications.html',
        {'notifications': user_notifications}
    )