// HTML 카드뉴스의 <section>을 한 장씩 1080x1350 PNG로 저장한다.
// 사용법: node cardnews/render.js cardnews/ep001.html
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const input = path.resolve(process.argv[2] || path.join(__dirname, 'ep001.html'));
  const name = path.basename(input, '.html');
  const outDir = path.join(__dirname, 'out');

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  await page.goto('file://' + input, { waitUntil: 'networkidle' });

  // 웹폰트는 쓰인 글자만 부분 로드되므로, 본문 글자 전체를 굵기별로 미리 불러온다.
  await page.evaluate(async () => {
    const text = document.body.innerText;
    for (const w of [400, 500, 700, 900]) {
      await document.fonts.load(`${w} 40px "Noto Sans KR"`, text);
    }
    await document.fonts.ready;
  });
  await page.waitForTimeout(800);

  const slides = await page.$$('section');
  for (let i = 0; i < slides.length; i++) {
    const file = path.join(outDir, `${name}_${String(i + 1).padStart(2, '0')}.png`);
    await slides[i].screenshot({ path: file });
    console.log(file);
  }
  await browser.close();
})();
