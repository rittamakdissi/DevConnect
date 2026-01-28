from collections import Counter
from datetime import timezone
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
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
import random
from django.db.models import Count, Value, IntegerField,Exists,OuterRef
from django.db.models.functions import Length
from collections import Counter
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
    page_size = 10

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
        if search_type == "people": # بالبداية بيطلع يلي عندو متابعين اكتر شي
            follow_subquery=Follow.objects.filter(
                follower=request.user,
                following=OuterRef("pk")
            )
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(specialization__icontains=query)
            ).exclude(
                id=request.user.id
            ).annotate(
              followers_total=Count("followers_set", distinct=True),
              is_following=Exists(follow_subquery)
             ).order_by(
                 "-is_following",
                "-followers_total",
                "username",
            ).distinct()
           # --- أسطر الـ Pagination ---
            paginator = SearchPagination()
            page = paginator.paginate_queryset(users, request)
            serializer = SearchUserSerializer(page, many=True, context={"request": request})
            # serializer = SearchUserSerializer(
            #     users,
            #     many=True,
            #     context={"request": request}
            # )# هدول قبل ما نضيف الpagination
            

            # SearchHistory.objects.create(
            #    user=request.user,
            #    query=query,
            #   search_type= search_type)
            SearchHistory.objects.update_or_create(
              user=request.user,
              search_type=search_type,
              query=query.lower(),
              defaults={}
 )
            if not page:
                return Response({
                    "type": "people",
                    "query": query,
                    "message": "no matching results found",
                    "results": []
                }, status=200)
            
            return Response({
                "type": "people",
                "query":query,
                "count": users.count(),
                "has_more": paginator.get_next_link() is not None, # عشان الـ Show More
                "results": serializer.data
            })

        # =====================
        # 🔍 SEARCH POSTS
        # =====================
        if search_type == "posts":# هون نحنا عم نرجع البوست كامل بس فينا اذا حبينا نعمل متل ما عملنا بالاقتراحات انو نرجع بوست مخفف ولما نضغط عليه بيطلع البوست كامل
            
            posts = Post.objects.filter(
                Q(content__icontains=query) |
                Q(tags__icontains=query)
            ).select_related(
                "user"
            ).prefetch_related(
                "images"
            ).annotate(
            likes_count=Count("reactions", distinct=True),
            comments_count=Count("comments", distinct=True),
            ).order_by(# فينا نغير ترتيبن
                "-created_at",        # 🔥 الأحدث أولاً واذا تنين بنفس التاريخ يلي عليه لايكات اكتر قبل
                "-likes_count",       # 👍 بعدها الأكثر تفاعل واذا تساوو بعدد التفاعلات عدد التعليقات هو يلي بيحسم
                "-comments_count"     # 💬 بعدها التعليقات
             ).distinct()
            # --- أسطر الـ Pagination ---
            paginator = SearchPagination()
            page = paginator.paginate_queryset(posts, request)
            serializer = PostSerializer(page, many=True, context={"request": request})
            

            
            # SearchHistory.objects.create(
            #    user=request.user,
            #    query=query,
            #   search_type= search_type)
            SearchHistory.objects.update_or_create(
              user=request.user,
              search_type=search_type,
              query=query.lower(),
              defaults={}
 )
            # فحص إذا كانت النتائج فارغة
            if not page:
                return Response({
                    "type": "posts",
                    "query": query,
                    "message": "no matching results foundة",
                    "results": []
                }, status=200)
            
            return Response({
                "type": "posts",
                "query":query,
                "count": posts.count(),
                "has_more": paginator.get_next_link() is not None,
                "results": serializer.data
            })
        

        # =====================
        # 🔍 SEARCH TAGS
            #search bar & click on post
        # =====================

        if search_type=="tag":
            posts = Post.objects.filter(
                tags__icontains=query
            ).select_related(
                "user" # لجلب بيانات صاحب البوست بطلب واحد
            ).prefetch_related(
                "images" # لجلب الصور المرتبطة بطلب واحد
            ).annotate(
                likes_count=Count("reactions", distinct=True),
                comments_count=Count("comments", distinct=True),
            ).order_by(   
                "-likes_count",       # الأكثر تفاعلاً
                "-comments_count"  ,# الأكثر نقاشاً
                 "-created_at",   #الاحدث 
            ).distinct()
            # --- أسطر الـ Pagination ---
            paginator = SearchPagination()
            page = paginator.paginate_queryset(posts , request)
            serializer = PostSerializer(page, many=True, context={"request": request})
            
            # serializer =  PostSerializer(
            #     posts,
            #     many=True,
            #     context={"request": request}
            # )#هدول قبل ما نضيف الpagination

            
            # SearchHistory.objects.create(
            #    user=request.user,
            #    query=query,
            #   search_type= search_type)
            SearchHistory.objects.update_or_create(
              user=request.user,
              search_type=search_type,
              query=query.lower(),
              defaults={}
 )

            
            if not page:
                return Response({
                    "type": "tag",
                    "query": query,
                    "message": "no matching results found",
                    "results": []
                }, status=200)
            
            return Response({
                "type": "tag",
                "query":query,
                "count": posts.count(),
                "has_more": paginator.get_next_link() is not None,
                "results": serializer.data
            })

        return Response(
            {"message": "Invalid search type"},
            status=400
         )
     
    
#  لجلب آخر عمليات البحث يعني سجل البحث
class SearchHistoryView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_type = request.query_params.get("type", "people")#الافتراضي هو الاشخاص

        qs = SearchHistory.objects.filter(user=request.user)

        if search_type:
            qs = qs.filter(search_type=search_type)

        qs = qs.order_by("-created_at")#بيرجع السجل مرتب يلي بالاول هني يلي بحثت عليون اخر شي

        result = []
        seen_per_type = {}

        for item in qs:
            t = item.search_type
            q = item.query

            if t not in seen_per_type:
                seen_per_type[t] = set()

            # منع التكرار داخل نفس النوع
            if q in seen_per_type[t]:
                continue

            seen_per_type[t].add(q)
            result.append(item)

            # يعرض اخر 15 عمليات بحث
            if len(seen_per_type[t]) == 15:
                continue

            # إذا كل الأنواع وصلوا للحد، نوقف
            if all(len(v) >= 15 for v in seen_per_type.values()):
                break

        serializer = SearchHistorySerializer(result, many=True)
        return Response(serializer.data)

#لاحذف عنصر من سجل البحث
class DeleteSearchHistoryView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]
    
    def delete(self,request, pk):
      item=get_object_or_404(SearchHistory,id=pk,user=request.user)
      item.delete()
      return Response({"message:deleted succefully"},status=204)
    



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
             follow_subquery=Follow.objects.filter(
                follower=request.user,
                following=OuterRef("pk")
            )
            #  following_ids = Follow.objects.filter(
            #   follower=request.user
            # ).values_list("following_id", flat=True)

             users = User.objects.filter(
               Q(username__icontains=query) |
               Q(specialization__icontains=query)
             ).exclude(
              id=request.user.id
            #  ).exclude(
            #   id__in=following_ids
             ).annotate(
              is_following=Exists(follow_subquery),
              followers_total=Count("followers_set", distinct=True),
              
             ).order_by(# اقتراحات الاشخاص يعني انا وعم اكتب بالبحث ببلشو يطلعو الاشخاص يلي انا متابعتن بالاول وبعدا ببلشو حسب يلي الاشهر يعني يلي عندو متابعين اكثر
               "-is_following",
              "-followers_total"
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
         LIMIT = 20  # أو 15 أو 20 حسب ما بدك
         posts = Post.objects.filter(
            Q(content__icontains=query) |
            Q(tags__icontains=query)
            ).annotate(
             likes_count=Count("reactions", distinct=True),
             comments_count=Count("comments", distinct=True),
            ).order_by(#      وفينا نغير فيون متل ما بدنا
                "-likes_count",
               "-comments_count",
               "-created_at",
               )[:LIMIT]
        
         return Response({"type": "posts",
                          "results": SuggestedPostMiniSerializer(
                              posts, many=True,context={"request": request}).data})
                
        # TAGS       
        # هاد و يلي بعدو عم يعطو نفس النتيجة بس رح خليون لنشوف كيف الششكل يلي رح يرجعولنا ياه الفرونت لحتى نخزن التاغات بقاعدة البيانات  
        # if search_type == "tag":             #  وبقلبا التاغاتlist هاد للشكل يلي مخزن 
        #    posts = Post.objects.exclude(     # واذا بدنا نستخدمو بدنا نضفلو تحسينات متل انو يطلعو التاغات الاكثر استخداما بالاول
        #      tags=[]
        #    ).values_list("tags", flat=True)

        #    tag_set = set()
                                         # هيك شكل التاغات المخزنة هون
        #    for tags in posts:          # tags = ["django", "backend"]
        #        if not tags:
        #         continue
               
        #        for tag in tags:
        #          if query.lower() in tag.lower():
        #            tag_set.add(tag.lower())
        #    return Response({
        #       "type": "tag",
        #       "query": query,
        #       "results": sorted(tag_set)[:10]
        #     })    

        # بجوز ما يكون سريع اداؤه
        if search_type == "tag":
           query_lower = query.lower()
           posts = Post.objects.exclude(tags=[]).values_list("tags", flat=True)
           counter = Counter()
           for tags in posts:     #tags = ["django", "backend"] or tags = "#django #backend" or "py web backend"
             if not tags:
               continue
             extracted = []
             # إذا String
             if isinstance(tags, str):
               extracted = tags.replace("#", "").lower().split()
             # إذا List
             elif isinstance(tags, list):
               for tag in tags:
                extracted.extend(tag.replace("#", "").lower().split())
             # فلترة مبكرة (تحسين أداء)
             for tag in extracted:
              if query_lower in tag:
                counter[tag] += 1

            # تقسيم التاغات
           starts_with = []
           contains = []
           for tag, count in counter.items():
              if tag.startswith(query_lower):
                 starts_with.append((tag, count))
              else:
                 contains.append((tag, count))

            # 🧠 ترتيب حسب الاستخدام
           starts_with.sort(key=lambda x: -x[1])
           contains.sort(key=lambda x: -x[1])

           results = [tag for tag, _ in starts_with + contains][:10]

           return Response({
                "type": "tag",
                 "query": query,
                "results": results
           })
        return Response([])    
