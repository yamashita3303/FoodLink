from django.contrib import admin
from .models import User, Product, Category, Order, OrderItem, Notification

admin.site.register(User)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Notification)