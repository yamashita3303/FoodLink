from django.contrib import admin
from .models import User, Store, Product

admin.site.register(User)
admin.site.register(Store)
admin.site.register(Product)