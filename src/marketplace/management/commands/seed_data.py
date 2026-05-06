from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from marketplace.models import (
    BasketItem,
    Customer,
    CustomerOrder,
    Notification,
    OrderItem,
    Producer,
    Product,
    ProductReview,
    Recipe,
    RecipeImage,
    RecurringOrder,
    RecurringOrderItem,
    RecurringOrderUpcomingItem,
)


class Command(BaseCommand):
    help = 'Seeds a realistic BRFN marketplace dataset for demonstrations/submission marking.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Seeding realistic marketplace data...'))

        with transaction.atomic():
            self._seed()

        self.stdout.write(self.style.SUCCESS('\nSeed complete. Demo credentials:'))
        self.stdout.write('  Admin:    brfn_admin / Admin@BRFN2026')
        self.stdout.write('  Producer: olivia.barnes / Harvest!2026')
        self.stdout.write('  Producer: marcus.reed / Cotswold#2026')
        self.stdout.write('  Producer: hannah.clarke / Dairy&Grain2026')
        self.stdout.write('  Customer: daniel.price / Shopper!2026')
        self.stdout.write('  Customer: aisha.khan / Basket#2026')
        self.stdout.write('  Customer: tom.watkins / FreshFood2026!')

    def _seed(self):
        today = date.today()
        self.seed_images_dir = Path(__file__).resolve().parents[2] / 'fixtures' / 'seed_images'

        usernames_to_replace = [
            'brfn_admin',
            'olivia.barnes', 'marcus.reed', 'hannah.clarke',
            'daniel.price', 'aisha.khan', 'tom.watkins',
            'admin1', 'prod1', 'prod2', 'cust1',
        ]
        User.objects.filter(username__in=usernames_to_replace).delete()

        admin = self._create_admin()
        producers = self._create_producers(today)
        customers = self._create_customers(today)
        products = self._create_products(producers)
        self._create_recipes(producers, products)

        orders = self._create_orders(today, customers, products)
        recurring_data = self._create_recurring_orders(today, customers, products)

        self._create_baskets(customers, products)
        self._create_reviews(customers, orders)
        self._create_notifications(admin, producers, customers, orders, recurring_data)

    def _aware_datetime(self, day_value, hour_value=10):
        return timezone.make_aware(datetime.combine(day_value, time(hour=hour_value, minute=0)))

    def _create_admin(self):
        admin = User.objects.create_superuser(
            username='brfn_admin',
            email='admin@brfn.co.uk',
            password='Admin@BRFN2026',
        )
        User.objects.filter(id=admin.id).update(date_joined=self._aware_datetime(date.today() - timedelta(days=120), 9))
        self.stdout.write('Created admin account: brfn_admin')
        return admin

    def _create_producers(self, today):
        producer_data = [
            {
                'username': 'olivia.barnes',
                'password': 'Harvest!2026',
                'email': 'olivia@bristolgreens.co.uk',
                'business_name': 'Bristol Greens Cooperative',
                'contact_name': 'Olivia Barnes',
                'phone_number': '+441179000111',
                'business_address': '12 Stokes Croft, Bristol',
                'postcode': 'BS13QY',
                'bio': 'Urban market garden collective focused on organic seasonal vegetables and herbs.',
                'joined_days_ago': 95,
            },
            {
                'username': 'marcus.reed',
                'password': 'Cotswold#2026',
                'email': 'marcus@reedorchards.co.uk',
                'business_name': 'Reed Orchard & Meats',
                'contact_name': 'Marcus Reed',
                'phone_number': '+441179000222',
                'business_address': '4 Ashton Road, Bristol',
                'postcode': 'BS31JD',
                'bio': 'Family-run orchard and small livestock producer supplying fruit, preserves, and free-range meat.',
                'joined_days_ago': 82,
            },
            {
                'username': 'hannah.clarke',
                'password': 'Dairy&Grain2026',
                'email': 'hannah@clarkefarmdairy.co.uk',
                'business_name': 'Clarke Farm Dairy & Bakery',
                'contact_name': 'Hannah Clarke',
                'phone_number': '+441179000333',
                'business_address': '28 Gloucester Road, Bristol',
                'postcode': 'BS72AB',
                'bio': 'Artisan dairy and bakery supplying local milk, cheeses, yoghurts, and fresh loaves.',
                'joined_days_ago': 70,
            },
        ]

        producers = {}
        for row in producer_data:
            user = User.objects.create_user(
                username=row['username'],
                email=row['email'],
                password=row['password'],
            )
            User.objects.filter(id=user.id).update(
                date_joined=self._aware_datetime(today - timedelta(days=row['joined_days_ago']), 11)
            )

            producer = Producer.objects.create(
                user=user,
                business_name=row['business_name'],
                contact_name=row['contact_name'],
                email=row['email'],
                phone_number=row['phone_number'],
                business_address=row['business_address'],
                postcode=row['postcode'],
                bio=row['bio'],
            )
            producers[row['username']] = producer
            self.stdout.write(f'Created producer: {row["username"]}')

        return producers

    def _create_customers(self, today):
        customer_data = [
            {
                'username': 'daniel.price',
                'password': 'Shopper!2026',
                'email': 'daniel.price@email.com',
                'name': 'Daniel Price',
                'phone_number': '+447700910101',
                'address': '18 Park Row, Bristol',
                'postcode': 'BS15LT',
                'joined_days_ago': 63,
            },
            {
                'username': 'aisha.khan',
                'password': 'Basket#2026',
                'email': 'aisha.khan@email.com',
                'name': 'Aisha Khan',
                'phone_number': '+447700920202',
                'address': '91 Redland Road, Bristol',
                'postcode': 'BS66UP',
                'joined_days_ago': 41,
            },
            {
                'username': 'tom.watkins',
                'password': 'FreshFood2026!',
                'email': 'tom.watkins@email.com',
                'name': 'Tom Watkins',
                'phone_number': '+447700930303',
                'address': '7 North Street, Bedminster, Bristol',
                'postcode': 'BS39TS',
                'joined_days_ago': 22,
            },
        ]

        customers = {}
        for row in customer_data:
            user = User.objects.create_user(
                username=row['username'],
                email=row['email'],
                password=row['password'],
            )
            User.objects.filter(id=user.id).update(
                date_joined=self._aware_datetime(today - timedelta(days=row['joined_days_ago']), 12)
            )

            customer = Customer.objects.create(
                user=user,
                name=row['name'],
                email=row['email'],
                phone_number=row['phone_number'],
                address=row['address'],
                postcode=row['postcode'],
            )
            customers[row['username']] = customer
            self.stdout.write(f'Created customer: {row["username"]}')

        return customers

    def _create_products(self, producers):
        product_rows = [
            {
                'key': 'kale',
                'producer': producers['olivia.barnes'],
                'name': 'Organic Kale',
                'category': 'VEG',
                'description': 'Dark leafy kale harvested twice weekly from raised beds.',
                'price': '2.40',
                'unit': 'per bunch',
                'stock_quantity': 18,
                'is_organic': True,
                'allergens': [],
                'seasonal_from': 'AUTUMN',
                'seasonal_to': 'SPRING',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'organic-kale.jpg',
            },
            {
                'key': 'rainbow_carrots',
                'producer': producers['olivia.barnes'],
                'name': 'Rainbow Carrots',
                'category': 'VEG',
                'description': 'Mixed heritage carrots ideal for roasting and soups.',
                'price': '1.90',
                'unit': 'per kg',
                'stock_quantity': 42,
                'is_organic': True,
                'allergens': [],
                'seasonal_from': 'SUMMER',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'rainbow-carrots.jpg',
            },
            {
                'key': 'courgette_surplus',
                'producer': producers['olivia.barnes'],
                'name': 'Courgette (Surplus)',
                'category': 'VEG',
                'description': 'Oversupply from this week’s harvest; perfect for grilling.',
                'price': '1.80',
                'unit': 'per kg',
                'stock_quantity': 36,
                'is_organic': True,
                'allergens': [],
                'seasonal_from': 'SUMMER',
                'seasonal_to': 'AUTUMN',
                'is_surplus': True,
                'discount_percent': 25,
                'low_stock_threshold': 10,
                'image': 'courgette-surplus.jpg',
            },
            {
                'key': 'spinach',
                'producer': producers['olivia.barnes'],
                'name': 'Baby Spinach',
                'category': 'VEG',
                'description': 'Tender baby spinach leaves washed and packed same day.',
                'price': '2.10',
                'unit': 'per bag',
                'stock_quantity': 9,
                'is_organic': True,
                'allergens': [],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'AUTUMN',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'baby-spinach.jpg',
            },
            {
                'key': 'apples',
                'producer': producers['marcus.reed'],
                'name': 'Braeburn Apples',
                'category': 'FRUIT',
                'description': 'Hand-picked Braeburn apples from our local orchard.',
                'price': '2.60',
                'unit': 'per kg',
                'stock_quantity': 28,
                'is_organic': False,
                'allergens': [],
                'seasonal_from': 'AUTUMN',
                'seasonal_to': 'SPRING',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'braeburn-apples.jpg',
            },
            {
                'key': 'pear_surplus',
                'producer': producers['marcus.reed'],
                'name': 'Conference Pears (Surplus)',
                'category': 'FRUIT',
                'description': 'Ripe pears near end of shelf life offered at reduced price.',
                'price': '2.20',
                'unit': 'per kg',
                'stock_quantity': 24,
                'is_organic': False,
                'allergens': [],
                'seasonal_from': 'AUTUMN',
                'seasonal_to': 'WINTER',
                'is_surplus': True,
                'discount_percent': 30,
                'low_stock_threshold': 10,
                'image': 'conference-pears.jpg',
            },
            {
                'key': 'strawberry_jam',
                'producer': producers['marcus.reed'],
                'name': 'Small-Batch Strawberry Jam',
                'category': 'BAKERY',
                'description': 'No-additive preserve made with orchard fruit and less sugar.',
                'price': '4.20',
                'unit': 'per jar',
                'stock_quantity': 15,
                'is_organic': False,
                'allergens': [],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'small-batch-strawberry-jam.jpg',
            },
            {
                'key': 'chicken',
                'producer': producers['marcus.reed'],
                'name': 'Free-Range Chicken Thighs',
                'category': 'MEAT',
                'description': 'Locally reared free-range chicken portions.',
                'price': '6.80',
                'unit': 'per 500g',
                'stock_quantity': 7,
                'is_organic': False,
                'allergens': [],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'free-range-chicken-thighs.jpg',
            },
            {
                'key': 'whole_milk',
                'producer': producers['hannah.clarke'],
                'name': 'Whole Milk',
                'category': 'DAIRY',
                'description': 'Pasteurised whole milk from grass-fed herd.',
                'price': '1.45',
                'unit': 'per litre',
                'stock_quantity': 33,
                'is_organic': False,
                'allergens': ['MILK'],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'whole-milk.jpg',
            },
            {
                'key': 'greek_yoghurt',
                'producer': producers['hannah.clarke'],
                'name': 'Greek-Style Yoghurt',
                'category': 'DAIRY',
                'description': 'Thick strained yoghurt with high protein.',
                'price': '2.85',
                'unit': 'per 500g',
                'stock_quantity': 19,
                'is_organic': False,
                'allergens': ['MILK'],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'greek-style-yogurt.jpg',
            },
            {
                'key': 'sourdough_surplus',
                'producer': producers['hannah.clarke'],
                'name': 'Sourdough Loaf (Surplus)',
                'category': 'BAKERY',
                'description': 'Fresh sourdough from today’s surplus bake.',
                'price': '3.40',
                'unit': 'per loaf',
                'stock_quantity': 22,
                'is_organic': False,
                'allergens': ['GLUTEN'],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': True,
                'discount_percent': 20,
                'low_stock_threshold': 10,
                'image': 'sourdough-loaf-surplus.jpg',
            },
            {
                'key': 'cheddar',
                'producer': producers['hannah.clarke'],
                'name': 'Mature Cheddar',
                'category': 'DAIRY',
                'description': 'Aged cheddar from local milk, crumbly and sharp.',
                'price': '4.90',
                'unit': 'per 250g',
                'stock_quantity': 8,
                'is_organic': False,
                'allergens': ['MILK'],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'mature-cheddar.jpg',
            },
            {
                'key': 'brown_eggs',
                'producer': producers['hannah.clarke'],
                'name': 'Brown Eggs',
                'category': 'DAIRY',
                'description': 'Free-range eggs from mixed heritage hens.',
                'price': '3.10',
                'unit': 'per dozen',
                'stock_quantity': 26,
                'is_organic': False,
                'allergens': ['EGGS'],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'brown-eggs.jpg',
            },
            {
                'key': 'beetroot',
                'producer': producers['olivia.barnes'],
                'name': 'Golden Beetroot',
                'category': 'VEG',
                'description': 'Sweet golden beetroot ideal for roasting and pickling.',
                'price': '2.20',
                'unit': 'per bunch',
                'stock_quantity': 14,
                'is_organic': True,
                'allergens': [],
                'seasonal_from': 'SUMMER',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'golden-beetroot.jpg',
            },
            {
                'key': 'lamb_mince',
                'producer': producers['marcus.reed'],
                'name': 'Pasture-Raised Lamb Mince',
                'category': 'MEAT',
                'description': 'Lean lamb mince from pasture-raised lamb.',
                'price': '7.20',
                'unit': 'per 500g',
                'stock_quantity': 11,
                'is_organic': False,
                'allergens': [],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'pasture-raised-lamb-mince.jpg',
            },
            {
                'key': 'baguette',
                'producer': producers['hannah.clarke'],
                'name': 'Stone-Baked Baguette',
                'category': 'BAKERY',
                'description': 'Crisp crust baguette baked fresh every morning.',
                'price': '2.30',
                'unit': 'per loaf',
                'stock_quantity': 13,
                'is_organic': False,
                'allergens': ['GLUTEN'],
                'seasonal_from': 'SPRING',
                'seasonal_to': 'WINTER',
                'is_surplus': False,
                'discount_percent': 0,
                'low_stock_threshold': 10,
                'image': 'stone-baked-baguette.jpg',
            },
        ]

        products = {}
        product_images_attached = 0
        for row in product_rows:
            product = Product.objects.create(
                producer=row['producer'],
                name=row['name'],
                category=row['category'],
                description=row['description'],
                price=Decimal(row['price']),
                unit=row['unit'],
                stock_quantity=row['stock_quantity'],
                low_stock_threshold=row['low_stock_threshold'],
                is_organic=row['is_organic'],
                allergens=row['allergens'],
                seasonal_from=row['seasonal_from'],
                seasonal_to=row['seasonal_to'],
                is_surplus=row['is_surplus'],
                discount_percent=row['discount_percent'],
            )
            if self._attach_image_file(product, 'image', row.get('image')):
                product_images_attached += 1
            products[row['key']] = product

        self.stdout.write(f'Created {len(products)} marketplace products.')
        self.stdout.write(f'Attached {product_images_attached} product images.')
        return products

    def _create_recipes(self, producers, products):
        recipes = [
            {
                'producer': producers['olivia.barnes'],
                'title': 'Roasted Rainbow Veg Traybake',
                'description': 'Seasonal traybake using carrots, beetroot, and courgette.',
                'ingredients': 'Rainbow Carrots\nGolden Beetroot\nCourgette\nOlive oil\nSea salt',
                'instructions': '1. Chop vegetables.\n2. Toss with oil and seasoning.\n3. Roast at 200C for 35 minutes.',
                'seasonal_tag': 'AUTUMN',
                'linked': ['rainbow_carrots', 'beetroot', 'courgette_surplus'],
                'images': ['rainbow-veg-tray-bake-recipe.jpg'],
            },
            {
                'producer': producers['marcus.reed'],
                'title': 'Apple & Pear Crumble',
                'description': 'Classic crumble with orchard fruit.',
                'ingredients': 'Braeburn Apples\nConference Pears\nFlour\nButter\nSugar',
                'instructions': '1. Slice fruit.\n2. Prepare crumble mix.\n3. Bake until golden.',
                'seasonal_tag': 'AUTUMN',
                'linked': ['apples', 'pear_surplus'],
                'images': ['apple-pear-crumble-recipe-1.jpg', 'apple-pear-crumble-recipe-2.jpg'],
            },
            {
                'producer': producers['hannah.clarke'],
                'title': 'Cheddar & Egg Breakfast Muffin',
                'description': 'Quick protein breakfast with local eggs and cheddar.',
                'ingredients': 'Brown Eggs\nMature Cheddar\nStone-Baked Baguette\nButter',
                'instructions': '1. Toast sliced baguette.\n2. Scramble eggs.\n3. Add cheddar and serve.',
                'seasonal_tag': 'ALL',
                'linked': ['brown_eggs', 'cheddar', 'baguette'],
                'images': ['cheddar-egg-breakfast-muffin-recipe.jpg'],
            },
        ]

        recipe_images_attached = 0
        for row in recipes:
            recipe = Recipe.objects.create(
                producer=row['producer'],
                title=row['title'],
                description=row['description'],
                ingredients=row['ingredients'],
                instructions=row['instructions'],
                seasonal_tag=row['seasonal_tag'],
            )
            recipe.linked_products.set([products[key] for key in row['linked']])

            image_files = row.get('images', [])
            if image_files:
                if self._attach_image_file(recipe, 'image', image_files[0]):
                    recipe_images_attached += 1

                for image_name in image_files:
                    image_path = self.seed_images_dir / image_name
                    if not image_path.exists():
                        self.stdout.write(self.style.WARNING(f'Missing recipe image file: {image_name}'))
                        continue
                    with image_path.open('rb') as image_handle:
                        recipe_image = RecipeImage(recipe=recipe)
                        recipe_image.image.save(image_path.name, File(image_handle), save=True)
                        recipe_images_attached += 1

        self.stdout.write(f'Created {len(recipes)} recipes with linked products.')
        self.stdout.write(f'Attached {recipe_images_attached} recipe image files.')

    def _attach_image_file(self, model_obj, field_name, image_name):
        if not image_name:
            return False

        image_path = self.seed_images_dir / image_name
        if not image_path.exists():
            self.stdout.write(self.style.WARNING(f'Missing image file: {image_name}'))
            return False

        with image_path.open('rb') as image_handle:
            image_field = getattr(model_obj, field_name)
            image_field.save(image_path.name, File(image_handle), save=False)

        model_obj.save(update_fields=[field_name])
        return True

    def _create_order(self, customer, line_items, status, created_days_ago, preferred_delivery_offset_days=2, source_recurring=None, source_scheduled_for=None):
        total_price = Decimal('0.00')
        for product, quantity in line_items:
            total_price += product.discounted_price * quantity

        order = CustomerOrder.objects.create(
            customer=customer,
            source_recurring_order=source_recurring,
            source_scheduled_for=source_scheduled_for,
            delivery_address=customer.address,
            preferred_delivery_date=date.today() - timedelta(days=created_days_ago - preferred_delivery_offset_days),
            card_holder_name=customer.name,
            card_number_last4='4242',
            total_price=total_price,
            status=status,
        )

        for product, quantity in line_items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.discounted_price,
            )
            if quantity <= product.stock_quantity:
                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])

        created_day = date.today() - timedelta(days=created_days_ago)
        CustomerOrder.objects.filter(id=order.id).update(created_at=self._aware_datetime(created_day, 14))
        order.refresh_from_db()
        return order

    def _create_orders(self, today, customers, products):
        order_map = {}

        order_map['week_3_delivered_a'] = self._create_order(
            customer=customers['daniel.price'],
            line_items=[
                (products['rainbow_carrots'], 2),
                (products['whole_milk'], 1),
                (products['apples'], 1),
            ],
            status='DELIVERED',
            created_days_ago=20,
            preferred_delivery_offset_days=2,
        )
        order_map['week_3_delivered_b'] = self._create_order(
            customer=customers['aisha.khan'],
            line_items=[
                (products['sourdough_surplus'], 2),
                (products['brown_eggs'], 1),
                (products['pear_surplus'], 1),
            ],
            status='DELIVERED',
            created_days_ago=18,
            preferred_delivery_offset_days=2,
        )

        order_map['week_2_delivered_a'] = self._create_order(
            customer=customers['tom.watkins'],
            line_items=[
                (products['kale'], 2),
                (products['chicken'], 1),
                (products['greek_yoghurt'], 1),
            ],
            status='DELIVERED',
            created_days_ago=13,
            preferred_delivery_offset_days=2,
        )
        order_map['week_2_delivered_b'] = self._create_order(
            customer=customers['daniel.price'],
            line_items=[
                (products['beetroot'], 1),
                (products['cheddar'], 1),
                (products['apples'], 2),
            ],
            status='DELIVERED',
            created_days_ago=11,
            preferred_delivery_offset_days=2,
        )

        order_map['week_1_delivered_a'] = self._create_order(
            customer=customers['aisha.khan'],
            line_items=[
                (products['courgette_surplus'], 3),
                (products['whole_milk'], 2),
                (products['baguette'], 1),
            ],
            status='DELIVERED',
            created_days_ago=6,
            preferred_delivery_offset_days=1,
        )
        order_map['week_1_delivered_b'] = self._create_order(
            customer=customers['tom.watkins'],
            line_items=[
                (products['lamb_mince'], 1),
                (products['spinach'], 1),
                (products['strawberry_jam'], 1),
            ],
            status='DELIVERED',
            created_days_ago=4,
            preferred_delivery_offset_days=1,
        )

        order_map['incoming_pending'] = self._create_order(
            customer=customers['daniel.price'],
            line_items=[
                (products['kale'], 1),
                (products['sourdough_surplus'], 1),
            ],
            status='PENDING',
            created_days_ago=1,
            preferred_delivery_offset_days=3,
        )
        order_map['incoming_confirmed'] = self._create_order(
            customer=customers['aisha.khan'],
            line_items=[
                (products['apples'], 1),
                (products['cheddar'], 1),
            ],
            status='CONFIRMED',
            created_days_ago=1,
            preferred_delivery_offset_days=4,
        )
        order_map['incoming_ready'] = self._create_order(
            customer=customers['tom.watkins'],
            line_items=[
                (products['whole_milk'], 2),
                (products['rainbow_carrots'], 1),
            ],
            status='READY',
            created_days_ago=0,
            preferred_delivery_offset_days=2,
        )

        self.stdout.write(f'Created {len(order_map)} one-off orders across delivered and incoming states.')
        return order_map

    def _create_recurring_orders(self, today, customers, products):
        recurring = RecurringOrder.objects.create(
            customer=customers['aisha.khan'],
            frequency='WEEKLY',
            recurrence_day=0,
            delivery_week_offset=0,
            delivery_day=2,
            delivery_address=customers['aisha.khan'].address,
            next_order_date=today + timedelta(days=7),
            status='ACTIVE',
        )

        RecurringOrderItem.objects.create(recurring_order=recurring, product=products['whole_milk'], quantity=2)
        RecurringOrderItem.objects.create(recurring_order=recurring, product=products['sourdough_surplus'], quantity=1)
        RecurringOrderItem.objects.create(recurring_order=recurring, product=products['apples'], quantity=2)

        RecurringOrderUpcomingItem.objects.create(
            recurring_order=recurring,
            product=products['whole_milk'],
            scheduled_for=recurring.next_order_date,
            quantity=3,
        )

        generated_order = self._create_order(
            customer=customers['aisha.khan'],
            line_items=[
                (products['whole_milk'], 2),
                (products['sourdough_surplus'], 1),
                (products['apples'], 1),
            ],
            status='DELIVERED',
            created_days_ago=9,
            preferred_delivery_offset_days=2,
            source_recurring=recurring,
            source_scheduled_for=today - timedelta(days=9),
        )

        self.stdout.write('Created recurring template, upcoming override, and one generated recurring order.')
        return {
            'template': recurring,
            'generated_order': generated_order,
        }

    def _create_baskets(self, customers, products):
        BasketItem.objects.create(customer=customers['daniel.price'], product=products['greek_yoghurt'], quantity=1)
        BasketItem.objects.create(customer=customers['daniel.price'], product=products['beetroot'], quantity=2)

        BasketItem.objects.create(customer=customers['aisha.khan'], product=products['kale'], quantity=1)
        BasketItem.objects.create(customer=customers['aisha.khan'], product=products['pear_surplus'], quantity=2)

        BasketItem.objects.create(customer=customers['tom.watkins'], product=products['brown_eggs'], quantity=1)
        BasketItem.objects.create(customer=customers['tom.watkins'], product=products['baguette'], quantity=2)

        self.stdout.write('Created basket items for all three customers.')

    def _create_reviews(self, customers, orders):
        delivered_for_reviews = [
            ('daniel.price', orders['week_3_delivered_a'], 5, 'Great freshness and quality across all items.'),
            ('aisha.khan', orders['week_2_delivered_b'], 4, 'Very good produce; delivery was on time.'),
            ('tom.watkins', orders['week_1_delivered_b'], 5, 'Excellent lamb mince and very fresh spinach.'),
        ]

        for username, order, rating, comment in delivered_for_reviews:
            item = order.items.first()
            if item is None:
                continue
            ProductReview.objects.create(
                customer=customers[username],
                product=item.product,
                order_item=item,
                rating=rating,
                comment=comment,
                is_anonymous=False,
            )

        self.stdout.write('Created sample product reviews from delivered orders.')

    def _create_notifications(self, admin, producers, customers, orders, recurring_data):
        # Producer notifications (order events + low stock warnings)
        for order in orders.values():
            for item in order.items.select_related('product__producer').all():
                Notification.objects.create(
                    user=item.product.producer.user,
                    message=(
                        f'New order #{order.id} includes {item.quantity}x {item.product.name} '
                        f'for delivery on {order.preferred_delivery_date}.'
                    ),
                    is_read=False,
                )

        low_stock_products = Product.objects.filter(stock_quantity__lte=10).select_related('producer__user')
        for product in low_stock_products:
            Notification.objects.create(
                user=product.producer.user,
                message=f'Low stock alert: {product.name} has {product.stock_quantity} units remaining.',
                is_read=False,
            )

        # Customer notifications (status updates and recurring activity)
        Notification.objects.create(
            user=customers['daniel.price'].user,
            message=f'Your order #{orders["incoming_pending"].id} is currently Pending and awaiting producer confirmation.',
            is_read=False,
        )
        Notification.objects.create(
            user=customers['aisha.khan'].user,
            message=(
                f'Your recurring order is active. Next run: '
                f'{recurring_data["template"].next_order_date}.'
            ),
            is_read=False,
        )
        Notification.objects.create(
            user=customers['tom.watkins'].user,
            message=f'Order #{orders["week_1_delivered_b"].id} has been marked Delivered. You can now leave a review.',
            is_read=True,
        )

        # Admin notifications (reporting cues)
        Notification.objects.create(
            user=admin,
            message='Weekly financial report ready: delivered orders and commissions are available for the past 3 weeks.',
            is_read=False,
        )
        Notification.objects.create(
            user=admin,
            message='Platform usage report updated with new producer and customer signups this month.',
            is_read=False,
        )

        self.stdout.write('Created producer/customer/admin notifications.')
