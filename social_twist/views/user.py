import datetime
import random
import string

from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route, api_view, permission_classes
from rest_framework import mixins
from rest_framework import status
from rest_framework import permissions
from rest_framework.generics import CreateAPIView

from social_twist.models import FriendRequest, Event,\
    ChatMessage, Invitation
from social_twist.serializers import UserSerializer, EventSerializer, FriendRequestSerializer,\
    FriendSerializer, PersonWithFriendsSerializer, InvitationSerializer


class RegisterUser(CreateAPIView):
    model = User
    permission_classes = [
        permissions.AllowAny # Or anon users can't register
    ]
    serializer_class = UserSerializer


def generate_password(length=8):
    choices = string.digits + string.ascii_lowercase + string.ascii_uppercase
    return ''.join([random.choice(choices) for _ in range(length)])


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def reset_password(request):
    try:
        user = User.objects.get(email__iexact=request.data['email'])
    except:
        return Response({"error": "incorrect_email",
                         "error_description": "Can't find a user with such email."}, status=404)
    password = generate_password()
    user.set_password(password)
    send_mail(
        'Your new social twist password',
        'Here is your new social twist password: %s\nPlease reset it at the first convenient moment.' % password,
        'staff@social_twist.com',
        [request.data['email']],
        fail_silently=False,
    )

    return Response({"msg": "ok"})


class ProfileView(mixins.UpdateModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request):
        """
        Here you can retrieve your profile.
        """
        context = {
            "request": request
        }
        serializer = UserSerializer(request.user, context=context)
        return Response(serializer.data)

    @list_route(methods=['GET'])
    def attends(self, request):
        """
        Gets events that you attend.
        - - -
        Additional optional parameters are:\n
        __after__ & __before__ - timestamps which limit desired timerange.
        """
        queryset = request.user.events
        after = request.GET.get('after')
        if after is not None:
            queryset = queryset.filter(start_time__gte=after)
        before = request.GET.get('before')
        if before is not None:
            queryset = queryset.filter(start_time__lte=before)
        serializer = EventSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def remove_attend(self, request, pk=None):
        """
        This marks you as not going to an event.
        - - -
        Params:\n

        __id__ - Unwanted event id.
        """
        event = Event.objects.get(pk=int(pk))
        event.attenders.remove(request.user)
        return Response({"code": 1})

    @list_route(methods=['GET'])
    def notifications(self, request):
        """
        Gets all your notifications, to be displayed as in Facebook for example.
        """
        chatters = User.objects.filter(id__in=ChatMessage.objects.filter(receiver=request.user,
                                                                         seen=False)\
                                       .values('sender_id'))
        serialized_chatters = PersonWithFriendsSerializer(chatters, many=True)

        invitations = Invitation.objects.filter(receiver=request.user)
        serialized_invitators = InvitationSerializer(invitations, many=True)

        requesters = User.objects.filter(id__in=FriendRequest.objects.filter(receiver=request.user,
                                                                             seen=False)\
                                         .values('sender_id'))
        serialized_requesters = PersonWithFriendsSerializer(requesters, many=True)
        result = {
            'messages': serialized_chatters.data,
            'invitations': serialized_invitators.data,
            'friend_requests': serialized_requesters.data
        }
        return Response(result)

    @list_route(methods=['GET'])
    def notifications_count(self, request):
        """
        This returns count of notifications to be display, as it does in Facebook for example.
        """
        result = {
            'messages': ChatMessage.objects.filter(receiver=request.user, seen=False).count(),
            'invitations': Invitation.objects.filter(receiver=request.user, seen=False).count(),
            'friend_requests': FriendRequest.objects.filter(receiver=request.user, seen=False).count()
        }
        return Response(result)


class UserView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = PersonWithFriendsSerializer

    @detail_route()
    def attends(self, request, pk=None):
        """
        Retrieve a list of events which target user attends.
        - - -
        Params:\n

        __id__ - Target user id.
        """
        user = User.objects.get(pk=int(pk))
        day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        serializer = EventSerializer(user.events.filter(start_time__gte=day_ago), many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def add_friend(self, request, pk=None):
        """
        Send person a friend request.
        - - -
        Params:\n

        __id__ - Target user id.
        """
        user = User.objects.get(pk=int(pk))
        FriendRequest.objects.get_or_create(sender=request.user,
                                            receiver=user)
        return Response({"code": 1})

    @list_route()
    def search(self, request):
        """
        Searches through users (your friends and others).
        - - -
        Params:\n

        __name__ - sent as GET param, against this users will be filtered.
        """
        name = request.GET.get("name", "")
        queryset = self.get_queryset().filter(Q(first_name__contains=name)|
                                              Q(last_name__contains=name))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FriendView(viewsets.ViewSet):
    @list_route()
    def requests(self, request):
        """
        Gets all friend requests that target current user.
        These can be shown as list somewhere in the app.
        """
        friend_requests = FriendRequest.objects.filter(receiver=request.user)
        # TODO Check the impact
        friend_requests.update(seen=True)
        serializer = FriendRequestSerializer(friend_requests, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        Returns all your friends.
        """
        serializer = FriendSerializer(request.user.info.friends, many=True)
        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def delete(self, request, pk=None):
        """
        Removes a person from your friends.
        - - -
        Params:\n

        __id__ - friend id, who is to be removed
        """
        user = User.objects.get(pk=int(pk))
        request.user.info.friends.remove(user)
        user.info.friends.remove(request.user)
        return Response({"code": 1})

    @detail_route(methods=['POST'])
    def accept(self, request, pk=None):
        """
        Accept a friend request
        - - -
        Params:\n

        __id__ - friend request id, obtained from /friends/requests/
        """
        return self.react_to_invitation(request, pk, True)

    @detail_route(methods=['POST'])
    def reject(self, request, pk=None):
        """
        Rejects a friend request
        - - -
        Params:\n

        __id__ - friend request id, obtained from /friends/requests/
        """
        return self.react_to_invitation(request, pk, False)

    @detail_route(methods=['POST'])
    def cancel(self, request, pk=None):
        """
        Cancels a friend request, that you have sent
        - - -
        Params:\n

        __id__ - friend request id
        """
        return self.react_to_invitation(request, pk, False)

    def react_to_invitation(self, request, pk, accept=False):
        friend_request = FriendRequest.objects.get(pk=int(pk))
        if friend_request.receiver == request.user\
                or friend_request.sender == request.user:
            if accept:
                request.user.info.friends.add(friend_request.sender)
                friend_request.sender.info.friends.add(request.user)
            friend_request.delete()
            # TODO notify the sender!
            return Response({"code": 1})
        return Response({"code": -1}, status=status.HTTP_403_FORBIDDEN)

    @list_route()
    def search(self, request):
        """
        Searches through your friends.
        - - -
        Params:\n

        __name__ - sent as GET param, against this friends will be filtered.
        """
        name = request.GET.get("name", "")
        queryset = request.user.info.friends.filter(Q(first_name__contains=name)|
                                                    Q(last_name__contains=name))
        serializer = FriendSerializer(queryset, many=True)
        return Response(serializer.data)
