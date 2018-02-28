"""untitled URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from social_twist.views.user import ProfileView, UserView, FriendView,\
    RegisterUser
from social_twist.views.chat import MessageView
from social_twist.views.events import EventView, InvitationView

router = routers.DefaultRouter()
router.register(r'events', EventView, base_name="events")
router.register(r'messages', MessageView, base_name="messages")
router.register(r'users', UserView, base_name="users")
router.register(r'friends', FriendView, base_name="friends")
router.register(r'profile', ProfileView, base_name="profile")
router.register(r'invitations', InvitationView, base_name="invitations")

schema_view = get_schema_view(title="Many things here")
docs = get_swagger_view(title='Social Twist API')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('oauth/', include(('oauth2_provider.urls', 'oauth2_provider',), namespace='oauth2_provider'),),
    path('oauth/register/', RegisterUser.as_view()),
    path('schema/', schema_view),
    path('docs/', docs),
]
