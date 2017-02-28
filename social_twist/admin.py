from django.contrib import admin
from django.contrib.auth.admin import User, UserAdmin

from social_twist.models import CustomUserData, Event


class CustomUserDataAdmin(admin.StackedInline):
    model = CustomUserData


class ExtendedUserAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [CustomUserDataAdmin]
admin.site.unregister(User)
admin.site.register(User, ExtendedUserAdmin)
admin.site.register(Event)