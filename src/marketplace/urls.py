from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_choice, name='signup_choice'),
    path('signup/producer/', views.signup_producer, name='signup_producer'),
    path('signup/customer/', views.signup_customer, name='signup_customer'),
]