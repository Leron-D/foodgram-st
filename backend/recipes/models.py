from django.db import models
from users.models import User
from django.core.validators import MinValueValidator


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name = 'Название ингредиента',
        max_length = 150,
        unique = True,
        blank = False
    )

    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length = 50,
        blank = False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
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
        related_name = 'recipes'
    )

    image = models.ImageField(
        verbose_name = 'Картинка',
        upload_to = 'recipes/images/'
    )

    author = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = 'recipes',
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
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f"ID рецепта: {self.id} | {self.name}"

class IngredientInRecipe(models.Model):
    """Промежуточная модель для связи рецептов с ингредиентами"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт"
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipes",
        verbose_name="Ингредиент"
    )

    amount = models.IntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount} {self.ingredient.measurement_unit} для {self.recipe.name}"


class Favorite(models.Model):
    """Модель избранных рецептов"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт"
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.recipe.id}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
        verbose_name="Рецепт"
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"
