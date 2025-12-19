from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
    )

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
    links = models.TextField(blank=True, null=True)
    #links = models.JSONField(default=dict, blank=True, null=True)
    #updated_at = models.DateTimeField(auto_now=True)
    #created_at = models.DateTimeField(auto_now_add=True)
    gender = models.CharField(
    max_length=10,
    choices=GENDER_CHOICES,
    )
    
    # Login with email instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "age", "phone_number"]

    @property
    def followers_count(self):
      return self.followers_set.count()

    @property
    def following_count(self):
      return self.following_set.count()

    

    def __str__(self):
        return self.email


############################################################################################################
class Post(models.Model):
    POST_TYPES = (
        ("question", "Question"),
        ("project", "Project"),
        ("problem", "Problem"),
        ("information", "Information"),
        ("artical", "Artical"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    #المحتوى النصي
    content = models.TextField(blank=True, null=True)

    # الكود يلي المستخدم رفعو
    code=models.TextField(blank=True, null=True)

    # الوسوم يلي الذكاء رح يولدها
    tags = models.JSONField(default=list, blank=True)

    # شرح الذكاء للكود
    ai_code_summary = models.TextField(blank=True, null=True)

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

  
    #  🔥 دالة حساب عدد التفاعلات
    def get_reaction_counts(self):
        """"          
        ترجع عدد كل نوع تفاعل على المنشور كقاموس:
        {
            "useful": 3,
            "not_useful": 1,
            "same_problem": 0,
            "creative_solution": 2
        }
        """
       
        from django.db.models import Count
        from .models import Reaction  # رح نعرّف الموديل لاحقاً

        data = self.reactions.values("reaction_type").annotate(count=Count("reaction_type"))
        result = {item["reaction_type"]: item["count"] for item in data}

        # لضمان ظهور الأنواع التي ليس لها أي تفاعل (صفر)
        for rt, _ in Reaction.REACTION_TYPES:
            result.setdefault(rt, 0)

        return result
    
 # 🔥 عدد جميع التعليقات (الرئيسية + الردود)
    @property
    def total_comments(self):
        return self.comments.count()
    
    # 🔥 دالة لإرجاع جميع المنشورات التي تحتوي على تاغ محدد
    @classmethod
    def get_posts_by_tag(cls, tag_name):
        return cls.objects.filter(tags__icontains=tag_name)

    def __str__(self):
        return f"Post {self.id} by {self.user.username}"
    

"""  
اذا بدنا نضيف عدد التعليقات الرئيسية على المنشور فقط  
    @property
    def comments_count(self):
        return self.comments.filter(parent__isnull=True).count()"""



############################################################################################################
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



############################################################################################################
class Media(models.Model):
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="images")
    # هاد الحقل قلي انو خياري يعني ما بعرف اذا رح نستفيد منو لبعدين 
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to="post_images/")  # سيحفظ داخل MEDIA_ROOT/post_images/
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} for Post {self.post.id}"
    

############################################################################################################
class Reaction(models.Model):
    REACTION_TYPES = (
        ("useful", "Useful"),
        ("not_useful", "Not Useful"),
        ("same_problem", "Same Problem"),
        ("creative_solution", "Creative Solution"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions"
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="reactions"
    )

    reaction_type = models.CharField(
        max_length=20,
        choices=REACTION_TYPES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")  
        #  كل مستخدم له تفاعل واحد فقط على نفس البوست
        # وإذا غيّر رأيه يتم تغيير نوع التفاعل بدل إنشاء واحد جديد

    def __str__(self):
        return f"{self.user.username} reacted '{self.reaction_type}' on Post {self.post.id}"
    


############################################################################################################
class Comment(models.Model):
    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    content = models.TextField()# نص التعليق

    parent = models.ForeignKey( # التعليق الرئيسي
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    # ما بظن ضروري لانو ما عنا مكان نعرض فيه تم التعديل 
    updated_at = models.DateTimeField(auto_now=True)

    # -----------  عدد useful على التعليق -----------
    @property
    def useful_count(self):
        return self.reactions.filter(reaction_type='useful').count()
    
    # -----------  عدد not useful على التعليق -----------
    @property
    def not_useful_count(self):
        return self.reactions.filter(reaction_type='not_useful').count()

    # -----------  عدد الردود المباشرة فقط -----------
    @property
    def replies_count(self):
        return self.replies.count()
    
    def __str__(self):
        return f"Comment {self.id} by {self.user.username}"

    

############################################################################################################
class CommentReaction(models.Model):
    REACTION_TYPES = [
        ('useful', 'Useful'),
        ('not_useful', 'Not Useful'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_reactions"
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="reactions"
    )

    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "comment")

    def __str__(self):
        return f"{self.user.username} reacted ({self.reaction_type}) on {self.comment}"


############################################################################################################
class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ("post_reaction", "Reaction on your post"),
        ("comment_reaction", "Reaction on your comment"),
        ("new_comment", "New comment on your post"),
        ("reply_comment", "Reply to your comment"),
        ("follow", "New follower"),
    )

    # الشخص اللي يستقبل الإشعار
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    # الشخص اللي عمل الفعل (المصدر)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications"
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    # إشعار نحطو داخلو post, comment, etc حسب نوع الفعل
    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    comment = models.ForeignKey(
        "Comment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # هل المستخدم شاف الإشعار؟
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification to '{self.to_user.username}' -> ({self.notification_type})"


############################################################################################################
class AiTask(models.Model):

    TASK_TYPES = [
        ("classify_post", "Classify Post"),
        ("auto_tags", "Auto Tags for Post"),
        ("code_summary", "Code Summary"),
        ("improve_post", "Improve Post Writing"),
        ("generate_post", "Generate Post"),
    ]

    STATUS_TYPES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    # مين طلب المهمة
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_tasks"
    )

    # نوع المهمة
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)

    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default="pending")

    # المدخلات → الشي يلي بدك AI يشتغل عليه
    input_text = models.TextField(null=True, blank=True)

    # النتيجة → رجعها AI
    output_text = models.TextField(null=True, blank=True)

    #هاد الصح لانو المهام مرتبطة بالبوست فقط
    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        related_name="ai_tasks",
    )
 

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(null=True, blank=True)

    class Meta:
     
     indexes = [
        models.Index(fields=["post"]),
        models.Index(fields=["user", "status"]),
    ]
    
    def __str__(self):
        return f"{self.task_type} - ({self.status}) by {self.user.username}"
    