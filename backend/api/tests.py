import os
from http import HTTPStatus
from django.test import Client, TestCase
from recipes.models import Recipe, Ingredient
from users.models import User


class FoodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            email="testemail@mail.ru",
            first_name="Test",
            last_name="Test",
            username="testuser",
            password="testpassword",
            avatar=None
        )
        self.auth_client = Client()
        self.auth_client.login(username="testuser", password="testpassword")

        # Создание тестового ингредиента
        self.ingredient = Ingredient.objects.create(name="Соль", measurement_unit="грамм")

        # Путь к изображению
        self.image_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "images",
            "brauni.jpg"
        )

    def test_list_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_recipe_authorized(self):
        """Тест на создание рецепта авторизованным пользователем."""
        with open(self.image_path, "rb") as image:
            data = {
                "name": "Тестовый рецепт",
                "text": "Описание тестового рецепта",
                "cooking_time": 30,
                "image": image,
                "ingredients": [{"id": self.ingredient.id, "amount": 10}],
            }
            response = self.auth_client.post(
                "/api/recipes/",
                data,
                content_type="multipart/form-data"
            )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(Recipe.objects.count(), 1)
        recipe = Recipe.objects.first()
        self.assertEqual(recipe.name, "Тестовый рецепт")

    '''def test_create_recipe_unauthorized(self):
        """Тест на запрет создания рецепта неавторизованным пользователем."""
        data = {
            "name": "Тестовый рецепт",
            "text": "Описание тестового рецепта",
            "cooking_time": 30,
            "image": None,
            "ingredients": [{"id": self.ingredient.id, "amount": 10}],
        }
        response = self.guest_client.post("/api/recipes/", data, format="multipart")
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(Recipe.objects.count(), 0)'''