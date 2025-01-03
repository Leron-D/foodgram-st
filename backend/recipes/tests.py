"""import pytest
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User
from recipes.models import Recipe, Ingredient, IngredientInRecipe


@pytest.fixture
def user():
    """"""Фикстура для создания пользователя""""""
    return User.objects.create_user(email='testuser@example.com', password='testpass123')


@pytest.fixture
def another_user():
    """"""Фикстура для создания другого пользователя"""""""
    return User.objects.create_user(email='anotheruser@example.com', password='anotherpass456')


@pytest.fixture
def ingredient():
    """"""Фикстура для создания ингредиента""""""
    return Ingredient.objects.create(name='Tomato', measurement_unit='kg')


@pytest.fixture
def client():
    """"""Фикстура для API-клиента""""""
    return APIClient()


@pytest.fixture
def authenticated_client(user, client):
    """"""Фикстура для аутентифицированного клиента""""""

    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_get_recipe_list(client, user, ingredient):
    """"""Тест получения списка рецептов с ингредиентами""""""

    # Создаем рецепты
    recipe1 = Recipe.objects.create(
        name='Recipe 1',
        cooking_time=10,
        author=user,
        text='Test description 1',
        image=SimpleUploadedFile(
            name='test_image1.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        ),
    )
    recipe2 = Recipe.objects.create(
        name='Recipe 2',
        cooking_time=20,
        author=user,
        text='Test description 2',
        image=SimpleUploadedFile(
            name='test_image2.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        ),
    )

    # Связываем ингредиенты с рецептами
    IngredientInRecipe.objects.create(
        recipe=recipe1,
        ingredient=ingredient,
        amount=2
    )
    IngredientInRecipe.objects.create(
        recipe=recipe2,
        ingredient=ingredient,
        amount=3
    )

    response = client.get('/api/recipes/')

    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['name'] == 'Recipe 1'
    assert 'ingredients' in response.data['results'][0]
    assert len(response.data['results'][0]['ingredients']) == 1
    assert response.data['results'][0]['ingredients'][0]['name'] == 'Tomato'


@pytest.mark.django_db
def test_create_recipe(authenticated_client, ingredient):
    """"""Тест создания нового рецепта""""""

    image = SimpleUploadedFile(
        name='test_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )

    recipe_data = {
        'name': 'New Recipe',
        'text': 'Delicious food',
        'cooking_time': 30,
        'ingredients': [{'id': ingredient.id, 'amount': 2}],
        'image': image,
    }

    response = authenticated_client.post(
        '/api/recipes/',
        recipe_data,
        format='multipart'
    )

    assert response.status_code == 201
    assert response.data['name'] == 'New Recipe'
    assert Recipe.objects.count() == 1
    assert IngredientInRecipe.objects.count() == 1
    assert IngredientInRecipe.objects.first().amount == 2


@pytest.mark.django_db
def test_create_recipe_unauthenticated(client, ingredient):
    """"""Тест создания рецепта без аутентификации""""""

    image = SimpleUploadedFile(
        name='test_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )

    recipe_data = {
        'name': 'New Recipe',
        'text': 'Delicious food',
        'cooking_time': 30,
        'ingredients': [{'id': ingredient.id, 'amount': 2}],
        'image': image,
    }

    response = client.post('/api/recipes/', recipe_data, format='multipart')

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_recipe_invalid_data(authenticated_client):
    """"""Тест создания рецепта с некорректными данными""""""

    recipe_data = {
        'name': '',
        'text': '',
        'cooking_time': -5,  # Некорректное значение
        'ingredients': [],
        'image': None,  # Поле image обязательно
    }

    response = authenticated_client.post(
        '/api/recipes/',
        recipe_data,
        format='json'
    )

    assert response.status_code == 400"""
