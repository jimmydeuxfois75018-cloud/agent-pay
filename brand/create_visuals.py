from PIL import Image, ImageDraw, ImageFont
import math
import os

FONTS_DIR = r"C:\Users\Administrateur\.claude\skills\canvas-design\canvas-fonts"
OUT_DIR = r"C:\Users\Administrateur\agent-pay\brand"

DARK = (10, 10, 10)
BLUE = (0, 82, 255)
GREEN = (0, 211, 149)
BLUE_DIM = (0, 42, 128)
GREEN_DIM = (0, 106, 75)
LIGHT = (245, 245, 245)

def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)
    except:
        return ImageFont.load_default()

def create_profile():
    W, H = 400, 400
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    cx, cy = 200, 200

    # Grid
    for x in range(0, W, 20):
        d.line([(x, 0), (x, H)], fill=(15, 15, 20), width=1)
    for y in range(0, H, 20):
        d.line([(0, y), (W, y)], fill=(15, 15, 20), width=1)

    # Outer hex
    outer = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        outer.append((cx + 85 * math.cos(a), cy + 85 * math.sin(a)))
    for i in range(6):
        d.line([outer[i], outer[(i+1)%6]], fill=BLUE, width=3)

    # Inner hex
    inner = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        inner.append((cx + 50 * math.cos(a), cy + 50 * math.sin(a)))
    for i in range(6):
        d.line([inner[i], inner[(i+1)%6]], fill=GREEN, width=2)

    # Connect inner to outer
    for i in range(6):
        d.line([inner[i], outer[i]], fill=BLUE_DIM, width=1)

    # Dots
    for pt in outer:
        d.ellipse([pt[0]-5, pt[1]-5, pt[0]+5, pt[1]+5], fill=BLUE)
    for pt in inner:
        d.ellipse([pt[0]-4, pt[1]-4, pt[0]+4, pt[1]+4], fill=GREEN)

    # Center
    d.ellipse([cx-8, cy-8, cx+8, cy+8], fill=LIGHT)
    d.ellipse([cx-4, cy-4, cx+4, cy+4], fill=DARK)

    # Radiating lines
    for i in range(12):
        a = math.radians(30 * i)
        r1, r2 = 100, 140 + (i%3)*20
        col = BLUE_DIM if i%2==0 else GREEN_DIM
        d.line([(cx+r1*math.cos(a), cy+r1*math.sin(a)), (cx+r2*math.cos(a), cy+r2*math.sin(a))], fill=col, width=1)

    # Satellites
    for sx, sy, col in [(70, 100, GREEN), (340, 120, BLUE), (320, 310, GREEN), (90, 320, BLUE)]:
        d.ellipse([sx-3, sy-3, sx+3, sy+3], fill=col)
        nearest = min(outer, key=lambda p: (p[0]-sx)**2 + (p[1]-sy)**2)
        d.line([(sx, sy), nearest], fill=(col[0]//3, col[1]//3, col[2]//3), width=1)

    # AP monogram
    f = font("GeistMono-Bold.ttf", 28)
    bb = d.textbbox((0,0), "AP", font=f)
    d.text((cx-(bb[2]-bb[0])//2, cy-(bb[3]-bb[1])//2-2), "AP", fill=LIGHT, font=f)

    img.save(os.path.join(OUT_DIR, "profile-400x400.png"))
    print("Profile saved")


def create_banner():
    W, H = 1500, 500
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)

    # Grid
    for x in range(0, W, 30):
        v = 18 if x%90==0 else 14
        d.line([(x,0),(x,H)], fill=(v,v,v+5), width=1)
    for y in range(0, H, 30):
        v = 18 if y%90==0 else 14
        d.line([(0,y),(W,y)], fill=(v,v,v+5), width=1)

    # LEFT: Branding
    ft = font("GeistMono-Bold.ttf", 52)
    d.text((80, 160), "agent-pay", fill=LIGHT, font=ft)
    d.rectangle([(80, 225), (340, 228)], fill=BLUE)

    fs = font("GeistMono-Regular.ttf", 20)
    d.text((80, 245), "The payment protocol for AI agents", fill=(140, 140, 155), font=fs)

    # Terminal box
    fc = font("JetBrainsMono-Regular.ttf", 16)
    d.rectangle([(78, 295), (430, 328)], fill=(18, 18, 25), outline=(60, 60, 70), width=1)
    d.text((90, 300), "$ pip install agentpay-protocol", fill=GREEN, font=fc)

    fm = font("GeistMono-Regular.ttf", 13)
    d.text((80, 360), "USDC / ETH", fill=BLUE, font=fm)
    d.text((200, 360), "Base L2", fill=BLUE, font=fm)
    d.text((300, 360), "< $0.001 fees", fill=GREEN, font=fm)

    fv = font("GeistMono-Regular.ttf", 11)
    d.text((80, 400), "v0.1.0", fill=(60, 60, 70), font=fv)

    # Divider
    for y in range(40, H-40, 4):
        if y%8==0:
            d.point((650, y), fill=(30, 30, 40))

    # RIGHT: Network
    nodes = [
        (850, 250, 18, BLUE), (1020, 140, 14, GREEN), (1050, 340, 14, GREEN),
        (1200, 200, 16, BLUE), (1180, 380, 12, GREEN), (1350, 280, 14, BLUE),
        (1300, 120, 10, GREEN_DIM), (1400, 400, 10, BLUE_DIM),
        (920, 380, 10, BLUE_DIM), (780, 130, 10, GREEN_DIM),
    ]

    conns = [
        (0,1,BLUE,2), (0,2,GREEN,2), (1,3,BLUE_DIM,1), (2,4,GREEN_DIM,1),
        (3,5,BLUE,2), (1,5,GREEN_DIM,1), (3,6,BLUE_DIM,1), (5,7,GREEN_DIM,1),
        (0,8,BLUE_DIM,1), (0,9,GREEN_DIM,1), (4,5,GREEN,1), (2,3,BLUE_DIM,1),
    ]

    for c in conns:
        n1, n2 = nodes[c[0]], nodes[c[1]]
        d.line([(n1[0],n1[1]),(n2[0],n2[1])], fill=c[2], width=c[3])
        if c[3] == 2:
            for t in [0.3, 0.5, 0.7]:
                mx = n1[0]+(n2[0]-n1[0])*t
                my = n1[1]+(n2[1]-n1[1])*t
                d.ellipse([mx-2, my-2, mx+2, my+2], fill=c[2])

    for x, y, r, col in nodes:
        for gr in range(r+8, r, -1):
            gc = (col[0]//6, col[1]//6, col[2]//6)
            d.ellipse([x-gr, y-gr, x+gr, y+gr], fill=gc)
        d.ellipse([x-r, y-r, x+r, y+r], fill=DARK, outline=col, width=2)
        ir = max(3, r//3)
        d.ellipse([x-ir, y-ir, x+ir, y+ir], fill=col)

    fl = font("GeistMono-Regular.ttf", 9)
    d.text((930, 185), "0.50 USDC", fill=(50, 55, 75), font=fl)
    d.text((1100, 260), "1.00 USDC", fill=(40, 60, 50), font=fl)
    d.text((1250, 330), "0.01 USDC", fill=(50, 55, 75), font=fl)

    fw = font("GeistMono-Regular.ttf", 10)
    d.text((1300, 30), "agentpay-protocol", fill=(30, 30, 40), font=fw)

    # Bottom accent
    d.rectangle([(0, H-3), (W, H)], fill=BLUE)
    d.rectangle([(W//3, H-3), (W//3+200, H)], fill=GREEN)

    img.save(os.path.join(OUT_DIR, "banner-1500x500.png"))
    print("Banner saved")


if __name__ == "__main__":
    create_profile()
    create_banner()
    print("Done: " + OUT_DIR)
