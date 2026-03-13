from collections import Counter
from datetime import timezone
from django.contrib.auth import get_user_model
from django.core import paginator
from django.forms import BooleanField
from .serializers import RegisterSerializer
from django.http import Http404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, query
import random
from django.db.models import Value, IntegerField, Case, When
from django.db.models import Count, Value, IntegerField, Exists, OuterRef, F
from django.db.models.functions import Length
from collections import Counter
from django.db.models.functions import Lower
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Post
from .utils import translate_text
#from .ai.improve_post import improve_post_text
from deep_translator import GoogleTranslator
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Post
import re
from rest_framework.decorators import api_view, permission_classes
from .utils import (
    normalize_specialization,
    expand_words,
    similarity_score
)

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
class MyProfileView(APIView):
    """شغالة"""
    def get(self, request):
        user=request.user
        serializer = MyProfileSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    permission_classes = [IsAuthenticated]




# OtherUserProfile
class OtherUserProfileView(APIView):
    """شغالة"""
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
    permission_classes = [IsAuthenticated]



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

    #  حذف الصورة الشخصية
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

##########################################################################################################

#لانشاء تفاعل جديد او تغييره او حذفه في حال كان الشخص عامل تفاعل ما مسبقا
class ReactToPostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        serializer = ReactionSerializer(
            data=request.data,
            context={"request": request, "post": post}
        )

        if serializer.is_valid():
            reaction = serializer.save()

            # حذف التفاعل (ضغط نفس النوع)
            if reaction is None:
                return Response({"message": "Reaction removed."}, status=200)

            return Response({
                "message": "Reaction added or updated.",
                "data": ReactionSerializer(reaction).data
            }, status=200)

        return Response(serializer.errors, status=400)
# class ReactToPostView(APIView):
#     """ هاد الصح ومنحطو بعد ما نعمل البوست"""
#     permission_classes = [IsAuthenticated]

#     def post(self, request, post_id):
#          post = get_object_or_404(Post, id=post_id)

#          serializer = ReactionSerializer(
#              data=request.data,
#              context={"request": request, "post": post}
#          )

#          if serializer.is_valid():
#             reaction = serializer.save()

#             # بعد كل عملية (إضافة - تعديل - حذف) نجلب البوست مع العدادات
#             updated_post_data = PostSerializer(post, context={"request": request}).data

#             # حذف التفاعل
#             if reaction is None:
#                 return Response({
#                     "message": "Reaction removed.",
#                     "post": updated_post_data   # 🔥 البيانات الجديدة مباشرة
#                 }, status=200)

#             # إضافة / تعديل
#             return Response({
#                 "message": "Reaction added or updated.",
#                 "post": updated_post_data,   # 🔥 البوست بعد التحديث
#                 "reaction": ReactionSerializer(reaction).data
#             }, status=200)

#          return Response(serializer.errors, status=400)




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

################################################################################

#يجلب التعليقات الرئيسية فقط + ترتيب افتراضي حسب الأقدم    
class PostCommentsView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        ordering = request.GET.get("ordering", "desc")  # الافتراضي  descيعني التعليقات الاجدد بتطلع من فوق

        post = get_object_or_404(Post, id=post_id)

        # نجلب فقط التعليقات الرئيسية
        comments = post.comments.filter(parent=None)

        if ordering == "desc":
            comments = comments.order_by("-created_at")
        else:
            comments = comments.order_by("created_at")

        serializer = CommentSerializer(comments, many=True, context={"request": request})
        return Response(serializer.data, status=200)  


#لجلب ردود تعليق معيّن
class CommentRepliesView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        replies = comment.replies.all().order_by("-created_at")

        serializer = CommentSerializer(replies, many=True, context={"request": request})
        return Response(serializer.data, status=200)



#Create comment OR reply
class CommentCreateView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        serializer = CommentCreateSerializer(
            data=request.data,
            context={"request": request, "post": post}
        )

        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerializer(comment, context={"request": request}).data, status=201)

        return Response(serializer.errors, status=400)
  #Create comment OR reply
# class CommentCreateView(APIView):
""" هاد الصح ومنحطو بعد ما نعمل البوست"""
#     permission_classes = [IsAuthenticated]

#     def post(self, request, post_id):
#         post = get_object_or_404(Post, id=post_id)

#         serializer = CommentCreateSerializer(
#             data=request.data,
#             context={"request": request, "post": post}
#         )

#         if serializer.is_valid():
#             comment = serializer.save()

#             # 🔥 بعد إنشاء التعليق → نجلب البوست مع عدادات التعليقات الجديدة
#             updated_post_data = PostSerializer(post, context={"request": request}).data

#             return Response({
#                 "message": "Comment created successfully",
#                 "comment": CommentSerializer(comment, context={"request": request}).data,
#                 "post": updated_post_data  # ← البيانات الجديدة + total_comments محدث
#             }, status=201)

#         return Response(serializer.errors, status=400)





#Add or change reaction on comment
class CommentReactionView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        serializer = CommentReactionSerializer(
            data=request.data,
            context={"request": request, "comment": comment},
        )

        if serializer.is_valid():
            reaction = serializer.save()

            # حالة الحذف (ضغط نفس التفاعل)
            if reaction is None:
                return Response({"message": "Reaction removed."}, status=200)

            # إضافة أو تعديل
            return Response({
                "message": "Reaction added or updated.",
                "data": CommentReactionSerializer(reaction).data
            }, status=200)

        return Response(serializer.errors, status=400)
#Add or change reaction on comment
# class CommentReactionView(APIView):
""" هاد الصح ومنحطو بعد ما نعمل البوست"""
#     permission_classes = [IsAuthenticated]

#     def post(self, request, comment_id):
#         comment = get_object_or_404(Comment, id=comment_id)

#         serializer = CommentReactionSerializer(
#             data=request.data,
#             context={"request": request, "comment": comment},
#         )

#         if serializer.is_valid():
#             reaction = serializer.save()

#             # 🔥 بعد أي تعديل أو حذف → نعمل serialize للتعليق المحدث
#             updated_comment_data = CommentSerializer(comment, context={"request": request}).data

#             # ❌ حذف التفاعل (ضغط نفس النوع)
#             if reaction is None:
#                 return Response({
#                     "message": "Reaction removed.",
#                     "comment": updated_comment_data     # ← العدادات بعد الحذف
#                 }, status=200)

#             # ✔ إضافة أو تعديل تفاعل
#             return Response({
#                 "message": "Reaction added or updated.",
#                 "reaction": CommentReactionSerializer(reaction).data,
#                 "comment": updated_comment_data        # ← العدادات بعد التعديل
#             }, status=200)

#         return Response(serializer.errors, status=400)





#تعديل تعليق و الحذف 
class CommentDetailView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def put(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        # مستخدم غير صاحب التعليق → رفض
        if comment.user != request.user:
            return Response({"message": "You are not allowed to edit this comment."}, status=403)

        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Comment updated successfully",
                "data": CommentSerializer(comment, context={"request": request}).data
            }, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user != request.user:
            return Response({"message": "You are not allowed to delete this comment."}, status=403)

        comment.delete()
        return Response({"message": "Comment deleted successfully"}, status=200)
#تعديل تعليق و الحذف 
# class CommentDetailView(APIView):
""" هاد الصح ومنحطو بعد ما نعمل البوست"""

#     permission_classes = [IsAuthenticated]

#     def put(self, request, comment_id):
#         comment = get_object_or_404(Comment, id=comment_id)

#         # مستخدم غير صاحب التعليق → رفض
#         if comment.user != request.user:
#             return Response({"message": "You are not allowed to edit this comment."}, status=403)

#         serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()

#             # 🔥 نرجّع معلومات التعليق بعد التحديث
#             updated_comment = CommentSerializer(comment, context={"request": request}).data

#             return Response({
#                 "message": "Comment updated successfully",
#                 "comment": updated_comment
#             }, status=200)

#         return Response(serializer.errors, status=400)

#     def delete(self, request, comment_id):
#         comment = get_object_or_404(Comment, id=comment_id)

#         if comment.user != request.user:
#             return Response({"message": "You are not allowed to delete this comment."}, status=403)

#         post = comment.post  # مهم جداً قبل الحذف

#         comment.delete()

#         # 🔥 نرجع عدد التعليقات الجديد مباشرة بعد الحذف
#         return Response({
#             "message": "Comment deleted successfully",
#             "total_comments": post.total_comments
#         }, status=200)

##########################################################################################
class CreatePostView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = PostCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            post = serializer.save()

            # أعرض البوست بعد الحفظ
            return Response({
                "message": "Post created successfully",
                "post": PostCreateSerializer(post, context={"request": request}).data
            }, status=201)

        return Response(serializer.errors, status=400)


#عرض منشور واحد
class PostDetailView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        serializer = PostSerializer(post, context={"request": request})
        return Response(serializer.data, status=200)
    


#تعديل المنشور او حذفه
class PostUpdateDeleteView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, post_id):
        """تعديل البوست (نص + كود + صور إضافة/حذف)"""
        post = get_object_or_404(Post, id=post_id)

        if post.user != request.user:
            return Response({"message": "You cannot edit this post."}, status=403)

        serializer = PostUpdateSerializer(
            post,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            post = serializer.save()
            return Response({
                "message": "Post updated successfully",
                "post": PostSerializer(post, context={"request": request}).data
            }, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, post_id):
        """حذف البوست"""
        post = get_object_or_404(Post, id=post_id)

        if post.user != request.user:
            return Response({"message": "You cannot delete this post."}, status=403)

        post.delete()
        return Response({"message": "Post deleted successfully"}, status=200)
######################################################################################    
 #feedاظهار منشورات ال   
class FeedView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # الأشخاص يلي المستخدم بيتابعن
        following_ids = user.following_set.values_list(
            "following_id", flat=True
        )

        # جلب منشوراتهم
        posts = Post.objects.filter(user_id__in=following_ids)

        # 🔹 فلترة حسب نوع المنشور (اختياري)
        post_type = request.GET.get("type")
        if post_type:
            posts = posts.filter(post_type=post_type)

        # 🔹 ترتيب (افتراضي: الأحدث)
        ordering = request.GET.get("ordering", "desc")
        if ordering == "asc":
            posts = posts.order_by("created_at")
        else:
            posts = posts.order_by("-created_at")

        serializer = PostSerializer(
            posts,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data, status=200)


#اقتراح مستخدمين بناءً على التخصص
class SuggestedUsersView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user
        
        # تحضير بيانات المستخدم الحالي
        user_words_normalized = normalize_specialization(current_user.specialization)
        user_words_expanded = expand_words(user_words_normalized)

        # جلب المرشحين (استثناء النفس ومن أتابعهم)
        following_ids = Follow.objects.filter(follower=current_user).values_list("following_id", flat=True)
        candidates = User.objects.exclude(id=current_user.id).exclude(id__in=following_ids)

        scored_users = []      # أصحاب التخصص (Strong/Medium)
        zero_score_users = []  # البعيدين عن التخصص (Fallback)

        for user in candidates:
            cand_words_normalized = normalize_specialization(user.specialization)
            cand_words_expanded = expand_words(cand_words_normalized)

            score = similarity_score(
                user_words_expanded, cand_words_expanded,
                user_words_normalized, cand_words_normalized
            )
            
            # الدرجة 1 هي الحد الأدنى لاعتبار الشخص "ذو صلة"
            if score >= 1:
                scored_users.append((score, user))
            else:
                zero_score_users.append(user)

        # أ. ترتيب أصحاب التخصص (الأعلى درجة أولاً، مع عشوائية بسيطة للتبديل)
        scored_users.sort(key=lambda x: x[0], reverse=True)

        # ب. سحب أول 8 أشخاص (النظام يعطي الأولوية المطلقة للمجال)
        final_users = [u for _, u in scored_users[:8]]

        # ج. إذا كان مجالك فيه أقل من 8، نكمل الباقي من الغرباء عشوائياً (Shuffle)
        if len(final_users) < 8:
            remaining_from_scored = [u for _, u in scored_users[8:]]
            fallback_pool = remaining_from_scored + zero_score_users
            random.shuffle(fallback_pool)
            
            needed = 8 - len(final_users)
            final_users.extend(fallback_pool[:needed])

        # د. إرسال النتائج النهائية
        serializer = UserSuggestionSerializer(final_users, many=True, context={"request": request})
        return Response(serializer.data, status=200)


##############################################################
#لبعدين منجربن ومنشوف شو وضعن


# # لانشاء مهمة ذكاء اصطناعي جديدة
# class CreateAiTaskView(APIView):
    """مو شغالة لانو ما نعمل الذكاء الاصطناعي ومانا مجربة"""
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = AiTaskCreateSerializer(
#             data=request.data,
#             context={"request": request}
#         )

#         if serializer.is_valid():
#             task = serializer.save()

#             return Response(
#                 AiTaskSerializer(task).data,
#                 status=201
#             )

#         return Response(serializer.errors, status=400)  
# 
#   
# #جلب تفاصيل مهمة ذكاء اصطناعي معينة واحدة 
# class AiTaskDetailView(APIView):
                  #  """مو شغالة لانو ما نعمل الذكاء الاصطناعي ومانا مجربة"""
#     permission_classes = [IsAuthenticated]

#     def get(self, request, task_id):
#         task = get_object_or_404(
#             AiTask,
#             id=task_id,
#             user=request.user
#         )

#         return Response(
#             AiTaskSerializer(task).data,
#             status=200
#         )    
    
# """#بجوز يكون اسا بدنا وحدة لجلب مهام بوست معين    """
###########################################################################


class SearchPagination(PageNumberPagination):
    page_size = 15

# البحث
class SearchView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]
    pagination_class = SearchPagination

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        search_type = request.query_params.get("type", "people")
         
        if not query:
            return Response(
                {"message": "Search query is required"},
                status=400)
       
        # =====================
        # 🔍 SEARCH PEOPLE
        # =====================
        if search_type == "people": # الافتراضي هو الاشخاص

          following_subquery = Follow.objects.filter(
          follower=request.user,
          following=OuterRef("pk")
           )

          users = User.objects.filter(  # ببحث عن الاشخاص حسب اسمن او اختصاصن
          Q(username__icontains=query) |
          Q(specialization__icontains=query)
          ).exclude(
          id=request.user.id
          ).annotate(
          is_following=Exists(following_subquery),
          starts_with=Case(When(username__istartswith=query, then=Value(1)), default=Value(0), output_field=IntegerField()),
          followers_total=Count("followers_set", distinct=True)
          ).order_by(
              "-is_following", # لما ابحث لازم يلي بتابعن يطلعو بالاول
              "-starts_with", # بعدا الاشخاص يلي اسمهم يبدأ بـ query )(عند التعادل في الفولو)
              "-followers_total", #  بعدا المشهورين يلي عندن متابعين كتير
               "username" # بعدن الاشخاص يلي اسمن بيتطابق مع الاسم يلي بحثت عليه
          )

 # هون مشان تسجيل البحث يلي عملناه حطينا الاسطر بفيو الاشخاص الاخرين مشان يتسجل بسجل البحث الاشخاص يلي فتت على حساباتن
          paginator = SearchPagination()
          page = paginator.paginate_queryset(users, request)
          if not page:
            return Response({
                "type": "people",
                "query": query,
                "message": "no matching results found",
                "results": []
            })
          serializer = SearchUserSerializer(
          page,
          many=True,
          context={"request": request}
          )
          
          return Response({
             "type": "people",
             "query": query,
             "count": users.count(),
             "has_more": paginator.get_next_link() is not None,
              "results": serializer.data
           })
        # =====================
         # 🔍 SEARCH TAGS
        #search bar & click on post
        # =====================
        if search_type == "tags": # برجع البوستات التي تحتوي التاغ المطلوب
            posts = Post.objects.filter(
              tags__icontains=query
            ).select_related(
              "user"
            ).prefetch_related(
             "images"
            ).annotate(
            likes_count=Count("reactions", distinct=True),
            comments_count=Count("comments", distinct=True),
            total_engagement=F("likes_count") + F("comments_count")
            ).order_by(
             "-total_engagement",# بيطلعولي البوستات يلي عليون تفاعل اكتر بالاول
              "-created_at" # وبعدا الاحدث
            )
            paginator = SearchPagination()
            page = paginator.paginate_queryset(posts, request)
            if not page:
             return Response({
                "type": "tags",
                "query": query,
                "message": "no matching results found",
                "results": []
            })
            serializer = PostSerializer(
               page,
               many=True,
              context={"request": request}
            )

            SearchHistory.objects.update_or_create(
              user=request.user,
              search_type="tags",
              query=query.lower(),
              defaults={}
           )
            return Response({
             "type": "tags",
             "query": query,
             "count": posts.count(),
             "has_more": paginator.get_next_link() is not None,
             "results": serializer.data
         })
        # =====================
        # 🔍 SEARCH POSTS
#       # =====================
# هون نحنا عم نرجع البوست كامل بس فينا اذا حبينا نعمل متل ما عملنا بالاقتراحات انو نرجع بوست مخفف ولما نضغط عليه بيطلع البوست كامل
        if search_type == "posts":
          keywords = [word for word in query.lower().split() if len(word) > 2] # استبعاد الكلمات الصغيرة جداً
          if not keywords: # إذا كان البحث فقط كلمات صغيرة مثل "في" أو "عن"
            keywords = [query.lower()]
    # فلترة مبدئية: المنشور يجب أن يحتوي على أي كلمة من كلمات البحث
          keyword_q = Q()
          for word in keywords:
            keyword_q &= Q(content__icontains=word) | Q(tags__icontains=word)

    # حساب النقاط (Relevance)
    # ملاحظة: للجودة والسرعة، سنستخدم 'Weighting' بسيط
          relevance_score = Value(0)
          for word in keywords:
            relevance_score += Case(
            When(content__icontains=word, then=Value(2)),
            When(tags__icontains=word, then=Value(1)), # التاغ له وزن أقل قليلاً من المحتوى
            default=Value(0),
            output_field=IntegerField()
            )
          posts = Post.objects.filter(keyword_q).select_related(
            "user"
          ).prefetch_related(
            "images"
          ).annotate(
          likes_count=Count("reactions", distinct=True),
          comments_count=Count("comments", distinct=True),
        # حساب النتيجة النهائية للترتيب
          search_rank=Case(
            # إذا تطابقت الجملة كاملة يأخذ أعلى تقييم (20 نقطة)
            When(content__icontains=query, then=Value(20)),
            default=relevance_score,
            output_field=IntegerField()
          )
          ).order_by(
            "-search_rank",   # الأهمية أولاً
            "-created_at",   # الاحدث ثانياً
            "-likes_count"   ,  # االاكثر تفاعلا أخيراً
            "-comments_count",
          )
          paginator = SearchPagination()
          page = paginator.paginate_queryset(posts, request)

          if not page:
            return Response({
                "type": "posts",
                "query": query,
                "message": "no matching results found",
                "results": []
            })

          serializer = PostSerializer(
            page,
            many=True,
            context={"request": request}
        )

          SearchHistory.objects.update_or_create(
            user=request.user,
            search_type="posts",
            query=query.lower(),
            defaults={}
        )

          return Response({
             "type": "posts",
             "query": query,
             "count": posts.count(),
             "has_more": paginator.get_next_link() is not None,
             "results": serializer.data
        })


#لتسجيل حساب الشخص يلي بفوت عليه لما ابحث عنو يعني يلي بضغط عليه و
class PeopleSearchClickView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get("username")

        if not username:
            return Response(
                {"message": "username is required"},
                status=400
            )

        SearchHistory.objects.update_or_create(
            user=request.user,
            search_type="people",
            query=username
        )

        return Response({"status": "saved"})    

    
#  لجلب  سجل البحث
class SearchHistoryView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_type = request.GET.get("type", "people")  # الافتراضي people

        if search_type not in ["people", "tags", "posts"]:
            return Response(
                {"message": "Invalid search type"},
                status=400
            )

        history_qs = (
            SearchHistory.objects
            .filter(
                user=request.user,
                search_type=search_type
            )
            .order_by("-created_at")[:15]
        )

        # =====================
        # 👤 PEOPLE
        # =====================
        if search_type == "people":  # برجعلي حسابات الاشخاص يلي فتت عليون
            usernames = [h.query for h in history_qs]
            users_map={u.username: u for u in User.objects.filter(username__in=usernames).exclude(id=request.user.id)}
            sorted_users=[]
            for name in usernames:
              if name  in users_map:
                sorted_users.append(users_map[name])
           
           
            # users = (
            #     User.objects
            #     .filter(username__in=usernames)
            #     .exclude(id=request.user.id)
            # )

            serializer = SearchUserSerializer(
                sorted_users,
                many=True,
                context={"request": request}
            )

            return Response({
                "type": "people",
                #"count": len(serializer.data),
                "results": serializer.data
            })

        # =====================
        # 🏷 TAGS
        # =====================
        if search_type == "tags": # هو والبوست برجعو الكلمات يلي بحثنا عليها
            return Response({
                "type": "tags",
                #"count": history_qs.count(),
                "results": [
                    {
                        "query": h.query,
                        #"searched_at": h.created_at
                    }
                    for h in history_qs
                ]
            })

        # =====================
        # 📝 POSTS
        # =====================
        if search_type == "posts":
            return Response({
                "type": "posts",
                #"count": history_qs.count(),
                "results": [
                    {
                        "query": h.query,
                        #"searched_at": h.created_at
                    }
                    for h in history_qs
                ]
            })


#لاحذف عنصر من سجل البحث
class DeleteSearchHistoryView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]
    
    def delete(self,request, pk):
      item=get_object_or_404(SearchHistory,id=pk,user=request.user)
      item.delete()
      return Response({"message":"deleted successfully"},status=204)
    



#هي ليظهرو الاقتراحات نحنا وعم نكتب
class SearchSuggestionsView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get("q", "").strip()
        search_type = request.GET.get("type", "people")

        if not query:
            return Response([])

  
        # 👤 PEOPLE ب
        if search_type == "people":
            query_lower = query.lower()
            # 1. المتابعة (هل أنا أتابع هذا الشخص؟)
            follow_subquery = Follow.objects.filter(
              follower=request.user,
              following=OuterRef("pk")
             )
            # 2. سجل البحث: منبحث إذا اليوزرنيم تبع هاد الشخص موجود ضمن الكلمات اللي بحثت عنها سابقاً
            # أو إذا اليوزرنيم نفسه مخزن كعملية بحث كاملة
            history_subquery = SearchHistory.objects.filter(
               user=request.user,
               search_type="people",
               query__icontains=OuterRef("username") 
            )
            # 3. الاستعلام الأساسي مع الترتيب المطلوب
            users = User.objects.filter(
              Q(username__icontains=query_lower) | 
              Q(specialization__icontains=query_lower)
            ).exclude(
              id=request.user.id
            ).annotate(
               is_following=Exists(follow_subquery),
               is_in_history=Exists(history_subquery), # بصير True إذا الشخص بسجلك
               starts_with=Case(When(username__istartswith=query_lower, then=Value(1)), default=Value(0), output_field=IntegerField()),
               followers_total=Count("followers_set", distinct=True),
            ).order_by(
              "-is_in_history",   # 1️⃣ اللي بحثت عنهم أولاً
              "-is_following",    # 2️⃣ اللي بتابعهم ثانياً
              "-starts_with",      #دقة المطابقة (من البداية)
              "-followers_total", #  المشهورين رابعااً
              "username"
          )[:15]
            
            return Response({
           "type": "people",
            "results": SearchUserSerializer(
            users,
            many=True,
            context={"request": request}
            ).data
            })

    
        # 📝 POSTS 
        if search_type == "posts":
          query_lower = query.lower()  
          suggestions=(SearchHistory.objects.filter(
              user=request.user,
              search_type="posts",
              query__icontains=query_lower )
          .order_by("-created_at")
          .values_list('query',flat=True)
          .distinct()[:20]
          )
          return Response({
               "type": "posts",
                "query":query ,
                "results":list(suggestions)})
                

        # 📝TAGS       
       # هاد و يلي بعدو عم يعطو نفس النتيجة بس رح خليون لنشوف كيف الشكل يلي رح يرجعولنا ياه الفرونت لحتى نخزن التاغات بقاعدة البيانات  
        if search_type == "tags":                                  #  وبقلبا التاغاتlist هاد للشكل يلي مخزن 
          query_lower = query.lower()                                        # هيك شكل التاغات المخزنة هون
          # هون منخلي قاعدة البيانات تحسب كم مرة تكرر كل تاغ               # tags = ["django", "backend"]
          all_tags = Post.objects.filter(tags__icontains=query_lower)\
                           .values_list('tags', flat=True)
          tag_counts = {}
          for tags_list in all_tags:
            if not tags_list:
               continue
            for t in tags_list:
              t_lower = t.lower().strip()
              if query_lower in t_lower:
                tag_counts[t_lower] = tag_counts.get(t_lower, 0) + 1
           # 2. ترتيب التاغات حسب الشهرة (الأكثر استخداماً)
           # وإعطاء أولوية للتاغ اللي بيبدأ تماماً بكلمة البحث
          sorted_tags = sorted(
            tag_counts.keys(),
            key=lambda x: (x.startswith(query_lower), tag_counts[x]),
            reverse=True
          )
          return Response({
           "type": "tags",
            "query": query,
             "results": sorted_tags[:10]
        })
        # if search_type == "tag":
        #    query_lower = query.lower()
        #    posts = Post.objects.exclude(tags=[]).values_list("tags", flat=True)
        #    counter = Counter()    # اذا كان شكل التخزين هيك
        #    for tags in posts:     #tags = ["django", "backend"] or tags = "#django #backend" or "py web backend"
        #      if not tags:
        #        continue
        #      extracted = []
        #      # إذا String
        #      if isinstance(tags, str):
        #        extracted = tags.replace("#", "").lower().split()
        #      # إذا List
        #      elif isinstance(tags, list):
        #        for tag in tags:
        #         extracted.extend(tag.replace("#", "").lower().split())
        #      # فلترة مبكرة (تحسين أداء)
        #      for tag in extracted:
        #       if query_lower in tag:
        #         counter[tag] += 1

        #     # تقسيم التاغات
        #    starts_with = []
        #    contains = []
        #    for tag, count in counter.items():
        #       if tag.startswith(query_lower):
        #          starts_with.append((tag, count))
        #       else:
        #          contains.append((tag, count))

        #     # 🧠 ترتيب حسب الاستخدام
        #    starts_with.sort(key=lambda x: -x[1])
        #    contains.sort(key=lambda x: -x[1])

        #    results = [tag for tag, _ in starts_with + contains][:10]

        #    return Response({
        #         "type": "tag",
        #          "query": query,
        #         "results": results
        #    })
        return Response([])    
#####################################################################################
# class ImprovePostView(APIView):

#     def post(self, request):

#         content = request.data.get("content","")

#         if not content:
#             return Response(
#                 {"error": "content is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         improved = improve_post_text(content)

#         return Response({
#             "original": content,
#             "ai_improved": improved
#         })


# # استدعاء الدالة اللي جهزناها على Colab
# from .ai.improve_post import improve_text  # هنا دالتك اللي في Colab أو محلية

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])

# def improve_post_api(request):
#     """
#     Endpoint لتحسين النصوص:
#     - يتلقى JSON: { "content": "النص" }
#     - يرجع JSON: { "improved": "النص المحسن" }
#     """
#     content = request.data.get("content", "")
#     if not content:
#         return Response({"error": "No content provided"}, status=400)

#     # نرسل النص للنموذج لتحسينه
#     improved_text = improve_text(content)

#     return Response({"improved": improved_text})
#################################################################################################  

# ترجمة المنشور
class TranslatePostView(APIView):
    "شغالة"
    def post(self, request):

        post_id = request.data.get("post_id")

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        translated_data = {}

        try:
            if post.content:
                translated_data["content"] = translate_text(post.content)
                time.sleep(0.2) # ممكن اذا صار عنا مشاكل نزيدو لل 0.5 بصير اضمن

            if post.ai_improved:
                translated_data["ai_improved"] = translate_text(post.ai_improved)
                time.sleep(0.2)

            if post.ai_generated:
                translated_data["ai_generated"] = translate_text(post.ai_generated)
                time.sleep(0.2)

            if post.ai_code_summary:
                translated_data["ai_code_summary"] = translate_text(post.ai_code_summary)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return Response(translated_data)
    


#  " هي متل يلي فوق بس بجوز اسرع بشوي بس ولكننن مشكلتا اذا كان عنا حقول بالعربي وحفول بالانكليزي ما رح تترجم الحقل المختلف صح"
# class TranslatePostView(APIView):

#     def post(self, request):

#         post_id = request.data.get("post_id")

#         try:
#             post = Post.objects.get(id=post_id)
#         except Post.DoesNotExist:
#             return Response({"error": "Post not found"}, status=404)

#         separator = "|||SPLIT|||"

#         texts = [
#             post.content or "",
#             post.ai_improved or "",
#             post.ai_generated or "",
#             post.ai_code_summary or ""
#         ]

#         combined_text = separator.join(texts)

#         # تحديد اتجاه الترجمة
#         arabic_pattern = re.compile(r'[\u0600-\u06FF]')

#         if arabic_pattern.search(post.content or ""):
#             source = "ar"
#             target = "en"
#         else:
#             source = "en"
#             target = "ar"

#         translated = GoogleTranslator(source=source, target=target).translate(combined_text)

#         parts = translated.split(separator)

#         # ضمان عدم حدوث IndexError
#         while len(parts) < 4:
#             parts.append("")

#         return Response({
#             "content": parts[0],
#             "ai_improved": parts[1],
#             "ai_generated": parts[2],
#             "ai_code_summary": parts[3]
#         })

#عرض النص الاصلي للمنشور
class ShowOriginalPostView(APIView):
    "شغالة"
    def post(self, request):

        post_id = request.data.get("post_id")

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        original_data = {
            "content": post.content,
            "ai_improved": post.ai_improved,
            "ai_code_summary": post.ai_code_summary,
            "ai_generated": post.ai_generated
        }

        return Response(original_data)


# ترجمة التعليقات
class TranslateCommentView(APIView):
    "شغالة"
    def post(self, request):
     
        comment_id = request.data.get("comment_id")

        if not comment_id:
            return Response({"error": "comment_id required"}, status=400)

        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)

        return Response({
            "comment": translate_text(comment.content)
        })



#عرض النص الاصلي للتعليق
class ShowOriginalCommentView(APIView):
    "شغالة"
    def post(self, request):

        comment_id = request.data.get("comment_id")

        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)

        return Response({
            "content": comment.content
        })
    
#############################################################################    
