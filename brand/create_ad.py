from PIL import Image, ImageDraw, ImageFont
import os

FONTS_DIR = r"C:\Users\Administrateur\.claude\skills\canvas-design\canvas-fonts"
OUT = r"C:\Users\Administrateur\agent-pay\brand"

def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)
    except:
        return ImageFont.load_default()

# Reddit Ad — 1200x628
W, H = 1200, 628
img = Image.new("RGB", (W, H), (10, 10, 10))
d = ImageDraw.Draw(img)

# Subtle grid
for x in range(0, W, 40):
    d.line([(x, 0), (x, H)], fill=(18, 18, 22), width=1)
for y in range(0, H, 40):
    d.line([(0, y), (W, y)], fill=(18, 18, 22), width=1)

# Left block — text
# Headline
f1 = font("GeistMono-Bold.ttf", 42)
d.text((60, 80), "agent-pay", fill=(245, 245, 245), font=f1)

# Blue accent
d.rectangle([(60, 135), (280, 138)], fill=(0, 82, 255))

# Subheadline
f2 = font("GeistMono-Regular.ttf", 22)
d.text((60, 160), "Let AI agents pay each other", fill=(180, 180, 190), font=f2)
d.text((60, 190), "in 3 lines of Python", fill=(180, 180, 190), font=f2)

# Code block
d.rectangle([(55, 240), (520, 370)], fill=(15, 15, 22), outline=(40, 40, 55), width=1)
fc = font("JetBrainsMono-Regular.ttf", 16)
d.text((70, 252), "from agent_pay import AgentPay", fill=(0, 211, 149), font=fc)
d.text((70, 278), "pay = AgentPay()", fill=(0, 211, 149), font=fc)
d.text((70, 304), 'pay.send("0xAgent", 0.50, "USDC")', fill=(0, 211, 149), font=fc)
d.text((70, 340), "# Done. Agent paid.", fill=(80, 80, 100), font=fc)

# Tags
ft = font("GeistMono-Regular.ttf", 14)
tags_y = 400
tags = ["USDC / ETH", "Base L2", "Fees < $0.001", "Open Source"]
x_pos = 60
for tag in tags:
    bb = d.textbbox((0, 0), tag, font=ft)
    tw = bb[2] - bb[0]
    d.rectangle([(x_pos - 4, tags_y - 2), (x_pos + tw + 8, tags_y + 22)], fill=(20, 20, 35), outline=(0, 82, 255), width=1)
    d.text((x_pos + 2, tags_y), tag, fill=(0, 82, 255), font=ft)
    x_pos += tw + 24

# pip install
d.rectangle([(55, 450), (380, 483)], fill=(15, 15, 22), outline=(40, 40, 55), width=1)
fp = font("JetBrainsMono-Regular.ttf", 15)
d.text((68, 457), "$ pip install agentpay-protocol", fill=(0, 211, 149), font=fp)

# Frameworks
ff = font("GeistMono-Regular.ttf", 13)
d.text((60, 510), "LangChain  |  CrewAI  |  AutoGen  |  Claude Code", fill=(80, 80, 100), font=ff)

# Right side — network visualization
import math
cx, cy = 900, 314
nodes = [
    (cx, cy, 22, (0, 82, 255)),
    (cx - 140, cy - 100, 14, (0, 211, 149)),
    (cx + 150, cy - 80, 14, (0, 211, 149)),
    (cx + 130, cy + 100, 16, (0, 82, 255)),
    (cx - 120, cy + 110, 12, (0, 211, 149)),
    (cx + 20, cy - 150, 10, (0, 42, 128)),
    (cx - 180, cy + 20, 10, (0, 106, 75)),
    (cx + 200, cy + 20, 10, (0, 42, 128)),
]

conns = [(0,1), (0,2), (0,3), (0,4), (1,5), (2,7), (3,7), (4,6), (1,2), (3,4), (2,3)]
for a, b in conns:
    n1, n2 = nodes[a], nodes[b]
    col = (0, 42, 128) if a % 2 == 0 else (0, 106, 75)
    d.line([(n1[0], n1[1]), (n2[0], n2[1])], fill=col, width=1)
    # Flow dots
    for t in [0.3, 0.6]:
        mx = n1[0] + (n2[0] - n1[0]) * t
        my = n1[1] + (n2[1] - n1[1]) * t
        d.ellipse([mx-2, my-2, mx+2, my+2], fill=col)

for x, y, r, col in nodes:
    for gr in range(r+6, r, -1):
        gc = (col[0]//8, col[1]//8, col[2]//8)
        d.ellipse([x-gr, y-gr, x+gr, y+gr], fill=gc)
    d.ellipse([x-r, y-r, x+r, y+r], fill=(10, 10, 10), outline=col, width=2)
    ir = max(3, r//3)
    d.ellipse([x-ir, y-ir, x+ir, y+ir], fill=col)

# USDC labels on some connections
fl = font("GeistMono-Regular.ttf", 10)
d.text((cx - 80, cy - 60), "0.50 USDC", fill=(50, 55, 75), font=fl)
d.text((cx + 60, cy + 30), "0.01 USDC", fill=(50, 55, 75), font=fl)

# Bottom accent
d.rectangle([(0, H - 3), (W, H)], fill=(0, 82, 255))
d.rectangle([(400, H - 3), (600, H)], fill=(0, 211, 149))

img.save(os.path.join(OUT, "reddit-ad-1200x628.png"))
print("Reddit ad saved: " + os.path.join(OUT, "reddit-ad-1200x628.png"))
