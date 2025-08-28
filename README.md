# ✅ Чек-лист по заданию

## Функциональные требования
- [ ] Добавление нового твита (`POST /api/tweets`)
- [ ] Удаление своего твита (`DELETE /api/tweets/{id}`)
- [ ] Фолловинг пользователя (`POST /api/users/{id}/follow`)
- [ ] Отписка от пользователя (`DELETE /api/users/{id}/follow`)
- [ ] Лайк твита (`POST /api/tweets/{id}/likes`)
- [ ] Удаление лайка (`DELETE /api/tweets/{id}/likes`)
- [ ] Получение ленты твитов (`GET /api/tweets`)
- [ ] Поддержка картинок в твитах (`POST /api/medias`)
- [ ] Получение информации о себе (`GET /api/users/me`)
- [ ] Получение информации о пользователе по id (`GET /api/users/{id}`)

## Нефункциональные требования
- [ ] Развёртывание через **Docker Compose**
- [ ] Сохранение данных между перезапусками (PostgreSQL volume)
- [ ] Документация API через **Swagger** (автоматически в FastAPI)
- [ ] README с инструкцией по запуску
- [ ] Линтер (`wemake-python-styleguide` или аналог)
- [ ] Unit-тесты (`pytest`)

## Технические детали
- [ ] Используется PostgreSQL (SQLAlchemy)
- [ ] Подключение через `docker-compose.yml`
- [ ] Структура проекта приведена к модульному виду
- [ ] Реализованы базовые модели: User, Tweet, Media, Like, Follow