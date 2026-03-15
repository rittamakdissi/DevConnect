import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

# اشعارات Firebase Cloud Messaging (FCM) - FCM Manager

# تهيئة Firebase (بتتنفذ مرة وحدة لما يشتغل السيرفر)
# تأكدي إن ملف الـ JSON اللي حملتيه اسمه firebase_key.json وموجود بالمجلد الرئيسي للمشروع
cred_path = os.path.join(settings.BASE_DIR, 'firebase_key.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

def send_push_notification(token, title, body, extra_data=None):
    """
    token: عنوان المتصفح اللي رح يستلم
    title: عنوان الإشعار اللي رح يظهر فوق
    body: نص الإشعار
    extra_data: البيانات التقنية (target_id, target_type)
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        # الـ data لازم تكون كلها نصوص (Strings) عشان Firebase يقبلها
        data=extra_data or {},
        token=token,
    )
    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
        return response
    except Exception as e:
        print('Error sending message:', e)
        return None