from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Follow, Media


admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Media)
admin.site.register(User)
