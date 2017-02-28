from django.db.models import Q
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import detail_route


from social_twist.models import ChatMessage
from social_twist.serializers import MessageSerializer


class MessageView(viewsets.GenericViewSet):
    """
    Get, will get overview of messages
    """
    queryset = ChatMessage.objects.all()
    serializer_class = MessageSerializer

    def list(self, request):
        messages = ChatMessage.objects.filter(Q(sender=request.user.id) | Q(receiver=request.user.id)) \
            .order_by("-id")
        serializer = MessageSerializer(messages, many=True, context={"request": request})
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def send(self, request, pk=None):
        message = ChatMessage(sender_id=request.user.id,
                              receiver_id=int(pk),
                              text=request.POST['text'])
        message.save()
        return Response({"code": 1}, status=status.HTTP_201_CREATED)

    @detail_route()
    def get(self, request, pk=None):
        messages = ChatMessage.objects.filter(Q(sender_id=request.user.id,
                                                receiver_id=int(pk)) |
                                              Q(sender_id=int(pk),
                                                receiver_id=request.user.id))\
            .order_by("-id")
        # TODO Check the impact
        messages.update(seen=True)
        serializer = MessageSerializer(data=messages, many=True)
        serializer.is_valid()
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        message = ChatMessage.objects.get(pk=int(pk))
        if message.sender == request.user:
            message.delete()
            return Response({"code": 1})
        return Response({"code": -1}, status=status.HTTP_403_FORBIDDEN)
