from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.utils import timezone

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
    product_id = models.AutoField("商品ID", primary_key=True)
    name = models.CharField("商品名", max_length=100, blank=False)
    category = models.ForeignKey(
        Category,
        verbose_name="カテゴリ",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    price = models.IntegerField("価格", blank=False)
    expiration_date = models.DateTimeField("消費期限", blank=False)
    quantity = models.IntegerField("在庫数", default=1, blank=False)
    origin = models.CharField("原産地", max_length=50, blank=True, null=True)

    image1 = models.ImageField("商品画像①", upload_to='products/', blank=False)
    image2 = models.ImageField("商品画像②", upload_to='products/', blank=True, null=True)
    image3 = models.ImageField("商品画像③", upload_to='products/', blank=True, null=True)
    image4 = models.ImageField("商品画像④", upload_to='products/', blank=True, null=True)
    image5 = models.ImageField("商品画像⑤", upload_to='products/', blank=True, null=True)

    notes = models.TextField("備考", max_length=100, blank=True, null=True)

    store = models.ForeignKey(
        User,
        verbose_name="店舗ユーザー",
        on_delete=models.CASCADE,
        related_name="products"
    )
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    expiration_notified = models.BooleanField(
        "期限切れ通知済み",
        default=False
    )
    auto_cancel_notified = models.BooleanField(
        "自動キャンセル通知済み",
        default=False)

    def __str__(self):
        return self.name
    
    @property
    def is_expired(self):
        return self.expiration_date < timezone.now()
    
    @property
    def remaining_time_display(self):
        """
        残り時間を
        ・○日
        ・○時間○分
        ・○分
        の形で返す
        """
        if self.is_expired:
            return "期限切れ"

        diff = self.expiration_date - timezone.now()
        total_seconds = int(diff.total_seconds())

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days >= 1:
            return f"{days}日"
        elif hours >= 1:
            return f"{hours}時間"
        else:
            return f"{minutes}分"
        
    @property
    def is_urgent(self):
        """
        残り5分未満なら True
        """
        if self.is_expired:
            return False

        remaining_seconds = (self.expiration_date - timezone.now()).total_seconds()
        return remaining_seconds < 300  # 5分 = 300秒
    
# =========================
# Cartモデル
# =========================
class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.product.price * self.quantity


# =========================
# Orderモデル
# =========================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '準備待ち'),
        ('completed', '完了'),
        ('canceled', 'キャンセル'),
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

    # ← ここが「準備完了かどうか」
    ready = models.BooleanField(default=False)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_total_price(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])

    def mark_ready(self):
        """準備完了にする"""
        self.ready = True
        self.status = 'completed'
        self.save(update_fields=['ready', 'status'])


# =========================
# OrderItemモデル
# =========================
class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.IntegerField()
    subtotal = models.IntegerField(blank=True, null=True)

    is_canceled = models.BooleanField(default=False)  # ← 追加

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
        
class Qr(models.Model):
    code_data = models.IntegerField()
    pin = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code_data} ({self.pin}) - {self.created_at:%Y-%m-%d %H:%M}"