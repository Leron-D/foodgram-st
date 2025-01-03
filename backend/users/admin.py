from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription


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

    list_display = ('user', 'author', 'get_created_at')
    search_fields = ('user__email', 'author__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    def get_created_at(self, obj):
        """Отображает поле created_at с другим названием"""
        return obj.created_at

    get_created_at.short_description = 'Когда подписался'