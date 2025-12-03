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
    def get(self, request):
        user=request.user
        serializer = UserInfoUpdateSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    def get(self, request):
        user=request.user
        serializer = UserPhotoUpdateSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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

            return Response({"detail": "Photo updated successfully","data":serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# تعديل اسم المستخدم
class UserNameChangeView(APIView):
    """شغالة"""
    def get(self, request):
        user=request.user
        serializer = UsernameUpdateSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = UsernameUpdateSerializer(user,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "username updated successfully","data":serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #permission_classes = [IsAuthenticated]



# إعدادات الملف الشخصي يعني عرض اسم المستخدم وايميلو
class SettingsView(APIView):
    """  شغالة"""
    def get(self, request):
        user=request.user
        serializer = SettingsProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    #permission_classes = [IsAuthenticated]


# تغيير كلمة المرور
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



# عرض قائمة المتابعين لمستخدم معين
class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # المستخدم الذي نريد معرفة متابعيه
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        followers = User.objects.filter(following_set__following=user)

        serializer = UserMiniSerializer(
            followers,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=200)
    #permission_classes = [IsAuthenticated]




# عرض قائمة المتابعين الذين يتابعهم مستخدم معين
class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,user_id):
        # المستخدم الذي نريد معرفة من يتابعه
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        following = User.objects.filter(followers_set__follower=user)

        serializer = UserMiniSerializer(
            following,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=200)
    #permission_classes = [IsAuthenticated]



# متابعة مستخدم معين
class FollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """المستخدم الحالي يتابع user_id"""
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        serializer = FollowSerializer(
            data={"following": target_user.id},
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User followed successfully"}, status=201)

        return Response(serializer.errors, status=400)
    #permission_classes = [IsAuthenticated]



# إلغاء متابعة مستخدم معين
class UnfollowView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        follower = request.user

        try:
            following = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        follow_obj = Follow.objects.filter(follower=follower, following=following).first()

        if not follow_obj:
            return Response({"detail": "You are not following this user."}, status=400)

        follow_obj.delete()
        return Response({"detail": "Unfollowed successfully"}, status=200)
    #permission_classes = [IsAuthenticated]


