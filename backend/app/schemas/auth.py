from pydantic import BaseModel, EmailStr, Field, field_validator


def _strip(value: str) -> str:
    return " ".join(value.split())


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(max_length=200)
    dietary_preferences: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("first_name", "last_name")
    @classmethod
    def _clean_names(cls, value: str) -> str:
        value = _strip(value)
        if not value:
            raise ValueError("must not be blank")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=200)


class PreferencesUpdate(BaseModel):
    dietary_preferences: list[str] = Field(default_factory=list, max_length=10)


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        value = _strip(value)
        if not value:
            raise ValueError("must not be blank")
        return value


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(max_length=200)
