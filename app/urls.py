from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/', views.category, name='category'),
    path('cart/', views.cart, name='cart'),
    path('history/', views.history, name='history'),
        path('mypage/', views.mypage, name='mypage'),
    path('alert/', views.alert, name='alert'),
]