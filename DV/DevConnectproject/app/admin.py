from django.contrib import admin
from .models import User, Post, Follow, Media,Comment,Reaction,CommentReaction,Notification,AiTask,SearchHistory
#from django.contrib.auth.admin import UserAdmin



admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Media)
admin.site.register(User)
admin.site.register(Reaction)
admin.site.register(Comment)
admin.site.register(CommentReaction)
admin.site.register(Notification)
admin.site.register(AiTask)
admin.site.register(SearchHistory)