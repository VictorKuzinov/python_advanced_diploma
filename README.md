# ✅ Чек-лист по заданию

## Функциональные требования
- [x] Добавление нового твита (`POST /api/tweets`)
- [x] Удаление своего твита (`DELETE /api/tweets/{id}`)
- [x] Фолловинг пользователя (`POST /api/users/{id}/follow`)
- [x] Отписка от пользователя (`DELETE /api/users/{id}/follow`)
- [x] Лайк твита (`POST /api/tweets/{id}/likes`)
- [x] Удаление лайка (`DELETE /api/tweets/{id}/likes`)
- [x] Получение ленты твитов (`GET /api/tweets`)
- [x] Поддержка картинок в твитах (`POST /api/medias`)
- [x] Получение информации о себе (`GET /api/users/me`)
- [x] Получение информации о пользователе по id (`GET /api/users/{id}`)

## Нефункциональные требования
- [x] Развёртывание через **Docker Compose**
- [x] Сохранение данных между перезапусками (PostgreSQL volume)
- [x] Документация API через **Swagger** (автоматически в FastAPI)
- [x] README с инструкцией по запуску
- [x] Линтер (`ruff` + `black` + `mypy`)
- [x] Unit-тесты (`pytest`)

## Технические детали
- [x] Используется PostgreSQL (SQLAlchemy)
- [x] Подключение через `docker-compose.yml`
- [x] Структура проекта приведена к модульному виду
- [x] Реализованы базовые модели: User, Tweet, Media, Like, Follow