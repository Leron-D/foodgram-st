from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from recipes.models import (
    Recipe, Ingredient, Favorite, ShoppingCart
)
from users.models import User, Subscription
from .serializers import (
    UserSerializer, RegistrationSerializer, PasswordChangeSerializer,
    RecipeSerializer, ShortRecipeSerializer, IngredientSerializer,
    SubscribedUserSerializer, FavoriteSerializer, ShoppingCartSerializer
)
from .pagination import PagesPagination
import csv


class BaseViewSet(viewsets.ModelViewSet):
    """Базовый класс для RecipeViewSet с общими методами."""

    def handle_create_or_delete(self, request, obj, serializer_class, model):
        """
        Метод для создания и удаления объектов в
        списках избранных рецептов и покупок
        """

        if request.method == "POST":
            serializer = serializer_class(
                data={"user": request.user.id, "recipe": obj.id},
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                ShortRecipeSerializer(obj).data, status=status.HTTP_201_CREATED
            )

        obj_instance = model.objects.filter(user=request.user, recipe=obj).first()
        if obj_instance:
            obj_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"error": "Объект не найден"},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(BaseViewSet):
    """ViewSet, описывающий работу с пользователями и подписками"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PagesPagination

    def get_permissions(self):
        """Метод на получение разрешений для других методов класса"""

        if self.action in ['create', 'login', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Метод для регистрации пользователя"""

        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Пользователь успешно зарегистрирован'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """Метод для авторизации пользователя"""

        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if not user:
            return Response(
                {'error': 'Неверные учётные данные'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})

    @action(detail=False, methods=['get'], url_path='me')
    def get_me(self, request):
        """Метод для получения текущего пользователя"""

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def change_avatar(self, request):
        """Метод для смены или удаления аватара пользователя"""

        user = request.user
        if request.method == "PUT":
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': serializer.data['avatar']}, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            if not user.avatar:
                return Response(
                    {'error': 'Аватар уже удалён'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.avatar.delete()
            user.save()
            return Response(
                {'message': 'Аватар успешно удалён'},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(
            {"error": "Метод не поддерживается."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        """Метод для изменения пароля"""

        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'error': 'Неправильный старый пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Пароль успешно изменён'})

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe_and_unsubscribe(self, request, pk=None):
        """Метод для создания и удаления подписки на авторов"""

        author = get_object_or_404(User, id=pk)
        if author == request.user:
            return Response(
                {'error': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscription.objects.filter(user=request.user, author=author)
        if request.method == "POST":
            if subscription.exists():
                return Response(
                    {"errors": "Подписка уже была оформлена"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = Subscription.objects.create(author=author, user=request.user)
            serializer = SubscribedUserSerializer(subscription, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """
        Метод для вывода всех авторов,
        на которых подписан пользователь
        """

        user = request.user
        subscriptions = (
            Subscription.objects.filter(user=user)
            .select_related('author')
            .order_by('created_at')
        )

        # Пагинация
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('limit', 6)
        paginated_subscriptions = paginator.paginate_queryset(subscriptions, request)

        serializer = SubscribedUserSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet, описывающий работу с ингредиентами"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        """Метод для получения ингредиентов по имени"""
        name = self.request.query_params.get('name')
        if name:
            return self.queryset.filter(name__istartswith=name.lower())
        return self.queryset


class RecipeViewSet(BaseViewSet):
    """ViewSet, описывающий работу с рецептами"""

    queryset = Recipe.objects.all().order_by('-created_at')
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PagesPagination

    def get_queryset(self):
        """Метод для получения рецептов"""

        queryset = super().get_queryset()
        author_id = self.request.query_params.get('author')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if author_id:
            queryset = queryset.filter(author__id=author_id)
        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorite_set__user=self.request.user)
        if is_in_shopping_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(shoppingcart_set__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Метод для автоматического указания автора рецепта"""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def change_favorited_recipes(self, request, pk=None):
        """Метод для создания и удаления избранных рецептов"""

        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_create_or_delete(request, recipe, FavoriteSerializer, Favorite)

    @action(detail=True, methods=["post", "delete"], url_path="shopping_cart")
    def change_shopping_cart(self, request, pk=None):
        """
        Метод для создания и удаления
        рецептов в списке покупок
        """

        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_create_or_delete(request, recipe, ShoppingCartSerializer, ShoppingCart)

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        """Метод для загрузки csv-файла со списком покупок"""

        shopping_cart_items = ShoppingCart.objects.filter(user=request.user)
        ingredient_totals = {}
        for item in shopping_cart_items:
            for ingredient_in_recipe in item.recipe.recipe_ingredients.all():
                key = (
                    ingredient_in_recipe.ingredient.name,
                    ingredient_in_recipe.ingredient.measurement_unit
                )
                ingredient_totals[key] = ingredient_totals.get(key, 0) + ingredient_in_recipe.amount

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        for (name, unit), amount in ingredient_totals.items():
            writer.writerow([name, amount, unit])
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """Метод для получения короткой ссылки на рецепт"""

        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"{get_current_site(request).domain}/recipes/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)