// Screenshot each slide HTML (1280x1600) at 2x. Usage: node render.js out_dir n
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [dir, n] = [process.argv[2], +process.argv[3]];
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 1280, height: 1600 }, deviceScaleFactor: 2 });
  for (let i = 1; i <= n; i++) {
    await page.goto('file://' + path.resolve(dir, `slide${i}.html`));
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => { const q = document.querySelector('.quote'), m = document.querySelector('.qm-end');
      if (q && m) m.style.top = (q.offsetTop + q.offsetHeight - 40) + 'px'; });
    await page.locator('.slide').screenshot({ path: path.resolve(dir, `_raw${i}.png`) });
  }
  await b.close();
})();
