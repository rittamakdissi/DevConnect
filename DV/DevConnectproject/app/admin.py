from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Follow, Media,Comment,Reaction,CommentUseful,Notification,AiTask


admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Media)
admin.site.register(User)
admin.site.register(Reaction)
admin.site.register(Comment)
admin.site.register(CommentUseful)
admin.site.register(Notification)
admin.site.register(AiTask)
