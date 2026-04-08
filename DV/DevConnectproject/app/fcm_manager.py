import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings
import json
# اشعارات Firebase Cloud Messaging (FCM) - FCM Manager

# تهيئة Firebase (بتتنفذ مرة وحدة لما يشتغل السيرفر)
# تأكدي إن ملف الـ JSON اللي حملتيه اسمه firebase_key.json وموجود بالمجلد الرئيسي للمشروع
# cred_path = os.path.join(settings.BASE_DIR, 'firebase_key.json')
#cred = credentials.Certificate(cred_path)
#firebase_admin.initialize_app(cred)

firebase_json = os.environ.get('FIREBASE_CONFIG_JSON')

if firebase_json:
    try:
        # 2. تحويل النص إلى قاموس (Dictionary)
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
        
        # 3. التأكد من عدم تكرار التشغيل لتجنب الأخطاء
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully on Render!")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
else:
    print("Firebase configuration not found. Notifications will be disabled.")

def send_push_notification(token, title, body, extra_data=None):
    """
    token: عنوان المتصفح اللي رح يستلم
    title: عنوان الإشعار اللي رح يظهر فوق
    body: نص الإشعار
    extra_data: البيانات التقنية (target_id, target_type)
    """
    if not firebase_admin._apps:
        print("Firebase is not initialized. Cannot send notification.")
        return None
    
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