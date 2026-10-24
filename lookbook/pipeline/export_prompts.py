"""기획안의 룩별 프롬프트를 ChatGPT에 붙여넣기 좋은 마크다운으로 내보낸다.

사용법 (lookbook 폴더에서):
    python -m pipeline.export_prompts plans/2026-W44 > prompts/2026-W44.md
"""
import sys
from pathlib import Path

from .common import load_config, load_plan
from .prompting import build_prompt

FIRST = """같은 대화창에서 이어서 생성하세요. 첫 이미지로 모델(헤어·체형)이 정해지면, 다음부터는 **"같은 모델로, 아래 착장으로 바꿔줘"**를 앞에 붙이면 인물이 유지됩니다.
비율은 세로(2:3)로 요청하고, 이미지 안에 글자는 넣지 않습니다(자막은 편집 단계에서 입힘)."""


def main() -> int:
    folder = Path(sys.argv[1])
    cfg = load_config()
    out = [f"# {folder.name} 이미지 생성 프롬프트", "", FIRST, ""]

    for path in sorted(folder.glob("*.json")):
        plan = load_plan(path)
        out += [f"## {plan['hook']['title']} / {plan['hook']['sub']}",
                f"`{plan['id']}` · 게시 {plan['publish_at'][:16].replace('T', ' ')}", ""]
        for i, look in enumerate(plan["looks"]):
            name = look.get("label") or f"Look {look['no']}"
            lead = "" if i == 0 else "같은 모델로, 아래 착장으로 바꿔줘. "
            out += [f"### {name} · {look['overlay'].split(' · ')[-1]}", "",
                    "```", f"세로 2:3 비율 이미지를 만들어줘. {lead}{build_prompt(plan, look, cfg)}", "```", ""]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
