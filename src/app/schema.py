from typing import Any, Optional

from pydantic import BaseModel, field_validator

from app.entities import DebugData, TestData, TestsData
from app.utils import clean_str


class DebugRequest(BaseModel):
    data_in: Optional[str] = None
    code: str

    @field_validator('data_in', 'code', mode='before')
    @classmethod
    def clean_input(cls, value: Any) -> Any:
        return clean_str(value)

    def to_entity(self) -> DebugData:
        return DebugData(code=self.code, data_in=self.data_in)


class DebugResponse(BaseModel):
    result: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_entity(cls, data: DebugData) -> 'DebugResponse':
        return cls(result=data.result, error=data.error)


class TestRequest(BaseModel):
    data_in: Optional[str] = None
    data_out: str

    @field_validator('data_in', 'data_out', mode='before')
    @classmethod
    def clean_input(cls, value: Any) -> Any:
        return clean_str(value)

    def to_entity(self) -> TestData:
        return TestData(data_in=self.data_in, data_out=self.data_out)


class TestResponse(BaseModel):
    result: Optional[str] = None
    error: Optional[str] = None
    ok: Optional[bool] = None

    @classmethod
    def from_entity(cls, data: TestData) -> 'TestResponse':
        return cls(result=data.result, error=data.error, ok=data.ok)


class TestsRequest(BaseModel):
    tests: list[TestRequest]
    checker: str
    code: str

    @field_validator('checker', 'code', mode='before')
    @classmethod
    def clean_input(cls, value: Any) -> Any:
        return clean_str(value)

    def to_entity(self) -> TestsData:
        return TestsData(
            code=self.code,
            checker=self.checker,
            tests=[test.to_entity() for test in self.tests],
        )


class TestsResponse(BaseModel):
    num: int
    num_ok: int
    ok: bool
    tests: list[TestResponse]

    @classmethod
    def from_entity(cls, data: TestsData) -> 'TestsResponse':
        num_ok = 0
        num = len(data.tests)
        for test in data.tests:
            if test.ok:
                num_ok += 1
        return cls(
            num=num,
            num_ok=num_ok,
            ok=num == num_ok,
            tests=[TestResponse.from_entity(test) for test in data.tests],
        )


VALIDATION_ERROR = 'Validation error'


class BadRequestResponse(BaseModel):
    error: str = VALIDATION_ERROR
    details: dict[str, list[str]]


class ServiceExceptionResponse(BaseModel):
    error: Optional[str]
    details: Any = None


PYDANTIC_ERROR_MESSAGES = {
    'missing': 'Missing data for required field.',
}


def format_validation_errors(errors: list[dict[str, Any]]) -> dict[str, list[str]]:

    """ Преобразует ошибки валидации Pydantic в ожидаемый формат ответа API.

    Формат ошибки велидации FastAPI:
    {
      "detail": [
        {
          "type": "missing",
          "loc": ["body", "code"],
          "msg": "Field required",
          "input": {
            "data_in": "some input"
          }
        }
      ]
    }

     API проекта ожидает другой формат — словарь
    {
        "error": str,
        "details": ?str
    }

    Args:
        errors: Список ошибок из ``RequestValidationError.errors()``.

    """
    details: dict[str, list[str]] = {}
    for error in errors:
        loc = [str(part) for part in error['loc'] if part not in ('body', 'query', 'path')]
        field = loc[-1] if loc else 'body'
        message = PYDANTIC_ERROR_MESSAGES.get(error['type'], error['msg'])
        details.setdefault(field, []).append(message)
    return details
