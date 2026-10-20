# 카드뉴스 생성기

HTML/CSS로 카드뉴스를 디자인하고, 브라우저(Playwright + Chromium)로 한 장씩 캡처해 인스타그램용 PNG(1080×1350)를 만든다.
캐릭터는 이미지 파일 없이 SVG 코드로 그리므로 저작권 걱정이 없다.

## 구성

- `ep001.html`: 「말랑 대리의 회사생활」 EP.1 연차 편 (10장). `<section>` 하나가 카드 한 장.
- `render.js`: HTML의 각 `<section>`을 `out/<파일명>_NN.png`로 저장.
- `out/`: 렌더링 결과.

## 실행

```bash
npm install playwright        # 처음 한 번
node cardnews/render.js cardnews/ep001.html
```

웹폰트(Noto Sans KR)를 Google Fonts에서 불러오므로 인터넷 연결이 필요하다.

## 캐릭터 조합법

`ep001.html` 상단 `<defs>`에 몸통, 표정, 소품이 따로 정의되어 있고, `<use>`를 겹쳐서 장면을 만든다.

```html
<svg width="200" height="200">
  <use href="#body-daeri"/><use href="#f-shock"/><use href="#a-sweat"/>
</svg>
```

| 종류 | id |
|---|---|
| 몸통 | `body-daeri` (말랑 대리), `body-sinip` (뽀짝 신입), `body-bujang` (깐깐 부장) |
| 표정 | `f-happy`, `f-shock`, `f-smug`, `f-nervous`, `f-sad`, `f-flat`, `f-cool` |
| 소품 | `a-sweat` (땀), `a-boss` (안경+콧수염), `a-tie` (넥타이), `a-lei` (꽃목걸이) |
