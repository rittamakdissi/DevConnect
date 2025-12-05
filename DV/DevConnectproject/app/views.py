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
from rest_framework.parsers import MultiPartParser, FormParser


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
                {"message": "User not found."},
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
            return Response({"message": "User info updated successfully","data":serializer.data},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #permission_classes = [IsAuthenticated]


#تعديل الصورة الشخصية أو حذفها
class UpdateUserPhotoView(APIView):
    """شغالة"""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        serializer = UserPhotoUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                "detail": "Photo updated successfully",
                "data": serializer.data
            }, status=200)

        return Response(serializer.errors, status=400)

    # 🗑 حذف الصورة الشخصية
    def delete(self, request):
        user = request.user

        if user.personal_photo:
            user.personal_photo.delete(save=True)
            return Response({"detail": "Photo deleted successfully"}, status=200)

        return Response({"detail": "No photo to delete"}, status=400)



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
            return Response({"message": "username updated successfully","data":serializer.data}, status=status.HTTP_200_OK)
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
            return Response({"message": "Password changed successfully"},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #permission_classes = [IsAuthenticated]



# عرض قائمة المتابعين لمستخدم معين
class FollowersListView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # المستخدم الذي نريد معرفة متابعيه
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=404)

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
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request,user_id):
        # المستخدم الذي نريد معرفة من يتابعه
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=404)

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
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """المستخدم الحالي يتابع user_id"""
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)

        serializer = FollowSerializer(
            data={"following": target_user.id},
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User followed successfully"}, status=201)

        return Response(serializer.errors, status=400)
    #permission_classes = [IsAuthenticated]



# إلغاء متابعة مستخدم معين
class UnfollowView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        follower = request.user

        try:
            following = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)

        follow_obj = Follow.objects.filter(follower=follower, following=following).first()

        if not follow_obj:
            return Response({"message": "You don't actually follow this user."}, status=400)

        follow_obj.delete()
        return Response({"message": "Unfollowed successfully"}, status=200)
    #permission_classes = [IsAuthenticated]




#لانشاء تفاعل جديد او تغييره في حال كان الشخص عامل تفاعل ما مسبقا
class ReactToPostView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        # هل البوست موجود؟
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"message": "Post not found"}, status=404)

        # نمرر post داخل context
        serializer = ReactionSerializer(
            data=request.data,
            context={"request": request, "post": post}
        )

        if serializer.is_valid():
            reaction = serializer.save()
            return Response({
                "message": "You Reactad successfully",
                "reaction": ReactionSerializer(reaction).data
            }, status=200)

        return Response(serializer.errors, status=400)


#حذف التفاعل من على منشور معين
class RemoveReactionView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id):
        user = request.user

        try:
            reaction = Reaction.objects.get(user=user, post_id=post_id)
        except Reaction.DoesNotExist:
            return Response({"message": "No reaction to remove"}, status=404)

        reaction.delete()
        return Response({"message": "Reaction removed"}, status=200)


# عرض قائمة المستخدمين الذين عملوا تفاعل معين على منشور معين
class ReactionUsersListView(APIView):
    """شغالة بس لازم تنربط لاحقا مع البوست"""
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id, reaction_type):
        # تحقق من وجود البوست
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"message": "Post not found"}, status=404)

        # تحقق من reaction_type
        valid_types = dict(Reaction.REACTION_TYPES).keys()
        if reaction_type not in valid_types:
            return Response({"message": "Invalid reaction type"}, status=400)

        # جلب المستخدمين الذين عملوا هذا التفاعل
        reactions = Reaction.objects.filter(
            post=post,
            reaction_type=reaction_type
        )

        users = [reaction.user for reaction in reactions]

        serializer = UserMiniSerializer(
            users,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=200)