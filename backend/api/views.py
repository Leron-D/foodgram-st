import io

from django.http import FileResponse
from django.utils import timezone
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from users.models import Subscription, User

from .pagination import PagesPagination
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscribedUserSerializer,
    SubscriptionSerializer,
    UserSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """ViewSet, описывающий работу с пользователями и подписками"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PagesPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def get_me(self, request):
        """Метод для получения текущего пользователя"""
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def change_avatar(self, request):
        """Метод для смены или удаления аватара пользователя"""

        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user, data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK
            )
        user.avatar.delete()
        user.save()
        return Response(
            {'message': 'Аватар успешно удалён'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe'
    )
    def subscribe_and_unsubscribe(self, request, id=None):
        """Метод для создания и удаления подписки на авторов"""

        author = get_object_or_404(User, pk=id)
        if author == request.user:
            raise ValidationError(
                {'error': 'Нельзя подписаться на самого себя'}
            )

        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author
        )

        if request.method == 'POST':
            if not created:
                raise ValidationError({'errors': 'Подписка уже была оформлена'})

            return Response(
                SubscriptionSerializer(
                    subscription,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        if not created:
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        raise ValidationError({'error': 'Подписка не существует'})

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        """
        Метод для вывода всех авторов,
        на которых подписан пользователь
        """

        user = request.user
        subscriptions = (
            user.users_of_subscriptions.all()
            .select_related('author')
        )

        # Пагинация
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('limit', 6)
        paginated_subscriptions = paginator.paginate_queryset(
            subscriptions,
            request
        )

        authors = [subscription.author for subscription in paginated_subscriptions]

        serializer = SubscribedUserSerializer(
            authors,
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


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet, описывающий работу с рецептами"""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PagesPagination

    def get_queryset(self):
        """Метод для получения рецептов"""

        queryset = super().get_queryset()
        author_id = self.request.query_params.get('author')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if author_id:
            queryset = queryset.filter(author__id=author_id)
        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorite_set__user=self.request.user)
        if is_in_shopping_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(
                shoppingcart_set__user=self.request.user
            )
        return queryset

    def perform_create(self, serializer):
        """Метод для автоматического указания автора рецепта"""
        serializer.save(author=self.request.user)

    @staticmethod
    def _handle_create_or_delete(request, recipe, model):
        """
        Метод для создания и удаления рецептов
        в списке избранных или в корзине покупок
        """
        if request.method == 'POST':
            if model.objects.filter(
                    user=request.user,
                    recipe=recipe
            ).exists():
                raise ValidationError('Рецепт уже добавлен')
            model.objects.create(user=request.user, recipe=recipe)
            return Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )

        recipe_instance = get_object_or_404(model, user=request.user, recipe=recipe)
        recipe_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def change_favorited_recipes(self, request, pk=None):
        """Метод для добавления или удаления рецепта из избранного"""
        return self._handle_create_or_delete(
            request,
            get_object_or_404(Recipe, pk=pk),
            Favorite
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart'
    )
    def change_shopping_cart(self, request, pk=None):
        """Метод для добавления или удаления рецепта из списка покупок"""
        return self._handle_create_or_delete(
            request,
            get_object_or_404(Recipe, pk=pk),
            ShoppingCart
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки текстового отчета со списком покупок"""

        ingredient_totals = {}
        recipe_names = set()

        for item in (request.user.shoppingcart_set.all()
                .select_related('recipe')):
            recipe_names.add(item.recipe.name)
            for ingredient_in_recipe in item.recipe.recipe_ingredients.all():
                key = (
                    ingredient_in_recipe.ingredient.name,
                    ingredient_in_recipe.ingredient.measurement_unit
                )
                ingredient_totals[key] = (ingredient_totals.get(key, 0)
                                          + ingredient_in_recipe.amount)

        today = timezone.now().strftime('%d.%m.%Y')
        report_lines = [
            f'Список покупок на {today}:',
            'Продукты:',
        ]

        '''Нумерация и сортировка ингредиентов по имени'''
        for number_of_product, ((name, unit), amount) in enumerate(
                sorted(ingredient_totals.items(), key=lambda x: x[0])
        ):
            report_lines.append(
                f'{number_of_product + 1}. '
                f'{name.capitalize()} ({unit}) - {amount}'
            )

        report_lines.append('\nРецепты, для которых нужны эти продукты:')
        for number_of_product, recipe_name in enumerate(sorted(recipe_names)):
            report_lines.append(f'{number_of_product + 1}. {recipe_name}')

        report_text = '\n'.join(report_lines)
        report_bytes = report_text.encode('utf-8')

        return FileResponse(
            io.BytesIO(report_bytes),
            content_type='text/plain',
            filename='shopping_cart.txt'
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Метод для получения короткой ссылки на рецепт"""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(f'/s/{recipe.id}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)
