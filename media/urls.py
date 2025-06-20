from django.urls import path
from .import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name = 'index'),

    path('create-post/', views.NewPost, name='newpost'),
    path('<uuid:post_id>/', views.PostDetail, name='post-details'),
    path('<uuid:post_id>/like/', views.like, name='like'),

    path('signup/', views.register, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),


    path('follow/<username>/', views.follow, name='follow'),

    path('post/<uuid:post_id>/edit/', views.edit_post, name='edit-post'),
    path('post/<uuid:post_id>/delete/', views.delete_post, name='delete-post'),
    
    path('comment/<int:comment_id>/edit/', views.comment_edit, name='comment-edit'),
    path('comment/<int:comment_id>/delete/', views.comment_delete, name='comment-delete'),
    
    path('search/', views.search_users, name='search_users'),

    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),


    path('profile/edit/', views.EditProfile, name="editprofile"),

    path('<str:username>/', views.UserProfile, name='profile'),


]
