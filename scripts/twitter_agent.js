/**
 * Twitter Engagement Agent for @agentpay_xyz
 *
 * Searches for relevant tweets, replies with smart comments,
 * and follows relevant accounts. Runs via Chrome CDP.
 *
 * Usage: node scripts/twitter_agent.js
 * Schedule: every 2-3 hours via Windows Task Scheduler
 */

const {chromium} = require('playwright');
const https = require('https');
const fs = require('fs');

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const STATE_FILE = 'C:/Users/Administrateur/agent-pay/scripts/.twitter_agent_state.json';

// Keywords to search for
const SEARCH_QUERIES = [
    'AI agents',
    'LangChain agent',
    'multi agent system',
    'autonomous AI agent',
    'CrewAI',
    'AutoGen agent',
    'agentic AI',
    'AI agent framework',
    'agent economy',
    'AI automation',
    'building AI agents',
    'Claude MCP',
    'AI agent Python',
    'agent orchestration',
    'AI agent tool',
];

// Smart reply templates — rotated and adapted to context
const REPLY_TEMPLATES = [
    "This is exactly the problem we're solving with agent-pay — let agents pay each other in 3 lines of Python. Open source: github.com/agentpay-protocol/agent-pay",
    "Interesting thread. We built an open-source SDK for exactly this use case — autonomous agent payments on Base L2. Fees < $0.001. pip install agentpay-protocol",
    "The agent economy needs payment rails. We open-sourced ours: works with LangChain, CrewAI, AutoGen, Claude Code. github.com/agentpay-protocol/agent-pay",
    "Great point. One of the biggest bottlenecks in multi-agent systems is money flow. We built agent-pay to fix that — 1 line to send USDC between agents.",
    "We've been thinking about this too. Built an SDK that gives every AI agent its own wallet. Non-custodial, instant settlement, < $0.001 fees. MIT license.",
    "This is why we built agent-pay. Your agent shouldn't need human approval for a $0.10 transaction. pip install agentpay-protocol",
    "Relevant: we open-sourced payment infrastructure for AI agents. Works with LangChain, CrewAI, and Claude Code (MCP). github.com/agentpay-protocol/agent-pay",
];

// Engagement-only replies (no promo, just value — used 50% of the time)
const VALUE_REPLIES = [
    "Great insight. The agent-to-agent payment layer is going to be massive. Most people underestimate how quickly this will scale.",
    "This is the right framing. Agents need financial autonomy to be truly useful. Otherwise it's just fancy automation with a human bottleneck.",
    "Agree. The coordination problem in multi-agent systems always comes back to incentives and payments.",
    "Interesting approach. The key challenge is making this work without introducing custody risk or KYC friction.",
    "The 402 Payment Required HTTP status was literally designed for this 29 years ago. We're finally getting there.",
    "The agent economy will be bigger than the creator economy. Most people aren't ready for this.",
    "Good point. Trust between agents is solved by escrow + on-chain settlement. No need for reputation systems.",
];

function loadState() {
    if (fs.existsSync(STATE_FILE)) {
        return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    }
    return { replied_tweets: [], followed_accounts: [], last_run: null, total_replies: 0, total_follows: 0 };
}

function saveState(state) {
    state.last_run = new Date().toISOString();
    fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function sendTelegram(msg) {
    const data = `chat_id=5047076645&text=${encodeURIComponent(msg)}`;
    const req = https.request({
        hostname: 'api.telegram.org',
        path: '/bot8685866733:AAEhP42Qc5i-_Yw5MOfYwuXRmqOpbphILhg/sendMessage',
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }, () => {});
    req.write(data);
    req.end();
}

(async () => {
    const state = loadState();

    // Limit: max 5 replies + 5 follows per run (avoid ban)
    const MAX_REPLIES = 5;
    const MAX_FOLLOWS = 5;
    let replies = 0;
    let follows = 0;

    let browser;
    try {
        browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
    } catch(e) {
        console.log('Chrome not available. Exiting.');
        return;
    }

    const ctx = browser.contexts()[0];
    const page = await ctx.newPage();

    // Pick a random search query
    const query = SEARCH_QUERIES[Math.floor(Math.random() * SEARCH_QUERIES.length)];
    console.log('Searching: ' + query);

    await page.goto(`https://x.com/search?q=${encodeURIComponent(query)}&src=typed_query&f=live`, {
        timeout: 25000, waitUntil: 'domcontentloaded'
    }).catch(() => {});
    await sleep(8000);

    if (page.url().includes('login')) {
        console.log('Not logged in. Exiting.');
        await page.close();
        return;
    }

    // Scroll multiple times to load tweets
    for (let s = 0; s < 3; s++) {
        await page.evaluate((offset) => window.scrollTo(0, offset), 500 + s * 800);
        await sleep(2000);
    }

    // Get tweet elements
    const tweets = await page.evaluate(() => {
        const items = [];
        document.querySelectorAll('article[data-testid="tweet"]').forEach(tweet => {
            const textEl = tweet.querySelector('[data-testid="tweetText"]');
            const userEl = tweet.querySelector('[data-testid="User-Name"]');
            const linkEls = tweet.querySelectorAll('a[href*="/status/"]');

            if (textEl && userEl) {
                // Get tweet link
                let tweetUrl = '';
                for (const a of linkEls) {
                    if (a.href.includes('/status/')) {
                        tweetUrl = a.href;
                        break;
                    }
                }

                items.push({
                    text: textEl.textContent.trim().substring(0, 200),
                    user: userEl.textContent.trim().substring(0, 50),
                    url: tweetUrl,
                    id: tweetUrl.split('/status/')[1]?.split('?')[0] || '',
                });
            }
        });
        return items;
    });

    console.log('Found ' + tweets.length + ' tweets');

    for (const tweet of tweets) {
        if (replies >= MAX_REPLIES) break;
        if (!tweet.id || state.replied_tweets.includes(tweet.id)) continue;

        // Skip our own tweets
        if (tweet.user.includes('agentpay')) continue;

        // Skip tweets with <10 chars
        if (tweet.text.length < 20) continue;

        console.log('\n--- Tweet by ' + tweet.user + ' ---');
        console.log('  ' + tweet.text.substring(0, 100));

        // Navigate to the tweet
        if (tweet.url) {
            await page.goto(tweet.url, {timeout: 15000, waitUntil: 'domcontentloaded'}).catch(() => {});
            await sleep(4000);
        }

        // Choose reply: 50% promo, 50% pure value
        const usePromo = Math.random() > 0.5;
        const templates = usePromo ? REPLY_TEMPLATES : VALUE_REPLIES;
        const reply = templates[Math.floor(Math.random() * templates.length)];

        // Click reply box
        const replyBox = await page.$('[data-testid="tweetTextarea_0"]');
        if (replyBox) {
            await replyBox.click();
            await sleep(500);
            await page.keyboard.type(reply, {delay: 15});
            await sleep(1000);

            // Click Reply button
            const replyBtn = await page.$('[data-testid="tweetButtonInline"]');
            if (replyBtn) {
                await replyBtn.click();
                replies++;
                state.replied_tweets.push(tweet.id);
                console.log('  REPLIED (' + (usePromo ? 'promo' : 'value') + ')');
                await sleep(3000);
            }
        }

        // Follow the user (if not already)
        if (follows < MAX_FOLLOWS) {
            const followBtn = await page.evaluate(() => {
                const btns = document.querySelectorAll('[data-testid$="-follow"]');
                for (const b of btns) {
                    if (b.textContent.includes('Follow') && !b.textContent.includes('Following')) {
                        b.click();
                        return true;
                    }
                }
                return false;
            });
            if (followBtn) {
                follows++;
                console.log('  FOLLOWED');
            }
        }

        // Wait between actions (human-like)
        await sleep(5000 + Math.random() * 5000);
    }

    // Keep replied_tweets list manageable (last 500)
    state.replied_tweets = state.replied_tweets.slice(-500);
    state.total_replies += replies;
    state.total_follows += follows;
    saveState(state);

    console.log('\n=== DONE: ' + replies + ' replies, ' + follows + ' follows ===');

    if (replies > 0) {
        sendTelegram('NEO Twitter Agent: ' + replies + ' replies + ' + follows + ' follows. Query: "' + query + '"');
    }

    await page.close();
})();
