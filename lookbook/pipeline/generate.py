"""기획안의 룩마다 GPT 이미지로 착장 사진을 생성한다.

사용법 (lookbook 폴더에서):
    python -m pipeline.generate plans/2026-W44/hagaek-tweed.json --dry-run   # 프롬프트만 확인
    python -m pipeline.generate plans/2026-W44/hagaek-tweed.json             # 실제 생성
    python -m pipeline.generate <plan> --look 2                              # 특정 룩만 다시 생성

결과: episodes/<id>/media/look<번호>_<후보>.png, 사용한 프롬프트는 episodes/<id>/prompts.json
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

from .common import ROOT, episode_dir, load_config, load_env, load_plan
from .prompting import build_prompt


def generate_image(client, cfg: dict, prompt: str, reference: Path | None) -> bytes:
    img = cfg["image"]
    if reference:
        with open(reference, "rb") as f:
            res = client.images.edit(model=img["model"], image=[f], prompt=prompt,
                                     size=img["size"], quality=img["quality"])
    else:
        res = client.images.generate(model=img["model"], prompt=prompt,
                                     size=img["size"], quality=img["quality"], n=1)
    return base64.b64decode(res.data[0].b64_json)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--dry-run", action="store_true", help="API를 호출하지 않고 프롬프트만 출력")
    ap.add_argument("--look", type=int, help="이 번호의 룩만 생성")
    ap.add_argument("--candidates", type=int, help="룩당 후보 수 (기본: config)")
    args = ap.parse_args()

    load_env()
    cfg = load_config()
    plan = load_plan(args.plan)
    n = args.candidates or cfg["image"]["candidates"]

    ref_setting = cfg["image"].get("model_reference", "")
    reference = (ROOT / ref_setting) if ref_setting else None
    if reference and not reference.exists():
        print(f"기준 이미지가 없습니다: {reference}", file=sys.stderr)
        return 1

    looks = [l for l in plan["looks"] if args.look in (None, l["no"])]
    prompts = {f"look{l['no']}": build_prompt(plan, l, cfg, with_reference=bool(reference)) for l in looks}

    if args.dry_run:
        print(f"[{plan['id']}] 모델 {cfg['image']['model']} · {cfg['image']['size']} · {cfg['image']['quality']} · 룩당 {n}장 · 총 {len(looks) * n}장")
        for key, p in prompts.items():
            print(f"\n## {key}\n{p}")
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 없습니다. lookbook/.env에 넣어주세요.", file=sys.stderr)
        return 1

    from openai import OpenAI
    client = OpenAI()
    out = episode_dir(plan)

    for look in looks:
        key = f"look{look['no']}"
        for k in range(1, n + 1):
            path = out / "media" / f"{key}_{k}.png"
            print(f"생성 중: {path.name}")
            try:
                path.write_bytes(generate_image(client, cfg, prompts[key], reference))
            except Exception as e:  # 한 장 실패해도 나머지는 계속
                print(f"  실패: {e}", file=sys.stderr)

    # 기존 기록과 합쳐서 저장 (특정 룩만 다시 돌린 경우 대비)
    log = out / "prompts.json"
    saved = json.loads(log.read_text(encoding="utf-8")) if log.exists() else {}
    saved.update(prompts)
    log.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
