import json
import os
from django.core.management.base import BaseCommand
from users.models import User
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = "Загрузка пользователей из JSON в базу данных"

    def handle(self, *args, **kwargs):
        # Определяем путь к файлу относительно корня проекта
        file_path = os.path.join(os.getcwd(), "data", "users.json")

        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            self.stderr.write(f"Файл {file_path} не найден.")
            return

        # Загружаем данные из JSON-файла
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                self.stderr.write(f"Ошибка декодирования JSON: {e}")
                return

        # Добавляем пользователей в базу данных
        for item in data:
            email = item.get("email")
            username = item.get("username")
            first_name = item.get("first_name")
            last_name = item.get("last_name")
            password = item.get("password")
            avatar = item.get("avatar")
            is_superuser = item.get("is_superuser", False)
            is_staff = item.get("is_staff", False)

            if not all([email, username, first_name, last_name, password]):
                self.stderr.write(f"Пропущены обязательные данные: {item}")
                continue

            try:
                if is_superuser:
                    # Создаём или обновляем суперпользователя
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": username,
                            "first_name": first_name,
                            "last_name": last_name,
                            "avatar": avatar,
                            "is_superuser": is_superuser,
                            "is_staff": is_staff,
                        },
                    )
                    if created or not user.is_superuser:
                        user.set_password(password)
                        user.is_superuser = True
                        user.is_staff = True
                        user.save()
                        self.stdout.write(self.style.SUCCESS(f"Суперпользователь {email} создан/обновлён."))
                else:
                    # Создаём обычного пользователя
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": username,
                            "first_name": first_name,
                            "last_name": last_name,
                            "password": make_password(password),
                            "avatar": avatar,
                            "is_staff": is_staff,
                        },
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Пользователь {email} создан."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Пользователь {email} уже существует."))
            except Exception as e:
                self.stderr.write(f"Ошибка при создании пользователя {email}: {e}")

        self.stdout.write(self.style.SUCCESS("Загрузка пользователей завершена!"))
