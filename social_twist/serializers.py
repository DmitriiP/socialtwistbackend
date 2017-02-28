from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User

from social_twist.models import Event, ChatMessage, Invitation, FriendRequest, CustomUserData


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    picture = serializers.ImageField(source="info.picture")
    sex = serializers.CharField(source="info.sex", max_length=2, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'picture', 'sex')


class FriendSerializer(serializers.HyperlinkedModelSerializer):
    location = serializers.CharField(source="info.location", max_length=1024, allow_blank=True)
    picture = serializers.ImageField(source="info.picture")
    phone_number = serializers.CharField(source="info.phone_number", max_length=1024, allow_blank=True)
    sex = serializers.CharField(source="info.sex", max_length=2, allow_blank=True)
    birthday = serializers.DateField(source="info.birthday", required=False)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name',
                  'location', 'picture', 'phone_number',
                  'sex', 'birthday')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    location = serializers.CharField(source="info.location", max_length=1024, allow_blank=True)
    picture = serializers.ImageField(source="info.picture", required=False)
    phone_number = serializers.CharField(source="info.phone_number",
                                         max_length=1024,
                                         allow_blank=True,
                                         required=False)
    is_ios = serializers.BooleanField(source="info.is_ios", default=False)
    device_token = serializers.CharField(source="info.device_token", max_length=1024)
    friends = FriendSerializer(many=True, read_only=True, source="info.friends")
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(validators=[UniqueValidator(User.objects.all(),
                                                               message="Email is already in use.")])
    sex = serializers.CharField(source="info.sex", max_length=2, required=False)
    birthday = serializers.DateField(source="info.birthday", required=False)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'location',
                  'picture', 'phone_number', 'is_ios', 'device_token',
                  'friends', 'password', 'email', 'username', 'sex', 'birthday')

    def create(self, validated_data):
        info = validated_data.pop('info', None)
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user.info = CustomUserData.objects.create(user=user, **info)
        return user

    def update(self, instance, validated_data):
        info = validated_data.pop('info', None)
        for attr, value in info.items():
            setattr(instance.info, attr, value)
        user = super(UserSerializer, self).update(instance, validated_data)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        return user


class EventSerializer(serializers.HyperlinkedModelSerializer):
    creator = PersonSerializer(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'creator', 'picture',
                  'start_time', 'coordinates', 'location', 'type', 'is_private')


class MessageSerializer(serializers.HyperlinkedModelSerializer):
    # def __init__(self, data, *args, **kwargs):
    #     if 'context' in kwargs:
    #         request = kwargs.get('context').get('request')
    #         if request is not None:
    #             companion = serializers.IntegerField
    #     super(serializers.HyperlinkedModelSerializer, self).__init__(*args, **kwargs)
    class Meta:
        model = ChatMessage
        fields = ('id', 'sender_id', 'receiver_id', 'text', 'timestamp')


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ('id', 'sender_id', 'receiver_id', 'event_id', 'timestamp')


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ('id', 'sender_id', 'receiver_id', 'timestamp')