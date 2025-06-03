from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid, os
from PIL import Image


# uploading user files to a specific directory
def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    picture = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    caption = models.CharField(max_length=10000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.caption[:30]}"

    def get_absolute_url(self):
        return reverse("post-details", args=[str(self.id)])

    def is_liked_by(self, user):
        return self.likes.filter(user=user).exists()

    @property
    def like_count(self):
        return self.likes.count()
    

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:30]
    

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    

class Stream(models.Model):
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_following', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # the user receiving this post in their feed
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} sees post by {self.following.username}"

    @staticmethod
    def add_post(sender, instance, created, **kwargs):
        if created:
            post = instance
            author = post.user
            followers = Follow.objects.filter(following=author)

            streams = [
                Stream(post=post, user=f.follower, date=post.created_at, following=author)
                for f in followers
            ]
            Stream.objects.bulk_create(streams)

# Connect signal
post_save.connect(Stream.add_post, sender=Post)



class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="profile_picture",blank=True, default="default.jpg" )
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    bio = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    favourite = models.ManyToManyField('Post', blank=True)

    def __str__(self):
        return f'{self.user.username} - Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            img_path = self.image.path
            if os.path.exists(img_path):  # extra check for robustness
                img = Image.open(img_path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(img_path)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

