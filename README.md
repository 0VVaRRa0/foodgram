# Foodgram

## Описание проекта
Foodgram - платформа для поиска гастрономического вдохновения. Ищите, сохраняйте любимые рецепты и делитесь своими

## Использованные технологии
- Python 3.9
- Django 3.2.3
- Django REST Framework 3.12.4
- PostgreSQL
- Docker
- Nginx
- Gunicorn
- Node.js


## Настройка проекта на локальном компьютере

1. Клонируйте репозиторий `git clone https://github.com/0VVaRRa0/foodgram.git`
2. В корне проекта создайте файл `.env` и добавьте в него необходимые переменные:
    ```
    POSTGRES_DB=название бд
    POSTGRES_USER=имя пользователя бд
    POSTGRES_PASSWORD=пароль для доступа к бд
    DB_HOST=имя контейнера бд
    DB_PORT=порт бд_по умолчанию 5432
    SECRET_KEY=ваш SECRET_KEY Django
    DEBUG=режим отладки True или False
    ALLOWED_HOSTS='127.0.0.1,localhost,ваш_домен'
    SITE_URL=ваш домен для генерации коротких ссылок
    SHORT_LINK_MIN_LENGTH=3 (минимальная длинна короткой ссылки)
    ```
* Если у вас нет значения SECRET_KEY, вы можете сгенерировать его командой:    
    `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`



## Установка и запуск проекта на удалённом сервере

1. Настройте Nginx. Выполните команду `sudo nano /etc/nginx/sites-enabled/default`    
* Если на вашем сервере порт `8000` занят, можете указать другой, например `9000`
    ```
    server {
        server_name ВАШ_ДОМЕН;

        location /api/ {
            proxy_set_header Host $http_host;
            proxy_pass http://127.0.0.1:8000;
        }

        location /admin/ {
            proxy_set_header Host $http_host;
            proxy_pass http://127.0.0.1:8000;
        }

        location /media/ {
            proxy_set_header Host $http_host;
            proxy_pass http://127.0.0.1:8000;
        }

        location / {
            proxy_set_header Host $http_host;
            proxy_pass http://127.0.0.1:8000;
        }
    }
    ```

2. На сервере создайте папку проекта `foodgram`, скопируйте в неё файл `docker-compose.yml` и `.env`
[Как это сделать?](https://help.reg.ru/support/servery-vps/oblachnyye-servery/rabota-s-serverom/kopirovaniye-faylov-cherez-ssh#0)

3. Авторизуйтесь в Docker `docker login -u <ваш-username>`

4. Выполните команду `docker compose -f docker-compose.yml up -d` и дождитесь окончания запуска контейнеров

5. Выполните миграции `docker compose -f docker-compose.yml exec backend python manage.py migrate`

6. Выполните команды `docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic` и    
    `docker compose exec backend cp -r /app/collected_static/. /backend_static/static/` для сбора статики бэкенда.

## Автор: Иван Данилин
GitHub: [0VVaRRa0](https://github.com/0VVaRRa0)    
Gmail: ioann.vorobey1029@gmail.com