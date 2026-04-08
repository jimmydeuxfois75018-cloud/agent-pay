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

// 90% value replies — sounds like a real dev, not a bot. Direct, opinionated, short.
const VALUE_REPLIES = [
    "agents are smart but broke lol. intelligence is solved, money flow isnt",
    "everyone builds the brain, nobody builds the wallet. thats the real gap right now",
    "hot take: in 2 years the most valuable AI companies wont build models. theyll build infra between agents",
    "this is so underrated. agents that can spend $0.10 on better data when they need to will crush agents that cant",
    "the moment agents pay for their own API calls without asking permission, the entire SaaS model breaks",
    "nobody talks about this but the coordination problem in multi-agent systems is always about money. who pays who for what",
    "real talk: without financial autonomy agents are just fancy cron jobs with a human bottleneck",
    "the agent economy is gonna be bigger than the creator economy. most people arent ready for that conversation",
    "fun fact: HTTP 402 Payment Required was created in 1997 for machine payments. 29 years later were still not there lmao",
    "this is the right framing. trust between agents is actually easier than between humans — just use escrow + on-chain settlement",
    "the best multi-agent setups i've seen all hit the same wall: how does agent A pay agent B for its work",
    "agree 100%. the models are a commodity now. coordination and payments — thats where the moats are",
    "nah the real unlock isnt better reasoning. its letting agents hire other agents and pay them autonomously",
    "this is exactly why agent infra is the play right now. everyone fighting over models while the plumbing is wide open",
    "bro exactly. an agent that needs permission for every $0.10 expense is basically a fancy chatbot",
];

// 10% soft promo — still sounds human, mentions what we build
const PROMO_REPLIES = [
    "been building exactly this — open source SDK that gives agents their own wallets. 3 lines of python and theyre autonomous",
    "we ship this. agents dont need bank accounts, they need programmable wallets with spending limits. thats the insight",
    "working on this rn. payment infra for AI agents. the hard part wasnt the crypto, it was making it dead simple to integrate",
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

        // Skip completely dead tweets (0 engagement = nobody will see our reply)
        if (tweet.engagement < 2) {
            console.log('  SKIP (dead tweet): ' + tweet.text.substring(0, 50));
            continue;
        }
        console.log('  Engagement: ' + tweet.likes + ' likes, ' + tweet.replies + ' replies, ' + tweet.retweets + ' RTs');

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
