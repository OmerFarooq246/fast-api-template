from app.core.security import hash_password, verify_and_update_password, verify_password

# A bcrypt hash for "legacy-password", retained to exercise a real migration path.
LEGACY_BCRYPT_HASH = "$2b$12$9bPXAw7zdfZrTfByLjz1cu0u9s7r9PTCxduZ719kstKBThW6n/lOu"


def test_new_passwords_use_argon2id() -> None:
    encoded = hash_password("correct horse battery staple")

    assert encoded.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_unknown_hashes_fail_closed() -> None:
    assert verify_and_update_password("password", "not-a-password-hash") == (False, None)


def test_legacy_bcrypt_hash_is_replaced_after_verification() -> None:
    valid, updated_hash = verify_and_update_password("legacy-password", LEGACY_BCRYPT_HASH)

    assert valid
    assert updated_hash is not None
    assert updated_hash.startswith("$argon2id$")
    assert verify_password("legacy-password", updated_hash)
