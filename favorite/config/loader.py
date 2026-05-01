import json
import os
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent.parent

def _load(name: str) -> dict:
    path = _BASE / "config" / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(name: str, data: dict) -> None:
    path = _BASE / "config" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Config:
    def __init__(self):
        self._keys = _load("api_keys.json")
        self._github = _load("github.json")

    @property
    def github_token(self) -> str:
        return self._github.get("token", "")

    @property
    def github_owner(self) -> str:
        return self._github.get("owner", "")

    @property
    def github_repo(self) -> str:
        return self._github.get("repo", "")

    @property
    def github_branch(self) -> str:
        return self._github.get("branch", "main")

    @property
    def favorite_api_keys(self) -> list[dict]:
        return self._keys.get("favorite_api", [])

    @property
    def openrouter_keys(self) -> list[dict]:
        return self._keys.get("openrouter", [])

    @property
    def void_ai_key(self) -> str:
        return self._keys.get("void_ai", "")

    @property
    def favorite_api_base_url(self) -> str:
        return self._keys.get("favorite_api_base_url", "http://127.0.0.1:5005")

    def default_openrouter_key(self) -> dict | None:
        for k in self.openrouter_keys:
            if k.get("is_default"):
                return k
        return self.openrouter_keys[0] if self.openrouter_keys else None

    def default_favorite_key(self) -> dict | None:
        for k in self.favorite_api_keys:
            if k.get("is_default"):
                return k
        return self.favorite_api_keys[0] if self.favorite_api_keys else None

    def save_keys(self) -> None:
        _save("api_keys.json", self._keys)


_cfg: Config | None = None

def get_config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg
