from django.urls import path
from . import views

urlpatterns = [
    path('', views.top, name='top'),

    path('user_signup/', views.user_signup, name='user_signup'),
    path('user_signin/', views.user_signin, name='user_signin'),
    path('user_home/', views.user_home, name='user_home'),
    path('category/', views.user_category, name='user_category'),
    path('cart/', views.user_cart, name='user_cart'),
    path('history/', views.user_history, name='user_history'),
    path('user_mypage/', views.user_mypage, name='user_mypage'),
    path('user_mypage/edit/', views.user_edit_menu, name='user_edit_menu'),
    path('user_mypage/edit/username/', views.user_edit_username, name='user_edit_username'),
    path('user_mypage/edit/email/', views.user_edit_email, name='user_edit_email'),
    path('user_mypage/edit/password/', views.user_edit_password, name='user_edit_password'),
    path('user_mypage/edit/phone/', views.user_edit_phone, name='user_edit_phone'),
    path('user_mypage/edit/address/', views.user_edit_address, name='user_edit_address'),
    path('user_alert/', views.user_alert, name='user_alert'),

    path('store_signup/', views.store_signup, name='store_signup'),
    path('store_signin/', views.store_signin, name='store_signin'),
    path('store_home/', views.store_home, name='store_home'),
    path('list/', views.store_list, name='store_list'),
    path('store_mypage/', views.store_mypage, name='store_mypage'),
    path('store_mypage/edit/', views.store_edit_menu, name='store_edit_menu'),
    path('store_mypage/edit/username/', views.store_edit_username, name='store_edit_username'),
    path('store_mypage/edit/phone/', views.store_edit_phone, name='store_edit_phone'),
    path('store_mypage/edit/password/', views.store_edit_password, name='store_edit_password'),
    path('store_mypage/edit/address/', views.store_edit_address, name='store_edit_address'),
    path('mypage/edit/hours/', views.store_edit_hours, name='store_edit_hours'),
    path('store_alert/', views.store_alert, name='store_alert'),
]