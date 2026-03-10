from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Customer, Producer, Product


class AddProductViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='producer1', password='testpass123')
        self.other_user = User.objects.create_user(username='producer2', password='testpass123')

        self.producer = Producer.objects.create(
            user=self.user,
            business_name='Green Farm',
            contact_name='Alice Grower',
            email='alice@example.com',
            business_address='1 Market Lane',
            postcode='BS11AA'
        )
        self.other_producer = Producer.objects.create(
            user=self.other_user,
            business_name='River Farm',
            contact_name='Bob Grower',
            email='bob@example.com',
            business_address='2 River Street',
            postcode='BS22BB'
        )

    def test_add_product_page_shows_only_logged_in_producer_products(self):
        own_product = Product.objects.create(
            producer=self.producer,
            name='Carrots',
            category='VEG',
            description='Fresh carrots',
            price='2.50',
            unit='per kg',
            stock_quantity=10,
            is_organic=True
        )
        Product.objects.create(
            producer=self.other_producer,
            name='Milk',
            category='DAIRY',
            description='Fresh milk',
            price='1.80',
            unit='per bottle',
            stock_quantity=5,
            is_organic=False
        )

        self.client.login(username='producer1', password='testpass123')
        response = self.client.get(reverse('add_product'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_product.name)
        self.assertNotContains(response, 'Milk')
        self.assertEqual(list(response.context['producer_products']), [own_product])

    def test_add_product_post_redirects_back_to_add_product(self):
        self.client.login(username='producer1', password='testpass123')

        response = self.client.post(
            reverse('add_product'),
            {
                'name': 'Apples',
                'category': 'FRUIT',
                'description': 'Sweet apples',
                'price': '3.25',
                'unit': 'per kg',
                'stock_quantity': 12,
                'is_organic': 'on',
                'allergen_information': '',
            }
        )

        self.assertRedirects(response, reverse('add_product'))
        self.assertTrue(Product.objects.filter(name='Apples', producer=self.producer).exists())

    def test_product_actions_page_only_allows_product_owner(self):
        owned_product = Product.objects.create(
            producer=self.producer,
            name='Spinach',
            category='VEG',
            description='Fresh spinach',
            price='2.10',
            unit='per bunch',
            stock_quantity=9,
            is_organic=True
        )
        other_product = Product.objects.create(
            producer=self.other_producer,
            name='Cheese',
            category='DAIRY',
            description='Local cheese',
            price='4.20',
            unit='per block',
            stock_quantity=6,
            is_organic=False
        )

        self.client.login(username='producer1', password='testpass123')
        owned_response = self.client.get(reverse('producer_product_actions', args=[owned_product.id]))
        forbidden_response = self.client.get(reverse('producer_product_actions', args=[other_product.id]))

        self.assertEqual(owned_response.status_code, 200)
        self.assertEqual(forbidden_response.status_code, 404)

    def test_edit_product_updates_database_record(self):
        product = Product.objects.create(
            producer=self.producer,
            name='Tomatoes',
            category='VEG',
            description='Juicy tomatoes',
            price='2.95',
            unit='per kg',
            stock_quantity=13,
            is_organic=False
        )

        self.client.login(username='producer1', password='testpass123')
        response = self.client.post(
            reverse('edit_product', args=[product.id]),
            {
                'name': 'Cherry Tomatoes',
                'category': 'VEG',
                'description': 'Small sweet tomatoes',
                'price': '3.40',
                'unit': 'per kg',
                'stock_quantity': 17,
                'is_organic': 'on',
                'allergen_information': '',
            }
        )

        product.refresh_from_db()
        self.assertRedirects(response, reverse('add_product'))
        self.assertEqual(product.name, 'Cherry Tomatoes')
        self.assertEqual(str(product.price), '3.40')
        self.assertTrue(product.is_organic)

    def test_delete_product_removes_database_record(self):
        product = Product.objects.create(
            producer=self.producer,
            name='Potatoes',
            category='VEG',
            description='Earthy potatoes',
            price='1.60',
            unit='per kg',
            stock_quantity=22,
            is_organic=False
        )

        self.client.login(username='producer1', password='testpass123')
        response = self.client.post(reverse('delete_product', args=[product.id]))

        self.assertRedirects(response, reverse('add_product'))
        self.assertFalse(Product.objects.filter(id=product.id).exists())


class CustomerMarketViewTests(TestCase):
    def setUp(self):
        self.producer_user = User.objects.create_user(username='producer_market', password='testpass123')
        self.customer_user = User.objects.create_user(username='customer_market', password='testpass123')

        self.producer = Producer.objects.create(
            user=self.producer_user,
            business_name='Hilltop Farm',
            contact_name='Farmer Hill',
            email='hill@example.com',
            business_address='10 Hill Road',
            postcode='BS33CC'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            name='Chris Buyer',
            email='buyer@example.com',
            address='5 City Street',
            postcode='BS44DD'
        )

    def test_customer_market_shows_products_and_producer_details(self):
        product = Product.objects.create(
            producer=self.producer,
            name='Lettuce',
            category='VEG',
            description='Fresh lettuce',
            price='1.40',
            unit='per head',
            stock_quantity=25,
            is_organic=True
        )

        self.client.login(username='customer_market', password='testpass123')
        response = self.client.get(reverse('customer_market'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        self.assertContains(response, self.producer.business_name)
        self.assertContains(response, self.producer.business_address)

    def test_customer_market_redirects_non_customer_user(self):
        self.client.login(username='producer_market', password='testpass123')
        response = self.client.get(reverse('customer_market'))

        self.assertRedirects(response, reverse('home'))
