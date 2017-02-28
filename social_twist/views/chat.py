from django.db.models import Q
from django.contrib.auth.models import User
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

    def get_queryset(self):
        """
        This limits only to the messages user had sent,
        or was recipient of.
        """
        user = self.request.user
        return ChatMessage.objects.filter(Q(sender=user) | Q(receiver=user))

    def list(self, request):
        """
        This is an overhead of messages.
        Here in typical fashion of all messengers you'll get list of companions to whom you
        spoke, and for each of them latest message, that either of you had sent to each other.
        """
        messages = ChatMessage.objects.filter(Q(sender=request.user.id) | Q(receiver=request.user.id)) \
            .order_by("-id")
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        companions = []

        def unique_for_companion(message):
            result = False
            if message['companion']['id'] not in companions:
                result = True
                companions.append(message['companion']['id'])
            return result
        result = [x for x in serializer.data if unique_for_companion(x)]
        return Response(result)

    @detail_route(methods=['POST'])
    def send(self, request, pk=None):
        """
        Sends a message toward user. Obviously this is a POST request.
        - - -
        Params:\n

        __id__ - companion id, to whom you want to say something
        """
        receiver = User.objects.get(pk=pk)
        message = ChatMessage(sender=request.user,
                              receiver=receiver,
                              text=request.data.get('text'))
        message.save()
        return Response({"code": 1}, status=status.HTTP_201_CREATED)

    # @detail_route(methods=['POST'])
    def seen(self, request, pk=None):
        """Updates all messages in chat to be seen."""
        companion = User.objects.get(pk=pk)
        messages = ChatMessage.objects.filter(Q(sender=request.user,
                                                receiver=companion) |
                                              Q(sender=companion,
                                                receiver=request.user))\
            .filter(seen=False)
        messages.update(seen=True)
        return Response({"code": 1})

    def retrieve(self, request, pk=None):
        """
        Retrieve chat with a person.
        - - -
        Params:\n

        __id__ - companion id, to whom we speak
        """
        messages = ChatMessage.objects.filter(Q(sender_id=request.user.id,
                                                receiver_id=pk) |
                                              Q(sender_id=pk,
                                                receiver_id=request.user.id))\
            .order_by("-id")
        serializer = MessageSerializer(data=messages, many=True)
        serializer.is_valid()
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        """
        This method is for deleting a message from chat.
        - - -
        Params:\n

        __id__ - of the message that is to be deleted.
        """
        message = ChatMessage.objects.get(pk=int(pk))
        if message.sender == request.user:
            message.delete()
            return Response({"code": 1})
        return Response({"code": -1}, status=status.HTTP_403_FORBIDDEN)
