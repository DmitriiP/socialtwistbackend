import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db.models import PointField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


def default_birthday():
    return datetime.date(2000, 1, 1)


class CustomUserData(models.Model):
    user = models.OneToOneField(User, models.CASCADE,
                                related_name='info')
    location = models.CharField(max_length=1024, blank=True)
    picture = models.ImageField(null=True)
    thumbnail = ImageSpecField(source="picture", processors=[ResizeToFill(80, 80)], format="PNG")
    phone_number = models.CharField(max_length=1024, blank=True)
    friends = models.ManyToManyField(User, blank=True)
    is_ios = models.BooleanField(default=False)

    device_token = models.CharField(max_length=1024, blank=True)
    sex = models.CharField(max_length=2, choices=[("f", "Female",), ("m", "Male",)])
    birthday = models.DateField(default=default_birthday)


class Event(models.Model):
    title = models.CharField(max_length=1024, blank=False)
    description = models.CharField(max_length=65536, blank=False)
    creator = models.ForeignKey(User, models.CASCADE,
                                related_name='owned_events')
    attenders = models.ManyToManyField(User, related_name='events')
    start_time = models.DateTimeField()
    picture = models.ImageField(null=True)
    thumbnail = ImageSpecField(source="picture", processors=[ResizeToFill(80, 80)], format="PNG")
    video = models.FileField(null=True)
    coordinates = PointField(blank=True)
    location = models.CharField(max_length=1024, blank=True)
    type = models.CharField(max_length=1024, blank=True)
    is_private = models.BooleanField(default=False)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return "[%d] %s (%s) by %s" % (self.id, self.title, self.start_time.isoformat(), self.creator)


class ChatMessage(models.Model):
    """
    Really awkward looking, but should get deal done.
    """
    sender = models.ForeignKey(User, models.CASCADE,
                               related_name="sent_messages")
    receiver = models.ForeignKey(User, models.CASCADE,
                                 related_name="received_messages")
    text = models.CharField(max_length=1024, blank=False)
    timestamp = models.DateTimeField(auto_now=True)
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']


class Invitation(models.Model):
    sender = models.ForeignKey(User, models.CASCADE,
                               related_name="sent_invitations")
    receiver = models.ForeignKey(User, models.CASCADE,
                                 related_name="received_invitations")
    timestamp = models.DateTimeField(auto_now=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name="invitations")
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return "%s invites %s to %s" % (self.sender, self.receiver, self.event)


class FriendRequest(models.Model):
    sender = models.ForeignKey(User, models.CASCADE,
                               related_name="sent_friend_requests")
    receiver = models.ForeignKey(User, models.CASCADE,
                                 related_name="received_friend_requests")
    timestamp = models.DateTimeField(auto_now=True)
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return "%s wants to be friends with %s" % (self.sender, self.receiver)


class EventReaction(models.Model):
    person = models.ForeignKey(User, models.CASCADE)
    event = models.ForeignKey(Event, models.CASCADE)
    liked = models.BooleanField(default=False)
    disliked = models.BooleanField(default=False)


class Comment(models.Model):
    author = models.ForeignKey(User, models.CASCADE)
    event = models.ForeignKey(Event, models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    text = models.CharField(max_length=1024, blank=False)

    class Meta:
        ordering = ['-timestamp']


class Image(models.Model):
    image = models.ImageField()
    thumbnail = ImageSpecField(source="image", processors=[ResizeToFill(80, 80)], format="PNG")
    owner = models.ForeignKey(User, models.CASCADE, related_name='images')
