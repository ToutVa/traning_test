"""파이프라인 공통: 경로, 설정, .env, 기획안 읽기."""
import json
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # lookbook/


def load_env(path: Path = ROOT / ".env") -> None:
    """.env의 KEY=VALUE를 환경변수로 올린다. 이미 설정된 값은 덮어쓰지 않는다."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path: Path = ROOT / "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_plan(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def episode_dir(plan: dict) -> Path:
    d = ROOT / "episodes" / plan["id"]
    (d / "media").mkdir(parents=True, exist_ok=True)
    return d
