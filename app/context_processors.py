from app.models import Notification

def notification_badge(request):
    if not request.user.is_authenticated:
        return {}

    # =====================
    # storeユーザーの場合
    # =====================
    if request.user.is_store:
        store = request.user

        # 注文通知（type="order"）
        order_notification_count = Notification.objects.filter(
            recipient_type='store',
            store=store,
            type='order',
            is_read=False
        ).count()

        # その他通知（order以外）
        other_notification_count = Notification.objects.filter(
            recipient_type='store',
            store=store,
            is_read=False
        ).exclude(type='order').count()

        return {
            'order_notification_count': order_notification_count,
            'other_notification_count': other_notification_count,
        }

    # =====================
    # 一般ユーザーの場合
    # =====================
    else:
        user = request.user

        user_notification_count = Notification.objects.filter(
            recipient_type='user',
            user=user,
            is_read=False
        ).count()

        return {
            'notification_count': user_notification_count
        }
