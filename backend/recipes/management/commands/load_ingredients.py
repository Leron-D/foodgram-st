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
        for item in data:
            name = item.get("name")
            measurement_unit = item.get("measurement_unit")
            if name and measurement_unit:
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )

        self.stdout.write(self.style.SUCCESS("Ингредиенты успешно загружены!"))