from http import HTTPStatus
from django.test import Client, TestCase
from django.contrib.auth import get_user_model


class FoodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_exists(self):
        """Проверка доступности списка рецептов"""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_registration(self):
        """Проверка регистрации нового пользователя."""
        user_data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'Test'
        }

        response = self.guest_client.post('/api/auth/register/', data=user_data)

        # Проверяем, что запрос завершился успешно (код 201 Created)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)

        # Проверяем, что пользователь был создан в базе данных
        user = get_user_model().objects.get(username='testuser')
        self.assertEqual(user.email, 'testuser@example.com')

    def test_create_recipe_unauthorized(self):
        """Проверка создания рецепта для неавторизованного пользователя (ошибка 401)"""
        recipe_data = {
            'name': 'Тестовый рецепт',
            'ingredients': [],
            'cooking_time': 15
        }

        response = self.guest_client.post('/api/recipes/', data=recipe_data)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)