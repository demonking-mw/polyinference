// Real DOM/entry/save qualification. The caller must explicitly install Playwright/Chromium.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve, sep, extname } from 'node:path';
import assert from 'node:assert/strict';

const option = name => process.argv.find(arg => arg.startsWith(`--${name}=`))?.slice(name.length + 3);
const toolRoot = option('tools') || process.env.QUALIFICATION_BROWSER_TOOLS || process.cwd();
if (option('browsers')) process.env.PLAYWRIGHT_BROWSERS_PATH = option('browsers');
const { chromium } = createRequire(resolve(toolRoot, 'package.json'))('playwright');
if (process.argv.includes('--preflight')) {
  const browser = await chromium.launch({headless: true});
  await browser.close();
} else {
  const root = process.cwd();
  const server = createServer(async (request, response) => {
    try {
      const path = resolve(root, '.' + decodeURIComponent(new URL(request.url, 'http://localhost').pathname));
      if (path !== root && !path.startsWith(root + sep)) throw new Error('outside fixture');
      response.setHeader('Content-Type', extname(path) === '.js' ? 'text/javascript' : 'text/html');
      response.end(await readFile(path === root ? resolve(root, 'index.html') : path));
    } catch {
      response.writeHead(404); response.end();
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({headless: true});
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    assert.deepEqual(errors, []);
    await page.locator('#increment').click();
    assert.equal(await page.locator('#value').textContent(), '1');
    await page.locator('#pause').click();
    assert.equal(await page.locator('#status').textContent(), 'paused');
    await page.locator('#save').click();
    await page.reload();
    assert.equal(await page.locator('#value').textContent(), '1');
    assert.deepEqual(errors, []);
    console.log('Actual entry increment, pause, save and reload passed in Chromium.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
