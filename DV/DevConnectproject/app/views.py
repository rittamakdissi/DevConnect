from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer
from django.http import Http404
from rest_framework import status 
from rest_framework.request import Request
from rest_framework.response import Response  
from rest_framework.views import APIView
from .models import * 
from .serializers import * 
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404



User = get_user_model()


# Rigister
"""شغالة"""
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User registered successfully.", "user": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# Login  
"""   هي لازم اتاكد منها من الشات لانو ما بظن صح 

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
"""


# MyProfile
""" جاهز بس ضل لمل نضيف البوست سيريالايزر شيل التعليق عن الاسطر مشان يطلعولي المنشورات بهاد ال api"""
class MyProfileView(APIView):
    def get(self, request):
        user=request.user
        serializer = MyProfileSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    #permission_classes = [IsAuthenticated]




# OtherUserProfile
""" شغال بس متل فكرة يلي قبلو لازم نشيل التعليق عن اسطر البوست"""   
class OtherUserProfileView(APIView):

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OtherUserProfileSerializer(
            user,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    #permission_classes = [IsAuthenticated]



#تعديل معلومات المستخدم من اختصاص و بيو و روابط
class UpdateUserInfoView(APIView):
    """شغالة"""
    def patch(self, request):
        user = request.user
        # نمرّر partial=True لأنه تعديل جزئي
        serializer = UserInfoUpdateSerializer(user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User info updated successfully","data":serializer.data},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #permission_classes = [IsAuthenticated]


#تعديل الصورة الشخصية أو حذفها
class UpdateUserPhotoView(APIView):
    """الحذف شغال بس ما عم اعرف شو صياغة الصورة يلي بدي مرقا مشان جرب التعديل"""
    def put(self, request):
        user = request.user

        serializer = UserPhotoUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            # إذا بدك تحذفي الصورة: personal_photo = null
            if request.data.get("personal_photo") is None:
                user.personal_photo.delete(save=True)
                return Response({"detail": "Photo deleted successfully"}, status=status.HTTP_200_OK)

            else:
                serializer.save()

            return Response({"detail": "Photo updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# تعديل اسم المستخدم
class UserNameChangeView(APIView):
    """شغالة"""
    def put(self, request):
        user = request.user
        serializer = UsernameUpdateSerializer(user,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "username updated successfully","data":serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #permission_classes = [IsAuthenticated]



class SettingsView(APIView):
    """  شغالة"""
    def get(self, request):
        user=request.user
        serializer = SettingsProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    #permission_classes = [IsAuthenticated]


class ChangePasswordView(APIView):
    """ شغالة"""
    def put(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(user,data=request.data,context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password changed successfully"},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #permission_classes = [IsAuthenticated]
