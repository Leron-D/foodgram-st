import json
import os
from django.core.management.base import BaseCommand
from recipes.models import Recipe, Ingredient, IngredientInRecipe
from users.models import User
from django.core.files import File

class Command(BaseCommand):
    help = "Загрузка рецептов из JSON в базу данных"

    def handle(self, *args, **kwargs):
        # Определяем путь к JSON-файлу и папке с изображениями
        json_path = os.path.join(os.getcwd(), "data", "recipes.json")
        images_path = os.path.join(os.getcwd(), "data", "images")

        # Проверяем, существует ли JSON-файл
        if not os.path.exists(json_path):
            self.stderr.write(f"Файл {json_path} не найден.")
            return

        # Загружаем данные из JSON-файла
        with open(json_path, "r", encoding="utf-8") as file:
            try:
                recipes = json.load(file)
            except json.JSONDecodeError as e:
                self.stderr.write(f"Ошибка декодирования JSON: {e}")
                return

        # Обработка каждого рецепта
        for recipe_data in recipes:
            name = recipe_data.get("name")
            text = recipe_data.get("text")
            image_name = recipe_data.get("image")
            author_email = recipe_data.get("author_email")
            cooking_time = recipe_data.get("cooking_time")
            ingredients_data = recipe_data.get("ingredients", [])

            if not all([name, text, image_name, author_email, cooking_time]):
                self.stderr.write(f"Пропущены обязательные данные: {recipe_data}")
                continue

            # Получаем автора
            try:
                author = User.objects.get(email=author_email)
            except User.DoesNotExist:
                self.stderr.write(f"Автор с email {author_email} не найден. Пропущено.")
                continue

            # Создаём рецепт
            recipe, created = Recipe.objects.get_or_create(
                name=name,
                defaults={
                    "text": text,
                    "author": author,
                    "cooking_time": cooking_time,
                },
            )

            # Загружаем изображение
            if created and image_name:
                image_path = os.path.join(images_path, image_name)
                if os.path.exists(image_path):
                    with open(image_path, "rb") as img_file:
                        recipe.image.save(image_name, File(img_file))
                        recipe.save()
                else:
                    self.stderr.write(f"Изображение {image_name} не найдено.")

            # Добавляем ингредиенты
            for ingredient_data in ingredients_data:
                ingredient_name = ingredient_data.get("name")
                amount = ingredient_data.get("amount")

                if not ingredient_name or not amount:
                    self.stderr.write(f"Пропущены данные об ингредиенте: {ingredient_data}")
                    continue

                try:
                    ingredient = Ingredient.objects.get(name=ingredient_name)
                except Ingredient.DoesNotExist:
                    self.stderr.write(f"Ингредиент {ingredient_name} не найден. Пропущено.")
                    continue

                # Создаём связь между рецептом и ингредиентом
                IngredientInRecipe.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    defaults={"amount": amount},
                )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Рецепт '{name}' успешно создан."))
            else:
                self.stdout.write(self.style.WARNING(f"Рецепт '{name}' уже существует."))

        self.stdout.write(self.style.SUCCESS("Загрузка рецептов завершена!"))