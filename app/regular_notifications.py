from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Notification, Order, Product

# =========================
# 注文の未受取キャンセル通知
# =========================
def notify_unreceived_orders():
    orders = Order.objects.filter(status="pending")

    for order in orders:
        has_expired_product = False

        for item in order.items.all():
            product = item.product

            # ⭐ 期限切れ商品のみ対象
            if (
                product.expiration_date < timezone.now()
                and product.quantity >= 1
                and not product.auto_cancel_notified
            ):
                has_expired_product = True

                # ユーザー向け通知
                Notification.objects.create(
                    recipient_type="user",
                    user=order.user,
                    order=order,
                    product=product,
                    type="auto_cancel",
                    is_read=False,
                    message=f"期限までに受け取り完了しなかったため、商品「{product.name}」の注文がキャンセルされました。"
                )

                # 店舗向け通知
                Notification.objects.create(
                    recipient_type="store",
                    store=order.store,
                    order=order,
                    product=product,
                    type="auto_cancel",
                    is_read=False,
                    message=f"購入者が期限までに受け取れなかったため、商品「{product.name}」を自己回収してください。"
                )

                # ⭐ 二重通知防止
                product.auto_cancel_notified = True
                product.save()

        # ⭐ 1つでも期限切れ商品があれば注文をキャンセル
        if has_expired_product:
            order.status = "canceled"
            order.save()

# =========================
# 期限切れ在庫の通知
# =========================
def notify_expired_products():
    expired_products = Product.objects.filter(
        expiration_date__lt=timezone.now(),
        quantity__gte=1,
        expiration_notified=False
    )

    for product in expired_products:
        Notification.objects.create(
            recipient_type="store",
            store=product.store,
            product=product,
            type="expiration_date",
            is_read=False,
            message=f"商品「{product.name}」は消費期限切れですが、在庫が残っています。"
        )

        # ⭐ 二重通知防止
        product.expiration_notified = True
        product.save()


# =========================
# 定期実行されるメイン処理
# =========================
def update():
    print("Regular notification check running...")

    notify_unreceived_orders()
    notify_expired_products()


# =========================
# スケジューラー起動
# =========================
def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update, 'interval', minutes=1)  # 5分ごとに実行
    scheduler.start()
