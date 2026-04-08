"""
URL configuration for DevConnectproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.http import HttpResponse           
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def create_admin(request):
    if not User.objects.filter(username='rittamakdissi').exists():
        # 1. إنشاء المستخدم الأساسي
        user = User.objects.create_superuser('rittamakdissi', 'rittamakdissi@gmail.com', 'r1i2t3t4a5')
        
        # 2. تعبئة الحقول الإضافية (بما أنها Required في المودل)
        user.first_name = 'Ritta'
        user.last_name = 'Makdissi'
        user.age = 23             # ضعي عمركِ الحقيقي هنا
        user.gender = 'female'     # أو القيمة التي تعتمدينها في المودل
        user.phone_number = '0991419699'
        
        user.save() # حفظ الحقول الجديدة
        
        return HttpResponse("Done! User: rittamakdissi created with all fields.")
    return HttpResponse("Admin already exists.")



urlpatterns = [
    path('admin/', admin.site.urls),
    path('make-me-admin/', create_admin), 

    path('',include('app.urls')),
   # path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin

# هذه هي الدالة (الوظيفة) التي ستنشئ الحساب
def create_admin(request):
    if not User.objects.filter(username='rita_dev').exists(): # غيرت الاسم لـ rita_dev
        User.objects.create_superuser('rita_dev', 'rita@example.com', 'Rita@2026')
        return HttpResponse("Done! User: rita_dev, Pass: Rita@2026")
    return HttpResponse("Admin already exists.")


    
 