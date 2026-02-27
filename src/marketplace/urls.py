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
]