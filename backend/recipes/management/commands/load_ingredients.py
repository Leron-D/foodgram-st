import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов из JSON в базу данных"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "data", "ingredients.json")

        if not os.path.exists(file_path):
            self.stderr.write(f"Файл {file_path} не найден.")
            return

        with open(file_path, "r", encoding="utf-8") as file:
            ingredient_objects = [
                Ingredient(**item) for item in json.load(file)
            ]

        created_count = Ingredient.objects.bulk_create(ingredient_objects)

        count = len(created_count)
        message = (
            f"{count} ингредиент загружен!"
            if count == 1
            else f"{count} ингредиента загружено!"
            if 2 <= count <= 4
            else f"{count} ингредиентов загружено!"
        )

        self.stdout.write(self.style.SUCCESS(message))
