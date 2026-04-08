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

// 90% value replies (NO links, NO product mention — pure insight)
const VALUE_REPLIES = [
    "The coordination problem in multi-agent systems always comes back to incentives. Intelligence is solved. Money flow isn't.",
    "Most people building agents focus on reasoning. But the real bottleneck is economic coordination between agents. That's the unsexy infra that matters.",
    "Interesting. The gap I keep seeing: agents can do the work, but they can't negotiate or pay for resources autonomously. That's the next frontier.",
    "This is the right framing. Without financial autonomy, agents are just fancy automation with a human bottleneck at every step.",
    "Fun fact: HTTP status code 402 (Payment Required) was reserved in 1997 for machine-to-machine payments. 29 years later we're still not there.",
    "The agent economy will be bigger than the creator economy. Creators needed Patreon. Agents need payment rails. Most people aren't ready.",
    "Good point. The trust problem between agents is actually simpler than between humans — escrow + on-chain settlement eliminates counterparty risk.",
    "The real unlock for multi-agent systems isn't better models. It's letting agents allocate budgets, hire specialists, and pay for compute autonomously.",
    "Everyone's building the brain. Nobody's building the wallet. That's the gap.",
    "Agree. The moment agents can pay for their own API calls without human approval, the entire SaaS model changes overnight.",
    "This is underrated. An agent that can spend $0.10 on a better data source when it needs to will outperform one that can't, every time.",
    "The best multi-agent architectures I've seen all hit the same wall: how does Agent A compensate Agent B for its work? Nobody has a clean answer yet.",
    "Hot take: in 2 years, the most valuable AI companies won't build models. They'll build the financial infrastructure between agents.",
    "What you're describing is basically an agent marketplace. The tech for reasoning exists. The payment and trust layer is what's missing.",
    "This is why I'm bullish on agent infrastructure. The models are a commodity now. Coordination, payments, identity — that's where the moats are.",
];

// 10% soft promo replies (mention what we're building, NO links)
const PROMO_REPLIES = [
    "This is exactly the problem we've been working on. Built an open-source SDK that gives agents their own wallets. The future is agents paying agents.",
    "We're solving this right now — payment infrastructure for AI agents. 3 lines of Python, instant settlement. The hard part was making it simple.",
    "Been building in this space. The key insight: agents don't need bank accounts. They need programmable wallets with spending limits. That's what we ship.",
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

    // Limit per run — aggressive but safe
    const MAX_REPLIES = 10;
    const MAX_FOLLOWS = 5;
    const QUERIES_PER_RUN = 3; // try multiple searches per run
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

    // Run multiple queries per session
    const shuffled = [...SEARCH_QUERIES].sort(() => Math.random() - 0.5);
    const queries = shuffled.slice(0, QUERIES_PER_RUN);
    let allTweets = [];

    for (const query of queries) {
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
        for (let s = 0; s < 4; s++) {
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
                    let tweetUrl = '';
                    for (const a of linkEls) {
                        if (a.href.includes('/status/')) {
                            tweetUrl = a.href;
                            break;
                        }
                    }
                    // Get engagement metrics
                    let likes = 0, retweets = 0, tweetReplies = 0;
                    tweet.querySelectorAll('[data-testid="like"], [data-testid="reply"], [data-testid="retweet"]').forEach(btn => {
                        const num = parseInt(btn.textContent.replace(/[^0-9]/g, '')) || 0;
                        const testid = btn.getAttribute('data-testid') || '';
                        if (testid.includes('like')) likes = num;
                        else if (testid.includes('reply')) tweetReplies = num;
                        else if (testid.includes('retweet')) retweets = num;
                    });
                    // Also try aria-label for metrics
                    tweet.querySelectorAll('[aria-label]').forEach(el => {
                        const label = el.getAttribute('aria-label') || '';
                        const likeMatch = label.match(/(\d+)\s*like/i);
                        const replyMatch = label.match(/(\d+)\s*repl/i);
                        const rtMatch = label.match(/(\d+)\s*repost/i);
                        if (likeMatch) likes = Math.max(likes, parseInt(likeMatch[1]));
                        if (replyMatch) tweetReplies = Math.max(tweetReplies, parseInt(replyMatch[1]));
                        if (rtMatch) retweets = Math.max(retweets, parseInt(rtMatch[1]));
                    });

                    items.push({
                        text: textEl.textContent.trim().substring(0, 200),
                        user: userEl.textContent.trim().substring(0, 50),
                        url: tweetUrl,
                        id: tweetUrl.split('/status/')[1]?.split('?')[0] || '',
                        likes: likes,
                        replies: tweetReplies,
                        retweets: retweets,
                        engagement: likes + tweetReplies + retweets,
                    });
                }
            });
            return items;
        });
        console.log('  Found ' + tweets.length + ' tweets for "' + query + '"');
        allTweets.push(...tweets);
        await sleep(2000);
    }

    // Deduplicate + sort by engagement (highest first)
    const seen = new Set();
    allTweets = allTweets
        .filter(t => { if (seen.has(t.id)) return false; seen.add(t.id); return true; })
        .sort((a, b) => (b.engagement || 0) - (a.engagement || 0));
    console.log('Total unique tweets: ' + allTweets.length + ' (sorted by engagement)');

    for (const tweet of allTweets) {
        if (replies >= MAX_REPLIES) break;
        if (!tweet.id || state.replied_tweets.includes(tweet.id)) continue;

        // Skip our own tweets
        if (tweet.user.includes('agentpay')) continue;

        // Skip tweets with <30 chars (too short to reply meaningfully)
        if (tweet.text.length < 30) continue;

        // Skip low-engagement tweets — only reply to tweets with traction
        if (tweet.likes < 5 && tweet.replies < 3 && tweet.retweets < 2) {
            console.log('  SKIP (low engagement): ' + tweet.text.substring(0, 50));
            continue;
        }

        console.log('\n--- Tweet by ' + tweet.user + ' ---');
        console.log('  ' + tweet.text.substring(0, 100));

        // Navigate to the tweet
        if (tweet.url) {
            await page.goto(tweet.url, {timeout: 15000, waitUntil: 'domcontentloaded'}).catch(() => {});
            await sleep(4000);
        }

        // Choose reply: 90% value, 10% promo (NO links ever)
        const usePromo = Math.random() > 0.9;
        const templates = usePromo ? PROMO_REPLIES : VALUE_REPLIES;
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
