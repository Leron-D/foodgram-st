from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователей"""

    email = models.EmailField(
        unique = True,
        max_length = 254
    )

    username = models.CharField(
        max_length = 150,
        unique = True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message="Username должен содержать только буквы, цифры и следующие символы: @ . + -"
        )]
    )

    first_name = models.CharField(
        max_length=150,
        blank=True,
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
    )

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
        'password'
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email',)

    def __str__(self):
        return self.email

class Subscription(models.Model):
    """Модель подписок"""

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='users_of_subscriptions',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор рецептов'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
