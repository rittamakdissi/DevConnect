from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer
from django.http import Http404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
import random
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



# class SuggestedUsersView(APIView):
#     """شغالة"""
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         current_user = request.user

#         following_ids = Follow.objects.filter(
#             follower=current_user
#         ).values_list("following_id", flat=True)

#         user_words = expand_words(
#             normalize_specialization(current_user.specialization)
#         )

#         candidates = User.objects.exclude(
#             id=current_user.id
#         ).exclude(
#             id__in=following_ids
#         )

#         strong_matches = []
#         medium_matches = []
#         weak_matches = []

#         for user in candidates:
#             candidate_words = expand_words(
#                 normalize_specialization(user.specialization)
#             )

#             score = similarity_score(user_words, candidate_words)

#             if score >= 6:
#                 strong_matches.append((score, user))
#             elif score >= 3:
#                 medium_matches.append((score, user))
#             else:
#                 weak_matches.append(user)

#         # ترتيب الأقوياء
#         strong_matches.sort(key=lambda x: x[0], reverse=True)
#         medium_matches.sort(key=lambda x: x[0], reverse=True)

#         final_users = []

#         # 1️⃣ أقوى تشابه
#         final_users.extend([u for _, u in strong_matches[:5]])

#         # 2️⃣ تشابه متوسط
#         final_users.extend([u for _, u in medium_matches[:5]])

#         # 3️⃣ Fallback ذكي (لو لسا ناقص)
#         if len(final_users) < 8:
#             random.shuffle(weak_matches)
#             final_users.extend(weak_matches[:8 - len(final_users)])

#         serializer = UserSuggestionSerializer(
#             final_users,
#             many=True,
#             context={"request": request}
#         )

#         return Response(serializer.data, status=200)
    


class SuggestedUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user

        # (يُفترض وجود User, Follow, UserSuggestionSerializer)
        
        # 1. تحضير بيانات المستخدم الحالي والمرشحين
        following_ids = Follow.objects.filter(
            follower=current_user
        ).values_list("following_id", flat=True)

        user_words_normalized = normalize_specialization(current_user.specialization)
        user_words_expanded = expand_words(user_words_normalized)

        candidates = User.objects.exclude(
            id=current_user.id
        ).exclude(
            id__in=following_ids
        )

        scored_users = []      # (score, user) حيث score >= 1
        zero_score_users = []  # (user) حيث score < 1
        
        # 2. حساب الدرجات والفصل
        for user in candidates:
            candidate_words_normalized = normalize_specialization(user.specialization)
            candidate_words_expanded = expand_words(candidate_words_normalized)

            score = similarity_score(
                user_words_expanded, 
                candidate_words_expanded, 
                user_words_normalized, 
                candidate_words_normalized
            )
            
            if score >= 1:
                scored_users.append((score, user))
            else:
                zero_score_users.append(user) 


        # 3. الترتيب وتشكيل القائمة النهائية (التركيز على أول 8)
        
        # ترتيب النتائج الموجبة تنازلياً (بما فيها عامل كسر الثبات العشوائي)
        scored_users.sort(key=lambda x: x[0], reverse=True)

        final_users = []
        
        # 3.1: الأولوية المطلقة: سحب أفضل 8 نتائج موزونة (الأكثر صلة)
        num_to_display = 8
        top_similar = [u for _, u in scored_users[:num_to_display]]
        final_users.extend(top_similar)
        
        # 3.2: ملء الفراغ بالنتائج الصفرية العشوائية (Fallback)
        # إذا لم نجد 8 مرشحين ذوي صلة، نملأ البقية من المستخدمين الآخرين عشوائياً.
        if len(final_users) < num_to_display:
            
            # نجمع كل المستخدمين الذين بقوا في قائمة scored_users (بعد أول 8) مع المستخدمين الصفرية
            remaining_scored_users = [u for _, u in scored_users[num_to_display:]]
            fallback_list = remaining_scored_users + zero_score_users
            
            random.shuffle(fallback_list) # خلط الـ Fallback لضمان التنويع
            
            num_to_add = num_to_display - len(final_users)
            final_users.extend(fallback_list[:num_to_add])

        # 4. إرسال البيانات
        serializer = UserSuggestionSerializer(
            final_users,
            many=True,
            context={"request": request}
        )

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