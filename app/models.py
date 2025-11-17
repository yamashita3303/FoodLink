from django.db import models
from django.core.validators import RegexValidator

# =========================
# Userモデル（ユーザ情報）
# =========================
class User(models.Model): 
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(unique=True, blank=False)
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{2,4}-\d{2,4}-\d{4}$',
            message="電話番号はハイフン付きで入力してください"
        )]
    )
    postal_code = models.CharField(max_length=10, blank=False)
    address = models.CharField(max_length=255, blank=False)

    def __str__(self):
        return self.name  # 修正済み

# =========================
# Storeモデル（店舗情報）
# =========================
class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    phone = models.CharField(
        max_length=15,
        blank=False,
        validators=[RegexValidator(
            regex=r'^\d{2,4}-\d{2,4}-\d{4}$',
            message="電話番号はハイフン付きで入力してください"
        )]
    )
    password = models.CharField(max_length=255, blank=False)  # ハッシュ化推奨
    postal_code = models.CharField(max_length=10, blank=False)
    address = models.CharField(max_length=255, blank=False)
    opening_time = models.TimeField(blank=False)
    closing_time = models.TimeField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# =========================
# Productモデル（商品情報）
# =========================
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    category = models.CharField(max_length=50, blank=False)
    price = models.IntegerField(blank=False)
    expiration_date = models.DateField(blank=False)
    quantity = models.IntegerField(default=1, blank=False)
    origin = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # メイン画像1枚
    notes = models.TextField(max_length=100, blank=True, null=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# =========================
# ProductImageモデル（追加画像用）
# =========================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='products/additional/')

    def __str__(self):
        return f"{self.product.name} の画像"

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders")
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.recipient_type == 'user' and not self.user:
            raise ValidationError("recipient_type が user の場合、user を指定してください")
        if self.recipient_type == 'store' and not self.store:
            raise ValidationError("recipient_type が store の場合、store を指定してください")
