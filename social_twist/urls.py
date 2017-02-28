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
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from rest_framework.schemas import get_schema_view

from social_twist.views.user import ProfileView, UserView, FriendView
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

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^schema/', schema_view),
]
