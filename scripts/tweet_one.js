// Post a single tweet via Chrome CDP
// Usage: node scripts/tweet_one.js "Tweet text here"

const {chromium} = require('playwright');
async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const fs = require('fs');
const arg = process.argv[2];
if (!arg) { console.log('NO_TEXT'); process.exit(1); }
// If arg is a file path, read from file. Otherwise use as direct text.
let tweetText;
if (fs.existsSync(arg)) {
    tweetText = fs.readFileSync(arg, 'utf-8').trim();
} else {
    tweetText = arg;
}

(async () => {
    try {
        const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
        const ctx = browser.contexts()[0];
        const page = await ctx.newPage();
        await page.goto('https://x.com/home', {timeout: 20000, waitUntil: 'domcontentloaded'});
        await sleep(5000);

        if (page.url().includes('login')) { console.log('NOT_LOGGED_IN'); process.exit(1); }

        const composer = await page.$('[data-testid="tweetTextarea_0"]');
        if (!composer) { console.log('NO_COMPOSER'); process.exit(1); }

        await composer.click();
        await sleep(500);

        const lines = tweetText.split('\\n');
        for (let i = 0; i < lines.length; i++) {
            if (lines[i] === '') {
                await page.keyboard.press('Enter');
            } else {
                await page.keyboard.type(lines[i], {delay: 12});
            }
            if (i < lines.length - 1) await page.keyboard.press('Enter');
            await sleep(30);
        }

        await sleep(2000);
        const btn = await page.$('[data-testid="tweetButtonInline"]');
        if (btn) {
            await btn.click();
            console.log('POSTED');
            await sleep(3000);
        } else {
            console.log('NO_BUTTON');
        }
        await page.close();
    } catch(e) {
        console.log('ERROR: ' + e.message.substring(0, 80));
        process.exit(1);
    }
})();
