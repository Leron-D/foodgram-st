from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth.password_validation import validate_password
from recipes.models import (
    Recipe,
    Ingredient,
    IngredientInRecipe,
    Favorite,
    ShoppingCart,
)
from drf_extra_fields.fields import Base64ImageField
from users.models import User, Subscription
from rest_framework.pagination import PageNumberPagination


class UserSerializer(DjoserUserSerializer):
    """Сериалайзер для получения пользователей с дополнительными полями"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request_user = self.context["request"].user
        return Subscription.objects.filter(author=obj.id, user=request_user.id).exists()


class RegistrationSerializer(serializers.ModelSerializer):
    """Сериалайзер для регистрации пользователей"""

    password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ("email", "password", "username", "first_name", "last_name")

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Сериалайзер для смены пароля"""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сераилайзер для получения ингредиентов в рецепте"""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient.id"
    )
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ["id", "name", "measurement_unit", "amount"]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для работы с рецептами"""

    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source="recipe_ingredients", many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "text",
            "image",
            "author",
            "cooking_time",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
        ]
        read_only_fields = ["author"]

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        instance = super().update(instance, validated_data)
        instance.ingredients.clear()
        self._save_ingredients(instance, ingredients_data)
        return instance

    def _save_ingredients(self, recipe, ingredients_data):
        for ingredient in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient["ingredient"]["id"],
                amount=ingredient["amount"],
            )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and Favorite.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        )


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения рецептов на странице подписки"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(UserSerializer, PageNumberPagination):
    """Сериалайзер для получения подписок пользователя"""

    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    email = serializers.ReadOnlyField(source="author.email")
    avatar = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author.recipes.count")

    class Meta:
        model = Subscription
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_avatar(self, obj):
        return obj.author.avatar.url if obj.author.avatar else None

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        author_recipes = obj.author.recipes.all().order_by('-created_at')

        if recipes_limit:
            author_recipes = author_recipes[:int(recipes_limit)]

        return ShortRecipeSerializer(
            author_recipes, context={"request": request}, many=True
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для работы с избранными рецептами"""

    class Meta:
        model = Favorite
        fields = ("user", "recipe")

    def validate(self, data):
        """Переопределение встроенного метода validate"""

        self._validate_uniqueness(data, Favorite)
        return data

    def _validate_uniqueness(self, data, model):
        """Метод для проверки уникальности рецепта в списке избранного"""

        if model.objects.filter(
                user=self.context["request"].user,
                recipe=data["recipe"]
        ).exists():
            raise serializers.ValidationError("Рецепт уже добавлен.")


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер для работы со списком покупок"""

    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")

    def validate(self, data):
        user = self.context["request"].user
        recipe = data["recipe"]
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в корзину.")
        return data