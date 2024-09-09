from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handles validation errors.

    Returns a JSON response with a 422 status code containing a list of errors.

    Args:
        request (Request): The incoming request.
        exc (RequestValidationError): The validation error.

    Returns:
        JSONResponse: A JSON response with a 422 status code.
    """
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": [
                {
                    "field": error["loc"][1:],
                    "msg": error["msg"],
                    "type": error["type"]
                }
                for error in exc.errors()
            ]
        },
        media_type="application/json",
    )
