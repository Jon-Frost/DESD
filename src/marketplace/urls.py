from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_choice, name='signup_choice'),
    path('signup/producer/', views.signup_producer, name='signup_producer'),
    path('signup/customer/', views.signup_customer, name='signup_customer'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='marketplace/login.html'), name='login'),
    path('products/add/', views.add_product, name='add_product'),
    path('market/', views.customer_market, name='customer_market'),
    path('producer/bio/', views.producer_bio, name='producer_bio'),
    path('producers/<int:producer_id>/', views.producer_bio_public, name='producer_bio_public'),
    path('products/<int:product_id>/', views.producer_product_actions, name='producer_product_actions'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
]