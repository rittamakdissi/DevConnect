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


# def create_admin(request):
#     # نستخدم اسم مستخدم جديد أو نتأكد أن القديم غير موجود
#     username = 'rittamakdissi' 
#     if not User.objects.filter(username=username).exists():
#         User.objects.create_superuser(
#             username=username,
#             email='rittamakdissi@gmail.com',
#             password='r1i2t3t4a5', # غيري الباسورد لما تحبين
#             first_name='Ritta',
#             last_name='Makdissi',
#             age=25,               # القيمة التي كانت تنقصنا!
#             gender='female',      # أضيفي باقي الحقول المطلوبة هنا
#             phone_number='0991419699'
#         )
#         return HttpResponse(f"Done! Admin '{username}' created successfully.")
#     return HttpResponse("Admin already exists.")


urlpatterns = [
    path('admin/', admin.site.urls),
   # path('make-me-admin/', create_admin), 

    path('',include('app.urls')),
    # هدول كانو مفعلين من قبل
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    
 