from pydantic import BaseModel
import datetime


class CreateRoleRequest(BaseModel):
    name: str
    description: str


class RoleResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    last_modified_at: datetime.datetime
    name: str
    description: str


class RoleInUserResponse(BaseModel):
    id: int
    name: str
    description: str


class AddRoleToUserRequest(BaseModel):
    user_id: int
    role_id: int


class RemoveRoleFromUserRequest(BaseModel):
    user_id: int
    role_id: int
