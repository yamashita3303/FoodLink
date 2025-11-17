from django.urls import path
from . import views

urlpatterns = [
    path('', views.top, name='top'),

    # user
    path('user_home/', views.user_home, name='user_home'),
    path('category/', views.user_category, name='user_category'),
    path('cart/', views.user_cart, name='user_cart'),
    path('history/', views.user_history, name='user_history'),
    path('user_mypage/', views.user_mypage, name='user_mypage'),
    path('user_alert/', views.user_alert, name='user_alert'),

    # store
    path('store_home/', views.store_home, name='store_home'),
    path('list/', views.store_list, name='store_list'),
    path('store_mypage/', views.store_mypage, name='store_mypage'),
    path('store_alert/', views.store_alert, name='store_alert'),
    path('store_registar/', views.store_registar, name='store_registar'),

    # 複数画像登録用
    path('product_create/', views.product_create, name='product_create'),
]
