"""Password hashing using Argon2id."""
import re
from typing import List, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, hash: str) -> bool:
    try:
        _hasher.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    errors = []
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be at most {MAX_PASSWORD_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    return (len(errors) == 0, errors)
