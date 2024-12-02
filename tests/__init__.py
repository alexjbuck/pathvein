import random
import string
from contextlib import contextmanager
from typing import Generator

import fsspec
from upath import UPath


@contextmanager
def isolated_memory_filesystem():
    fs = fsspec.filesystem("memory")
    archive_store = fs.store
    archive_dirs = fs.pseudo_dirs
    try:
        fs.store = {}
        fs.pseudo_dirs = [""]
        yield fs
    finally:
        fs.store = archive_store
        fs.pseudo_dirs = archive_dirs


def generate_random_string(length=6):
    """Generates a random string of uppercase letters and digits."""
    characters = string.ascii_lowercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))


@contextmanager
def ephemeral_s3_bucket(**config) -> Generator[UPath, None, None]:
    bucket = generate_random_string()
    path = UPath(f"s3://{bucket}", **config)
    try:
        path.mkdir()
        yield path
    finally:
        path.rmdir(recursive=True)
