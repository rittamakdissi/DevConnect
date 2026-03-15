from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Media
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Follow, Comment, Reaction, CommentReaction, Notification
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .fcm_manager import send_push_notification


# حذف ملف الصورة من الميديا نهائيا عندما المستخدم يحذفا
@receiver(post_delete, sender=Media)
def delete_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)



# 1. إشعار المتابعة (Follow)
@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            to_user=instance.following,
            from_user=instance.follower,
            notification_type="follow"
        )

# 2. إشعار التفاعل على المنشور (Post Reaction)
@receiver(post_save, sender=Reaction)
def create_post_reaction_notification(sender, instance, created, **kwargs):
    # نرسل إشعار فقط إذا كان التفاعل جديداً والمستخدم لا يتفاعل مع منشوره الخاص
    if created and instance.user != instance.post.user:
        Notification.objects.create(
            to_user=instance.post.user,
            from_user=instance.user,
            notification_type="post_reaction",
            post=instance.post
        )

# 3. إشعار التفاعل على التعليق (Comment Reaction)
@receiver(post_save, sender=CommentReaction)
def create_comment_reaction_notification(sender, instance, created, **kwargs):
    # نرسل إشعار لصاحب التعليق
    if created and instance.user != instance.comment.user:
        Notification.objects.create(
            to_user=instance.comment.user,
            from_user=instance.user,
            notification_type="comment_reaction",
            comment=instance.comment,
            post=instance.comment.post # ربط البوست لسهولة الوصول
        )

# 4. إشعار تعليق جديد على منشوري (New Comment)
# 5. إشعار الرد على تعليقي (Reply to Comment)
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        # الحالة أ: الرد على تعليق (Reply)
        if instance.parent and instance.user != instance.parent.user:
            Notification.objects.create(
                to_user=instance.parent.user,
                from_user=instance.user,
                notification_type="reply_comment",
                comment=instance,
                post=instance.post
            )
        # الحالة ب: تعليق جديد على منشور (New Comment)
        # منبعت إشعار لصاحب البوست بشرط ما يكون هو نفسه اللي علّق
        elif not instance.parent and instance.user != instance.post.user:
            Notification.objects.create(
                to_user=instance.post.user,
                from_user=instance.user,
                notification_type="new_comment",
                comment=instance,
                post=instance.post
            )


# firebase
@receiver(post_save, sender=Notification)
def trigger_notification_push(sender, instance, created, **kwargs):
    if created:
        # وصول مباشر للتوكن من المستخدم
        token = instance.to_user.fcm_token 
        
        if token:
            # القاموس: أنظف وأسهل للإضافة والتعديل
            # body_messages = {
            #     "follow": f"بدأ {instance.from_user.username} بمتابعتك",
            #     "post_reaction": f"تفاعل {instance.from_user.username} مع منشورك",
            #     "comment_reaction": f"أعجب {instance.from_user.username} بتعليقك",
            #     "new_comment": f"علق {instance.from_user.username} على منشورك",
            #     "reply_comment": f"رد {instance.from_user.username} على تعليقك",
            # }
            body_messages = {
                  "follow": f"{instance.from_user.username} started following you",
                  "post_reaction": f"{instance.from_user.username} reacted to your post",
                 "comment_reaction": f"{instance.from_user.username} liked your comment",
                 "new_comment": f"{instance.from_user.username} commented on your post",
                 "reply_comment": f"{instance.from_user.username} replied to your comment",
                }

            
            # جلب الرسالة بناءً على النوع، وإذا مو موجودة بياخد الرسالة الافتراضية
            body = body_messages.get(instance.notification_type,"New notification from DevConnect")
            title = "DevConnect"

            # تحديد الـ target_id بذكاء
            target_id = str(instance.post.id if instance.post else (instance.comment.id if instance.comment else ""))

            data_payload = {
                "target_id": target_id,
                "target_type": str(instance.notification_type),
            }

            # الإرسال الفعلي
            send_push_notification(token, title, body, data_payload)