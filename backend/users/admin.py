from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Subscription, User

@admin.register(User)
class UserAdmin(UserAdmin):
    """Модель пользователей для админ-зоны проекта"""

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'password',
    )
    search_fields = ('username', 'email')

    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Модель подписок для админ-зоны проекта"""

    list_display = ('user', 'author')
    search_fields = ('user__email', 'author__email')
