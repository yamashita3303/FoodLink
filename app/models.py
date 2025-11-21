from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator

# =========================
# Userモデル（ユーザ情報）
# =========================
class User(AbstractUser):
    is_store = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{2,4}-\d{2,4}-\d{4}$',
            message="電話番号はハイフン付きで入力してください"
        )]
    )

    # 一般ユーザー用住所
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    prefecture = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    address_line1 = models.CharField(max_length=100, blank=True, null=True)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)

    # Store 固有情報
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="カテゴリ名")

    def __str__(self):
        return self.name

# =========================
# Productモデル（商品情報）
# =========================
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    price = models.IntegerField(blank=False)
    expiration_date = models.DateField(blank=False)
    quantity = models.IntegerField(default=1, blank=False)
    origin = models.CharField(max_length=50, blank=True, null=True)
    image1 = models.ImageField(upload_to='products/', blank=False)
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    image4 = models.ImageField(upload_to='products/', blank=True, null=True)
    image5 = models.ImageField(upload_to='products/', blank=True, null=True)
    notes = models.TextField(max_length=100, blank=True, null=True)
    store = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
# =========================
# Cartモデル
# =========================
class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# =========================
# CartItemモデル
# =========================
class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.IntegerField()
    subtotal = models.IntegerField(blank=True, null=True)
    checked = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.product.price * self.quantity
        super().save(*args, **kwargs)

# =========================
# Orderモデル
# =========================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    order_id = models.AutoField(primary_key=True)
    # 注文した人
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_orders"
    )

    # 店舗（注文を受けた側）
    store = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="store_orders"
    )
    total_price = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_total_price(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

# =========================
# OrderItemモデル
# =========================
class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.IntegerField()
    subtotal = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.product.price * self.quantity
        super().save(*args, **kwargs)
        self.order.update_total_price()

# =========================
# Notificationモデル
# =========================
class Notification(models.Model):
    RECIPIENT_CHOICES = [
        ('user', 'User'),
        ('store', 'Store'),
    ]
    notification_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50)
    message = models.TextField()
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)
     # 受け取るユーザー（一般）
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="user_notifications"
    )
    # 受け取る店舗
    store = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="store_notifications"
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.recipient_type == 'user' and not self.user:
            raise ValidationError("recipient_type が user の場合、user を指定してください")
