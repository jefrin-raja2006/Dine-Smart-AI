from pydantic import BaseModel, Field, field_validator


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=5, max_length=2000)

    @field_validator("text")
    @classmethod
    def _clean_text(cls, value: str) -> str:
        # collapse whitespace, drop control characters
        value = "".join(ch for ch in value if ch.isprintable() or ch in "\n ")
        value = " ".join(value.split())
        if len(value) < 5:
            raise ValueError("Review must contain at least 5 characters")
        return value
