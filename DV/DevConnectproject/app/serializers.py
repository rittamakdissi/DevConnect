from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model


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
    #####################################################################################################



class UserSerializer(serializers.ModelSerializer):

    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    personal_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",


            "first_name",
            "last_name",
            "username",
            "email",
            "age",
            "gender",
            "bio",
            "specialization",


            "phone_number",
            "links",


            "personal_photo",
            "personal_photo_url",


            "followers_count",
            "following_count",
        ]

        extra_kwargs = {
            "email": {"read_only": True},     # لا يعدل من هنا (التعديل يحتاج سيرفر تأكيد غالباً)
            "username": {"read_only": True},  # إذا حابة نخليه غير قابل للتعديل
        }

    def get_personal_photo_url(self, obj):
        """إرجاع رابط الصورة الكامل"""
        try:
            request = self.context.get("request")
            if obj.personal_photo and hasattr(obj.personal_photo, 'url'):
                return request.build_absolute_uri(obj.personal_photo.url)
            return None
        except:
            return None
#######################################################################################################
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=[ 'personal_photo','bio','links','specialization']
        extra_kwargs={
            'personal_photo':{'required':False},
            'bio':{'required':False},
            'links':{'required':False},
            'specialization':{'required':False}
        }
#####################################################################################################
User = get_user_model()
class UsernameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['username']
    def validate_username(self,value):
            # 1) التحقق من وجوده مسبقاً
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
                # 2) تشغيل الـ regex validator الموجود في الموديل
        try:
            User.username.field.run_validators(value)
        except Exception as e:
            raise serializers.ValidationError(e.messages[0])

        return value

    def update(self, instance, validated_data):
        instance.username = validated_data["username"]
        instance.save()
        return instance
#######################################################################################################
User = get_user_model()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user

        # 1) التحقق من كلمة السر القديمة
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        # 2) التأكد من أن الباسورد الجديد غير القديم
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError({"new_password": "New password must be different."})

        # 3) التحقق من طول كلمة السر الجديدة
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError({"new_password": "Password must be at least 8 characters long."})

        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save()
        return user
#############################################################################################################################


