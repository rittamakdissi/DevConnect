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
    path("posts/<int:post_id>/react/remove/", RemoveReactionView.as_view(), name="remove-reaction"),

    # List users who reacted to a post with a specific reaction
    path("posts/<int:post_id>/reactions/<str:reaction_type>/",ReactionUsersListView.as_view(),name="reaction-users"),
]


    