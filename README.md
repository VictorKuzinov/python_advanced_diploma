# Итоговый проект «Python Advanced»

## 📌 Описание проекта

Учебный проект — упрощённый клон Twitter.  
Реализован бэкенд на **FastAPI** + **SQLAlchemy (async)**, база данных **PostgreSQL**.  
Фронтенд (Vue.js, собранный `dist`) монтируется как статические файлы через FastAPI.  
Инфраструктура Docker Compose · Alembic · Pytest · Ruff/Black/Mypy.

### Основные возможности:
- Постинг твитов с текстом и медиа
- Лента твитов (сортировка: лайки ↓, дата ↓)
- Подписки и отписки между пользователями
- Лайки и снятие лайков
- Загрузка медиа (PNG, JPG)
- Просмотр профиля пользователя и «о себе» (`/api/users/me`)

---

## ⚙️ Архитектура

### Слои проекта
- **models/** — ORM-модели (User, Tweet, Media, Like, Follow)
- **schemas/** — Pydantic-схемы (DTO-объекты для API)
- **services/** — бизнес-логика (CRUD, валидации)
- **routers/** — REST API маршруты (FastAPI)
- **exceptions.py** — собственные ошибки (EntityNotFound, DomainValidation и др.)
- **dependencies.py** — зависимости FastAPI (например, current_user)

### Модели
- **User** — пользователь (username/api_key)
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship("Tweet", back_populates="author", cascade="all, delete-orphan")

    # отношения подписок реализованы через модель Follow
    followers = relationship(
        "Follow", foreign_keys="Follow.followee_id",
        back_populates="followee", cascade="all, delete-orphan"
    )
    following = relationship(
        "Follow", foreign_keys="Follow.follower_id",
        back_populates="follower", cascade="all, delete-orphan"
    )

    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
```
> В API атрибут пользователя называется name, в БД — username. Отображение сделано через Pydantic-алиасы (см. схемы).
- **Tweet** — твит, текст ≤ 280 символов, может содержать медиа
```python
class Tweet(Base):
    __tablename__ = "tweets"
    id = mapped_column(Integer, primary_key=True)
    author_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content = mapped_column(String(280), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User", back_populates="tweets")
    attachments = relationship("Media", secondary="tweet_media", back_populates="tweets", lazy="selectin")
    likes = relationship("Like", back_populates="tweet", cascade="all, delete-orphan")
```
- **Media** — прикреплённые файлы (PNG/JPG), хранятся как `path`
```python
class Media(Base):
    __tablename__ = "medias"
    id = mapped_column(Integer, primary_key=True)
    path = mapped_column(String, nullable=False)  # относительный путь, например "media/abc.png"
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship("Tweet", secondary="tweet_media", back_populates="attachments")

TweetMedia (M2M)

tweet_media = Table(
    "tweet_media", Base.metadata,
    Column("tweet_id", ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True),
    Column("media_id", ForeignKey("medias.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("tweet_id", "media_id", name="uq_tweet_media")
)
```
- **Like** — связь User ↔ Tweet
```python
class Like(Base):
    __tablename__ = "likes"
    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tweet_id = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"), index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "tweet_id", name="uq_user_tweet"),)

    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")
```
- **Follow** — подписки между User ↔ User
```python
class Follow(Base):
    __tablename__ = "follows"
    id = mapped_column(Integer, primary_key=True)
    follower_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    followee_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followee = relationship("User", foreign_keys=[followee_id], back_populates="followers")
```
### Схемы (контракты API, Pydantic)
Общие
```python
class SimpleResult(BaseModel):
    result: bool = True

class ErrorResponse(BaseModel):
    result: bool = False
    error_type: str
    error_message: str
```
Пользователи
```python
class UserPublic(BaseModel):
    id: int
    name: str = Field(alias="username", serialization_alias="name")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class UserProfile(UserPublic):
    followers: list[UserPublic]
    following: list[UserPublic]

class UserProfileResponse(BaseModel):
    result: bool = True
    user: UserProfile
```
Твиты и лайки
```python
class LikeUser(BaseModel):
    user_id: int
    name: str

class TweetCreate(BaseModel):
    tweet_data: str = Field(min_length=1, max_length=280)
    tweet_media_ids: list[int] | None = None

class TweetOut(BaseModel):
    id: int
    content: str
    attachments: list[str]
    author: UserPublic         # строго {id, name}
    likes: list[LikeUser] = Field(default_factory=list)

class PostTweetResponse(BaseModel):
    result: bool = True
    tweet_id: int

class TweetsResponse(BaseModel):
    result: bool = True
    tweets: list[TweetOut]
```
Медиа
```python
class MediaUploadResponse(BaseModel):
    result: bool = True
    media_id: int
```

### Бизнес-логика (services)
services/users.py:
- get_public_profile(session, user_id) — профиль с followers/following.
- follow(session, follower_id, followee_id) — запрет самоподписки, уникальность пары; duplicate → AlreadyExists.
- unfollow(session, follower_id, followee_id) — идемпотентно (всегда OK).

services/tweets.py:
- create_tweet(session, author_id, content, media_ids) — валидация, привязка медиа, возврат DTO.
- delete_tweet(session, author_id, tweet_id) — только автор может удалить.
- list_tweets(session, author_id?) — список твитов (опционально автора).
- list_feed_for_user(session, viewer_id) — feed = мои + тех, на кого я подписан; сортировка likes ↓, created_at ↓.

services/likes.py:
- like_tweet(session, user_id, tweet_id) — уникальность (двойной лайк → AlreadyExists).
- unlike_tweet(session, user_id, tweet_id) — идемпотентно.

services/medias.py:
- upload_media(session, file: UploadFile) — одиночная загрузка, MIME-whitelist, запись на диск, возврат media_id.

### API (контракты)
- `POST /api/tweets` — создать твит
- `DELETE /api/tweets/{id}` — удалить твит
- `GET /api/tweets` — лента твитов
- `POST /api/medias` — загрузить медиа
- `POST /api/tweets/{id}/likes` — поставить лайк
- `DELETE /api/tweets/{id}/likes` — убрать лайк
- `POST /api/users/{id}/follow` — подписаться
- `DELETE /api/users/{id}/follow` — отписаться
- `GET /api/users/me` — текущий пользователь
- `GET /api/users/{id}` — профиль пользователя

### Ошибки и зависимости
- Исключения → JSON-ошибки
- EntityNotFound → 404: {"result": false, "error_type":"EntityNotFound", "error_message": "..."}
- ForbiddenAction → 403
- AlreadyExists → 409
- DomainValidation → 400
- get_current_user (dependency)
- Читает заголовок api-key.
  Если отсутствует — 401 "Missing api-key".
   Если невалиден — 401 "Invalid api-key".
- Возвращает User для сервисов.

---

## ⚡️ Разработка и отладка

- На этапе отладки роутов использовалась **SQLite** (in-memory / file) для упрощения тестирования. 
- Финальная версия использует **PostgreSQL** с миграциями Alembic. 

### Переменные окружения
- `.env` — для production (PostgreSQL, Docker Compose). 
- `.env.local` — для локальной разработки и отладки (например, SQLite). 
- Файлы с секретами и локальными настройками в репозиторий не добавляются (`.gitignore`). 

---

## 🔧 Alembic

Миграции базы данных управляются с помощью **Alembic**. 

### Конфигурация
- `alembic.ini` — общие настройки (путь к миграциям, логирование). 
- `app/db/migrations/` — каталог с версиями миграций. 
- В `env.py` используется `settings.DATABASE_URL` из `.env` или `.env.local`. 

### Основные команды
```bash
# создать новую ревизию (после изменения моделей)
alembic revision --autogenerate -m "описание изменений"

# применить все миграции
alembic upgrade head

# откатить последнюю миграцию
alembic downgrade -1
```
---

## 🚀 Запуск

### 🔧 Dev-режим (локально, для разработки)

1. Установить зависимости для разработки (тесты + линтеры):  
```bash
pip install -r requirements-dev.txt
```
2. Поднять PostgreSQL через docker (если локально нет базы):
```bash
docker-compose up db -d
```
3. Применить миграции:
```bash
alembic upgrade head
```
После этого API доступно по адресу: [http://localhost:8000](http://localhost:8000)

---

### 🌐 Prod-режим (Docker Compose, с фронтендом)

1. Собрать и запустить проект (backend + PostgreSQL + фронт):
```bash
docker-compose up --build -d
```
2. После запуска доступны:

API по адресу: [http://localhost:8000](http://localhost:8000)

Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

Фронтенд (Vue dist): [http://localhost:8000](http://localhost:8000)


Сервисы:
- `app` — FastAPI-приложение
- `db` — PostgreSQL (volume для данных)
- `alembic` — миграции
---

## 🌱 Инициализация тестовых данных (seed)

Для работы фронтенда и проверки API нужен тестовый пользователь с API-ключом `test`.

В проекте есть скрипт `seed.py`, который добавляет такого пользователя в базу:

```bash
python seed.py
```
---

## 🐳 Docker

- База данных сохраняется в volume `pg_data`
- Запуск фронтенда — монтируется из `dist/`
- Переменные окружения берутся из `.env`

---

## 🧪 Тестирование

Фреймворк: **pytest + pytest-asyncio**.  
Все тесты лежат в `app/tests/`.

### Покрытые сценарии
- **users**: `me`, профиль, follow/unfollow (успех, ошибки, идемпотентность)
- **tweets**: создание (с/без медиа), удаление, валидации, лента, сортировка
- **likes**: постановка лайка, снятие, дубликаты, отображение в ленте
- **medias**: загрузка PNG, привязка к твиту, неверный формат → ошибка

Запуск:
```bash
pytest -v
```

---

## 🔍 Линтеры и стиль

Используются:
- **ruff** — проверка стиля (PEP8 + isort)
- **black** — автоформатирование
- **mypy** — статическая типизация

Запуск:
```bash
ruff check .
black .
mypy .
```

---

## 📊 Дорожная карта / История изменений

1. chore: init backend structure
2. chore: add root __init__.py and dist static frontend
3. feat: add User and Tweet models
4. feat: add Media, Like and Follow models
5. chore: configure SQLAlchemy with PostgreSQL
6. chore: setup Alembic migrations (init schema)
7. feat: add CRUD services for tweets and users
8. feat: add Tweet and User routers (endpoints)
9. feat: add Media upload endpoint
10. feat: implement likes and follows endpoints
11. docs: update README with API usage examples
12. test: add unit tests for Tweet API
13. test: add unit tests for User API
14. chore: add pytest configuration
15. build: add docker-compose for postgres and app
16. chore: add wemake-python-styleguide lint config
17. refactor: clean up routers and services
18. docs: final update of README with deploy instructions

---

## 👤 Пользователь для запуска фронта

Для работы фронтенда нужен пользователь с API-ключом "test":  
```json
{ "username": "test", "api_key": "test" }
```
(создать вручную в базе или через seed).

## 🌱 Инициализация тестовых данных (seed)

Для работы фронтенда и проверки API нужен тестовый пользователь с API-ключом `test`.

В проекте есть скрипт `seed.py`, который добавляет такого пользователя в базу:

```bash
python seed.py
```
---

## ✅ Чек-лист

### Функциональные требования
- [x] Добавление нового твита
- [x] Удаление твита
- [x] Подписка / отписка
- [x] Лайки
- [x] Лента твитов
- [x] Медиа
- [x] Профиль / о себе

### Нефункциональные требования
- [x] Docker Compose
- [x] Сохранение данных в volume
- [x] Swagger
- [x] Unit-тесты
- [x] Линтеры
- [x] README


---

## ℹ️ Почему в модели `username`, а в API `name`?

В базе данных и модели SQLAlchemy используется поле `username` — это техническое имя,
которое удобно для хранения и однозначной идентификации пользователей.

В Pydantic-схемах и ответах API это поле транслируется в `name`, чтобы интерфейс был
более «человечным» и соответствовал формату ТЗ.  
Это реализовано через алиасы (`ConfigDict(from_attributes=True)`), поэтому внутри кода
используется `username`, а наружу всегда возвращается `name`.

Таким образом:
- **В БД и моделях:** `username`
- **В API-ответах:** `name`

Это осознанное решение для разделения внутреннего уровня (ORM) и внешнего контракта (API).
