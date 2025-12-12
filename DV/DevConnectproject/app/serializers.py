from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .models import *
from django.db import transaction
from django.conf import settings

User = get_user_model()



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        # 1) تأكد إنو المستخدم أدخل القيمتين
        if not email:
            raise serializers.ValidationError("email is required.")
        if not password :
            raise serializers.ValidationError("password is required.")

        # 2) جرّب تسجيل الدخول
        user = authenticate(username=email, password=password)

        # 3) إذا ما لقي مستخدم → البيانات غلط
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        # 4) خزّن المستخدم ليرجع للـ view
        data['user'] = user
        return data


##################################################################################################
class RegisterSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "confirm_password",
            "age",
            "gender",
            "phone_number",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    #  VALIDATION
    def validate(self, data):

        #  تطابق الباسوردين
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Password and Confirm Password do not match."}
            )

          #  التحقق من طول كلمة السر (على الأقل 8 محارف)
        if len(data["password"]) < 8:
             raise serializers.ValidationError(
              {"password": "Password must be at least 8 characters ."}
            )

        #  التحقق من الإيميل انو لازم يكون غير موجود مسبقا عندي بالموقع مشان اقدر انشئ مستخدم
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "This email is already registered."}
            )

       # التحقق من اسم المستخدم انو لازم يكون غير موجود مسبقا
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "This username is already taken."}
            )

        #  التحقق من رقم الهاتف انو اذا دخلتو لازم ما يكون في متلو عندي مسبقا (لانو حطينا ادخال رقم الهاتف غير اجباري )
        if data.get("phone_number"):
            if User.objects.filter(phone_number=data["phone_number"]).exists():
                raise serializers.ValidationError(
                    {"phone_number": "This phone number is already in use."}
                )

        return data

    # انشاء المستخدم
    def create(self, validated_data):

        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


#######################################################################################################33

class MyProfileSerializer(serializers.ModelSerializer):
    personal_photo_url = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    posts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "personal_photo_url",
            "followers_count",
            "following_count",
            "specialization",
            "bio",
            "links",
            "posts",
        ]

        """إرجاع رابط الصورة الكامل"""
    def get_personal_photo_url(self, obj):
        request = self.context.get("request")
        if obj.personal_photo and hasattr(obj.personal_photo, "url"):
            return request.build_absolute_uri(obj.personal_photo.url)
        return None

    def get_posts(self, obj):
       # جلب كل منشورات المستخدم
        posts = obj.posts.all().order_by("-created_at")   # ← منشورات المستخدم
        return PostSerializer(posts, many=True, context=self.context).data

########################################################################################################33

class OtherUserProfileSerializer(serializers.ModelSerializer):
    personal_photo_url = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(read_only=True)
    posts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "personal_photo_url",
            "followers_count",
            "specialization",
            "bio",
            "links",
            "posts",
        ]

        """إرجاع رابط الصورة الكامل"""
    def get_personal_photo_url(self, obj):
        request = self.context.get("request")
        if obj.personal_photo and hasattr(obj.personal_photo, "url"):
            return request.build_absolute_uri(obj.personal_photo.url)
        return None

#  رح علقو هلق وبس نعمل سيريالايزر البوست بيمشي الحال
    def get_posts(self, obj):
        # جلب كل منشورات المستخدم
      #  posts = Post.objects.filter(owner=obj).order_by("-created_at")
      #  return PostSerializer(posts, many=True, context=self.context).data
        posts = obj.posts.all().order_by("-created_at")   # ← منشورات المستخدم
        return PostSerializer(posts, many=True, context=self.context).data



#########################################################################################################

class UserPhotoUpdateSerializer(serializers.ModelSerializer):
     class Meta:
         model=User
         fields=['personal_photo']
         extra_kwargs={
             'personal_photo':{'required':False, 'allow_null': True},

         }
####################################################################################################
class UserInfoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['specialization','bio','links']
        extra_kwargs={
            'bio':{'required':False},
            'links':{'required':False},
            'specialization':{'required':False}
        }

#################################################################################################

class UsernameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]

    def validate_username(self, value):

        # 1) Check if taken by another user
        if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This username is already taken.")

        # 2) Run model regex validator
        try:
            User.username.field.run_validators(value)
        except Exception as e:
            raise serializers.ValidationError(e.messages[0])

        return value

    def update(self, instance, validated_data):
        instance.username = validated_data["username"]
        instance.save()
        return instance

###################################################################################################

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user

        # 1) التحقق من كلمة السر القديمة
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        # 2) التأكد من أن الباسورد الجديد غير القديم
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError({"new_password": "New password must be different from old password."})

        # 3) التحقق من طول كلمة السر الجديدة
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError({"new_password": "Password must be at least 8 characters long."})

        # 4) التأكد من تطابق كلمة السر الجديدة مع التأكيد
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})

        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return user
###############################################################################################################
class SettingsProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
        ]

        # كل الحقول للعرض فقط
        extra_kwargs = {
            #"username": {"read_only": True},
            "email": {"read_only": True},
        }
#####################################################################################################
class UserMiniSerializer(serializers.ModelSerializer):
    personal_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "personal_photo_url",
        ]

    def get_personal_photo_url(self, obj):
        request = self.context.get("request")
        if obj.personal_photo and hasattr(obj.personal_photo, "url"):
            return request.build_absolute_uri(obj.personal_photo.url)
        return None

#####################################################################################################
class FollowersListSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(source="follower", read_only=True)

    class Meta:
        model = Follow
        fields = ["user", "created_at"]

class FollowingListSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(source="following", read_only=True)

    class Meta:
        model = Follow
        fields = ["user", "created_at"]



class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ["id", "follower", "following", "created_at"]
        read_only_fields = ["id", "follower", "created_at"]

    def validate(self, data):
        follower = self.context["request"].user
        following = data["following"]

        # منع متابعة نفسك
        if follower == following:
            raise serializers.ValidationError("You cannot follow yourself.")

        # منع التكرار
        if Follow.objects.filter(follower=follower, following=following).exists():
            raise serializers.ValidationError("You already follow this user.")

        return data

    def create(self, validated_data):
        follower = self.context["request"].user
        following = validated_data["following"]
        return Follow.objects.create(follower=follower, following=following)
#####################################################################################################
class ReactionSerializer(serializers.ModelSerializer):
    reaction_type = serializers.ChoiceField(choices=Reaction.REACTION_TYPES)

    class Meta:
        model = Reaction
        fields = ["id", "user", "post", "reaction_type", "created_at"]
        read_only_fields = ["id", "user", "post", "created_at"]

    def save(self, **kwargs):
        user = self.context["request"].user
        post = self.context["post"]
        new_type = self.validated_data["reaction_type"]

        # جلب التفاعل القديم إن وجد
        existing = Reaction.objects.filter(user=user, post=post).first()

        # 1) إذا كان موجود ونفس النوع → احذف التفاعل
        if existing and existing.reaction_type == new_type:
            existing.delete()
            return None   # مهمّ جداً لنعرف بالـ view أنو حذف

        # 2) إذا كان موجود ونوع مختلف → عدّله
        if existing:
            existing.reaction_type = new_type
            existing.save()
            return existing

        # 3) لا يوجد تفاعل سابق → أنشئ واحد جديد
        return Reaction.objects.create(
            user=user,
            post=post,
            reaction_type=new_type
        )

####################################################################################################

#لعرض التعليق و الردود و التفاعلات
class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_photo_url = serializers.SerializerMethodField()
    useful_count = serializers.IntegerField(read_only=True)
    not_useful_count = serializers.IntegerField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    is_reply = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user_photo_url",
            "user_username",
            "content",
            "created_at",
            "useful_count",
            "not_useful_count",
            "replies_count",
            "is_reply",
        ]


    def get_is_reply(self, obj):
     return obj.parent is not None

    def get_user_photo_url(self, obj):
        request = self.context.get("request")
        if obj.user.personal_photo:
            return request.build_absolute_uri(obj.user.personal_photo.url)
        return None


# لانشاء تعليق او رد
class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["content", "parent"]

    def validate(self, data):
        # التأكد أن الرد ينتمي لنفس البوست
        parent = data.get("parent")
        if parent:
            post = self.context["post"]
            if parent.post != post:
                raise serializers.ValidationError("Reply must belong to the same post.")
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        post = self.context["post"]

        return Comment.objects.create(
            user=user,
            post=post,
            content=validated_data["content"],
            parent=validated_data.get("parent")
        )


# لاضافة  او تعديل او حذف التفاعل الخاص بالتعليق
class CommentReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentReaction
        fields = ["reaction_type"]

    def save(self, **kwargs):
        user = self.context["request"].user
        comment = self.context["comment"]
        new_type = self.validated_data["reaction_type"]

        # التفاعل السابق (إن وجد)
        existing = CommentReaction.objects.filter(user=user, comment=comment).first()

        # 1) إذا كان موجود ونفس النوع → احذف التفاعل
        if existing and existing.reaction_type == new_type:
            existing.delete()
            return None   # مهم جداً

        # 2) إذا كان موجود ونوع مختلف → عدّل التفاعل
        if existing:
            existing.reaction_type = new_type
            existing.save()
            return existing

        # 3) لا يوجد تفاعل مسبق → أنشئ واحد جديد
        return CommentReaction.objects.create(
            user=user,
            comment=comment,
            reaction_type=new_type
        )


# تعديل التعليق او الرد
class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["content"]

####################################################################################################

# لعرض الصور المرتبطة بالبوست في الـ response
class MediaSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ["id", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class PostCreateSerializer(serializers.ModelSerializer):
    # استقبال صور (قائمة) عند الإنشاء — write_only لأننا نعرض الصور عبر MediaSerializer بعد الحفظ
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    # الحقول الخاصة بالـ AI (يمكن أن يضعها backend/worker لاحقًا أو يدخِلها المستخدم)
    tags = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    ai_code_summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ai_improved = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    post_type = serializers.ChoiceField(choices=Post.POST_TYPES, required=False, allow_null=True)

    # حقول للـ response
    media = MediaSerializer(many=True, read_only=True, source="images")

    class Meta:
        model = Post
        fields = [
            "id",
            "content",
            "code",
            "tags",
            "ai_code_summary",
            "ai_improved",
            "post_type",
            "created_at",
            "images",   # للـ write (رفع)
            "media",    # للـ read (روابط الصور بعد الحفظ)
        ]
        read_only_fields = ["id", "created_at", "media"]


    @transaction.atomic
    def create(self, validated_data):
        # 1) أخرج الصور من البيانات المؤقتة
        images = validated_data.pop("images", None)

        # 2) جلب المستخدم من الـ context (مفترض مصادق)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create a post.")

        # 3) أنشئ البوست
        post = Post.objects.create(user=user, **validated_data)

        # 4) إذا في صور — انشئ Media لكل صورة
        #    دعم عملي: إذا self.context['request'].FILES يحتوي ملفات تحت 'images', نستخدمها أيضاً
        if images is None:
            # محاولة قراءة الملفات مباشرة من request.FILES (key = 'images')
            if request is not None:
                files = request.FILES.getlist("images")
                images = files if files else None

        if images:
            media_objs = []
            for img in images:
                m = Media.objects.create(post=post, uploaded_by=user, image=img)
                media_objs.append(m)

        return post


#عرض البوست كاملاً
class PostSerializer(serializers.ModelSerializer):
    
    user = UserMiniSerializer(read_only=True)             # معلومات المستخدم
    media = MediaSerializer(source="images", many=True)    # الصور
    reaction_counts = serializers.SerializerMethodField()  # عدد كل تفاعل
    user_reaction = serializers.SerializerMethodField()     # نوع تفاعل المستخدم الحالي
    total_comments = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "code",
            "tags",
            "ai_code_summary",
            "ai_improved",
            "post_type",
            "media",
            "reaction_counts",
            "user_reaction",
            "total_comments",
            "created_at",
        ]

    def get_reaction_counts(self, obj):
        """إرجاع عدد كل نوع تفاعل"""
        return obj.get_reaction_counts()

    def get_user_reaction(self, obj):
        """ما هو التفاعل الذي قام به المستخدم الحالي؟"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        reaction = Reaction.objects.filter(user=request.user, post=obj).first()
        if reaction:
            return reaction.reaction_type
        return None



#تعديل البوست او حذفه
class PostUpdateSerializer(serializers.ModelSerializer):
    # ملفات جديدة للإضافة
    images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    # ids للحذف
    delete_images = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Post
        fields = [
            "content", "code",
            "tags", "post_type", "ai_code_summary", "ai_improved",
            "images", "delete_images"
        ]

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        #حذف الصور
        delete_ids = validated_data.pop("delete_images", [])
        if delete_ids:
            Media.objects.filter(id__in=delete_ids, post=instance).delete()
        #اضافة صور جديدة
        images = validated_data.pop("images", [])
        if images:
            for f in images:
                Media.objects.create(post=instance, uploaded_by=user, image=f)

        # update other fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance