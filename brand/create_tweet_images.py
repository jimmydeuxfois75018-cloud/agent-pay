from PIL import Image, ImageDraw, ImageFont
import os

FONTS = r"C:\Users\Administrateur\.claude\skills\canvas-design\canvas-fonts"
OUT = r"C:\Users\Administrateur\agent-pay\brand\tweets"
os.makedirs(OUT, exist_ok=True)

DARK = (10, 10, 10)
BLUE = (0, 82, 255)
GREEN = (0, 211, 149)
LIGHT = (245, 245, 245)
GRAY = (120, 120, 135)
DARK_CARD = (18, 18, 25)

def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), size)
    except:
        return ImageFont.load_default()

def make_card(filename, lines, highlight_line=None, accent=BLUE):
    """Create a tweet card 1200x675 (Twitter optimal)"""
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)

    # Subtle grid
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=(14, 14, 18), width=1)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=(14, 14, 18), width=1)

    # agent-pay branding top-left
    fb = font("GeistMono-Bold.ttf", 18)
    d.text((50, 30), "agent-pay", fill=BLUE, font=fb)
    d.rectangle([(50, 55), (160, 57)], fill=BLUE)

    # Main text
    y = 120
    for i, line in enumerate(lines):
        if line.startswith("```"):
            continue
        elif line.startswith("CODE:"):
            # Code block
            code = line[5:]
            fc = font("JetBrainsMono-Regular.ttf", 22)
            # Background
            bb = d.textbbox((0, 0), code, font=fc)
            tw = bb[2] - bb[0]
            d.rectangle([(45, y - 5), (max(tw + 65, 600), y + 35)], fill=DARK_CARD, outline=(40, 40, 55), width=1)
            d.text((55, y), code, fill=GREEN, font=fc)
            y += 50
        elif line.startswith("BIG:"):
            # Big text
            text = line[4:]
            fl = font("GeistMono-Bold.ttf", 38)
            color = accent if i == highlight_line else LIGHT
            d.text((50, y), text, fill=color, font=fl)
            y += 55
        elif line.startswith("STAT:"):
            # Stat number
            text = line[5:]
            fl = font("GeistMono-Bold.ttf", 72)
            d.text((50, y), text, fill=GREEN, font=fl)
            y += 95
        elif line == "":
            y += 20
        else:
            fl = font("GeistMono-Regular.ttf", 24)
            color = LIGHT if i != highlight_line else accent
            d.text((50, y), line, fill=color, font=fl)
            y += 38

    # Bottom accent
    d.rectangle([(0, H - 3), (W, H)], fill=accent)
    d.rectangle([(400, H - 3), (600, H)], fill=GREEN if accent == BLUE else BLUE)

    # Bottom right: pip install
    fs = font("GeistMono-Regular.ttf", 14)
    d.text((W - 300, H - 30), "pip install agentpay-protocol", fill=(60, 60, 75), font=fs)

    img.save(os.path.join(OUT, filename))
    print(f"Saved: {filename}")


# === 7 IMAGES ===

# 1. The $30T stat
make_card("tweet_01_30t.png", [
    "BIG:2030",
    "",
    "AI agents will handle",
    "STAT:$30 Trillion",
    "in transactions.",
    "",
    "2026: There's still no standard",
    "way for them to pay each other.",
    "",
    "BIG:We're fixing that.",
])

# 2. The paywall story
make_card("tweet_02_paywall.png", [
    "BIG:A research agent finds a paper",
    "BIG:behind a paywall.",
    "",
    "It pays $0.02 to access it.",
    "No human needed.",
    "",
    'CODE:pay.send("0xJournal", 0.02, "USDC")',
    "",
    "Settlement: 1.2 seconds.",
    "This is the future we're building.",
], accent=GREEN)

# 3. The broken system
make_card("tweet_03_broken.png", [
    "OpenAI charges per token.",
    "Anthropic charges per token.",
    "Google charges per token.",
    "",
    "BIG:But your agent can't pay",
    "BIG:any of them without YOU",
    "BIG:clicking approve.",
    "",
    "That's broken.",
])

# 4. The cost
make_card("tweet_04_cost.png", [
    "Cost of one agent-to-agent",
    "payment on Base L2:",
    "",
    "STAT:$0.0003",
    "",
    "That's 3,333 transactions for $1.",
    "",
    "BIG:Micropayments are finally real.",
], accent=GREEN)

# 5. The Stripe comparison
make_card("tweet_05_stripe.png", [
    "BIG:Web2",
    "Stripe lets humans pay on websites.",
    "",
    "BIG:Web3",
    "agent-pay lets machines pay each other.",
    "",
    "Same simplicity. Different era.",
    "",
    'CODE:pay.send("0xAgent", 0.50, "USDC")',
])

# 6. Open source
make_card("tweet_06_opensource.png", [
    "BIG:We just open-sourced everything:",
    "",
    "  Python SDK",
    "  MCP server for Claude",
    "  REST API",
    "  LangChain + CrewAI + AutoGen",
    "  Live demo agent",
    "",
    "BIG:Free. MIT license.",
    "BIG:Build whatever you want.",
], accent=GREEN)

# 7. The competitor
make_card("tweet_07_competitor.png", [
    "Your competitor's AI agent",
    "just hired 3 specialist agents,",
    "paid them in USDC,",
    "and delivered the report.",
    "",
    "BIG:Your agent is still waiting",
    "BIG:for you to approve",
    "BIG:a $0.10 transaction.",
])

print("\nAll 7 tweet images created in " + OUT)
