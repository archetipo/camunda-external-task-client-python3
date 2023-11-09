from typing import Any, Dict, Union

from pydantic import BaseModel, field_validator


class AuthBearer(BaseModel):
    access_token: str

    @field_validator('access_token', mode="before")
    def get_token_from_dict(cls, value: Union[str, Dict[str, Any]]) -> str:
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            raise ValueError('token should be dict or str')
        if not value.get('access_token'):
            raise KeyError(
                'you should pass the token inside "access_token" key')
        return value['access_token']

    @field_validator('access_token')
    def concat_bearer(cls, value: str) -> str:
        if not any([
            value.startswith('Bearer'),
            value.startswith('bearer')
        ]):
            return f'Bearer {value}'
