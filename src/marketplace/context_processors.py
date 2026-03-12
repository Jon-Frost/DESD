# CONTEXT PROCESSOR TO MAKE THE BASKET ITEM COUNT AVAILABLE IN EVERY TEMPLATE
# THIS ALLOWS THE BASKET ICON IN THE TOP BAR TO DISPLAY THE CURRENT COUNT GLOBALLY

from .models import BasketItem


def basket_count(request):
    # ONLY COUNT BASKET ITEMS IF THE USER IS AUTHENTICATED
    is_customer = False
    is_producer = False

    if request.user.is_authenticated:
        try:
            # ATTEMPT TO GET THE CUSTOMER PROFILE LINKED TO THE LOGGED-IN USER
            customer = request.user.customer
            is_customer = True
            # COUNT THE TOTAL NUMBER OF DISTINCT PRODUCT LINES IN THE BASKET
            count = BasketItem.objects.filter(customer=customer).count()
        except Exception:
            # IF THE USER HAS NO CUSTOMER PROFILE, BASKET COUNT IS ZERO
            count = 0

        try:
            request.user.producer
            is_producer = True
        except Exception:
            is_producer = False
    else:
        # UNAUTHENTICATED USERS HAVE NO BASKET
        count = 0

    # RETURN THE COUNT SO IT IS AVAILABLE AS {{ basket_count }} IN ALL TEMPLATES
    return {
        'basket_count': count,
        'is_customer': is_customer,
        'is_producer': is_producer,
    }
