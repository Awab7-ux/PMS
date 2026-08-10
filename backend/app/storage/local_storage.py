import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_data: bytes, stored_filename: str) -> str:
        pass

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        pass

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or os.getenv("UPLOAD_DIR", "uploads"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_path: str) -> Path:
        resolved = (self.base_dir / storage_path).resolve()
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal detected")
        return resolved

    def save(self, file_data: bytes, stored_filename: str) -> str:
        subdir = stored_filename[:2]
        target_dir = self.base_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        rel_path = f"{subdir}/{stored_filename}"
        target = self._resolve(rel_path)
        target.write_bytes(file_data)
        return rel_path

    def read(self, storage_path: str) -> bytes:
        return self._resolve(storage_path).read_bytes()

    def delete(self, storage_path: str) -> None:
        target = self._resolve(storage_path)
        if target.exists():
            target.unlink()


def get_storage() -> StorageBackend:
    return LocalStorageBackend()
