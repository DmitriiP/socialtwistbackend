import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db.models import PointField, GeoManager


def default_birthday():
    return datetime.date(2000, 1, 1)

class CustomUserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='info')
    location = models.CharField(max_length=1024, blank=True)
    picture = models.ImageField(blank=True)
    phone_number = models.CharField(max_length=1024, blank=True)
    friends = models.ManyToManyField(User)
    is_ios = models.BooleanField(default=False)

    device_token = models.CharField(max_length=1024)
    sex = models.CharField(max_length=2, choices=[("f", "Female",), ("m", "Male",)])
    birthday = models.DateField(default=default_birthday)



class Event(models.Model):
    title = models.CharField(max_length=1024, blank=False)
    description = models.CharField(max_length=65536, blank=False)
    creator = models.ForeignKey(User, related_name='owned_events')
    attenders = models.ManyToManyField(User, related_name='events')
    start_time = models.DateTimeField()
    picture = models.ImageField()
    coordinates = PointField(blank=True)
    location = models.CharField(max_length=1024, blank=True)
    type = models.CharField(max_length=1024, blank=True)
    is_private = models.BooleanField(default=False)
    objects = GeoManager()


class ChatMessage(models.Model):
    """
    Really awkward looking, but should get deal done.
    """
    sender = models.ForeignKey(User, related_name="sent_messages")
    receiver = models.ForeignKey(User, related_name="received_messages")
    text = models.CharField(max_length=1024, blank=False)
    timestamp = models.DateTimeField(auto_now=True)
    seen = models.BooleanField(default=False)


class Invitation(models.Model):
    sender = models.ForeignKey(User,
                               related_name="sent_invitations")
    receiver = models.ForeignKey(User,
                                 related_name="received_invitations")
    timestamp = models.DateTimeField(auto_now=True)
    event = models.ForeignKey(Event,on_delete=models.CASCADE,
                              related_name="invitations")
    seen = models.BooleanField(default=False)


class FriendRequest(models.Model):
    sender = models.ForeignKey(User,
                               related_name="sent_friend_requests")
    receiver = models.ForeignKey(User,
                                 related_name="received_friend_requests")
    timestamp = models.DateTimeField(auto_now=True)
    seen = models.BooleanField(default=False)
