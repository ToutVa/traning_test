# 기획안 (plans)

클라우드 예약 작업이 매주 작성하고, PC의 `run.py`가 읽어서 처리한다. 주차별 폴더(`2026-W44/`)에 릴스 1개당 JSON 1개.

## 주요 필드

| 필드 | 설명 |
|---|---|
| `id`, `publish_at` | 고유 ID, 게시 시각 (한국 시간) |
| `hook.title` / `sub` / `badge` | 표지 문구. 한 줄 12자 안팎을 권장 |
| `rationale` | 이 주제를 고른 근거와 출처. 검수할 때 확인용 |
| `style` | 전체 룩에 공통으로 붙는 구도, 장소, 분위기 (ComfyUI 프롬프트에 합쳐짐) |
| `looks[].prompt` | 룩별 생성 프롬프트 |
| `looks[].overlay` | 영상에 들어갈 Look 자막 |
| `looks[].items[]` | 상품 매칭용 아이템 설명. `keywords`로 쿠팡 검색, `price_max` 이하로 필터 |
| `caption`, `hashtags`, `dm_keyword` | 인스타 캡션, 해시태그, 댓글→DM 키워드 |

광고 표기와 "AI 생성 · 비슷한 상품" 문구는 기획안에 쓰지 않는다. PC 쪽 파이프라인이 자동으로 붙인다.

## 미리보기

```bash
node lookbook/overlay/preview.js lookbook/plans/2026-W44/hagaek-tweed.json <출력폴더>
```
