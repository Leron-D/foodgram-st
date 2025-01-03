from django.contrib import admin
from .models import Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели ингредиентов."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для модели рецептов."""
    list_display = ('id', 'name', 'author', 'get_favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author', 'created_at')
    ordering = ('id',)

    def get_favorites_count(self, obj):
        """Отображает общее число добавлений рецепта в избранное."""
        return obj.favorites.count()

    get_favorites_count.short_description = 'Добавлений в избранное'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админка для промежуточной модели ингредиентов в рецепте."""
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для модели избранного."""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')
    list_filter = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для модели корзины покупок."""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')
    list_filter = ('user',)

