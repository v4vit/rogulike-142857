#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""像素贴图预览工具: 读取 rogue_rpg.py 中的贴图数据, 用 PIL 渲染成 PNG 供检查.

用法:
  python preview_pixels.py [键名...] [--all] [--scale 16] [--bg #2a2a3e]
不传参数时显示所有可用贴图键.
"""
import sys
import os
import argparse

from PIL import Image

import rogue_rpg as R

PAD = 2
PX = 8  # 每像素放大倍数


def render_art(art, scale=PX, bg=R.COLOR_PANEL):
    rows = list(art or [])
    if not rows:
        return None
    ncols = max(len(r) for r in rows)
    nrows = len(rows)
    img = Image.new("RGB", (ncols * scale + PAD * 2, nrows * scale + PAD * 2), bg)
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            col = R.PIXEL_COLORS.get(ch)
            if col is None:
                continue
            rgb = tuple(int(col[i:i+2], 16) for i in (1, 3, 5))
            for dy in range(scale):
                for dx in range(scale):
                    px[PAD + x * scale + dx, PAD + y * scale + dy] = rgb
    return img


def all_keys():
    keys = []
    for w in R.WEAPON_LIB.values():
        if "art" in w:
            keys.append(("武器:" + w["name"], w["art"]))
    for t in R.TRINKET_LIB.values():
        if "art" in t:
            keys.append(("饰品:" + t["name"], t["art"]))
    for name, art in R.MONSTER_ART.items():
        keys.append(("怪物:" + name, art))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--scale", type=int, default=PX)
    ap.add_argument("--out", default="_preview")
    args = ap.parse_args()

    keys = all_keys()
    if args.all:
        chosen = keys
    else:
        chosen = [k for k in keys if any(n in k[0] for n in args.names)]
    if not chosen:
        print("未找到匹配项。可用键(部分):")
        for k in keys[:60]:
            print("  ", k[0])
        return

    os.makedirs(args.out, exist_ok=True)
    # 拼成一张网格图
    per_row = 8
    cell = 16 * args.scale + PAD * 2
    label_h = 16
    cols = min(per_row, len(chosen))
    rows = (len(chosen) + per_row - 1) // per_row
    sheet = Image.new("RGB", (cols * cell, rows * (cell + label_h)), R.COLOR_PANEL)
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (name, art) in enumerate(chosen):
        img = render_art(art, args.scale, R.COLOR_PANEL)
        if img is None:
            continue
        cx = i % per_row
        cy = i // per_row
        sheet.paste(img, (cx * cell, cy * (cell + label_h)))
        d.text((cx * cell + 2, cy * (cell + label_h) + cell - 6), name,
               fill=(255, 255, 255))
    outp = os.path.join(args.out, "sheet.png")
    sheet.save(outp)
    print("已生成", outp, "共", len(chosen), "张贴图")


if __name__ == "__main__":
    main()
