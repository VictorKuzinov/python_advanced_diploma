class EntityNotFound(Exception):
    """Сущность не найдена в БД."""


class ForbiddenAction(Exception):
    """Действие запрещено (например, удаление чужого твита)."""


class AlreadyExists(Exception):
    """Нарушено уникальное ограничение (например, повторная подписка/лайк)."""
