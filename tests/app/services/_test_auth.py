import re

import pytest
from app.config import Settings
from app.services.auth import Auth
from jose import jwt
from tests.backend.conftest import get_settings_override


@pytest.mark.unittest
class TestAuth:
    def test_get_password_hash(self):
        """
        1. Password length greater then 0 - exp. valid hash created
        2. Password length equal to 0 - exp. valid hash created
        3. Password type is int instead of string - exp. TypeError
        4. Password type is None instead of string - exp. TypeError
        """
        assert Auth.get_password_hash(password="secretstring") != "secretstring"
        assert Auth.get_password_hash(password="") != ""
        with pytest.raises(TypeError) as excinfo:
            Auth.get_password_hash(password=12345)
        with pytest.raises(TypeError) as excinfo:
            Auth.get_password_hash(password=None)

    def test_verify_password(self):
        """
        1. Plain password corresponds with hashed password - exp. returns True
        2. Plain password does not correspond with hashed password - exp. returns False
        3. Plain password is None - exp. TypeError: secret must be unicode or bytes, not None

        """
        assert Auth.verify_password(
            plain_password="secretstring",
            hashed_password=Auth.get_password_hash(password="secretstring"),
        )
        assert (
            Auth.verify_password(
                plain_password="secretstring_mismatch",
                hashed_password=Auth.get_password_hash(password="secretstring"),
            )
            is False
        )
        with pytest.raises(TypeError) as excinfo:
            Auth.verify_password(
                plain_password=None,
                hashed_password=Auth.get_password_hash(password="secretstring"),
            )

    def test_get_token(self):
        """Tests Auth.get_token Token generation with email address"""
        token: str = Auth.get_token(data={"email": "test@test.com"}, expires_delta=10)
        assert token.startswith("ey")

    def test_get_confirmation_token(self, settings: Settings = get_settings_override()):
        # set regex pattern for uuid4
        re_pattern_uuid4 = r"[0-9a-f]{32}\Z"
        confirmation_token = Auth.get_confirmation_token(email="test@test.com")
        assert len(confirmation_token["jti"]) == 32
        assert re.search(re_pattern_uuid4, confirmation_token["jti"])
        decrypted_token = jwt.decode(
            confirmation_token["token"],
            settings.secret_key,
            algorithms=settings.token_algorithm,
        )
        assert decrypted_token.get("sub") == "test@test.com"
        assert decrypted_token.get("scope") == "registration"
        assert len(decrypted_token.get("jti")) == 32
        assert re.search(re_pattern_uuid4, decrypted_token.get("jti"))


# def test_get_access_token(settings: Settings = get_settings_override()):
#     # set regex pattern for uuid4
#     re_pattern_uuid4 = "[0-9a-f]{32}\Z"
#     access_token = Auth.get_access_token(email="test@test.com")
#     assert len(access_token["jti"]) == 32
#     assert re.search(re_pattern_uuid4, access_token["jti"])
#     decrypted_token = jwt.decode(
#         access_token["token"], settings.secret_key, algorithms=settings.token_algorithm
#     )
#     assert decrypted_token.get("sub") == "test@test.com"
#     assert decrypted_token.get("scope") == "login"
#     assert len(decrypted_token.get("jti")) == 32
#     assert re.search(re_pattern_uuid4, decrypted_token.get("jti"))
