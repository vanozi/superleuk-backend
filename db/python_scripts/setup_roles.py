from app.models.tortoise import Roles, Users, Addresses
from tortoise import run_async, Tortoise
import os
from app.services.auth import Auth


async def create_roles_and_users():
    await Tortoise.init(
        db_url=os.environ.get("DATABASE_URL"),
        modules={"models": ["app.models.tortoise"]},
    )
    roles = [
        {"name": "admin", "description": "User met admin rechten"},
        {"name": "werknemer", "description": "User met algemene werknemers rechten"},
        {"name": "monteur", "description": "User met monteurs rechten'"},
        {
            "name": "melker",
            "description": "Werkemer waarvoor de melkbeurten apart worden berekend",
        },
    ]
    for role in roles:
        # if role exists in the database dont create it and the user and ther address related
        if await Roles.exists(name=role["name"]):
            continue
        else:
            created_role = await Roles.create(**role)
            created_user = await Users.create(
                first_name=f"{role['name']}_voornaam",
                last_name=f"{role['name']}_achternaam",
                email=f"{role['name']}@{role['name']}.com",
                telephone_number="0612345678",
                hashed_password=Auth.get_password_hash(f"{role['name']}"),
                is_active=True,
                role=created_role,
            )
            created_address = await Addresses.create(
                street=f"{role['name']}_straat",
                number=f"{role['name']}_nummer",
                postal_code="1234AB",
                city=f"{role['name']}_stad",
                country=f"{role['name']}_land",
                user=created_user,
            )


if __name__ == "__main__":
    run_async(create_roles_and_users())
