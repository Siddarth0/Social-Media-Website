from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .forms import NewPostForm, CommentForm, UserRegisterForm, EditProfileForm
from .models import Post, Follow, Stream, Like, Comment, Profile
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse, resolve
from django.db import transaction

@login_required
def index(request):
    user = request.user

    stream_items = Stream.objects.filter(user=user)
    post_ids = stream_items.values_list('post_id', flat=True)

    post_items = Post.objects.filter(id__in=post_ids).select_related('user').order_by('-created_at')

    post_items = check_posts_like(post_items, user)

    query = request.GET.get('q')
    users_paginator = None
    if query:
        users = User.objects.filter(username__icontains=query)
        paginator = Paginator(users, 6)
        page_number = request.GET.get('page')
        users_paginator = paginator.get_page(page_number)

    context = {
        'post_items': post_items,
        'users_paginator': users_paginator,
    }
    return render(request, 'index.html', context)


# def register(request):
#     if request.method == "POST":
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             username = form.cleaned_data['username']
#             raw_password = form.cleaned_data['password1']
#             messages.success(request, f'Hurray {username}, your account was created!')

#             user = authenticate(username=username, password=raw_password)
#             if user is not None:
#                 login(request, user)
#                 return redirect('index')
#             else:
#                 messages.error(request, "Login failed. Try logging in manually.")
#                 return redirect('login')
#     else:
#         if request.user.is_authenticated:
#             return redirect('index')
#         form = UserRegisterForm()

#     return render(request, 'sign-up.html', {'form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    form = UserRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        raw_password = form.cleaned_data['password1']
        user = authenticate(username=user.username, password=raw_password)
        
        if user:
            login(request, user)
            messages.success(request, f'Hurray {user.username}, your account was created!')
            return redirect('index')
        messages.error(request, "Login failed. Try logging in manually.")
        return redirect('login')

    return render(request, 'sign-up.html', {'form': form})


@login_required
def NewPost(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)

    if request.method == "POST":
        form = NewPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = user
            post.save()
            return redirect('profile', username=profile.user.username)
    else:
        form = NewPostForm()

    return render(request, 'newpost.html', {'form': form})



@login_required
def PostDetail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # Check if the current user already liked the post
    post.already_liked = post.likes.filter(user=user).exists()

    comments = Comment.objects.filter(post=post).order_by('-created_at')
    form = CommentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = user
        comment.save()
        return redirect('post-details', post_id=post.id)
    else:
        print(form.errors)

    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'likes_count': post.likes.count()
    }
    return render(request, 'postdetail.html', context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.user != request.user:
        return redirect('post-details', post_id=post.id)

    form = NewPostForm(request.POST or None, request.FILES or None, instance=post)

    if form.is_valid():
        form.save()
        return redirect('post-details', post_id=post.id)

    return render(request, 'edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.user == request.user:
        post.delete()
        return redirect('profile', username=request.user.username)

    return redirect('post-details', post_id=post.id)


@login_required
def like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    obj, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        obj.delete()

    # Redirect back to the page user came from
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def check_posts_like(posts, user):
    for post in posts:
        post.already_liked = post.is_liked_by(user) if user.is_authenticated else False
    return posts


# @login_required
# def add_comment(request, post_id):
#     post = get_object_or_404(Post, id=post_id)

#     if request.method == 'POST':
#         body = request.POST.get('content')
#         if body:
#             Comment.objects.create(post=post, user=request.user, content=body)

#     return redirect('post-detail', post_id=post.id)

@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return redirect('post-details', post_id=comment.post.id)

    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        form.save()
        return redirect('post-details', post_id=comment.post.id)

    return render(request, 'comment_form.html', {'form': form})


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post.id

    if comment.user == request.user:
        comment.delete()

    return redirect('post-details', post_id=post_id)


# @login_required #change logic of follow/unfollow
# def follow(request, username, option):
#     user = request.user
#     following = get_object_or_404(User, username=username)

#     if user == following:
#         # Optional: Prevent users from following themselves
#         return redirect('profile', username=username)

#     if option == 0:
#         # Unfollow
#         Follow.objects.filter(follower=user, following=following).delete()
#         Stream.objects.filter(user=user, following=following).delete()
#     else:
#         # Follow
#         follow_obj, created = Follow.objects.get_or_create(follower=user, following=following)
#         if created:
#             posts = Post.objects.filter(user=following).order_by('-created_at')[:25]
#             with transaction.atomic():
#                 Stream.objects.bulk_create([
#                     Stream(post=post, user=user, date=post.created_at, following=following)
#                     for post in posts
#                 ])

#     return redirect('profile', username=username)

@login_required
def follow(request, username):
    user = request.user
    following = get_object_or_404(User, username=username)

    if user == following:
        return redirect('profile', username=username)  # Prevent following self

    follow_instance = Follow.objects.filter(follower=user, following=following).first()

    if follow_instance:
        # Unfollow
        follow_instance.delete()
        Stream.objects.filter(user=user, following=following).delete()
    else:
        # Follow
        Follow.objects.create(follower=user, following=following)
        posts = Post.objects.filter(user=following).order_by('-created_at')[:25]

        with transaction.atomic():
            Stream.objects.bulk_create([
                Stream(post=post, user=user, date=post.created_at, following=following)
                for post in posts
            ])

    return redirect('profile', username=username)


@login_required
def UserProfile(request, username):


    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    url_name = resolve(request.path).url_name

    if url_name == 'profile':
        posts = Post.objects.filter(user=user).order_by('-created_at')
    else:
        posts = profile.favourite.all()

    posts_count = posts.count()
    following_count = Follow.objects.filter(follower=user).count()
    followers_count = Follow.objects.filter(following=user).count()
    follow_status = Follow.objects.filter(following=user, follower=request.user).exists()

    paginator = Paginator(posts, 8)
    page_number = request.GET.get('page')
    posts_paginator = paginator.get_page(page_number)

    return render(request, 'profile.html', {
        'posts': posts,
        'profile': profile,
        'posts_count': posts_count,
        'following_count': following_count,
        'followers_count': followers_count,
        'posts_paginator': posts_paginator,
        'follow_status': follow_status,
    })


@login_required
def EditProfile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = EditProfileForm(instance=profile)

    return render(request, 'editprofile.html', {'form': form})


def search_users(request):
    query = request.GET.get('q')
    users = []

    if query:
        users = User.objects.filter(username__icontains=query).exclude(username=request.user.username)

    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'search.html', context)

