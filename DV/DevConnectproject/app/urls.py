from django.urls import path
from .views import *

urlpatterns = [
    # Register
    path("register/", RegisterView.as_view(), name="register"),

    # My Profile
    path("profile/me/", MyProfileView.as_view(), name="my-profile"),

    # Other user's profile
    path("profile/<str:username>/", OtherUserProfileView.as_view(), name="other-user-profile"),

    # Update user info
    path("profile/me/update/info/", UpdateUserInfoView.as_view()),

    # Update photo / Or remove photo
    path("profile/me/update/photo/", UpdateUserPhotoView.as_view()),

    # Settings screen
    path("profile/me/settings/", SettingsView.as_view()),

    # Change username
    path("profile/me/settings/change-username/", UserNameChangeView.as_view(), name="change-username"),

    # Change password
    path("profile/me/settings/change-password/", ChangePasswordView.as_view(), name="change-password"),

    #show followers list
    path("user/<int:user_id>/followers/", FollowersListView.as_view()),

    #show following list
    path("user/<int:user_id>/following/", FollowingListView.as_view()),

    # Follow a user
    path("follow/<int:user_id>/", FollowView.as_view(), name="follow"),

    # Unfollow a user
    path("unfollow/<int:user_id>/", UnfollowView.as_view(), name="unfollow"),

    # React to a post
    path("posts/<int:post_id>/react/", ReactToPostView.as_view(), name="react-post"),

    # Remove reaction from a post
    # path("posts/<int:post_id>/react/remove/", RemoveReactionView.as_view(), name="remove-reaction"),

    # List users who reacted to a post with a specific reaction
    path("posts/<int:post_id>/reactions/<str:reaction_type>/",ReactionUsersListView.as_view(),name="reaction-users"),

    # List comments for a post
    path("posts/<int:post_id>/comments/", PostCommentsView.as_view()),
    
    #list replies for a comment
    path("comments/<int:comment_id>/replies/", CommentRepliesView.as_view()),

    # Create a comment/reply on a post
    path("posts/<int:post_id>/comments/create/", CommentCreateView.as_view()),

    # React to a comment/ delete when react again
    path("comments/<int:comment_id>/react/", CommentReactionView.as_view()),

    # updata or delete comment
    path("comments/<int:comment_id>/", CommentDetailView.as_view()),

    #Create a post
    path("posts/create/", CreatePostView.as_view()),
    
   # path("posts/", PostListView.as_view(), name="posts-list"),

   # عرض منشور واحد
    path("posts/<int:post_id>/", PostDetailView.as_view(), name="post-detail"),

    # تعديل + حذف
    path("posts/<int:post_id>/edit/", PostUpdateDeleteView.as_view(), name="post-edit"),

    #feed posts
    path("feed/", FeedView.as_view(), name="feed"),

    #user Suggestions in feed
    path("suggested-users/", SuggestedUsersView.as_view(), name="suggested-users"),

    #  البحث و طبعا بدو كويري
    path("search/",SearchView.as_view(), name="search"),
    
    #لتسجيل حساب الشخص يلي فتت عليه لما عملت بحث عنو  ص  
    path("search/people/click/",PeopleSearchClickView.as_view()),

    # سجل اخر عمليات البحث وبدو كويري
    path("search/history/",SearchHistoryView.as_view()),

    #لاحذف عنصر من سجل البحث
    path("search/history/<int:pk>/",DeleteSearchHistoryView.as_view()),

    #اقتراحات الاشخاص مباشرة اثناء الكتابةو بدو كويري
    path("search/suggestions/",SearchSuggestionsView.as_view()),


    # AI Tasks Endpoints(معلقين مؤقتا)
    # path("ai-tasks/", CreateAiTaskView.as_view()),
    # path("ai-tasks/<int:task_id>/", AiTaskDetailView.as_view()),

]


