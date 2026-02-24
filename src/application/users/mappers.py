from typing import Optional

from src.application.users.dtos import UserDTO
from src.application.users.models import User


def orm_to_dto(row: User) -> Optional[UserDTO]:
    if not row:
        return None

    return UserDTO(
        id=row.id,
        email=row.email,
        password=row.password,
        name=row.name,
        is_onboarding_completed=row.is_onboarding_completed,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

def dto_to_orm(dto: UserDTO, row: Optional[User] = None) -> User:
    row = row or User()

    if dto.id is not None:
        row.id = dto.id

    updates = {
        "email": dto.email,
        "password": dto.password,
        "name": dto.name,
        "is_onboarding_completed": dto.is_onboarding_completed,
    }

    for field, value in updates.items():
        if value is not None:
            setattr(row, field, value)

    return row