from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger

class IPONotFoundException(Exception):
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"IPO with identifier '{identifier}' was not found.")

class DatabaseException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)

async def ipo_not_found_exception_handler(request: Request, exc: IPONotFoundException):
    logger.warning(f"IPO Not Found: {exc.identifier}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_code": "IPO_NOT_FOUND"}
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Internal Server Error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(IPONotFoundException, ipo_not_found_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
