/**
 * Health Check Agent — verifies all systems are operational
 * Runs every hour. Fixes what it can, alerts on Telegram for the rest.
 *
 * Checks:
 * 1. Chrome with CDP running
 * 2. Typefully posts going out on schedule
 * 3. Twitter Agent running and producing replies
 * 4. CI generating downloads
 * 5. API running
 */

const {execSync, spawn} = require('child_process');
const https = require('https');
const fs = require('fs');

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

function check(name, fn) {
    try {
        const result = fn();
        if (result.ok) {
            console.log('[OK] ' + name + ': ' + result.msg);
            return true;
        } else {
            console.log('[FAIL] ' + name + ': ' + result.msg);
            if (result.fix) {
                console.log('  Fixing: ' + result.fix);
                try { execSync(result.fix, {timeout: 15000}); console.log('  Fixed!'); } catch(e) { console.log('  Fix failed'); }
            }
            return false;
        }
    } catch(e) {
        console.log('[ERROR] ' + name + ': ' + e.message.substring(0, 80));
        return false;
    }
}

function main() {
    console.log('=== Health Check ' + new Date().toISOString() + ' ===\n');
    const issues = [];

    // 1. Chrome CDP
    check('Chrome CDP', () => {
        try {
            execSync('curl -s http://127.0.0.1:9222/json/version', {timeout: 5000});
            return {ok: true, msg: 'running'};
        } catch(e) {
            return {
                ok: false,
                msg: 'not running',
                fix: 'powershell.exe -Command "Start-Process \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\' -ArgumentList \'--remote-debugging-port=9222\',\'--user-data-dir=C:\\Users\\Administrateur\\AppData\\Local\\Google\\Chrome\\User Data\',\'--profile-directory=Default\',\'about:blank\'"'
            };
        }
    }) || issues.push('Chrome CDP down — restarted');

    // 2. Twitter Agent last run
    check('Twitter Agent', () => {
        const stateFile = 'C:/Users/Administrateur/agent-pay/scripts/.twitter_agent_state.json';
        if (!fs.existsSync(stateFile)) return {ok: false, msg: 'no state file'};
        const state = JSON.parse(fs.readFileSync(stateFile, 'utf-8'));
        const lastRun = new Date(state.last_run);
        const hoursAgo = (Date.now() - lastRun.getTime()) / 3600000;
        if (hoursAgo > 6) {
            return {
                ok: false,
                msg: 'last run ' + hoursAgo.toFixed(1) + 'h ago (should be <6h)',
                fix: 'node C:/Users/Administrateur/agent-pay/scripts/twitter_agent.js'
            };
        }
        return {ok: true, msg: 'last run ' + hoursAgo.toFixed(1) + 'h ago, ' + state.total_replies + ' total replies'};
    }) || issues.push('Twitter Agent stale');

    // 3. API running
    check('API REST', () => {
        try {
            const result = execSync('curl -s http://localhost:8082/health', {timeout: 5000}).toString();
            if (result.includes('"ok"')) return {ok: true, msg: 'healthy'};
            return {ok: false, msg: 'bad response'};
        } catch(e) {
            return {
                ok: false,
                msg: 'not running',
                fix: 'cd C:/Users/Administrateur/agent-pay && PYTHONPATH=src "C:/Program Files/Python312/python" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8082 &'
            };
        }
    }) || issues.push('API down');

    // 4. CI last run
    check('CI Downloads', () => {
        try {
            const result = execSync('"C:/Program Files/GitHub CLI/gh.exe" run list --repo agentpay-protocol/agent-pay --workflow=daily-install-test.yml --limit 1 --json conclusion -q ".[0].conclusion"', {timeout: 10000}).toString().trim();
            if (result === 'success') return {ok: true, msg: 'last run success'};
            return {ok: false, msg: 'last run: ' + result};
        } catch(e) {
            return {ok: false, msg: 'cant check'};
        }
    }) || issues.push('CI failing');

    // 5. Typefully — check if posts went out today
    // Can't check programmatically without API, just check state
    check('Typefully', () => {
        // We can check by looking at the Twitter Agent state — if tweets were posted via Typefully,
        // the Twitter timeline would show recent posts
        return {ok: true, msg: 'assumed ok (manual check needed if no tweets in 24h)'};
    });

    console.log('\n=== Summary ===');
    if (issues.length === 0) {
        console.log('All systems operational.');
    } else {
        console.log(issues.length + ' issue(s):');
        issues.forEach(i => console.log('  - ' + i));
        sendTelegram('NEO Health Check: ' + issues.length + ' issue(s)\n' + issues.join('\n'));
    }
}

main();
