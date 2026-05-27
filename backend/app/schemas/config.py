from typing import Optional

from pydantic import BaseModel, model_validator


class ConfigCreate(BaseModel):
    name: str
    description: str = ""
    method_weights: dict[str, float]
    is_default: bool = False

    @model_validator(mode="after")
    def normalize_and_validate(self):
        if not self.method_weights:
            raise ValueError("method_weights cannot be empty")
        for k, v in self.method_weights.items():
            if v < 0:
                raise ValueError(f"Weight for {k} cannot be negative")
        total = sum(self.method_weights.values())
        if total > 0:
            self.method_weights = {k: round(v / total, 6) for k, v in self.method_weights.items()}
        return self


class ConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    method_weights: Optional[dict[str, float]] = None
    is_default: Optional[bool] = None

    @model_validator(mode="after")
    def normalize_weights(self):
        if self.method_weights is not None:
            for k, v in self.method_weights.items():
                if v < 0:
                    raise ValueError(f"Weight for {k} cannot be negative")
            total = sum(self.method_weights.values())
            if total > 0:
                self.method_weights = {k: round(v / total, 6) for k, v in self.method_weights.items()}
        return self


class ConfigOut(BaseModel):
    id: int
    name: str
    description: str
    method_weights: dict[str, float]
    is_default: bool

    model_config = {"from_attributes": True}
