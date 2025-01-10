import json
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = "Загрузка ингредиентов из JSON в базу данных"

    def handle(self, *args, **kwargs):
        # Абсолютный путь к файлу ingredients.json внутри контейнера
        file_path = "/app/data/ingredients.json"

        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            self.stderr.write(f"Файл {file_path} не найден.")
            return

        # Загружаем данные из JSON-файла
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Добавляем ингредиенты в базу данных
        ingredient_objects = [Ingredient(**item) for item in data]
        created_count = Ingredient.objects.bulk_create(ingredient_objects)

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(created_count)} ингредиентов успешно загружено!"
            )
        )
