from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schema import (
    BadRequestResponse,
    DebugRequest,
    DebugResponse,
    ServiceExceptionResponse,
    TestsRequest,
    TestsResponse,
    format_validation_errors,
)
from app.service.exceptions import ServiceException
from app.service.main import KotlinService

APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR / 'templates'
STATIC_DIR = APP_DIR / 'static'


def create_app() -> FastAPI:
    app = FastAPI()
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    if STATIC_DIR.is_dir():
        app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=400,
            content=BadRequestResponse(
                details=format_validation_errors(exc.errors()),
            ).model_dump(),
        )

    @app.exception_handler(ServiceException)
    async def service_exception_handler(
        request: Request,
        exc: ServiceException,
    ):
        return JSONResponse(
            status_code=500,
            content=ServiceExceptionResponse(
                error=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        if exc.status_code == 400 and isinstance(exc.detail, list):
            return JSONResponse(
                status_code=400,
                content=BadRequestResponse(
                    details=format_validation_errors(exc.detail),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={'error': str(exc.detail)},
        )

    @app.get('/', response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(request, 'index.html')

    @app.post('/debug/', response_model=DebugResponse)
    async def debug(data: DebugRequest):
        result = KotlinService.debug(data.to_entity())
        return DebugResponse.from_entity(result)

    @app.post('/testing/', response_model=TestsResponse)
    async def testing(data: TestsRequest):
        result = KotlinService.testing(data.to_entity())
        return TestsResponse.from_entity(result)

    return app


app = create_app()
