// 기획안(plan JSON)을 읽어 표지 + Look 자막을 9:16 프레임에 입혀 미리보기 PNG로 저장한다.
// 실제 생성 이미지가 아직 없으므로 배경은 임시 그라데이션을 쓴다.
// 사용법: node lookbook/overlay/preview.js <plan.json> <출력폴더>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function html(plan) {
  const looks = plan.looks.map((l) => `
  <section class="f look">
    <div class="ph">AI 생성 이미지 자리<br><small>${esc(l.prompt)}</small></div>
    <div class="lk">${esc(l.label || `Look ${l.no}`)}</div>
    <div class="cap">${esc(l.overlay.replace(/^Look \d+ · /, ''))}</div>
    <div class="ai">AI 생성 이미지 · 비슷한 상품 추천</div>
  </section>`).join('');

  return `<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;700;900&family=Noto+Serif+KR:wght@500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR',sans-serif;word-break:keep-all}
.f{width:1080px;height:1920px;position:relative;overflow:hidden;background:linear-gradient(170deg,#f6c27a 0%,#d98a5a 45%,#5a4a63 100%)}
.ph{position:absolute;top:38%;left:120px;right:120px;text-align:center;color:rgba(255,255,255,.75);font-size:44px;font-weight:700;line-height:1.5}
.ph small{display:block;font-size:26px;font-weight:500;margin-top:20px;opacity:.8}
.cover .box{position:absolute;left:70px;right:70px;bottom:300px}
.cover .t1{font-size:88px;font-weight:900;line-height:1.25;color:#ffb37a;text-shadow:0 4px 18px rgba(0,0,0,.35);letter-spacing:-2px}
.cover .t2{color:#fff}
.cover .line{width:760px;height:3px;margin:34px 0;background:linear-gradient(90deg,#fff,transparent)}
.cover .badge{display:inline-block;background:rgba(255,255,255,.92);color:#5a3a2a;font-size:44px;font-weight:700;padding:18px 34px;border-radius:20px}
.lk{position:absolute;left:70px;top:200px;font-family:'Noto Serif KR',serif;font-size:120px;color:#fff;text-shadow:0 4px 16px rgba(0,0,0,.3)}
.cap{position:absolute;left:70px;right:70px;bottom:330px;font-size:54px;font-weight:700;color:#fff;text-shadow:0 3px 12px rgba(0,0,0,.5)}
.ai{position:absolute;right:40px;bottom:60px;font-size:26px;color:rgba(255,255,255,.85);background:rgba(0,0,0,.25);padding:8px 16px;border-radius:10px}
</style></head><body>
<section class="f cover">
  <div class="ph">AI 생성 이미지 자리</div>
  <div class="box">
    <div class="t1">${esc(plan.hook.title)}<br><span class="t2">${esc(plan.hook.sub)}</span></div>
    <div class="line"></div>
    <div class="badge">${esc(plan.hook.badge)}</div>
  </div>
  <div class="ai">AI 생성 이미지 · 비슷한 상품 추천</div>
</section>${looks}
</body></html>`;
}

(async () => {
  const [planPath, outDir] = process.argv.slice(2);
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.setContent(html(plan), { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    const t = document.body.innerText;
    for (const f of ['500 40px "Noto Sans KR"', '700 40px "Noto Sans KR"', '900 40px "Noto Sans KR"', '500 40px "Noto Serif KR"']) {
      await document.fonts.load(f, t);
    }
  });
  await page.waitForTimeout(800);

  const frames = await page.$$('section');
  for (let i = 0; i < frames.length; i++) {
    const file = path.join(outDir, `${plan.id}_${i}.png`);
    await frames[i].screenshot({ path: file });
    console.log(file);
  }
  await browser.close();
})();
