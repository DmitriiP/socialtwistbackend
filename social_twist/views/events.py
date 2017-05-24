from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from social_twist.models import Event, Invitation, Comment, EventReaction
from social_twist.serializers import EventSerializer, InvitationSerializer,\
    PersonSerializer, CommentSerializer


class EventView(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def create(self, request, **kwargs):
        """
        This creates your events.
        The fields should be pretty self explanatory.
        """
        result = super(viewsets.ModelViewSet, self).create(request, **kwargs)
        invites = request.POST.getlist('friends[]', [])
        for friend_id in invites:
            receiver = User.objects.get(pk=friend_id)
            invitation = Invitation(sender=request.user,
                                    receiver=receiver,
                                    event_id=result.data['id'])
            invitation.save()
        return result

    def list(self, request, *args, **kwargs):
        """
        This gives you a list of events.
        - - -
        It also takes several optional params as GET params:\n
        __lat__ - latitude\n
        __lon__ - longitude\n
        __radius__ - radius in km from the point specified.\n
        These 3 params together provide geographical filtering for the events.
        As the server is using SRID 4326 for calculating distances, specification is needed:\n
        -180 <= __lat__ <= 0 for the Western hemisphere
        and 0 <= __lat__ <= 180 for the Eastern one.\n
        Likewise -90 <= __lon__ <= 0 for the Southern hemisphere,
        and 0 <= __lon__ <= 90 for the Northern hemisphere.\n

        - - -
        Additional optional parameter is:\n
        __text__ - which enables a full text search through event fields.
        """
        queryset = self.get_queryset()
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        radius = int(request.GET.get('radius', 10))
        text = request.GET.get('text')
        point = Point(lat, lon)
        queryset = queryset.filter(coordinates__distance_lte=(point, Distance(km=radius)))
        queryset = queryset.filter(Q(is_private=False) |
                                   Q(creator__in=request.user.info.friends.all()))
        if text is not None:
            queryset.filter(Q(title__icontains=text) |
                            Q(description__icontains=text) |
                            Q(location__icontains=text) |
                            Q(creator__first_name__icontains=text) |
                            Q(creator__last_name__icontains=text))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        This is how you should update the event.
        The patch method allows us to send to the server only those field that we desire to change.
        - - -
        Param:
        __id__ - of the event that we going to update.
        __body__ - of the request is of the same structure as we have in create method.
        """
        result = super(viewsets.ModelViewSet, self).partial_update(request, *args, **kwargs)
        return result

    @list_route()
    def by_friends(self, request):
        """
        Shows events that were created by friends of the current user.
        """
        queryset = Event.objects.filter(creator__in=request.user.info.friends.all())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def by_me(self, request):
        """
        Shows events that were created by the current user.
        """
        queryset = Event.objects.filter(creator=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Allows creator to destroy his event.
        - - -
        Param:
        __id__ - of the event that is about to be destroyed.
        """
        event = Event.objects.get(pk=pk)
        if event.creator == request.user:
            event.delete()
            return Response({"code": 1})
        return Response({"code": -1}, status=status.HTTP_403_FORBIDDEN)

    @detail_route()
    def attenders(self, request, pk=None):
        """
        Returns a list of users that are going to the event specified.
        - - -
        Param:
        __id__ - of the event that we are interested in.
        """
        event = Event.objects.get(pk=pk)
        serializer = PersonSerializer(event.attenders, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def attend(self, request, pk=None):
        """
        Mark yourself as an attender to the event specified.
        - - -
        Param:
        __id__ - of the event that we are interested in.
        """
        event = Event.objects.get(pk=pk)
        event.attenders.add(request.user)
        return Response({"code": 1})

    @detail_route(methods=['post'])
    def like(self, request, pk=None):
        """
        Like this event.
        - - -
        Param:
        __id__ - of the event that we are interested in.
        """
        event = Event.objects.get(pk=pk)
        event_reaction = EventReaction.objects.get_or_create(event=event,
                                                             person=request.user)[0]
        if event_reaction.liked:
            return Response({"code": 1})
        if event_reaction.disliked:
            event.dislikes -= 1
            event_reaction.disliked = False
        event_reaction.liked = True
        event.likes += 1
        event.save()
        event_reaction.save()
        return Response({"code": 1})

    @detail_route(methods=['post'])
    def dislike(self, request, pk=None):
        """
        Dislike this event.
        - - -
        Param:
        __id__ - of the event that we are interested in.
        """
        event = Event.objects.get(pk=pk)
        event_reaction = EventReaction.objects.get_or_create(event=event,
                                                             person=request.user)[0]
        if event_reaction.disliked:
            return Response({"code": 1})
        if event_reaction.liked:
            event.likes -= 1
            event_reaction.liked = False
        event_reaction.disliked = True
        event.dislikes += 1
        event.save()
        event_reaction.save()
        return Response({"code": 1})

    @detail_route(methods=['post'])
    def comment(self, request, pk=None):
        """
        Leave a comment on this event
        - - -
        Param:
        __id__ - of the event that we are commenting.
        Request body:
        ```
        {
            "text": "string"
        }
        ```
        """
        comment = Comment(event_id=pk, author=request.user,
                          text=request.data['text'])
        comment.save()
        return Response(CommentSerializer(comment).data, 201)

    @detail_route()
    def comments(self, request, pk=None):
        """
        Get comments for the given event.
        - - -
        Param:
        __id__ - of the event that we are interested in.
        """
        event = Event.objects.get(pk=pk)
        queryset = event.comment_set
        return Response(CommentSerializer(queryset, many=True).data)


class InvitationView(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def create(self, request, **kwargs):
        """
        Creates an invitation for user to join in to a event.
        - - -
        Params:
        __sender_id__ - request user id
        __receiver_id__ - whom we are inviting
        __event_id__ - to what we are inviting
        """
        result = super(viewsets.ModelViewSet, self).create(request, **kwargs)
        return result

    def list(self, request, *args, **kwargs):
        """
        Lists all event invitations for the user.
        """
        queryset = self.get_queryset().filter(receiver=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def accept(self, request, pk=None):
        """
        Accept an invitation
        - - -
        Param:
        __id__ - of the invitation that we react to.
        """
        return self.react_to_invitation(request, pk, True)

    @detail_route(methods=['POST'])
    def reject(self, request, pk=None):
        """
        Reject an invitation
        - - -
        Param:
        __id__ - of the invitation that we react to.
        """
        return self.react_to_invitation(request, pk, False)

    def react_to_invitation(self, request, pk, accept=False):
        invitation = Invitation.objects.get(pk=int(pk))
        if invitation.receiver == request.user:
            if accept:
                invitation.event.attenders.add(request.user)
            invitation.delete()
            # TODO notify the sender!
            return Response({"code": 1})
        return Response({"code": -1}, status=status.HTTP_403_FORBIDDEN)
