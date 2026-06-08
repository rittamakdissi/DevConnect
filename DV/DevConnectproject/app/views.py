from collections import Counter
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.core import paginator
from django.forms import BooleanField
from sympy import content
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
from datetime import timedelta
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Post
from .utils import translate_text
from rest_framework_simplejwt.tokens import RefreshToken
#from .ai.improve_post import improve_post_text
from deep_translator import GoogleTranslator
from rest_framework.views import APIView
from rest_framework.response import Response
import random
from django.core.mail import send_mail
from .models import Post
import re
import json
import requests
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
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User registered successfully.", "user": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






# MyProfile
class MyProfileView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]
    # def get(self, request):
    #     user=request.user
    #     serializer = MyProfileSerializer(user, context={"request": request})
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        user = User.objects.filter(id=request.user.id).annotate(
        followers_count=Count('followers_set',distinct=True),
        following_count=Count('following_set',distinct=True)
    ).first()
        saved_ids = set(
            SavedPost.objects.filter(user=request.user)
            .values_list("post_id", flat=True)
         )
        serializer = MyProfileSerializer(user, context={"request": request,"saved_ids": saved_ids,})
        return Response(serializer.data, status=200)



class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


# OtherUserProfile
class OtherUserProfileView(APIView):
    """شغالة"""
    # def get(self, request, user_id):
    #     try:
    #         user = User.objects.get(pk=user_id)
    #     except User.DoesNotExist:
    #         return Response(
    #             {"message": "User not found."},
    #             status=status.HTTP_404_NOT_FOUND
    #         )

    #     serializer = OtherUserProfileSerializer(
    #         user,
    #         context={"request": request}
    #     )
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        user = User.objects.filter(pk=user_id).annotate(
        followers_count=Count('followers_set',distinct=True),
    ).first()
        if not user:
           return Response({"message": "User not found."}, status=404)
        saved_ids = set(
            SavedPost.objects.filter(user=request.user)
            .values_list("post_id", flat=True)
         )
        serializer = OtherUserProfileSerializer(user, context={"request": request,"saved_ids": saved_ids,})
        return Response(serializer.data, status=200)



#تعديل معلومات المستخدم من اختصاص و بيو و روابط
class UpdateUserInfoView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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



# إعدادات الملف الشخصي يعني عرض اسم المستخدم وايميلو
class SettingsView(APIView):
    """  شغالة"""
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user=request.user
        serializer = SettingsProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# تغيير كلمة المرور
class ChangePasswordView(APIView):
    """ شغالة"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(user,data=request.data,context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully"},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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




# عرض قائمة المتابعين الذين يتابعهم مستخدم معين
class FollowingListView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request,user_id):
        # 1. منع أي مستخدم من رؤية قائمة متابعات غيره
        if request.user.id != user_id:
            return Response(
                {"message": "You are not authorized to view this user's following list."}, 
                status=403
            )        
        
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
        # reactions = Reaction.objects.filter(
        #     post=post,
        #     reaction_type=reaction_type
        # )

        # users = [reaction.user for reaction in reactions]
        users = User.objects.filter(
           reactions__post=post,
           reactions__reaction_type=reaction_type
        )

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
        comments = post.comments.filter(parent=None).select_related('user').annotate(
            computed_useful=Count('reactions', filter=Q(reactions__reaction_type='useful')),
            computed_not_useful=Count('reactions', filter=Q(reactions__reaction_type='not_useful')),
            computed_replies=Count('replies')
            )
        if ordering == "desc":
            comments = comments.order_by("-created_at")
        else:
            comments = comments.order_by("created_at")

        serializer = CommentSerializer(comments, many=True, context={"request": request})
        return Response(serializer.data, status=200)  




class CommentRepliesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, comment_id):
        # يجب جلب التعليق الأساسي (parent) أولاً
        comment = get_object_or_404(Comment, id=comment_id)
        
        # جلب الردود التابعة لهذا التعليق فقط
        replies = comment.replies.all().select_related('user').annotate(
            computed_useful=Count('reactions', filter=Q(reactions__reaction_type='useful')),
            computed_not_useful=Count('reactions', filter=Q(reactions__reaction_type='not_useful')),
            computed_replies=Count('replies')
        ).order_by("created_at") # الردود عادة تُعرض بالتسلسل الزمني

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
           comment = Comment.objects.filter(id=comment.id).select_related('user').annotate(
               computed_useful=Count('reactions', filter=Q(reactions__reaction_type='useful')),
               computed_not_useful=Count('reactions', filter=Q(reactions__reaction_type='not_useful')),
               computed_replies=Count('replies')
           ).first()

           total_comments = Comment.objects.filter(post=post).count()
           return Response({
             "comment": CommentSerializer(comment, context={"request": request}).data,
              "total_comments": total_comments
              }, status=201)
           #return Response(CommentSerializer(comment, context={"request": request}).data, status=201)
        return Response(serializer.errors, status=400)
    




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



#تعديل تعليق و الحذف 
class CommentDetailView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, comment_id):
        comment=Comment.objects.filter(id=comment_id).select_related('user').annotate(
            computed_useful=Count('reactions',filter=Q(reactions__reaction_type='useful')),
            computed_not_useful=Count('reactions',filter=Q(reactions__reaction_type='not_useful')),
            computed_replies=Count('replies')).first()
        if not comment:
            return Response({"message":"Comment not found"},status=404)
        return Response(CommentSerializer(comment,context={"request":request}).data,status=200)
        

    def put(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        # مستخدم غير صاحب التعليق → رفض
        if comment.user != request.user:
            return Response({"message": "You are not allowed to edit this comment."}, status=403)

        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            comment = Comment.objects.filter(id=comment_id).select_related('user').annotate(
                   computed_useful=Count('reactions', filter=Q(reactions__reaction_type='useful')),
                   computed_not_useful=Count('reactions', filter=Q(reactions__reaction_type='not_useful')),
                   computed_replies=Count('replies')
              ).first()
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
       # post = get_object_or_404(Post, id=post_id)
        post = Post.objects.filter(id=post_id).annotate(
           total_comments=Count('comments')
            ).first()
        if not post:
            return Response({"message": "Post not found."}, status=404)
        saved_ids = set(
            SavedPost.objects.filter(user=request.user)
            .values_list("post_id", flat=True)
)
        serializer = PostSerializer(post, context={"request": request,
        "saved_ids": saved_ids,})
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
            post = Post.objects.filter(id=post.id).annotate(
               total_comments=Count('comments')
               ).first()
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
####################################################################################  
# حفظ أو إلغاء حفظ منشور
class ToggleSavePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        existing = SavedPost.objects.filter(user=request.user, post=post).first()

        if existing:
            existing.delete()
            return Response({"message": "Post unsaved.", "is_saved": False}, status=200)

        SavedPost.objects.create(user=request.user, post=post)
        return Response({"message": "Post saved.", "is_saved": True}, status=201)


# جلب المنشورات المحفوظة
class SavedPostsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = Post.objects.filter(
            saved_by__user=request.user
        ).select_related(
            "user"
        ).prefetch_related(
            "images"
        ).annotate(
            total_comments=Count("comments")
        ).order_by("-saved_by__created_at")

        saved_ids = set(
            SavedPost.objects.filter(user=request.user)
            .values_list("post_id", flat=True)
        )
        following_ids = set(
            Follow.objects.filter(follower=request.user)
            .values_list("following_id", flat=True)
        )
        user_reactions = dict(
            Reaction.objects.filter(user=request.user, post__in=posts)
            .values_list("post_id", "reaction_type")
        )

        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(posts, request)

        serializer = PostSerializer(result_page, many=True, context={
            "request": request,
            "saved_ids": saved_ids,
            "following_ids": following_ids,
            "user_reactions": user_reactions,
        })
        return paginator.get_paginated_response(serializer.data)
######################################################################################    
class FeedView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # 1. جلب IDs الأشخاص المتابَعين
        #following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        following_ids = set(Follow.objects.filter(follower=user).values_list('following_id', flat=True))

        # 2. استخراج التاغات المهتمة فيها بناءً على آخر 10 تفاعلات
        # مع استثناء البوستات يلي بتفاعل فيها ب غير مفيد
        user_reactions = Reaction.objects.filter(user=user)\
         .exclude(reaction_type='not_useful')\
          .select_related('post')\
          .order_by('-created_at')[:10] 


        interested_tags = []
        for r in user_reactions:
            if r.post.tags:
                tags_list = r.post.tags 
                if isinstance(tags_list, list):
                    interested_tags.extend(tags_list)
                else:
                    # تحسباً لو كانت التاغات مخزنة كنص مفصول بفاصلة
                    tags_list = str(r.post.tags).replace(',', ' ').split()
                    interested_tags.extend(tags_list)
        
        # استخدام Counter لجلب أكثر 3 تاغات تكراراً (الأكثر اهتماماً)
        tag_counts = Counter(interested_tags)
        unique_tags = [tag for tag, _ in tag_counts.most_common(3)]

        # 3. تجميع الـ IDs وتحديد الأسباب في قاموس (reasons_map)
        reasons_map = {}
        my_posts_ids = list(
           Post.objects.filter(user=user)
           .values_list('id', flat=True)
         )
        for p_id in my_posts_ids:
             reasons_map[p_id] = ""
        # أ. بوستات المتابعين
        following_posts_ids = list(Post.objects.filter(user_id__in=following_ids).values_list('id', flat=True))
        for p_id in following_posts_ids:
            reasons_map[p_id] = "Following"

        # ب. بوستات الاهتمامات
        interest_posts_ids = []
        if unique_tags: 
            tag_query = Q()
            for tag in unique_tags:
                tag_query |= Q(tags__icontains=tag)
            
            interest_posts_ids = list(Post.objects.filter(tag_query)
                .exclude(user_id__in=following_ids)
                .exclude(user=user)
                .values_list('id', flat=True)[:10])
            
            for p_id in interest_posts_ids:
                if p_id not in reasons_map: # لا نغير السبب إذا كان البوست أصلاً من المتابعين
                    reasons_map[p_id] = "Based on your interests" #Suggested for you

        # ج. بوستات الترند (أكثر تفاعل بآخر 3 أيام)
        last_3_days = timezone.now() - timedelta(days=3)
        trending_posts_ids = list(Post.objects.filter(created_at__gte=last_3_days)
            .annotate(reactions_count=Count('reactions'))
            .order_by('-reactions_count')
            .values_list('id', flat=True)[:10])
        
        for p_id in trending_posts_ids:
            if p_id not in reasons_map: # لا نغير السبب إذا كان موجوداً مسبقاً
                reasons_map[p_id] = "Trending 🔥"

        # 4. الدمج والفلترة النهائية بناءً على قائمة الـ IDs المجمعة
        all_ids = my_posts_ids+following_posts_ids + interest_posts_ids + trending_posts_ids
        final_posts = Post.objects.filter(id__in=all_ids)\
            .select_related('user')\
            .prefetch_related('images')\
            .annotate(total_comments=Count('comments'))\
            .distinct()\
            .order_by('-created_at')
        # فلترة حسب النوع (image/video) إذا تم إرساله في الـ Query Params
        post_type = request.GET.get("type")
        if post_type:
            final_posts = final_posts.filter(post_type=post_type)

        # الترتيب الزمني النهائي (الأحدث أولاً)

     # هاد في حال حبينا دائما نجيب منشورات الاشخاص يلي منتابعن بالاول
        # final_posts = final_posts.annotate(
        #   priority=Case(
        #     When(user_id__in=following_ids, then=Value(1)), # المتابعين لهم الأولوية 1
        #     default=Value(2),                              # المقترح له الأولوية 2
        #     output_field=IntegerField(),
        #     )
        # ).order_by('priority', '-created_at')
        paginator = PageNumberPagination()
        paginator.page_size = 5  # عرض 5 بوستات في كل صفحة
        
        result_page = paginator.paginate_queryset(final_posts, request)

        for post in result_page:
            post.suggestion_reason = reasons_map.get(post.id, "")
        # following_ids_set = set(
        #     Follow.objects.filter(follower=request.user)
        #     .values_list('following_id', flat=True)
        #       )
        user_reactions_map = dict(
             Reaction.objects.filter(user=request.user, post__in=result_page)
            .values_list('post_id', 'reaction_type')
             )
        saved_ids = set(
          SavedPost.objects.filter(user=request.user)
          .values_list("post_id", flat=True)
)
        #serializer = PostSerializer(result_page, many=True, context={'request': request})
        serializer = PostSerializer(result_page, many=True, context={
         'request': request,
         'following_ids': following_ids,
         'user_reactions': user_reactions_map,
         'saved_ids': saved_ids
})
        return paginator.get_paginated_response(serializer.data)


#اقتراح مستخدمين بناءً على التخصص
class SuggestedUsersView(APIView):
    """شغالة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user
        
        # تحضير بيانات المستخدم الحالي
        user_words_normalized = normalize_specialization(current_user.specialization)
        user_words_expanded = expand_words(user_words_normalized)

        # لو ما في تخصص واضح — رح الاقتراحات تكون عشوائية كلياً
        if not user_words_normalized:
            candidates_list = list(candidates)
            random.shuffle(candidates_list)
            final_users = candidates_list[:15]
            serializer = UserSuggestionSerializer(...)
            return Response(serializer.data, status=200)

        # جلب المرشحين (استثناء النفس ومن أتابعهم)
        following_ids = set(
            Follow.objects.filter(follower=current_user)
            .values_list("following_id", flat=True))
        candidates = User.objects.exclude(id=current_user.id)\
        .exclude(id__in=following_ids)\
        .exclude(specialization__isnull=True)\
        .exclude(specialization="")\
        .annotate(followers_count=Count('followers_set')) 
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
        #final_users = [u for _, u in scored_users[:8]]

        # ج. إذا كان مجالك فيه أقل من 8، نكمل الباقي من الغرباء عشوائياً (Shuffle)
        # if len(final_users) < 8:
        #     remaining_from_scored = [u for _, u in scored_users[8:]]
        #     fallback_pool = remaining_from_scored + zero_score_users
        #     random.shuffle(fallback_pool)
            
        #     needed = 8 - len(final_users)
        #     final_users.extend(fallback_pool[:needed])


        # أول 5 — نفس المجال (score عالي)
        high_match = [u for _, u in scored_users if _ >= 5][:5]

        # ثاني 5 — مجالات مشابهة (score متوسط)
        mid_match = [u for _, u in scored_users if 1 <= _ < 5][:5]

        # آخر 5 — مجالات مختلفة (fallback)
        random.shuffle(zero_score_users)
        low_match = zero_score_users[:5]
        #بس يصير عنا مستخدمين كتير برجع هالسطرين
        # random.shuffle(high_match)
        # random.shuffle(mid_match)

        final_users = high_match + mid_match + low_match

        serializer = UserSuggestionSerializer(
           final_users,
           many=True,
           context={
        "request": request,
        "following_ids": following_ids,
    }
)
        return Response(serializer.data, status=200)
  

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
          following_ids_set = set(
            Follow.objects.filter(follower=request.user)
            .values_list('following_id', flat=True)
)
          serializer = SearchUserSerializer(
          page,
          many=True,
          context={"request": request, "following_ids": following_ids_set}
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
            query = query.replace(" ", "_")
            posts = Post.objects.filter(
              tags__icontains=query
            ).select_related(
              "user"
            ).prefetch_related(
             "images"
            ).annotate(
            total_comments=Count("comments", distinct=True),   
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
            saved_ids = set(
                    SavedPost.objects.filter(user=request.user)
                    .values_list("post_id", flat=True)
                )
            serializer = PostSerializer(
               page,
               many=True,
              context={"request": request, "saved_ids": saved_ids}
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
          total_comments=Count("comments", distinct=True),    
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
          saved_ids = set(
                    SavedPost.objects.filter(user=request.user)
                    .values_list("post_id", flat=True)
                )
          serializer = PostSerializer(
            page,
            many=True,
            context={"request": request, "saved_ids": saved_ids}
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
            history_map = {h.query: h.id for h in history_qs} 
            users_map={u.username: u for u in User.objects.filter(username__in=usernames).exclude(id=request.user.id)}
            sorted_users=[]
            for name in usernames:
               if name  in users_map:
            #     sorted_users.append(users_map[name])
                   sorted_users.append({
                      "id": history_map.get(name),  # ← id سجل البحث
                      "user": SearchUserSerializer(users_map[name], context={"request": request}).data
            })
           
           
            # users = (
            #     User.objects
            #     .filter(username__in=usernames)
            #     .exclude(id=request.user.id)
            # )
            following_ids_set = set(
               Follow.objects.filter(follower=request.user)
               .values_list('following_id', flat=True)
)
            serializer = SearchUserSerializer(
                sorted_users,
                many=True,
                context={"request": request, "following_ids": following_ids_set}
            )

            return Response({
                "type": "people",
                #"count": len(serializer.data),
                #"results": serializer.data
                "results": sorted_users
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
                        "id":h.id,
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
                        "id":h.id,
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
          query_lower = query.lower()   
          query_lower = query.replace(" ", "_")                                     # هيك شكل التاغات المخزنة هون
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


#################################################################################################  

# ترجمة المنشور
class TranslatePostView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]
    def post(self, request):

        post_id = request.data.get("post_id")
        if not post_id:
            return Response({"error": "post_id required"}, status=400)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        translated_data = {}

        try:
            if post.content:
                translated_data["content"] = translate_text(post.content)
                time.sleep(0.2) # ممكن اذا صار عنا مشاكل نزيدو لل 0.5 بصير اضمن

            # if post.ai_improved:
            #     translated_data["ai_improved"] = translate_text(post.ai_improved)
            #     time.sleep(0.2)

            # if post.ai_generated:
            #     translated_data["ai_generated"] = translate_text(post.ai_generated)
            #     time.sleep(0.2)

            # if post.ai_code_summary:
            #     translated_data["ai_code_summary"] = translate_text(post.ai_code_summary)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return Response(translated_data)
    



#عرض النص الاصلي للمنشور
class ShowOriginalPostView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]
    def post(self, request):

        post_id = request.data.get("post_id")

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        original_data = {
            "content": post.content,
           # "ai_improved": post.ai_improved,
           # "ai_code_summary": post.ai_code_summary,
           # "ai_generated": post.ai_generated
        }

        return Response(original_data)


# ترجمة التعليقات
class TranslateCommentView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    def post(self, request):

        comment_id = request.data.get("comment_id")

        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)

        return Response({
            "content": comment.content
        })


#الترجمة 
class TranslateTextView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        text = request.data.get("content")
        
        if not text:
            return Response({"error": "text is required"}, status=400)
        
        return Response({
            "translated": translate_text(text)
        })


#############################################################################   
# لجلب عدد الإشعارات غير المقروءة للمستخدم مشان شغلة تطلع النقطة الحمرا للمستخدم انو عندو اشعار جديد 
"""
وظيفتها: ترجع بس "رقم" (مثلاً: 5).

 . هاد الرابط هو اللي بيستخدموه كل 30 ثانية (
عشان رفقاتك بالفرونت يحطوا هاد الرقم فوق "النقطة الحمراء" اللي على أيقونة الجرس
polling
"""
class UnreadNotificationsCountView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # منعد الإشعارات اللي لسا ما انقرت (is_read=False)
        count = request.user.notifications.filter(is_read=False).count()
        return Response({"unread_count": count})


# لجلب قائمة الإشعارات كاملة (مع تفاصيل كل إشعار) مرتبة من الأحدث للأقدم
class NotificationListView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # جلب إشعارات المستخدم مرتبة من الأحدث
        #notifications = request.user.notifications.all().order_by('-created_at')
        notifications = request.user.notifications\
          .select_related('from_user', 'post', 'comment')\
          .prefetch_related('post__images', 'comment__post__images')\
          .order_by('-created_at')[:25]
        serializer = NotificationSerializer(notifications, many=True, context={'request': request})
        return Response(serializer.data)

    # def post(self, request):
    #     return Response({"detail": "Notifications count reset."})        
    

# لعلامة إشعار معين كمقروء (لما المستخدم يضغط على الإشعار )
class MarkNotificationReadView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # منجيب الإشعار بناءً على الـ ID (pk) وبشرط يكون للمستخدم الحالي
            notification = Notification.objects.get(pk=pk, to_user=request.user)
            notification.is_read = True
            notification.save()
            return Response({"detail": "Notification marked as read."}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)



#مشان نستلم التوكن الخاص بمتصفح كل مستخدم
class UpdateFCMTokenView(APIView):
    "شغالة"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if token:
            user = request.user
            user.fcm_token = token
            user.save()
            return Response({"message": "Token updated successfully"})
        return Response({"error": "No token provided"}, status=400)    
#####################################################################################

# لارسال الكود على الايميل
class SendOTPView(APIView):
    "شغالة"
    permission_classes = [AllowAny] # أي شخص يستطيع طلب الكود

    def post(self, request):
        email = request.data.get('email')
        
        # 1. التأكد أن الإيميل مسجل في المنصة
        if not User.objects.filter(email=email).exists():
            return Response({"error": "User with this email don't exist"}, status=status.HTTP_404_NOT_FOUND)

        # 2. توليد رقم عشوائي من 6 خانات
        otp_code = str(random.randint(100000, 999999))

        # 3. حفظ الكود في قاعدة البيانات (تحديث إذا كان موجوداً أو إنشاء جديد)
        # PasswordResetCode.objects.update_or_create(
        #     email=email, 
        #     defaults={'code': otp_code}
        # )
        PasswordResetCode.objects.filter(email=email).delete()
        PasswordResetCode.objects.create(
            email=email,
            code=otp_code,
            attempts=0
        )

        # 4. إرسال الإيميل الحقيقي
        subject = "Password Reset Verification Code"
        message = f"Hello, welcome to DevConnect .\nYour verification code is: {otp_code}\nThis code is valid for 10 minutes."
        html_message = f"""
              <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
              <h2 style="color: #007bff; text-align: center;">DevConnect</h2>
              <hr>
              <p style="font-size: 16px; color: #333;">Hello,</p>
              <p style="font-size: 16px; color: #333;">You requested to reset your password. Use the verification code below to proceed:</p>
              <div style="background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
              <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #007bff;">{otp_code}</span>
              </div>
              <p style="font-size: 14px; color: #777;">This code is valid for 10 minutes. If you didn't request this, please ignore this email.</p>
              <hr>
              <p style="font-size: 12px; color: #aaa; text-align: center;">© 2026 DevConnect - Programmers Platform</p>
              </div>
              """
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email],html_message=html_message)
            return Response({"message": "Verification code has been sent to your email.Please check your inbox."}, status=status.HTTP_200_OK)
        except Exception as e:
           # return Response({"error": "Failed to send email. Please check your connection or settings."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
            return Response({"error": str(e)}, status=500)

# التحقق من صحة الكود وتغيير كلمة المرور
class VerifyOTPView(APIView):
    "شغالة"
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        
        # التأكد من تطابق كلمتي المرور
        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({"error": "Password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

       # البحث عن السجل بالإيميل فقط أولاً لفحص المحاولات والوقت
        try:
            record = PasswordResetCode.objects.get(email=email)
        except PasswordResetCode.DoesNotExist:
            return Response({"error": "No reset request found for this email."}, status=400)

        #  فحص عدد المحاولات الفاشلة (أمان ضد التخمين)
        if record.attempts >= 5:
            record.delete() 
            return Response({"error": "Too many failed attempts. Please request a new code."}, status=400)

        #  فحص وقت انتهاء الصلاحية (10 دقائق)
        if timezone.now() > record.created_at + timedelta(minutes=10):
            record.delete()
            return Response({"error": "Verification code has expired."}, status=400)
        
        # التحقق من صحة الكود 
        if record.code != otp:
            record.attempts += 1 # زيادة عدد المحاولات الفاشلة
            record.save()
            return Response({"error": f"Invalid code. "}, status=400)
        #  إذا الكود صح، نغير كلمة مرور المستخدم الحقيقي
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password) # دجانغو بيشفر الباسورد تلقائياً هون
            user.save()

            #  مسح الكود من الجدول لكي لا يُستخدم مرة أخرى (للأمان)
            record.delete()

            return Response({"message": "Password reset successfully!"}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)      

###########################################################################################

#  توليد التاغات بالذكاء
class SuggestTagsView(APIView):
    "نهائي"
    def post(self, request):
        content = request.data.get('content', '')

        if not content:
            return Response({"error": "المحتوى فارغ، لا يمكن توليد تاغات."}, status=status.HTTP_400_BAD_REQUEST)

        url = "https://api.groq.com/openai/v1/chat/completions"
        
       
        system_instruction = (
            "You are an expert in extracting high-quality technical tags.\n\n"

            "TASK:\n"
            "- Extract the MOST relevant and specific technical tags from the content.\n\n"

            "STRICT RULES:\n"
            "1. Return ONLY tags separated by commas.\n"
            "2. NO explanations, NO sentences.\n"
             "  . NO translations.\n"
            "6. NEVER say things like 'Here are the tags'.\n"
            "7. NEVER explain the language.\n"
            "8. NEVER respond with full sentences.\n"
            "3. NO generic tags like 'technology', 'software', 'system'.\n"
            "4. Focus on:\n"
            "   - Programming languages (Python, Java, etc.)\n"
            "   - Frameworks (Django, React, etc.)\n"
            "   - Concepts (AI, Machine Learning, APIs, etc.)\n"
            "5. Maximum 7 tags.\n"
            "6. Output MUST be in English ONLY.\n"
            "7. Avoid single-word tags that are too broad (e.g., 'code', 'project').\n"
            "8. if the extracted tag is two words, connect them with an underscore (e.g., 'machine_learning' instead of 'machine learning').\n"
           # "8. if the extracted tag is two words,connect them  together without space (e.g., 'machinelearning' instead of 'machine learning').\n"
        )

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Extract the most important tags from this text:\n\n{content}"}
            ],
            "temperature": 0.1
        }

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload,timeout=20)
            response.raise_for_status()
            result = response.json()
            tags_string = result['choices'][0]['message']['content'].strip()
        
            tags_list = [tag.strip() for tag in tags_string.split(',') if tag.strip()]

            return Response({
                "tags": tags_list
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###############################################################################################

#شرح الكود 

#هاد منبعتلو اللغة تبعت المستخدم 
# class ExplainCodeAPIView(APIView):
#     "شغالة" "ولكن البرومت تبع العربي بدو تعدييييل منيح "
#     permission_classes = [IsAuthenticated]

#     def post(self, request):

#         user_code = request.data.get("code_content")
#         user_lang = request.data.get("language", "en") # افتراضياً إنجليزي إذا ما انبعتت

#         if not user_code:
#             return Response({"error": "No code content provided"}, status=status.HTTP_400_BAD_REQUEST)
#         if user_lang == 'ar':
#            system_instruction = (
#     "أنت Senior Backend Developer تشرح الكود بأسلوب بشري احترافي واضح. "
#     "ابدأ بجملة قصيرة تعطي فكرة الكود أو وظيفته بشكل مباشر بدون استخدام أي عناوين مثل (الهدف). "
#     "بعدها اكتب فقرة واحدة تشرح اللوجيك بشكل تقني، . "
#     "اكتب وكأنك تشرح لزميل مبرمج وليس كأنك تكتب مقال."
#     "استخدم مصطلحات البرمجة بالإنجليزية داخل النص العربي بشكل طبيعي بدون ما تخرب ترتيب الجملة. "
#     "ركّز على كيف الكود يشتغل، شو بيعمل، وليش. "
#     "تجنب الحشو والمقدمات العامة وخليك مباشر."
#     "لا تكتب باللغة الروسية ابدا"
#           )

#            user_prompt = f"اشرح الكود التالي:\n\n{user_code}"
#         else:
#             system_instruction = (
#                 "You are a Senior Backend Developer. Explain the code in one focused technical paragraph starting with the Goal. "
#                 "STRICT RULES: "
#                 "1. Start with (Goal: [Code Function]) then proceed to technical logic. "
#                 "2. Use professional dev language. NO 'In this code' or 'There is a class'. "
#                 "3. NO Russian, NO markdown stars (*), NO bullet points. "
#                 "4. Keep it concise and direct."
#             )
#             user_prompt = f"Give me the goal and the logic of this code in a professional dev style:\n\n{user_code}"
#         url = "https://api.groq.com/openai/v1/chat/completions"
 
#         headers = {
#             "Authorization": f"Bearer {settings.GROQ_API_KEY}",
#             "Content-Type": "application/json"
#         }
         
        
#         payload = {
#             "model": "llama-3.3-70b-versatile",
#             "messages": [
#                 {"role": "system", "content": system_instruction},
#                 {"role": "user", "content": user_prompt}
#             ],
#             "temperature": 0.3 # لضمان رد رصين ومختصر
#         }

#         try: #ارسال الطلب لـ Groq
#             response = requests.post(url, json=payload, headers=headers)
#             result = response.json()
            
#             if 'choices' in result:
#                 explanation = result['choices'][0]['message']['content'].strip()
#                 return Response({
#                     "explanation": explanation,
#                     #"status": "success",
#                     #"language_used": user_lang
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({
#                     "error": "Failed to get response from Groq",
#                     "details": result
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({
#                 "error": "Connection error",
#                 "details": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExplainCodeAPIView(APIView):
    "نهائي"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_code = request.data.get("code_content")
        user_lang = request.data.get("language", "ar")  

        if not user_code:
            return Response(
                {"error": "No code content provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  اختيار البرومبت حسب اللغة
        if user_lang == 'ar':
            system_instruction = (
                "أنت Senior Backend Developer تشرح الكود لزميل مبرمج.\n\n"

                "RULES:\n"
                "- ابدأ بجملة قصيرة توضح الفكرة العامة مباشرة.\n"
                "- بعدها اشرح هالكود في فقرة واحدة فقط.\n"
                "- لا تستخدم عناوين.\n"
                "- لا تستخدم نقاط أو lists.\n"
                "- لا تكرر الكلام.\n"
                "- لا تكتب شرح عام أو نظري.\n"
                "- ركّز على كيف الكود يشتغل فعلياً.\n"
                "- استخدم مصطلحات البرمجة بالإنجليزية داخل النص العربي بشكل طبيعي.\n"
                "- خليك مختصر ودقيق.\n"
                "- لا تكتب أي لغة غير العربية والإنجليزية للمصطلحات التقنية فقط.\n"
            )

            user_prompt = f"اشرح الكود التالي:\n\n{user_code}"

        else:
            system_instruction = (
                "You are a Senior Backend Developer explaining code to another developer.\n\n"
                "RULES:\n"
                "- Start with one short sentence summarizing what the code does.\n"
                "- Then explain the logic in ONE paragraph only.\n"
                "- No bullet points, no lists, no headers.\n"
                "- No generic phrases.\n"
                "- Be concise and technical.\n"
                "- Focus on how the code works internally.\n"
            )

            user_prompt = f"Explain this code:\n\n{user_code}"

        # إعداد الطلب
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            result = response.json()

            if 'choices' in result and result['choices']:
                explanation = result['choices'][0]['message']['content'].strip()
                explanation = re.sub(r'[\u4E00-\u9FFF\u3400-\u4DBF]', '', explanation)

                explanation = explanation.replace("شفرة برمجية", "كود")
                explanation = explanation.replace("الشفرة", "الكود")
                explanation = explanation.replace("شفرة", "كود")

                explanation = explanation.replace("الفئة", "الكلاس")
                explanation = explanation.replace("فئة", "كلاس")

                if not explanation:
                    explanation = "No explanation generated"

                return Response({
                    "explanation": explanation,
                }, status=status.HTTP_200_OK)

            else:
                return Response({
                    "error": "Failed to get response from AI",
                    "details": result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": "Connection error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ExplainCodeLineByLineAPIView(APIView):
    """شرح الكود سطر بسطر"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_code = request.data.get("code_content")
        user_lang = request.data.get("language", "ar")

        if not user_code:
            return Response(
                {"error": "No code content provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_lang == 'ar':
#             system_instruction = (
#                 "أنت Senior Backend Developer  بتشرح كود لمبرمج مبتدئ.\n\n"
#                 "RULES:\n"
#                 "- قسّم الكود لـ sections منطقية (مثلاً:  fields،  validation،  save).\n"
#                 "- لكل section:\n"
#                 "  1. حط الكود.\n"
#                 "  2. اكتب 2-3 جمل: شو بيعمل ولیش موجودة بهالكود .\n"
#                 "- ربط الـ sections ببعض: قول كيف كل section بتوصل للي بعدها.\n"
#                 "- اختم بجملة وحدة تلخص الـ flow من البداية للنهاية.\n"
#                 "- لا تستخدم bullet points جوا الشرح.\n"
#                 "- لا تشرح الواضح (مثلاً لا تقول 'هاد تعريف كلاس').\n"
#                 "- لا تكرري نفس المعلومة أكثر من مرة داخل نفس الـ section.\n"
#                 "- لا تستخدمي جمل انتقال بين الـ sections مثل 'الآن ننتقل إلى'.\n"
#                 "- لا تكتبي ملخص في النهاية، الـ overall flow جملة وحدة كافية.\n"
#                 "- استخدم مصطلحات البرمجة بالإنجليزية داخل النص العربي.\n"
#                 "- ممنوع استخدام أي حرف ياباني أو صيني أو أي لغة غير العربية والإنجليزية.\n"
#                 "- خليك تقني وواضح.\n"
                
# )
 #           user_prompt = f"اشرح الكود التالي سطر بسطر:\n\n{user_code}"
             system_instruction = (
                "أنت Senior Backend Developer تشرح الكود لمبرمج مبتدئ.\n\n"

                "RULES:\n"
                "- قسّم الكود إلى sections منطقية (مثل: fields، validation، save logic).\n"
                "- لكل section:\n" 
                " 1. اعرض الكود داخل block واضح.\n" 
                " 2. ثم اشرح هذا الجزء بـ 2-3 جمل: ماذا يفعل ولماذا هو موجود.\n"
                "- ممنوع شرح أي section بدون عرض الكود الخاص به أولاً.\n"
                "- اربط الـ sections ببعض بشكل طبيعي ووضح كيف ينتقل الـ flow بينها.\n"
                "- اختم بجملة واحدة تلخص الـ overall flow من البداية للنهاية.\n"
                "- لا تستخدم bullet points داخل الشرح.\n"
                "- لا تشرح الأمور الواضحة جداً.\n"
                "- لا تكرر نفس الفكرة داخل نفس الـ section.\n"
                "- استخدم مصطلحات البرمجة بالإنجليزية داخل النص العربي بشكل طبيعي.\n"
                "- ممنوع استخدام أي أحرف غير العربية والإنجليزية.\n"
                "- اجعل الشرح تقني لكن واضح وسهل القراءة.\n")

             user_prompt = f"Explain this code step by step:\n\n{user_code}"

        else:
            system_instruction = (
                "You are a Senior Backend Developer explaining code to a junior developer.\n\n"
                "RULES:\n"
                "- Split the code into logical sections (e.g., fields, validation, save logic).\n"
                "- For each section:\n"
                "  1. Show the code block.\n"
                "  2. Write 2-3 sentences: what it does AND why it exists in this context.\n"
                "- Connect sections: briefly mention how each section feeds into the next.\n"
                "- End with one sentence: the overall flow from input to output.\n"
                "- No bullet points inside explanations.\n"
                "- No restating the obvious (e.g. don't say 'this is a class definition').\n"
                "- Do NOT add connector sentences between sections, the headers make the flow clear.\n"
                "- Be technical but readable.\n"
            )
            user_prompt = f"Explain this code step by step:\n\n{user_code}"

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,  
            "max_tokens": 1500    
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            result = response.json()

            if 'choices' in result and result['choices']:
                explanation = result['choices'][0]['message']['content'].strip()

                explanation = re.sub(r'[\u3000-\u9FFF\uAC00-\uD7AF]', '', explanation)

                # توحيد المصطلحات
                explanation = explanation.replace("شفرة برمجية", "كود")
                explanation = explanation.replace("الشفرة", "الكود")
                explanation = explanation.replace("شفرة", "كود")
                explanation = explanation.replace("الفئة", "الكلاس")
                explanation = explanation.replace("فئة", "كلاس")

                if not explanation:
                    explanation = "No explanation generated"

                return Response(
                    {"explanation": explanation},
                    status=status.HTTP_200_OK
                )

            else:
                return Response({
                    "error": "Failed to get response from AI",
                    "details": result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": "Connection error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# هاد الكود بيشرح بالعربي فقط 
# class ExplainCodeAPIView(APIView):
#      "شغالة"
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user_code = request.data.get("code_content")
        
#         if not user_code:
#             return Response({"error": "No code content provided"}, status=status.HTTP_400_BAD_REQUEST)

#         GROQ_API_KEY = "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" 
#         url = "https://api.groq.com/openai/v1/chat/completions"
        
#         groq_headers = {
#             "Authorization": f"Bearer {GROQ_API_KEY}",
#             "Content-Type": "application/json"
#         }
#         payload = {
#             "model": "llama-3.1-8b-instant",
#             "messages": [
#                 {
#                     "role": "system", 
#                     "content": (
#                         "أنت خبير برمجي. وظيفتك شرح منطق الكود بأسلوب 'المختصر المفيد'. "
#                         "تجنب التحية، وتجنب شرح الأمور البديهية، ولا تضع أمثلة استخدام إلا إذا طلبت منك. "
#                         "ركز فقط على وظيفة الكود الأساسية ."
#                     )
#                 },
#                 {
#                     "role": "user", 
#                     "content": f"اشرح هذا الكود باختصار شديد:\n\n{user_code}"
#                 }
#             ],
#             "temperature": 0.3 # تقليل العشوائية ليظل الرد دقيقاً ومختصراً
#         }
#         # 3. إرسال الطلب لـ Groq
#         try:
#             response = requests.post(url, json=payload, headers=groq_headers)
#             result = response.json()
            
#             if 'choices' in result:
#                 explanation = result['choices'][0]['message']['content']
#                 return Response({
#                     "explanation": explanation,
#                     "status": "success"
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({
#                     "error": "Failed to get explanation from AI",
#                     "details": result
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({
#                 "error": "Connection error",
#                 "details": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


####################################################################################


# class GeneratePostAPIView(APIView):
#     """
#    بيكتشف اللغة تلقائياً وبيولد منشور احترافي بناءً على المحتوى
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         # 1. استلام محتوى المنشور (سواء كان فكرة أو مسودة)
#         user_content = request.data.get("content")

#         if not user_content:
#             return Response({"error": "No content provided to enhance"}, status=status.HTTP_400_BAD_REQUEST)

# #         # 2. التعليمات الذكية (توجيه الموديل ليرد بنفس اللغة تلقائياً)
# #         system_instruction = (
# #     "You are a top-tier Tech Influencer and Social Media Strategist. "
# #     "Your goal is to turn boring ideas into 'VIRAL' posts. "
# #     "STYLE RULES: "
# #     "1. Hook the reader with a powerful first sentence. "
# #     "2. Use a professional yet 'enthusiastic' and modern tone. "
# #     "3. Keep it exactly 5 punchy sentences. "
# #     "4. NO robot talk (e.g., avoid 'In conclusion', 'It is important to'). "
# #     "5. Use the SAME LANGUAGE as the user (Arabic or English).no russian.no other language "
# #     "6. NO translations, NO explanations. Just the post."
#         system_instruction = (
# "You are a top-tier Tech Influencer and Social Media Strategist. "
# "Your goal is to turn ideas into VIRAL posts. "

# "LANGUAGE RULES: "
# "If the input is Arabic: "
# "- Write in natural, human Arabic (not formal, not translated). "
# "- Use smooth, conversational tone like real social media posts. "
# "- Avoid literal translation from English. "
# "- Keep sentences short, punchy, and well-flowing. "

# "If the input is English: "
# "- Use a modern, enthusiastic, professional tone. "

# "GENERAL RULES: "
# "- Think about the idea in English first, then write in the user's language. "
# "- Hook the reader with a strong first sentence. "
# "- Write exactly 5 punchy sentences. "
# "- No robotic phrases. No introductions. "
# "- No Russian, no other languages."
# )


#         # 3. إعدادات Groq
#         url = "https://api.groq.com/openai/v1/chat/completions"
        
#         headers = {
#             "Authorization": f"Bearer {settings.GROQ_API_KEY}",
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#              #"model": "gemma2-9b-it",
#             # "model": "llama-3.1-8b-instant",
#             "model": "llama-3.3-70b-versatile",
#             "messages": [
#                 {"role": "system", "content": system_instruction},
#                 {"role": "user", "content": f"Enhance this content into a 5-sentence post: {user_content}"}
#             ],
#             "temperature": 0.4,
#             "max_tokens":300

#         }

#         try:
#             response = requests.post(url, json=payload, headers=headers,timeout=20)
#             result = response.json()
            
#             if 'choices' in result:
#                 enhanced_post = result['choices'][0]['message']['content'].strip()
                
#                 return Response({
#                     "enhanced_post": enhanced_post,
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "AI Generation failed"}, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({"error": "Connection error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class GeneratePostAPIView(APIView):
    "نهائي"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_content = request.data.get("content")

        if not user_content:
            return Response(
                {"error": "No content provided to enhance"},
                status=status.HTTP_400_BAD_REQUEST
            )

        system_instruction = (
            "You are a top-tier Tech Influencer and Social Media Strategist. "
            "Your goal is to turn ideas into VIRAL posts.\n\n"

            "LANGUAGE RULES:\n"
            "- Detect the language of the input automatically.\n"
            "- If the input is clearly English → respond in English ONLY.\n"
            "- If the input is clearly Arabic → respond in Arabic ONLY.\n"
            "- do not use RUSSIAN words or characters\n"
            "- NEVER switch language or translate.\n\n"

            "ARABIC STYLE (when input is Arabic):\n"
            "- Write like a REAL human, not a translator.\n"
            "- Use simple, smooth, conversational Arabic.\n"
            "- Avoid formal, textbook, or heavy Arabic.\n"
            "- DO NOT translate from English literally.\n"
            "- Use natural phrasing like real social media posts.\n"
            "- Keep flow between sentences (important).\n"
            "- Fix any broken words or typos in the input.\n"
            "- Do NOT copy strange characters or corrupted text.\n"
            "- Prefer short sentences over long complex ones.\n\n"
            "- Make it sound like how people actually post on LinkedIn or Twitter.\n"
            "- Keep technical terms in English (e.g., web development, API, database,..etc).\n"
            "- Do NOT translate or transliterate technical terms into Arabic.\n"

            "ENGLISH STYLE:\n"
            "- Modern, confident, engaging tone.\n\n"

            "GENERAL RULES:\n"
            "- Think in English internally, but output in user's language.\n"
            "- Start with a strong hook.\n"
            "- Write EXACTLY 5 punchy sentences.\n"
            "- No robotic phrases.\n"
            "- No introductions.\n"
            "- No hashtags.\n"
            "- No emojis.\n"
            "- No Russian or other languages.\n"
            #"- Keep technical terms in English (e.g., web development, API, database,..etc).\n"
            "- Keep technical terms in English .\n"
            "- Do NOT translate or transliterate technical terms into Arabic.\n"
            "- Use ONLY valid Arabic or English characters. Do NOT generate any strange Unicode symbols or foreign characters.\n"
        )

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": f"""
                        Detect the language of this text and respond in the SAME language.
                        IMPORTANT:
                        If the text is Arabic, REWRITE it in a clean, natural, human way (not translation).
                        Turn it into a viral 5-sentence post:
                        {user_content}
                        """            }
            ],
            "temperature": 0.35,   
            "max_tokens": 500
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if response.status_code != 200:
                return Response(
                    {"error": "Groq API error", "details": response.text},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = response.json()

            if 'choices' in result:
                enhanced_post = result['choices'][0]['message']['content'].strip()
                enhanced_post = re.sub(r'[\u4E00-\u9FFF\u3400-\u4DBF]', '', enhanced_post)
                return Response({
                    "enhanced_post": enhanced_post,
                }, status=status.HTTP_200_OK)

            return Response(
                {"error": "AI Generation failed", "details": result},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": "Connection error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )      

##################################################################################################
# class ImprovePostAPIView(APIView):
#     "نهائي"
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user_text = request.data.get("content")

#         if not user_text:
#             return Response({"error": "No text provided to improve"}, status=status.HTTP_400_BAD_REQUEST)

#         system_instruction = (
#             "You are a professional multilingual editor. "
#             "Your task is to improve the user's text while keeping the exact meaning.\n\n"
#             #"- Use strong, professional wording instead of basic or vague phrases.\n"

#             "LANGUAGE RULES:\n"
#             "- Detect the input language automatically.\n"
#             "- If the input is English → respond in English ONLY.\n"
#             "- If the input is Arabic → respond in Arabic ONLY.\n"
#             "- NEVER translate.\n\n"

#             "ARABIC RULES:\n"
#             "- Rewrite in clean, natural, human Arabic.\n"
#             "- Avoid formal or academic language.\n"
#             "- Make it smooth and easy to read.\n\n"
#             "- Keep technical terms in English (e.g., web development, API, database,..etc).\n"
#             "- Do NOT translate or transliterate technical terms into Arabic.\n"


#             "GENERAL RULES:\n"
#             "- Fix grammar, clarity, and flow.\n"
#             "- Do NOT change the meaning.\n"
#             "- Do NOT add extra information.\n"
#             "- Keep technical terms in English (e.g., web development, API, database,..etc).\n"
#             "- Do NOT translate or transliterate technical terms into Arabic.\n"
#             "- Do NOT add hashtags or explanations.\n"
#             "- Do NOT generate strange characters or corrupted symbols.\n"
#             "- If the text has typos, fix them.\n"
#             "- Do NOT explain your reasoning."
#             " Do NOT output any thinking process."
#                 )
        
#         url = "https://api.groq.com/openai/v1/chat/completions"
        
#         headers = {
#             "Authorization": f"Bearer {settings.GROQ_API_KEY}",
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#             #"model": "gemma2-9b-it",
#             "model": "llama-3.3-70b-versatile",
#             #"model": "qwen/qwen3-32b",
#             "messages": [
#                 {"role": "system", "content": system_instruction},
#                 {"role": "user", "content": f"""
#                     Detect the language of this text.
#                     IMPORTANT:
#                         - If it's English → respond in English ONLY.
#                         - If it's Arabic → respond in Arabic ONLY.
#                         - Do NOT translate.
#                          Rewrite it professionally:{user_text}"""   }
#             ],
#             "temperature": 0.2 ,
#              "max_tokens": 300
#         }
#         try:
#           response = requests.post(url, json=payload, headers=headers, timeout=20)
#           result = response.json()
#           if 'choices' in result:
#                 improved_text = result['choices'][0]['message']['content'].strip()
#         # تنظيف النص من المحارف الغريبة
#                 improved_text = re.sub(r'[\u4E00-\u9FFF\u3400-\u4DBF]', '', improved_text)                
#                 return Response({
#                     "improved_text": improved_text,
#                      }, status=status.HTTP_200_OK)

#           else:
#                return Response({
#                 "error": "AI Improvement failed",
#                  "details": result
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({
#         "error": "Connection error",
#         "details": str(e)
#     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImprovePostAPIView(APIView):
    "نهائي"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_text = request.data.get("content")

        if not user_text:
            return Response({"error": "No text provided to improve"}, status=status.HTTP_400_BAD_REQUEST)

        system_instruction = (
            "You are a professional multilingual editor. "
            "Your task is to professionally rewrite the user's text to make it clearer, smoother, and more engaging while fully preserving the original meaning."            #"- Use strong, professional wording instead of basic or vague phrases.\n"

            "LANGUAGE RULES:\n"
            "- Detect the input language automatically.\n"
            "- If the input is English → respond in English ONLY.\n"
            "- If the input is Arabic → respond in Arabic ONLY.\n"
            "- NEVER translate.\n\n"
            "- Output ONLY the rewritten text.\n"
            "- Never say things like 'Here is the rewritten version'.\n"
            "- Never mention the detected language.\n"

            "ARABIC RULES:\n"
            "- Rewrite in clean, natural, human Arabic.\n"
            "- Avoid formal or academic language.\n"
            "- Make it smooth and easy to read.\n\n"
            "- Make the writing feel natural and expressive.\n"
            "- Use smoother and more engaging wording when appropriate.\n"
            "-  enhance the style while preserving the original meaning.\n"
            "- Keep the text realistic and human, not dramatic.\n"
            "- Keep technical terms in English \n"
            "- Do NOT translate or transliterate technical terms into Arabic.\n"
           

            "GENERAL RULES:\n"
            "- Fix grammar, clarity, and flow.\n"
            "- Do NOT change the meaning.\n"
            "- Do NOT add extra information.\n"
           # "- Keep technical terms in English (e.g. API, database,..etc).\n"
            "- Do NOT translate or transliterate technical terms into Arabic.\n"
            "- Do NOT add hashtags or explanations.\n"
            "- Do NOT generate strange characters or corrupted symbols.\n"
            "- If the text has typos, fix them.\n"
            "- Do NOT explain your reasoning."
            " Do NOT output any thinking process."
            "- Improve wording and sentence flow naturally.\n"
            "- Keep the tone modern and human.\n"
            "- Keep the original intent and personality of the user.\n"
            "- Do NOT exaggerate or become overly dramatic.\n"
            "- Do NOT turn the text into marketing language.\n"
                )
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            #"model": "gemma2-9b-it",
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Rewrite this professionally:\n\n{user_text}"}
            ],
            "temperature": 0.35,
            "max_tokens": 500
        }
        try:
          response = requests.post(url, json=payload, headers=headers, timeout=20)
          result = response.json()
          if 'choices' in result:
                improved_text = result['choices'][0]['message']['content'].strip()
        # تنظيف النص من المحارف الغريبة
                improved_text = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s.,!?،؟:;()\-\n]','',improved_text)
                improved_text = re.sub(r'\s{2,}', ' ', improved_text).strip()
                return Response({
                    "improved_text": improved_text,
                     }, status=status.HTTP_200_OK)

          else:
               return Response({
                "error": "AI Improvement failed",
                 "details": result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
        "error": "Connection error",
        "details": str(e)
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




########################################################################
  
# class ClassifyPostAPIView(APIView):
#     "نهائي"
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user_content = request.data.get("content")
#         user_lang = request.data.get("language", "en")

#         if not user_content:
#             return Response({"error": "No content provided"}, status=status.HTTP_400_BAD_REQUEST)

#         system_instruction = (
#             "You are a highly accurate classifier for tech content.\n\n"

#             "Classify the input into EXACTLY ONE of these categories:\n"
#             "[question, project, information, article]\n\n"

#             "DEFINITIONS:\n"
#             "- question: asking something (how, why, what, ما هو ,هل, كيف)\n"
#             " project: user built, created, developed, finished, or worked on something "
#             "(e.g., 'I built', 'I created', 'I worked on', 'I finished', 'اشتغلت على', 'بنيت', 'طورت'), "
#             "even if the sentence also includes explanation or opinion\n"        
#             "- information: short factual or simple statement or declarative statement\n"
#             "- article: long, analytical, or opinion-based content\n\n"
#             "- If unclear, choose the closest category. Never output anything outside the 4 categories.\n"

#             "STRICT RULES:\n"
#             "- Output ONLY one word\n"
#             "- No punctuation\n"
#             "- No explanation\n"
#             "- No extra text\n"
            
#         )


#هاد يلي عطاني ياه كلود بس ما جربتو
#  system_instruction = (
#     "You are a post classifier. Classify the post into exactly one of these categories:\n\n"
#     "- question: the user is asking for help or has a problem they need solved\n"
#     "- project: the user is announcing or presenting something they built or completed\n"
#     "- information: the user is sharing a short tip, fact, or useful info\n"
#     "- article: the user wrote a long detailed explanation or tutorial\n\n"
#     "RULES:\n"
#     "- Return ONLY the category name, nothing else\n"
#     "- No explanation, no punctuation, just one word\n"
#     "- If unsure between information and article, check length — short = information, long = article\n"
#     "- project ONLY if the user says they built, finished, or is presenting something they made\n"
# )

# user_prompt = f"Classify this post:\n\n{content}"



#         url = "https://api.groq.com/openai/v1/chat/completions"

#         headers = {
#             "Authorization": f"Bearer {settings.GROQ_API_KEY}",
#             "Content-Type": "application/json"
#         }

#         payload = {
#             "model": "llama-3.1-8b-instant",
#             "messages": [
#                 {"role": "system", "content": system_instruction},
#                 {"role": "user", "content": user_content}
#             ],
#             "temperature": 0.0,
#             "max_tokens": 5
#         }

#         try:
#             response = requests.post(url, json=payload, headers=headers, timeout=15)
#             result = response.json()

#             if 'choices' in result:
#                 post_type = result['choices'][0]['message']['content'].strip().lower()

#                 post_type = "".join(filter(str.isalpha, post_type))

#                 valid = ["question", "project", "information", "article"]
#                 if post_type not in valid:
#                     post_type = "information"


#                 return Response({
#                     "post_type": post_type
#                 }, status=status.HTTP_200_OK)

#             else:
#                 return Response({
#                     "error": "Classification failed",
#                     "details": result
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({
#                 "error": "Connection error",
#                 "details": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





def rule_based_classify(content):
    # 1. الأولوية القصوى للطول: إذا النص طويل جداً فهو مقال، اتركي القرار للـ AI
    if len(content) > 500:
        return "article"        

    if "?" in content or "؟" in content:
        return "question"

    # تنظيف النص: تحويله لصغير وإزالة علامات الترقيم الملتصقة بالكلمات
    # ريجكس يترك فقط الحروف العربية والإنجليزية والأرقام والمسافات
    clean_content = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', content.lower())
    words_set = set(clean_content.split())
        
    project_words = {
        "مشروعي", "تطبيقي", "موقعي", "بنيت", "صممت", "طورت", "أطلقت", "برمجت", 
        "انتهيت من", "اقدم لكم", "حابب شارككم", "رأيكم ببرنامجي", "شغال على مشروع",
        "تجربتي في بناء", "نسخة تجريبية", "لوحة تحكم","مشروع",
        "built", "finished", "presenting", "launched", "i made", "i created",
        "proud to share", "happy to announce", "just released", "my project", 
         "my app", "my website", "github repo", "repository", "deployed", "side project"
    }
    # تقاطع المجموعات (Intersection) أسرع بكثير وأدق
    if words_set.intersection(project_words):
        return "project"
        
    question_words = {
    "كيف", "ما هو", "هل", "ليش", "شو", "لماذا", "متى",  "كيفية",
    "حدا بيعرف", "مين عنده فكرة", "في طريقة لـ", "ممكن مساعدة",
    "عندي مشكلة", "عم يطلعلي خطأ", "كيف حل", "مشكلة في الـ", "error ", 
    "يظهر لي كود", "ليش عم يعلق", "ما عم يشتغل", "ضرب عندي", "فشل الاتصال",
    "how", "what", "why", "when", "where", "is it", "can i", "should i", 
    "how to", "anyone knows", "help with", "error", "issue", "bug", "problem",
    "failed to", "unable to", "not working", "how can ax"
   }
    if words_set.intersection(question_words):
        return "question"
    
    return None




def ai_classify(content):
    # استخدام رابط الـ router الافتراضي والمستقر
    API_URL = "https://router.huggingface.co/hf-inference/models/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
        "X-Wait-For-Model": "true"
    }
    
    payload = {
        "inputs": content,
        "parameters": {
            "candidate_labels": [
                "asking a technical question or seeking help",
                "presenting a completed software product",
                "sharing a useful technical fact or tip",
                "writing a detailed technical article or tutorial"
            ]
        }
    }
    
    label_mapping = {
        "asking a technical question or seeking help": "question",
        "presenting a completed software project": "project",
        "sharing a useful technical fact or tip": "information",
        "writing a detailed technical article or tutorial": "article",
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if isinstance(result, list):
            result = result[0]
        
        if "labels" in result:
            best_label = result["labels"][0]
            return label_mapping.get(best_label, "information")
            
    except Exception:
        pass
        
    return "information" # Fallback دائم في حال حدوث أي خطأ بالشبكة


class ClassifyPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        content = request.data.get("content")

        if not content:
            return Response(
                {"error": "No content provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # الخطوة 1: جرب القواعد الصارمة أولاً
        rule_result = rule_based_classify(content)

        # الخطوة 2: إذا أعطت القواعد جواباً حاسماً، رجعه فوراً (توفير وقت الـ API)
        if rule_result is not None:
            return Response({
                "post_type": rule_result,
                "source": "rules"
            }, status=status.HTTP_200_OK)
        
        # الخطوة 3: الحالات الرمادية أو غير الواضحة نرسلها للـ AI ليفصل فيها بطلب واحد موحد
        ai_result = ai_classify(content)

        return Response({
            "post_type": ai_result,
            "source": "ai"
        }, status=status.HTTP_200_OK)






# class AskAIView(APIView):
#     def post(self, request):
#         post_id = request.data.get('post_id')
#         action = request.data.get('action')  # (summarize, explain_code, analyze_comments)
#         user_lang = request.data.get('lang', 'ar')
        
#         post = get_object_or_404(Post, id=post_id)
#         comments = Comment.objects.filter(post=post).values_list('content', flat=True)
#         comments_text = "\n".join(comments)
#         comments_context = ""
#         if action == 'find_best_answer':
#             # استعلام ذكي جداً: حساب السكور داخل الـ DB والترتيب والحصر بـ 15
#             comments = Comment.objects.filter(post=post, parent__isnull=True).annotate(
#                 computed_useful=Count('reactions', filter=Q(reactions__reaction_type='useful')),
#                 computed_not_useful=Count('reactions', filter=Q(reactions__reaction_type='not_useful'))
#             ).annotate(
#                 score=F('computed_useful') - F('computed_not_useful')
#             ).order_by('-score')[:15].prefetch_related('replies')

#             # بناء النص للـ AI
#             for comment in comments:
#                 comments_context += f"\n[Main Comment ID: {comment.id} | Score: {comment.score}] Content: {comment.content}"
#                 for reply in comment.replies.all():
#                     comments_context += f"\n    -> [Reply to {comment.id}] Content: {reply.content}"
#         else:
#             # للـ Actions الأخرى (Summarize, etc)
#             comments = Comment.objects.filter(post=post).values_list('content', flat=True)
#             comments_context = "\n".join(comments)

#         # قواميس البرومبتات (عشان الكود يضل مرتب)
#             # التعديل هون في الـ f-string
#         prompts = {
#     'summarize': (
#         f"Provide a summary of the content. "
#         f"Text to summarize: {post.content}"
#         f"Structure your response exactly like this: "
#         f"1. Start with a one-sentence General Overview of the topic. "
#         f"2. Follow with exactly 3 numbered key technical takeaways. "
#         f"Respond in {user_lang}. Do not use markdown headers. No introductory phrases."
#     ),
    
#     'explain_code': (
#             f"Analyze the following code strictly. "
#             f"Rules: "
#             f"1. State the core idea of the code in exactly one sentence. "
#             f"2. Explain what the code does clearly and concisely. "
#             f"3. Do NOT add suggestions, best practices, optimizations, or lecture about the code. "
#             f"Respond in {user_lang}. "
#             f"Code: {post.code}"

#     ),

#     'analyze_comments': (
#          f"Analyze these comments and provide a high-level summary. "
#          f"Use exactly this format, no other text:\n"
#          f"1. Discussion Summary: [Provide a brief, narrative summary of the main points, disagreements, or consensus reached in the discussion]\n"
#          #f"1. Main Focus: [One sentence describing the core theme or consensus of the audience]\n"
#          f"2. most important points: [List of specific topics or questions mentioned]\n"
#          f"3. Sentiment: [One word]\n\n"
#          f"Respond in {user_lang}. "
#          f"Rules: Do not use polite filler, do not mention me, do not include introductory phrases. "
#          f"Comments: {comments_text}"
# ),

#     'code_difficulty': (
#             f"Analyze the following code snippet. "
#             f"Rules: "
#             f"1. Difficulty Level: Rate on a scale of 1 to 5 (1=Junior, 5=Expert). "
#             f"2. Reasoning: Provide a one-sentence explanation for this rating based on complexity and library usage. "
#             f"Respond in {user_lang}. "
#             f"Rules: Do not use markdown headers. No introductory phrases. "
#             f"Code: {post.code}"
#             ),
#     #     'find_best_answer': (
#     # f"You are an expert technical auditor. Analyze the following post and its comments. "
#     # f"Your goal is to extract the most technically accurate and helpful and best solution to the question asked in the post. "
#     # f"Rules: "
#     # f"1. Use the 'Score' provided for each main comment to gauge community consensus. "
#     # f"2. Consider content in replies as they might contain corrections or better solutions. "
#     # f"3. Cite which perspective is most valuable without saying 'Commenter X said'. "
#     # f"4. If no clear answer exists, state that 'No definitive solution was found in the discussion'. "
#     # f"Respond in {user_lang}. "
#     # f"Post Question: {post.content} "
#     # f"Comments: {comments_text}"
#     'find_best_answer': (
#                 f"You are a data extraction engine. "
#                 f"Your task is to identify the SINGLE most technically accurate comment (main or reply) that solves the user's problem. "
#                 f"Rules:\n"
#                 f"1. DO NOT summarize the discussion. DO NOT write an essay.\n"
#                 f"2. Output ONLY in the following format:\n"
#                 f"ID: [The ID of the best comment or reply]\n"
#                 f"Content: [Copy the exact content of the comment or reply]\n"
#                 f"Reasoning: [One short sentence explaining why this is the best solution]\n"
#                 f"3. If there is no solution, respond with: 'No definitive solution found'.\n\n"
#                  f"Respond in {user_lang}. "
#                  f"Post Question: {post.content}"
#                 f"Data (Comments and Replies):\n{comments_context}"
#             )
   
#         }

    
                                                                                                                                                                                                  
#         system_instruction = (
#             "أنت مساعد تقني ذكي. "
#             "رد بأسلوب مباشر ومهني. "
#             "استخدم التنسيق فقط إذا كان الطلب يتطلب قائمة (List) أو نقاط، وإلا فاجعل الرد نصاً متصلاً. "
#             "تجنب استخدام النجوم والخطوط العريضة (Markdown formatting) التي قد تسبب مشاكل في العرض."
#                         )        
#         payload = {
#             "model": "llama-3.1-8b-instant",
#             "messages": [
#                 {"role": "system", "content": system_instruction},
#                 {"role": "user", "content": prompts.get(action, "Explain this")}
#             ],
#             "temperature": 0.3
#         }
        
#         headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"}
        
#         # نداء الـ Groq API
#         response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        
#         return Response(response.json()['choices'][0]['message']['content'])            




class SummarizeAPIView(APIView):
    "نهائي"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        content = request.data.get('content')
        lang = request.data.get('lang', 'en')

        if not content:
            return Response(
                {"error": "No content provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        system_instruction = (
            "You are a smart assistant that summarizes content in a natural, human-friendly way.\n\n"
            "Your task is to summarize the given text.\n\n"
            "STRICT OUTPUT FORMAT:\n"
            "[A clear, engaging sentence that captures the main idea — write it as if explaining to a friend]\n\n"
            "● [key point]\n"
            "● [key point]\n"
            "● [add more if needed]\n\n"
            "RULES:\n"
            "- First line: ONE sentence that truly represents the post and  explain its idea — make it meaningful and natural,must feel like a human wrote it, not a machine.\n"
            "- Each point: 1 to 2 natural sentences that explain the idea clearly.\n"
            "- Write in a conversational tone — avoid stiff or mechanical language.\n"
            "- Add as many points as the content requires.\n"
            "- NO headers, NO labels, NO extra text.\n"
            # "- CRITICAL: You MUST write your response in {lang} language ONLY, regardless of the input language.\n"
            # "- If {lang} is Arabic: write complete sentences, use natural flowing Arabic. each point must be 2 sentences maximum, explain the idea and why it matters.\n"
            # "- If {lang} is English: write complete sentences, minimum 10 words per point.\n"
            "- CRITICAL: Detect the language of the input and respond in the SAME language.\n"
            "- If  Arabic: write complete sentences, use natural flowing Arabic. each point must be 2 sentences maximum,\n"
             "- If  English: write complete sentences, maximum 25 words per point.\n"
            "- Do NOT add anything before or after.\n"
        )

        user_prompt = (
              f"Summarize this:\n\n{content}"
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )
            result = response.json()

            if 'choices' in result:
                summary = result['choices'][0]['message']['content'].strip()

                return Response({
                    "summary": summary
                }, status=status.HTTP_200_OK)

            else:
                return Response({
                    "error": "Summarization failed",
                    "details": result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": "Connection error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class FindBestAnswerAPIView(APIView):
    " نهائي"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')

        if not post_id:
            return Response({"error": "post_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        post = get_object_or_404(Post, id=post_id)

        # جلب التعليقات مع السكور
        comments = Comment.objects.filter(post=post, parent__isnull=True)\
        .prefetch_related('replies')\
        .annotate(
            computed_useful=Count('reactions', filter=Q(reactions__reaction_type='useful')),
            computed_not_useful=Count('reactions', filter=Q(reactions__reaction_type='not_useful'))
        ).annotate(
            score=F('computed_useful') - F('computed_not_useful')
        ).order_by('-score')[:5]

        comments_context = ""
        for comment in comments:
            comments_context += f"\n[ID: {comment.id} | Score: {comment.score}] {comment.content}"
            for reply in comment.replies.all():
                comments_context += f"\n   -> [Reply ID: {reply.id}] {reply.content}"

        #  Prompt جديد يرجع JSON
        system_instruction = (
            "You are a data extraction engine.\n\n"

            "Task:\n"
            "Find the SINGLE best answer that solves the problem.\n\n"

            "IMPORTANT RULES:\n"
                "- The comments are already sorted by score (highest first)\n"
                "- You MUST choose ONLY from them\n"
                "- Prefer higher score unless clearly wrong\n\n"

            "RETURN ONLY JSON:\n"
            "{\n"
            '  "id": number,\n'
            '  "reason": "explain why this is the best answer"\n'
            "}\n\n"

            # "Rules:\n"
            # "- Do NOT explain outside JSON\n"
            # "- Pick the most accurate answer\n"
            # "- If no answer exists, return:\n"
            # '{ "id": null, "reason": "No definitive solution found"}\n'
            # "- Detect the language of the post content , and write the reason in that same language.\n"
            # "- Forbidden:  DO NOT USE ANY Vietnamese, Chinese, Japanese, Korean, or any non-Arabic/English characters.\n"
            "Rules:\n"
            "- Do NOT explain outside JSON.\n"
            "- Pick the most accurate technical answer that COMPLETELY solves the problem.\n"
            "- CRITICAL: If a comment only asks a question, complains, shares the same problem, or provides generic/unverified advice, it is NOT a solution.\n"
            "- If no definitive solution exists, you MUST return EXACTLY:\n"
            '  { "id": null, "reason": "No definitive solution found" }\n'
            "- Detect the language of the post content, and write the 'reason' in that same language.\n"
            "- Forbidden: DO NOT USE ANY Vietnamese, Chinese, Japanese, Korean, or any non-Arabic/English characters.\n"
        )
        post_context = f"Post:\n{post.content}\n"

        # إذا في كود بالمنشور أضفه
        if post.code:
            post_context += f"\nCode ({post.code_language or 'unknown'}):\n{post.code}\n"

        user_prompt = (
            f"{post_context}\n"
            #f"Post:\n{post.content}\n\n"
            f"Comments:\n{comments_context}"
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 300
        }

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )
            result = response.json()

            if 'choices' in result:
                ai_text = result['choices'][0]['message']['content'].strip()

              # حذف الكلمات التي تحتوي محارف غير عربية/إنجليزية
                ai_text = re.sub(
                    r'\b\S*[^؀-ۿA-Za-z0-9\s{}[\]":,._\-]\S*\b',
                    '',
                    ai_text
                )

                # تنظيف الفراغات
                ai_text = re.sub(r'\s{2,}', ' ', ai_text).strip()

                #  تحويل JSON
                try:
                    ai_text = ai_text.strip().replace("`json", "").replace("```", "").strip()
                    data = json.loads(ai_text)

                    valid_ids = [c.id for c in comments]
                    if data.get("id") and data["id"] not in valid_ids:
                            data["id"] = None
                            data["reason"] = "No best answer found yet"
                    if not data.get("id"):
                          data["reason"] = "No best answer found yet 🤔"
                # except:
                #     data = {
                #         "id": None,
                #         "reason": "Parsing failed",
                #         "message": "No best answer found for this post yet 🤔"
                #     }
                except (json.JSONDecodeError, KeyError) as e:
                    data = {"id": None, "reason": "Parsing failed", 
                            "reason": "No best answer found yet"}
                return Response(data, status=status.HTTP_200_OK)

            else:
                return Response({
                    "error": "AI failed",
                    "details": result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": "Connection error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

############THE END

#غير مستخدم
class SuggestReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get("post_id")
        comment_id = request.data.get("comment_id")
        
        post = get_object_or_404(Post, id=post_id)
        comment = get_object_or_404(Comment, id=comment_id)

        prompt = f"""
        You are a helpful assistant for a developer forum.
        Context:
        Post Title/Content: {post.content[:1000]}
        Comment to reply to: {comment.content[:500]}
        but keep technical terms in english even if the comment is in Arabic.
        Write a concise, helpful, and professional reply. 
        Keep it under 50 words. Do not use hashtags.
        """
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            #"model": "gemma2-9b-it",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status() # التأكد أن الطلب نجح
            
            data = response.json()
            suggestion = data['choices'][0]['message']['content']
            
            return Response({"suggestion": suggestion}, status=200)

        except requests.exceptions.ConnectionError:
            return Response({"error": "Connection to AI server failed."}, status=503)
        except Exception as e:
            return Response({"error": f"AI suggestion failed: {str(e)}"}, status=500)