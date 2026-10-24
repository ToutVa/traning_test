"""기획안의 아이템·장소를 바탕으로 참고 이미지를 모은다 (PC에서 실행).

1) 상품 이미지: 쿠팡파트너스 Open API로 아이템별 상품을 검색해 후보 이미지와 제휴 링크를 저장
   → 생성 단계에서 '실제로 링크할 상품'을 참고 이미지로 넣어, 생성된 옷이 판매 상품과 닮게 만든다
   → 상품 매칭(match) 후보로도 그대로 쓴다
2) 분위기·장소 이미지: Pexels API (상업적 이용·수정 허용 라이선스)

사용법 (lookbook 폴더에서):
    python -m pipeline.refs plans/2026-W44/barrel-jeans.json --dry-run   # 검색어만 확인
    python -m pipeline.refs plans/2026-W44/barrel-jeans.json             # 수집
    python -m pipeline.refs <plan> --only products                      # 상품만

결과: episodes/<id>/refs/look<N>/item<K>_<순위>.jpg, episodes/<id>/refs/mood/*.jpg, episodes/<id>/refs.json
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .common import episode_dir, load_config, load_env, load_plan

COUPANG_HOST = "https://api-gateway.coupang.com"
COUPANG_SEARCH = "/v2/providers/affiliate_open_api/apis/openapi/products/search"


def coupang_auth(method: str, path: str, query: str, access_key: str, secret_key: str) -> str:
    """쿠팡 Open API HMAC 서명 헤더."""
    signed_date = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
    message = signed_date + method + path + query
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={signed_date}, signature={signature}"


def http_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "lookbook/1.0", **headers})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url: str, path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lookbook/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            path.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  이미지 다운로드 실패: {e}", file=sys.stderr)
        return False


def search_coupang(keyword: str, limit: int) -> list[dict]:
    query = urllib.parse.urlencode({"keyword": keyword, "limit": limit})
    auth = coupang_auth("GET", COUPANG_SEARCH, query, os.environ["COUPANG_ACCESS_KEY"], os.environ["COUPANG_SECRET_KEY"])
    data = http_json(f"{COUPANG_HOST}{COUPANG_SEARCH}?{query}", {"Authorization": auth})
    products = (data.get("data") or {}).get("productData") or []
    return [{
        "name": p.get("productName"),
        "price": p.get("productPrice"),
        "image": p.get("productImage"),
        "url": p.get("productUrl"),        # 제휴 추적이 포함된 링크
        "product_id": p.get("productId"),
        "rocket": p.get("isRocket"),
    } for p in products]


def search_pexels(query: str, limit: int) -> list[dict]:
    q = urllib.parse.urlencode({"query": query, "orientation": "portrait", "per_page": limit})
    data = http_json(f"https://api.pexels.com/v1/search?{q}", {"Authorization": os.environ["PEXELS_API_KEY"]})
    return [{
        "image": p["src"]["large2x"],
        "page": p["url"],
        "photographer": p["photographer"],
        "license": "Pexels License",
    } for p in data.get("photos", [])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=["products", "mood"])
    args = ap.parse_args()

    load_env()
    cfg = load_config().get("refs", {})
    per_item = cfg.get("products_per_item", 3)
    max_price_filter = cfg.get("respect_price_max", True)
    interval = cfg.get("coupang_interval_sec", 2)
    plan = load_plan(args.plan)

    jobs_products = [(l["no"], k, item) for l in plan["looks"] for k, item in enumerate(l.get("items", []), 1)]
    mood_query = plan.get("style", {}).get("location", "")

    if args.dry_run:
        if args.only != "mood":
            print(f"[상품] 쿠팡 검색 {len(jobs_products)}회 (아이템당 후보 {per_item}개)")
            for no, k, item in jobs_products:
                print(f"  look{no} item{k}: '{item['keywords'][0]}' (≤{item.get('price_max', '-')}원)")
        if args.only != "products":
            print(f"[분위기] Pexels 검색: '{mood_query}'")
        return 0

    out = episode_dir(plan)
    refs_dir = out / "refs"
    manifest_path = out / "refs.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    if args.only != "mood":
        if not (os.environ.get("COUPANG_ACCESS_KEY") and os.environ.get("COUPANG_SECRET_KEY")):
            print("COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY가 없습니다. 상품 수집을 건너뜁니다.", file=sys.stderr)
        else:
            for no, k, item in jobs_products:
                print(f"look{no} item{k}: {item['desc']}")
                try:
                    found = search_coupang(item["keywords"][0], limit=10)
                except Exception as e:
                    print(f"  검색 실패: {e}", file=sys.stderr)
                    continue
                if max_price_filter and item.get("price_max"):
                    found = [p for p in found if p["price"] and p["price"] <= item["price_max"]] or found
                cands = []
                d = refs_dir / f"look{no}"
                d.mkdir(parents=True, exist_ok=True)
                for rank, p in enumerate(found[:per_item], 1):
                    path = d / f"item{k}_{rank}.jpg"
                    if p["image"] and download(p["image"], path):
                        p["file"] = str(path.relative_to(out))
                    cands.append(p)
                manifest.setdefault(f"look{no}", {})[f"item{k}"] = {
                    "desc": item["desc"], "candidates": cands, "selected": 0 if cands else None,
                }
                time.sleep(interval)  # API 호출 한도 보호

    if args.only != "products":
        if not os.environ.get("PEXELS_API_KEY"):
            print("PEXELS_API_KEY가 없습니다. 분위기 이미지 수집을 건너뜁니다.", file=sys.stderr)
        elif mood_query:
            d = refs_dir / "mood"
            d.mkdir(parents=True, exist_ok=True)
            moods = []
            for i, p in enumerate(search_pexels(mood_query, limit=cfg.get("mood_count", 4)), 1):
                path = d / f"mood_{i}.jpg"
                if download(p["image"], path):
                    p["file"] = str(path.relative_to(out))
                    moods.append(p)
            manifest["mood"] = moods

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
