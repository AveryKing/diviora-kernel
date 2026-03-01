from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import Any


class FieldInfo:
    def __init__(self, default: Any = None, default_factory: Any = None) -> None:
        self.default = default
        self.default_factory = default_factory


def Field(*, default: Any = None, default_factory: Any = None) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory)


class BaseModel:
    def __init__(self, **data: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            if name in data:
                value = data[name]
            else:
                default = getattr(self.__class__, name, None)
                if isinstance(default, FieldInfo):
                    if default.default_factory is not None:
                        value = default.default_factory()
                    else:
                        value = deepcopy(default.default)
                else:
                    value = deepcopy(default)
            setattr(self, name, value)

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "BaseModel":
        return cls(**data)

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in getattr(self.__class__, "__annotations__", {}):
            result[name] = _dump_value(getattr(self, name))
        return result

    def model_copy(self, update: dict[str, Any] | None = None) -> "BaseModel":
        payload = self.model_dump()
        if update:
            payload.update(update)
        return self.__class__(**payload)


def _dump_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump_value(val) for key, val in value.items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value
