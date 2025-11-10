from django.urls import path
from . import views

urlpatterns = [
    path('', views.userhome, name='home'),
    path('category/', views.category, name='category'),
    path('cart/', views.cart, name='cart'),
    path('history/', views.history, name='history'),
    path('mypage/', views.usermypage, name='mypage'),
    path('alert/', views.useralert, name='alert'),
]