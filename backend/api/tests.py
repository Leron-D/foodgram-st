from http import HTTPStatus
from django.test import Client, TestCase


class FoodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_exists(self):
        """Проверка доступности списка рецептов"""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_recipe_unauthorized(self):
        """Проверка создания рецепта для неавторизованного пользователя (ошибка 401)"""
        recipe_data = {
            'name': 'Тестовый рецепт',
            'ingredients': [],
            'cooking_time': 15
        }

        response = self.guest_client.post('/api/recipes/', data=recipe_data)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)