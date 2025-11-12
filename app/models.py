from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator

# =========================
# Userモデル（ユーザ情報）
# =========================
class User(AbstractUser):
    email = models.EmailField(unique=True)  # メールで一意
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{2,4}-\d{2,4}-\d{4}$',
            message="電話番号はハイフン付きで入力してください"
        )]
    )  # 電話番号（ハイフン付き、日本国内想定）
    postal_code = models.CharField(max_length=10, blank=False)  # 郵便番号
    postal_code = models.CharField(max_length=10, blank=False, default='000-0000')  # 郵便番号
    prefecture = models.CharField(max_length=10, blank=False, default='未設定') # 都道府県
    city = models.CharField(max_length=50, blank=False, default='未設定')   # 市区町村
    address_line1 = models.CharField(max_length=100, blank=False, default='未設定') # 町名・番地
    address_line2 = models.CharField(max_length=100, blank=True)    # 建物名・部屋番号
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now=True)      # 更新日時

    # groups と user_permissions を上書きして related_name を変える
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # ← default の user_set と衝突しないように変更
        blank=True,
        help_text='ユーザーが所属するグループ',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # ← default の user_set と衝突しないように変更
        blank=True,
        help_text='ユーザーが持つ権限',
        verbose_name='user permissions'
    )

    USERNAME_FIELD = 'email'  # メールアドレスでログイン
    REQUIRED_FIELDS = ['username']  # username は必須

    def __str__(self):
        return self.username

# =========================
# Storeモデル（店舗情報）
# =========================
class Store(AbstractUser):
    """
    商品を販売する店舗を表すモデル。
    """
    # username = models.CharField(max_length=100, blank=False)  # 店舗名
    email = models.EmailField(blank=True, null=True)  # メールアドレス（任意）
    # 電話番号（ログインIDとして使用）
    phone = models.CharField(
        max_length=15,
        blank=False,  # ← "break" は誤り。ここは blank=False に。
        unique=True,  # 一意制約（ログインIDなので必須）
        validators=[RegexValidator(
            regex=r'^\d{2,4}-\d{2,4}-\d{4}$',
            message="電話番号はハイフン付きで入力してください"
        )]
    )
    postal_code = models.CharField(max_length=10, blank=False, default='000-0000')
    prefecture = models.CharField(max_length=10, blank=False, default='未設定')
    city = models.CharField(max_length=50, blank=False, default='未設定')
    address_line1 = models.CharField(max_length=100, blank=False, default='未設定')
    opening_time = models.TimeField(blank=False)  # 開店時間
    closing_time = models.TimeField(blank=False)  # 閉店時間
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now=True)      # 更新日時

    # groups と user_permissions を上書きして related_name を変える（AbstractUserと衝突回避）
    groups = models.ManyToManyField(
        Group,
        related_name='customstore_set',
        blank=True,
        help_text='店舗が所属するグループ',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customstore_set',
        blank=True,
        help_text='店舗が持つ権限',
        verbose_name='user permissions'
    )

    USERNAME_FIELD = 'phone'  # ← 電話番号でログイン
    REQUIRED_FIELDS = ['username']  # ← AbstractUserは username が必須なのでそのまま

    def __str__(self):
        return f"{self.username} ({self.phone})"

# =========================
# Productモデル（商品情報）
# =========================
class Product(models.Model):
    """
    店舗で販売する商品を表すモデル。
    """
    product_id = models.AutoField(primary_key=True) # 主キー 
    name = models.CharField(max_length=100, blank=False)  # 商品名
    category = models.CharField(max_length=50, blank=False)  # カテゴリ
    price = models.IntegerField(blank=False)  # 価格
    expiration_date = models.DateField(blank=False)  # 消費期限
    quantity = models.IntegerField(default=1, blank=False)  # 在庫数量
    origin = models.CharField(max_length=50, blank=True, null=True)  # 産地
    image = models.ImageField(upload_to='products/', blank=False)   # 商品画像
    notes = models.TextField(max_length=100, blank=True, null=True)  # 備考
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")  # 所属店舗
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.phone})"

# =========================
# Cartモデル（カート情報）
# =========================
class Cart(models.Model):
    """
    ユーザごとのカート情報。
    """
    cart_id = models.AutoField(primary_key=True) # 主キー 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")  # 所有者ユーザ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# =========================
# CartItemモデル（カート内商品）
# =========================
class CartItem(models.Model):
    """
    カート内の商品情報。
    """
    cart_item_id = models.AutoField(primary_key=True) # 主キー 
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")  # 所属カート
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")  # 商品
    quantity = models.IntegerField()  # 個数
    subtotal = models.IntegerField(blank=True, null=True)  # 小計（price × quantity、自動計算）
    checked = models.BooleanField(default=True)  # 購入対象かどうか

    def save(self, *args, **kwargs):
        self.subtotal = self.product.price * self.quantity  # 自動計算
        super().save(*args, **kwargs)

# =========================
# Orderモデル（注文情報）
# =========================
class Order(models.Model):
    """
    注文情報。
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),     # 受け取り待ち
        ('completed', 'Completed'), # 受け取り完了
        ('canceled', 'Canceled'),   # 注文キャンセル
    ]

    order_id = models.AutoField(primary_key=True) # 主キー 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")  # 注文者
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders")  # 注文先店舗
    total_price = models.IntegerField(default=0)  # 合計金額
    ready = models.BooleanField(default=False)  # 注文準備完了フラグ
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # 注文状態
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_total_price(self):
        """
        OrderItem の subtotal を合計して total_price を更新
        """
        total = sum(item.subtotal for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])

    def save(self, *args, **kwargs):
        """
        新規作成時は subtotal がまだないので total_price は0、
        後から update_total_price() で合計を更新する想定
        """
        super().save(*args, **kwargs)

# =========================
# OrderItemモデル（注文内商品）
# =========================
class OrderItem(models.Model):
    """
    注文内の商品情報。
    """
    order_item_id = models.AutoField(primary_key=True) # 主キー
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")  # 所属注文
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items")  # 商品
    quantity = models.IntegerField()  # 個数
    subtotal = models.IntegerField(blank=True, null=True)  # 小計

    def save(self, *args, **kwargs):
        self.subtotal = self.product.price * self.quantity
        super().save(*args, **kwargs)
        # 保存後に order の total_price を更新
        self.order.update_total_price()

# =========================
# Notificationモデル（通知）
# =========================
class Notification(models.Model):
    """
    通知情報。
    recipient_typeで対象を判別（userまたはstore）。
    """
    RECIPIENT_CHOICES = [
        ('user', 'User'),
        ('store', 'Store'),
    ]

    notification_id = models.AutoField(primary_key=True) # 主キー
    type = models.CharField(max_length=50)  # 通知種別（例: 注文、キャンセル）
    message = models.TextField()  # メッセージ内容
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)  # 受信者タイプ
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)  # ユーザ向け通知
    store = models.ForeignKey(Store, on_delete=models.CASCADE, blank=True, null=True)  # 店舗向け通知
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)  # 関連注文
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)  # 関連商品
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        recipient_type に応じて user または store が必須であることをバリデーション。
        """
        from django.core.exceptions import ValidationError
        if self.recipient_type == 'user' and not self.user:
            raise ValidationError("recipient_type が user の場合、user を指定してください")
        if self.recipient_type == 'store' and not self.store:
            raise ValidationError("recipient_type が store の場合、store を指定してください")
