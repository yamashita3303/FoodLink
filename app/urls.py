from django.urls import path
from . import views

urlpatterns = [
    path('', views.top, name='top'),

    path('user_signup/', views.user_signup, name='user_signup'),
    path('user_signin/', views.user_signin, name='user_signin'),
    path('user_home/', views.user_home, name='user_home'),
    path('search/', views.user_search, name='user_search'),  # 検索ページ
    path('food/<int:pk>/', views.user_food_detail, name='user_food_detail'),
    path('user_store_search/', views.user_store_search, name='user_store_search'),
    path('store/<int:user_id>/', views.user_store_detail, name='user_store_detail'),# 店舗詳細ページ
    path('category/<int:category_id>/', views.user_category_results, name='user_category_results'),
    path('cart/', views.user_cart, name='user_cart'),
    path("cart/update/", views.update_cart_quantity, name="update_cart_quantity"),
    path('create_order_from_store/', views.create_order_from_store, name='create_order_from_store'),
    # path('create_order_from_session/', views.create_order_from_session, name='create_order_from_session'),
    # path("payment/entry/<str:cart_id>/", views.entry_tran, name="entry_tran"),
    path("payment/exec/<str:order_id>/", views.test_exec_tran, name="test_exec_tran"),
    path("payment/confirm/<str:order_id>/",views.payment_confirm,name="payment_confirm"),
    path("payment/result/", views.payment_result, name="payment_result"),
    path('user_history/', views.user_history, name='user_history'),
    path('order/cancel/<int:order_item_id>/', views.order_item_cancel, name='order_item_cancel'),
    path('user_mypage/', views.user_mypage, name='user_mypage'),
    path('user_mypage/edit/', views.user_edit_menu, name='user_edit_menu'),
    path('user_mypage/edit/username/', views.user_edit_username, name='user_edit_username'),
    path('user_mypage/edit/email/', views.user_edit_email, name='user_edit_email'),
    path('user_mypage/edit/password/', views.user_edit_password, name='user_edit_password'),
    path('user_mypage/edit/phone/', views.user_edit_phone, name='user_edit_phone'),
    path('user_mypage/edit/address/', views.user_edit_address, name='user_edit_address'),
    path('user_alert/', views.user_alert, name='user_alert'),
    path("user/qr/read/<int:notification_id>/", views.user_read_qr_code, name="user_qr_read"),
    path("user/qr/result/<int:notification_id>/", views.user_qr_result, name="user_qr_result"),



    path('store_signup/', views.store_signup, name='store_signup'),
    path('store_signin/', views.store_signin, name='store_signin'),
    path('store_home/', views.store_home, name='store_home'),
    path('list/', views.store_purchased_list, name='store_list'),
    path('store_mypage/', views.store_mypage, name='store_mypage'),
    path('store_mypage/edit/', views.store_edit_menu, name='store_edit_menu'),
    path('store_mypage/edit/username/', views.store_edit_username, name='store_edit_username'),
    path('store_mypage/edit/phone/', views.store_edit_phone, name='store_edit_phone'),
    path('store_mypage/edit/password/', views.store_edit_password, name='store_edit_password'),
    path('store_mypage/edit/address/', views.store_edit_address, name='store_edit_address'),
    path('mypage/edit/hours/', views.store_edit_hours, name='store_edit_hours'),
    path('store_alert/', views.store_alert, name='store_alert'),
    path("cancel/", views.user_cancel_list, name="user_cancel_list"),

    path('store_registar/', views.store_registar, name='store_registar'),
    path('store/sales/', views.store_sales, name='store_sales'),

    # 複数画像登録用
    # path('product_create/', views.product_create, name='product_create'),
    path('product/<int:product_id>/ocr/', views.product_ocr, name='product_ocr'),
    # 商品編集
    path('product/<int:product_id>/edit/', views.product_edit, name='product_edit'),

    path(
    'product/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path("store/qr/read/<int:notification_id>/", views.store_read_qr_code, name="store_qr_read"),
    path("store/qr/result/<int:notification_id>/", views.store_qr_result, name="store_qr_result"),
    path("store/qr/verify/<int:notification_id>/", views.store_qr_verify, name="store_qr_verify"),

    path("store/qr/generate/", views.store_qr_generate, name="store_qr_generate"),
    path('store/qr/confirm/<int:notification_id>/',views.store_qr_confirm,name='store_qr_confirm'),

]
