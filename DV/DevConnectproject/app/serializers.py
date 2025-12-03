from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .models import Follow


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


############################################################

class MyProfileSerializer(serializers.ModelSerializer):
    personal_photo_url = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    # posts = serializers.SerializerMethodField()

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
            # "posts",
        ]

        """إرجاع رابط الصورة الكامل"""
    def get_personal_photo_url(self, obj):
        request = self.context.get("request")
        if obj.personal_photo and hasattr(obj.personal_photo, "url"):
            return request.build_absolute_uri(obj.personal_photo.url)
        return None

#  رح علقو هلق وبس نعمل سيريالايزر البوست بيمشي الحال
    #def get_posts(self, obj):
        # جلب كل منشورات المستخدم
       # posts = Post.objects.filter(owner=obj).order_by("-created_at")
      #  return PostSerializer(posts, many=True, context=self.context).data

########################################################################

class OtherUserProfileSerializer(serializers.ModelSerializer):
    personal_photo_url = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(read_only=True)
   # posts = serializers.SerializerMethodField()

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
           # "posts",
        ]

        """إرجاع رابط الصورة الكامل"""
    def get_personal_photo_url(self, obj):
        request = self.context.get("request")
        if obj.personal_photo and hasattr(obj.personal_photo, "url"):
            return request.build_absolute_uri(obj.personal_photo.url)
        return None

#  رح علقو هلق وبس نعمل سيريالايزر البوست بيمشي الحال
   # def get_posts(self, obj):
        # جلب كل منشورات المستخدم
      #  posts = Post.objects.filter(owner=obj).order_by("-created_at")
      #  return PostSerializer(posts, many=True, context=self.context).data


########################################################################

class UserPhotoUpdateSerializer(serializers.ModelSerializer):
     class Meta:
         model=User
         fields=['personal_photo']
         extra_kwargs={
             'personal_photo':{'required':False, 'allow_null': True},

         }
########################################################################
class UserInfoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['specialization','bio','links']
        extra_kwargs={
            'bio':{'required':False},
            'links':{'required':False},
            'specialization':{'required':False}
        }

###############################################################

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

############################################################

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
##################################################################################
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
#####################################################################################################
class FollowingListSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(source="following", read_only=True)

    class Meta:
        model = Follow
        fields = ["user", "created_at"]
#####################################################################################################
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
