"""Per-run artifact store. Each stage's output is saved so runs can resume."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, TypeVar

from pydantic import BaseModel, TypeAdapter

T = TypeVar("T")


class RunStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, *parts: str) -> Path:
        p = self.root.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def stage(self, name: str, type_: type[T], produce: Callable[[], T]) -> T:
        """Return the saved artifact for `name`, or produce, save and return it."""
        adapter = TypeAdapter(type_)
        f = self.path(f"{name}.json")
        if f.exists():
            return adapter.validate_json(f.read_text(encoding="utf-8"))
        value = produce()
        f.write_bytes(adapter.dump_json(value, indent=2))
        return value

    def save(self, name: str, value: BaseModel | list | dict) -> None:
        data = value.model_dump() if isinstance(value, BaseModel) else TypeAdapter(type(value)).dump_python(value)
        self.path(f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
