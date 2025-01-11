from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)
from rest_framework import serializers
from users.models import Subscription, User


class UserSerializer(DjoserUserSerializer):
    """Сериалайзер для получения пользователей с дополнительными полями"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, user):
        request_user = self.context['request'].user
        return Subscription.objects.filter(
            author=user.id,
            user=request_user.id
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сераилайзер для получения ингредиентов в рецепте"""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для работы с рецептами"""

    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'image',
            'author',
            'cooking_time',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        instance.ingredients.clear()
        self._save_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _save_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient['ingredient']['id'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients_data
            ]
        )

    def _check_existence(self, model, recipe):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._check_existence(Favorite, recipe)

    def get_is_in_shopping_cart(self, recipe):
        return self._check_existence(ShoppingCart, recipe)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения рецептов на странице подписки"""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribedUserSerializer(UserSerializer):
    """Сериалайзер для получения информации об авторах,
    на которых подписан текущий пользователь"""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(
        source='author.recipes.count'
    )

    class Meta(UserSerializer.Meta):
        fields = (
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, author):
        return ShortRecipeSerializer(
            author.recipes.all()[:int(self.context.get('request').GET.get(
                'recipes_limit',
                10**10
            ))],
            many=True
        ).data
