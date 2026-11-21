import sys
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None

# Design spec palette (light paper tabloid).
# Override the dark-mode plan: use the spec's RGB palette for determinism.
PAPER = (247, 241, 227)
INK = (20, 33, 61)
ACCENT_RED = (193, 39, 45)
NAVY = (27, 42, 74)
TEAL = (14, 124, 123)
GOLD = (217, 164, 65)
WHITE = (255, 255, 255)

BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _font(size, bold):
    path = BOLD_PATH if bold else REG_PATH
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.load_default()
        except Exception:
            return None


def font(size, bold=False):
    return _font(size, bold)


def wrap_text(draw, text, f, max_width):
    if f is None or not text:
        return [str(text)]
    words = str(text).split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if not lines:
        lines = [str(text)]
    return lines


def leading_for(f):
    if f is not None:
        try:
            a, b = f.getmetrics()
            m = a + b
            if m and m > 0:
                return int(round(m * 1.18))
        except Exception:
            pass
    return 20


def draw_wrapped(draw, xy, lines, f, fill, leading):
    x, y = int(xy[0]), int(xy[1])
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


def chip(draw, x, y, text, bg, f, white_label=True):
    f = f or font(14, True)
    pad_x = 12
    h = 24
    w = int(draw.textlength(text, font=f or font(14, True))) + pad_x * 2
    try:
        rr = 8
    except Exception:
        rr = 8
    draw.rounded_rectangle([x, y, x + w, y + h], radius=rr, fill=bg, outline=None)
    draw.text((x + pad_x, y + (h - 14) // 2), text,
              font=f, fill=(255, 255, 255) if white_label else INK)
    return w, h


def icon(draw, cx, cy, r, kind, color, fill):
    # Simple geometric pictograms only.
    kind = (kind or "dot").lower()
    try:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
        if kind == "conflict":
            # Target ring dot
            draw.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3],
                         fill=fill, outline=color, width=2)
            line_len = r
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                x1 = cx + int(dx * (r + 2))
                y1 = cy + int(dy * (r + 2))
                x2 = cx + int(dx * (r * 2))
                y2 = cy + int(dy * (r * 2))
                draw.line([(x1, y1), (x2, y2)], fill=color, width=4)
        elif kind == "weather":
            # Storm / cyclone spiral simplified as three arcs
            draw.arc([cx - int(r * 0.85), cy - int(r * 0.85),
                      cx + int(r * 0.85), cy + int(r * 0.85)],
                     start=20, end=160, fill=color, width=4)
            draw.arc([cx - int(r * 0.55), cy - int(r * 0.55),
                      cx + int(r * 0.55), cy + int(r * 0.55)],
                     start=200, end=340, fill=color, width=4)
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=color)
        elif kind == "justice":
            # Scales
            draw.line([(cx, cy - r), (cx, cy + r // 2)], fill=color, width=4)
            draw.line([(cx - r, cy - r // 4), (cx + r, cy - r // 4)],
                      fill=color, width=3)
            draw.polygon([(cx - r, cy - r // 4), (cx - r + int(r * 0.6), cy + int(r * 0.3)),
                          (cx - r - int(r * 0.6), cy + int(r * 0.3))], fill=color)
            draw.polygon([(cx + r, cy - r // 4), (cx + r - int(r * 0.6), cy + int(r * 0.3)),
                          (cx + r + int(r * 0.6), cy + int(r * 0.3))], fill=color)
            draw.line([(cx - int(r * 0.35), cy + r // 2), (cx + int(r * 0.35), cy + r // 2)],
                      fill=color, width=4)
        elif kind == "economy":
            # Downward arrow / chart
            draw.polygon([(cx - r, cy + r // 2), (cx - r // 2, cy + r // 2 - int(r * 0.4)),
                          (cx, cy + r // 2), (cx + r // 2, cy - r // 2), (cx + r, cy)],
                         fill=color)
            draw.line([(cx + r, cy), (cx + r, cy + r // 2)], fill=color, width=3)
            draw.line([(cx + r, cy + r // 2), (cx + r - int(r * 0.35), cy)], fill=color, width=3)
        elif kind == "diplomacy":
            # Two interlocking circles + handshake bar
            draw.ellipse([cx - r, cy - int(r * 0.6), cx, cy + int(r * 0.6)],
                         outline=color, width=3)
            draw.ellipse([cx, cy - int(r * 0.6), cx + r, cy + int(r * 0.6)],
                         outline=color, width=3)
            draw.line([(cx - int(r * 0.8), cy + int(r * 0.8)),
                       (cx + int(r * 0.8), cy + int(r * 0.8))], fill=color, width=3)
        elif kind == "security":
            # Shield with key dot
            pts = [(cx, cy - r), (cx + int(r * 0.8), cy - int(r * 0.4)),
                   (cx + int(r * 0.8), cy + int(r * 0.3)), (cx, cy + r),
                   (cx - int(r * 0.8), cy + int(r * 0.3)), (cx - int(r * 0.8), cy - int(r * 0.4))]
            draw.polygon(pts, outline=color, width=3, fill=fill)
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=color)
        else:
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=color)
    except Exception:
        try:
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
        except Exception:
            pass


def rule(draw, x0, y, x1, color, w):
    draw.line([(x0, y), (x1, y)], fill=color, width=w)


def draw_variant1(w, h):
    if Image is None:
        raise SystemExit("PIL not available")
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    ink = INK
    # ----- Masthead ---
    band_h = 120
    d.rectangle([0, 0, w, band_h], fill=NAVY)
    m = 40
    f_mast = font(46, True)
    d.text((m, 30), "THE WORLD IN ONE IMAGE", font=f_mast, fill=WHITE)
    f_date = font(24, True)
    d.text((m, 84), "SATURDAY 21 NOVEMBER 2026", font=f_date, fill=GOLD)
    # right corner tag
    tag = "GLOBAL WIRE"
    f_tag = font(18, True)
    tw = d.textlength(tag, font=f_tag)
    d.text((w - m - tw, 90), tag, font=f_tag, fill=WHITE)
    # thin gold rule under masthead
    rule(d, 0, band_h, w, GOLD, 3)

    # ----- Lead story (story 1) full-width ---
    y = band_h + 16
    lead_h = 170
    d.rectangle([20, y, w - 20, y + lead_h], outline=ACCENT_RED, width=3)
    inner_x = 36
    inner_w = w - 72
    # Kicker chip
    cw, ch = chip(d, inner_x, y + 12, "CONFLICT · NATO AIRSPACE", ACCENT_RED, font(14, True))
    # Left icon of lead
    icon(d, w - 90, y + lead_h // 2, 40, "conflict", ACCENT_RED, PAPER)
    h1 = font(34, True)
    head = "Russian missiles hit Poland; NATO calls it a grave airspace violation"
    head_lines = wrap_text(d, head, h1, inner_w - 110)
    if not head_lines:
        head_lines = [head]
    hy = y + 52
    hy = draw_wrapped(d, (inner_x, hy), head_lines[:2], h1, ink, leading_for(h1))
    s1 = font(17, False)
    summ = ("Warsaw branded the strikes a deliberate provocation; the attack crossed borders "
            "and rattled Article-5 allies as fallout spread across NATO capitals.")
    sl = wrap_text(d, summ, s1, inner_w - 110)
    draw_wrapped(d, (inner_x, hy + 2), sl[:2], s1, ink, leading_for(s1))

    # ----- 2x2 grid: stories 2..5 ---
    gy = y + lead_h + 18
    gap = 14
    grid_w = w - 40
    cell_w = (grid_w - gap) // 2
    cell_h = 132
    items = [
        ("WEATHER", TEAL, "weather", "Cyclone Akvan battering Odisha coast",
         "Landfall near Gopalpur; ~300,000 evacuated, massive rescue underway as the eye weakens."),
        ("JUSTICE", GOLD, "justice", "ICJ: Myanmar committed genocide vs Rohingya",
         "Court found the 2017 crackdown genocidal; rights groups demanded international intervention."),
        ("ECONOMY", ACCENT_RED, "economy", "AI unwind drives S&P 500, Dow into correction",
         "US indexes fell ~3.7% as a sharp chip/AI sell-off pushed both into correction territory."),
        ("DIPLOMACY", NAVY, "diplomacy", "Trump-Xi-Putin trilateral ends in Shenzhen",
         "Marking APEC, the three met with a joint peace declaration but few concrete deliverables."),
    ]
    for i, (cat, col, icon_kind, head, summ) in enumerate(items):
        r = i // 2
        c = i % 2
        x0 = 20 + c * (cell_w + gap)
        y0 = gy + r * (cell_h + gap)
        # tile background
        d.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=PAPER, outline=col, width=2)
        # left accent bar
        d.rectangle([x0, y0, x0 + 6, y0 + cell_h], fill=col)
        ix = x0 + 14
        iw = cell_w - 28
        cw, ch = chip(d, ix, y0 + 10, cat, col, font(12, True))
        icon(d, x0 + cell_w - 28, y0 + 30, 16, icon_kind, col, PAPER)
        th = font(19, True)
        tl = wrap_text(d, head, th, iw - 40)
        ty = draw_wrapped(d, (ix, y0 + 36), tl[:2], th, ink, leading_for(th))
        ts = font(14, False)
        sl = wrap_text(d, summ, ts, iw)
        draw_wrapped(d, (ix, ty + 2), sl[:3], ts, ink, leading_for(ts))

    # ----- Bottom: security story (story 6) + ticker (story 7) ---
    sy = gy + 2 * cell_h + 2 * gap + 12
    sec_h = 110
    d.rounded_rectangle([16, sy, w - 16, sy + sec_h], radius=12,
                        fill=(245, 240, 224), outline=NAVY, width=2)
    sx = 30
    sw = w - 60
    cw, ch = chip(d, sx, sy + 12, "SECURITY · VENDOR HACK", NAVY, font(13, True))
    icon(d, w - 60, sy + sec_h // 2, 22, "security", NAVY, (245, 240, 224))
    sh = font(20, True)
    stl = wrap_text(d, "JPMorgan, Visa, Mastercard hit in vendor cyberattacks", sh, sw - 60)
    sty = draw_wrapped(d, (sx, sy + 44), stl[:2], sh, ink, leading_for(sh))
    ssum = ("All three said their core payment networks remain unaffected; firms said they have "
            "noted attacks on third-party vendors and are coordinating response.")
    ssm_l = wrap_text(d, ssum, s1, sw - 60)
    draw_wrapped(d, (sx, sty + 2), ssm_l[:2], s1, ink, leading_for(s1))

    # Ticker strip (story 7): COP31 + UK drones + EU aid + NSE
    tk = font(15, True)
    tk_y = sy + sec_h + 12
    tk_h = 38
    d.rectangle([0, tk_y, w, tk_y + tk_h], fill=NAVY)
    items7 = [
        ("COP31 FINAL STAGE", TEAL),
        ("UK PLEDGES 1,000 DRONES £260M", GOLD),
        ("EU ADOPTS €1BN AID FOR UKRAINE", ACCENT_RED),
        ("NSE NOW WORLD'S 5TH-LARGEST EXCHANGE", PAPER),
    ]
    # Build a single flowing line by measuring widths and dropping items if too long
    max_x = w - 12
    x = 12
    for label, color in items7:
        wl = d.textlength(label, font=tk)
        if x + wl > max_x:
            break
        d.text((x, tk_y + (tk_h - 16) // 2), label, font=tk, fill=color)
        x += wl + 16
        if label != items7[-1][0]:
            # small diamond divider
            d.polygon([(x, tk_y + tk_h // 2 - 3), (x + 6, tk_y + tk_h // 2),
                       (x, tk_y + tk_h // 2 + 3), (x - 6, tk_y + tk_h // 2)],
                      fill=PAPER)
            x += 16

    # ----- Footer ---
    fy = h - 28
    ffoot = font(12, True)
    ftxt = "All stories first reported 21 November 2026"
    ftw = d.textlength(ftxt, font=ffoot)
    d.text(((w - ftw) // 2, fy - 8), ftxt, font=ffoot, fill=INK)
    # tiny masthead repeat
    d.text((16, fy - 8), "TWIO| 1", font=ffoot, fill=ACCENT_RED)
    d.rectangle([w - 56, fy - 8, w - 16, fy + 4], outline=GOLD, width=2)
    return img


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "1"
    fn = globals().get("draw_variant" + str(variant))
    if fn is None:
        raise SystemExit("no variant %s" % variant)
    img = fn(1024, 1024)
    name = "entry_v%s.png" % variant
    out = os.path.join(os.getcwd(), name)
    img.save(out, "PNG")
    size = os.path.getsize(out)
    print("wrote entry_v%s.png 1024x1024 bytes %d" % (variant, size))


def draw_variant2(w, h):
    if Image is None:
        raise SystemExit("PIL not available")
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    ink = INK

    # ----- Masthead / Date Banner ---------
    band_h = 110
    d.rectangle([0, 0, w, band_h], fill=NAVY)
    m = 36
    f_mast = font(44, True)
    d.text((m, 24), "THE WORLD IN ONE IMAGE", font=f_mast, fill=WHITE)
    f_date = font(28, True)
    d.text((m, 74), "SATURDAY 21 NOVEMBER 2026", font=f_date, fill=GOLD)
    # Right tag
    tag = "SIX-PANEL BRIEF"
    f_tag = font(16, True)
    tw = d.textlength(tag, font=f_tag)
    d.text((w - m - tw, 82), tag, font=f_tag, fill=WHITE)
    rule(d, 0, band_h, w, GOLD, 3)

    # ----- 2x3 Grid ---------
    gx = 24
    gy = band_h + 20
    gap = 16
    grid_w = w - 2 * gx
    cell_w = (grid_w - 2 * gap) // 3
    grid_h = h - gy - 20
    cell_h = (grid_h - 2 * gap) // 3

    items = [
        ("CONFLICT", ACCENT_RED, "conflict",
         "Russian missiles hit Poland; NATO calls it grave violation",
         "Warsaw called strike a deliberate provocation; fallout spread across NATO capitals."),
        ("WEATHER", TEAL, "weather",
         "Cyclone Akvan crosses Odisha coast",
         "~300,000 evacuated, massive rescue under way as eye weakens near Gopalpur."),
        ("JUSTICE", GOLD, "justice",
         "ICJ: Myanmar committed genocide vs Rohingya",
         "Court found 2017 crackdown genocidal; rights groups demanded intervention."),
        ("ECONOMY", ACCENT_RED, "economy",
         "AI unwind drives S\u0026P 500, Dow into correction",
         "Indexes fell ~3.7% as sharp chip / AI sell-off pushed both into correction."),
        ("DIPLOMACY", NAVY, "diplomacy",
         "Trump-Xi-Putin trilateral ends in Shenzhen",
         "First-ever three-way meeting (APEC) wrapped with few concrete deliverables."),
        ("SECURITY", NAVY, "security",
         "JPMorgan, Visa, Mastercard hit in vendor cyberattacks",
         "Core payment networks unaffected; firms coordinating response to third-party hit."),
    ]

    for i, (cat, col, icon_kind, head, summ) in enumerate(items):
        r = i // 3
        c = i % 3
        x0 = gx + c * (cell_w + gap)
        y0 = gy + r * (cell_h + gap)

        # Panel box
        d.rounded_rectangle([x0, y0, x0 + cell_w, y0 + cell_h], radius=10,
                            fill=WHITE, outline=col, width=2)
        # Top accent bar
        d.rectangle([x0, y0, x0 + cell_w, y0 + 6], fill=col)

        ix = x0 + 14
        iw = cell_w - 28

        # Header chip
        cw_, ch_ = chip(d, ix, y0 + 16, cat, col, font(12, True))

        # Icon top-right
        icon(d, x0 + cell_w - 34, y0 + 34, 13, icon_kind, col, WHITE)

        # Headline (up to 2 lines)
        th = font(17, True)
        tl = wrap_text(d, head, th, iw)
        ty = draw_wrapped(d, (ix, y0 + 54), tl[:2], th, ink, leading_for(th))

        # Summary (one or two short lines)
        ts = font(14, False)
        sl = wrap_text(d, summ, ts, iw)
        draw_wrapped(d, (ix, ty + 6), sl[:3], ts, ink, leading_for(ts))

    # Footer
    fy = h - 24
    ffoot = font(12, True)
    ftxt = "All stories first reported 21 November 2026"
    ftw = d.textlength(ftxt, font=ffoot)
    d.text(((w - ftw) // 2, fy - 8), ftxt, font=ffoot, fill=INK)
    d.text((16, fy - 8), "TWIO| 2", font=ffoot, fill=ACCENT_RED)
    return img


def draw_variant3(w, h):
    if Image is None:
        raise SystemExit("PIL not available")
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    ink = INK

    # ----- Masthead / Date Line ---------
    band_h = 90
    d.rectangle([0, 0, w, band_h], fill=NAVY)
    m = 36
    f_mast = font(38, True)
    d.text((m, 18), "THE WORLD IN ONE IMAGE", font=f_mast, fill=WHITE)
    f_date = font(24, True)
    d.text((m, 64), "SATURDAY 21 NOVEMBER 2026", font=f_date, fill=GOLD)
    rule(d, 0, band_h, w, GOLD, 3)

    # ----- Huge Lead Headline (Story 1) ---------
    y = band_h + 24
    lead_h = 150
    ix = 40
    iw = w - 80
    d.rectangle([ix, y, ix + iw, y + lead_h], outline=ACCENT_RED, width=3)
    cw_, ch_ = chip(d, ix + 16, y + 14, "CONFLICT \u00b7 NATO AIRSPACE", ACCENT_RED, font(15, True))
    icon(d, w - 84, y + lead_h // 2, 44, "conflict", ACCENT_RED, PAPER)
    h1 = font(42, True)
    head = "Russian missiles hit Poland"
    head_lines = wrap_text(d, head, h1, iw - 120)
    if not head_lines:
        head_lines = [head]
    hy = draw_wrapped(d, (ix + 16, y + 58), head_lines[:1], h1, ink, leading_for(h1))
    s1 = font(20, False)
    sub = "Poland: deliberate provocation \u2014 NATO: grave violation of its airspace"
    sl = wrap_text(d, sub, s1, iw - 120)
    draw_wrapped(d, (ix + 16, hy + 6), sl[:2], s1, ink, leading_for(s1))

    # Red rule under lead
    ry = y + lead_h + 12
    rule(d, 20, ry, w - 20, ACCENT_RED, 5)

    # ----- 5 Brief Rows ---------
    by = ry + 22
    row_h = 110
    gap = 8
    items = [
        ("WEATHER", TEAL, "weather",
         "Cyclone Akvan crosses Odisha coast",
         "~300,000 evacuated; massive rescue under way near Gopalpur."),
        ("JUSTICE", GOLD, "justice",
         "ICJ: Myanmar committed genocide vs Rohingya",
         "Ruling covers 2017 crackdown; rights groups call for international action."),
        ("ECONOMY", ACCENT_RED, "economy",
         "AI unwind drives S\u0026P 500, Dow into correction",
         "Indexes down ~3.7% as chip / AI sell-off pushed both into correction."),
        ("DIPLOMACY", NAVY, "diplomacy",
         "Trump-Xi-Putin trilateral ends in Shenzhen",
         "APEC summit wrapped with joint peace declaration but few concrete results."),
        ("SECURITY", NAVY, "security",
         "JPMorgan, Visa, Mastercard hit in vendor cyberattacks",
         "Core payment networks unaffected; firms coordinating on third-party vendor hit."),
    ]
    for i, (cat, col, icon_kind, head, summ) in enumerate(items):
        y0 = by + i * (row_h + gap)
        d.rounded_rectangle([24, y0, w - 24, y0 + row_h], radius=10,
                            fill=WHITE, outline=col, width=2)
        d.rectangle([24, y0, 30, y0 + row_h], fill=col)

        rx = 44
        rw = w - 24 - 44 - 90
        cw_, ch_ = chip(d, rx, y0 + 14, cat, col, font(13, True))
        icon(d, w - 70, y0 + row_h // 2, 22, icon_kind, col, WHITE)

        th = font(22, True)
        tl = wrap_text(d, head, th, rw)
        ty = draw_wrapped(d, (rx, y0 + 50), tl[:2], th, ink, leading_for(th))

        ts = font(16, False)
        sl = wrap_text(d, summ, ts, rw)
        draw_wrapped(d, (rx, ty + 8), sl[:2], ts, ink, leading_for(ts))

    # ----- Bottom Ticker (Story 7) ---------
    bty = by + 5 * (row_h + gap) + 8
    tk_h = 60
    d.rounded_rectangle([16, bty, w - 16, bty + tk_h], radius=10,
                        fill=(245, 240, 224), outline=TEAL, width=2)
    d.text((32, bty + 8), "ALSO TODAY \u25b6", font=font(12, True), fill=TEAL)
    tk = font(16, True)
    tks = [
        ("COP31 FINAL STAGE: FOSSIL FUELS & CLIMATE FINANCE", GOLD),
    ]
    ty = bty + 26
    for label, color in tks:
        # measure; if too wide truncate
        while d.textlength(label, font=tk) > w - 80 and len(label) > 10:
            label = label[:-1]
        d.text((32, ty), label, font=tk, fill=color)
        ty += 26

    # Footer
    fy = h - 22
    ffoot = font(12, True)
    ftxt = "All stories first reported 21 November 2026"
    ftw = d.textlength(ftxt, font=ffoot)
    d.text(((w - ftw) // 2, fy - 8), ftxt, font=ffoot, fill=INK)
    d.text((16, fy - 8), "TWIO| 3", font=ffoot, fill=ACCENT_RED)
    return img

if __name__ == "__main__":
    main()
