from django.db import models
from users.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        verbose_name = 'Название',
        max_length = 128,
        unique = False,
        blank = False
    )

    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length = 64,
        blank = False
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецептов"""
    RECIPE_RELATED_NAME = 'recipes'

    name = models.CharField(
        verbose_name = 'Название',
        max_length = 256,
    )

    text = models.TextField(
        verbose_name = 'Описание'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through = 'IngredientInRecipe',
        related_name = RECIPE_RELATED_NAME
    )

    image = models.ImageField(
        verbose_name = 'Картинка',
        upload_to = 'recipes/images/'
    )

    author = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = RECIPE_RELATED_NAME,
        verbose_name = 'Автор'
    )

    cooking_time = models.IntegerField(
        verbose_name = 'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1, 'Время приготовления не может быть менее 1 минуты'
            )
        ]
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return f'ID рецепта: {self.id} | {self.name}'


class IngredientInRecipe(models.Model):
    """Промежуточная модель для связи рецептов с ингредиентами"""
    INGREDIENT_RELATED_NAME = 'recipe_ingredients'

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name=INGREDIENT_RELATED_NAME,
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name=INGREDIENT_RELATED_NAME,
        verbose_name='Ингредиент'
    )

    amount = models.IntegerField(verbose_name='Количество')

    def clean(self):
        """Пользовательская валидация для поля amount"""
        if self.amount <= 0:
            raise ValidationError(
                {'amount': 'Количество ингредиента должно быть больше нуля!'}
            )

    class Meta:
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount}'
                f'{self.ingredient.measurement_unit}'
                f'для {self.recipe.name}')


class UserOfRecipeBase(models.Model):
    """Базовый класс для Favorite и ShoppingCart"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user.username} -> {self.recipe.name}'


class Favorite(UserOfRecipeBase):
    """Модель избранных рецептов"""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name} добавлен в избранное '
                f'{self.user.last_name} {self.user.first_name}')


class ShoppingCart(UserOfRecipeBase):
    """Модель корзины покупок"""

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.recipe}'
