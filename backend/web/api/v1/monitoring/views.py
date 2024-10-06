from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Проверка работоспособности проекта")
def health_check() -> None:
    """
    Checks the health of a project.

    It returns 200 if the project is healthy.
    """
