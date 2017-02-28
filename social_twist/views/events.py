from django.db.models import Q
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from social_twist.models import Event, Invitation
from social_twist.serializers import EventSerializer, InvitationSerializer,\
    PersonSerializer


class EventView(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def create(self, request, **kwargs):
        result = super(viewsets.ModelViewSet, self).create(request, **kwargs)
        invites = request.data.get('friends', [])
        for friend_id in invites:
            invitation = Invitation(sender=request.user,
                                    receiver_id=int(friend_id),
                                    event_id=result.data.id)
            invitation.save()
        return result

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        lon = float(request.data.get('lon', 0))
        lat = float(request.data.get('lat', 0))
        radius = int(request.data.get('radius', 10))
        point = Point(lon, lat)
        queryset = queryset.filter(coordinates__distance_lt=(point, Distance(km=radius)))
        queryset = queryset.filter(Q(is_private=False)|
                                   Q(creator__in=request.user.info.friends))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def by_friends(self, request):
        queryset = Event.objects.filter(creator__in=request.user.info.friends)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def by_me(self, request):
        queryset = Event.objects.filter(creator=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        event = Event.objects.get(pk=int(pk))
        if event.creator == request.user:
            event.delete()
            return Response({"code": 1})
        return Response({"code": -1}, status=status.HTTP_403_FORBIDDEN)

    @detail_route()
    def attenders(self, request, pk=None):
        event = Event.objects.get(pk=int(pk))
        serializer = PersonSerializer(event.attenders, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def attend(self, request, pk=None):
        event = Event.objects.get(pk=int(pk))
        event.attenders.add(request.user)
        return Response({"code": 1})
    # def retrieve(self, request, pk=None, *args, **kwargs):
    #     event = Event.objects.get(pk=int(pk))
    #     serializer =


class InvitationView(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(receiver=request.user)
        # TODO Check the impact
        queryset.update(seen=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def accept(self, request, pk=None):
        return self.react_to_invitation(request, pk, True)

    @detail_route(methods=['POST'])
    def reject(self, request, pk=None):
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
