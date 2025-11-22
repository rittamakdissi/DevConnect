from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    # Validators
    username_validator = RegexValidator(
        regex=r'^[A-Za-z_][A-Za-z0-9_]{2,29}$',
        message="user name must start with letter or _ only, no spaces or special characters, length between 3 and 30.")
    

    phone_validator = RegexValidator(
        regex=r'^\+?\d{6,15}$',
        message="phone number must contain only digits and can start with +."
    )

    # Override username field
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[username_validator]
    )

    # Extra fields
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(11)])
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[phone_validator],
        blank=True,
        null=True
    )
    specialization = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    personal_photo = models.ImageField(upload_to="avatars/", blank=True, null=True)
    links = models.JSONField(default=dict, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Login with email instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "age", "phone_number"]

    @property
    def followers_count(self):
       return self.followers.count()

    @property
    def following_count(self):
      return self.following.count()
    


    def __str__(self):
        return self.email

###################################################################
class Post(models.Model):
    POST_TYPES = (
        ("question", "Question"),
        ("project", "Project"),
        ("bug", "Bug"),
        ("information", "Information"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    # محتوى المنشور: نص عادي أو كود أو نسخة محسّنة من الذكاء
    content = models.TextField()

    # الوسوم يلي الذكاء رح يولدها
    tags = models.JSONField(default=list, blank=True)

    # شرح الذكاء للكود
    ai_summary = models.TextField(blank=True, null=True)

     # نص محسّن أو ملخّص يولده الذكاء
    ai_improved = models.TextField(blank=True, null=True)   


    # نوع المنشور — الذكاء هو يلي يختارو
    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPES,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post {self.id} by {self.user.username}"


####################################################
class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="following_set",on_delete=models.CASCADE )
    following = models.ForeignKey( settings.AUTH_USER_MODEL, related_name="followers_set", on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")  # منع التكرار
        ordering = ["-created_at"]

    def clean(self):
        if self.follower == self.following:
            raise ValidationError("you cannot follow yourself.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


###################################################################
class Media(models.Model):
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="images")
    # هاد الحقل قلي انو خياري يعني ما بعرف اذا رح نستفيد منو لبعدين 
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to="post_images/")  # سيحفظ داخل MEDIA_ROOT/post_images/
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} for Post {self.post.id}"