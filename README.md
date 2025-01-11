# Проект Foodgram

Foodgram - это проект, который дает возможность пользователям создавать и хранить рецепты на онлайн-платформе. Кроме того,
есть возможность скачать список продуктов, необходимых для приготовления блюда, посмотреть рецепты друзей и добавить любимые
рецепты в список избранных.

Чтобы использовать все возможности сайта — нужна регистрация. Проверка адреса электронной почты не осуществляется, вы можете ввести любой email.
Заходите и делитесь своими любимыми рецептами!

Проект выполнил [Шаньгин Максим Русланович](leronshangin@yandex.ru).

---

## **Описание проекта**
Foodgram реализует функционал социальной платформы с RESTful API. Основные возможности:
- Получение списка рецептов с поддержкой пагинации;
- Регистрация и авторизация пользователей; 
- Выбор аватара у пользователя;
- Добавление, редактирование и удаление рецептов;
- Добавление рецептов в избранные;
- Получение списка избранных рецептов с поддержкой пагинации;
- Подписка и отписка от авторов рецептов;
- Получение информации о своих подписках с поддержкой пагинации;
- Добавление рецептов в список покупок;
- Скачивание списка ингредиентов для покупок в формате CSV;

API разработан с использованием **Django REST Framework** и JWT-токенов для аутентификации пользователей.

---

## **Технологии**
- Python
- Django
- Django REST Framework
- SimpleJWT
- Djoser

---

## **Установка и запуск проекта**

### **1. Установка Docker**
Скачать приложение docker на вашу локальную машину.

### **2. Скачивание репозитория**
Скачать данный репозиторий на вашу локальную машину.

### **3. Загрузка образов и контейнеров**
Для настройки базы данных необходимо в папке infra создать файл .env и заполнить его следующими данными:

```bash
POSTGRES_USER=django_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=django_foodgram

DB_HOST=db
DB_PORT=5432
```

Пароль можно указать свой.


Находясь в папке infra, в консоли выполнить следующую команду:

```bash
docker-compose up --build -d
```

Загрузка образов и контейнеров может идти достаточно долго.

### **4. Предзагрузка тестовых данных**
После того как образы и контейнеры соберутся, необходимо, находясь в папке infra, в строгом порядке выполнить следующие команды:

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py collectstatic --no-input
```

В результате выполнения этих команд в приложении выполнятся миграции и загрузятся ингредиенты.

### **5. Работа с сайтом**
Сайт доступен через [localhost](http://localhost) или через [127.0.0.1](http://127.0.0.1)

Работа с админ-панелью осуществляется через [localhost/admin](http://localhost/admin).
Суперпользователь уже был создан (email: admin@gmail.com, пароль: admin123).
Чтобы создать нового суперпользователя необходимо выполнить команду:

```bash
docker-compose exec backend python manage.py createsuperuser
```

Если вдруг пропали рецепты или интерфейс админ-панели на сайте, то можно попробовать очистить кэш и cookie.
