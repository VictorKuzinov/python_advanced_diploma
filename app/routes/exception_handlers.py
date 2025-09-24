from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.exceptions import (
    AlreadyExists,
    DomainValidation,
    EntityNotFound,
    ForbiddenAction,
)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EntityNotFound)
    async def not_found_handler(_, exc: EntityNotFound):
        return JSONResponse(
            status_code=404,
            content={"result": False, "error_type": "EntityNotFound", "error_message": str(exc)},
        )

    @app.exception_handler(ForbiddenAction)
    async def forbidden_handler(_, exc: ForbiddenAction):
        return JSONResponse(
            status_code=403,
            content={"result": False, "error_type": "ForbiddenAction", "error_message": str(exc)},
        )

    @app.exception_handler(AlreadyExists)
    async def conflict_handler(_, exc: AlreadyExists):
        return JSONResponse(
            status_code=409,
            content={"result": False, "error_type": "AlreadyExists", "error_message": str(exc)},
        )

    @app.exception_handler(DomainValidation)
    async def validation_handler(_, exc: DomainValidation):
        return JSONResponse(
            status_code=400,
            content={
                "result": False,
                "error_type": "DomainValidation",
                "error_message": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def generic_handler(_, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "result": False,
                "error_type": "InternalError",
                "error_message": str(exc),
            },
        )
