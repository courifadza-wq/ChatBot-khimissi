// Génération du guide PDF via Chromium (Playwright)
const { chromium } = require('playwright')

async function main() {
  const browser = await chromium.launch()
  const page = await browser.newPage()

  await page.goto('file:///home/user/darlila/docs/guide-source.html', { waitUntil: 'networkidle' })
  // Attendre que les polices Google soient chargées et mises en page
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(800)

  await page.pdf({
    path: '/home/user/darlila/GUIDE-PROJET-DARLILA.pdf',
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
  })

  await browser.close()
  console.log('PDF généré ✓')
}
main().catch((e) => { console.error('ÉCHEC :', e.message); process.exit(1) })
