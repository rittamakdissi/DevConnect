from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User



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