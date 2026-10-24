"""기획안의 룩 + 공통 스타일 + 설정을 합쳐 이미지 생성 프롬프트를 만든다."""


def build_prompt(plan: dict, look: dict, cfg: dict, with_reference: bool = False) -> str:
    style = plan.get("style", {})
    p = cfg["image"]["prompt"]

    parts = []
    if with_reference:
        parts.append("Same model as the reference image: keep her hair, body shape and skin tone identical. Change only the outfit and the setting.")
    parts += [
        look["prompt"],
        f"default setting unless stated above: {style['location']}" if style.get("location") else "",
        style.get("mood", ""),
        f"framing: {style['framing']}" if style.get("framing") else "",
        "vertical portrait composition",
        p["quality_suffix"],
        p["avoid"],
    ]
    return ". ".join(s.strip().rstrip(".") for s in parts if s and s.strip()) + "."
