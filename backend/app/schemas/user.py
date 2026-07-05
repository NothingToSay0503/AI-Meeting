from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    email: str | None = None
    role: str = "member"


class UserRead(BaseModel):
    id: int
    username: str
    display_name: str
    email: str | None
    role: str
    status: str

    model_config = {"from_attributes": True}
