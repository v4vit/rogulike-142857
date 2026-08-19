# -*- coding: utf-8 -*-
"""样板贴图设计+校验脚本: 设计好贴图后校验尺寸(16x16)和色板合法性."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import rogue_rpg as R

# 用 "." 表示透明(不绘制). 每行必须正好 16 字符.
DESIGNS = {
    # ---------------- 史莱姆 (Minecraft 绿史莱姆, 高光+渐变+暗部) ----------------
    "slime": [
        "................",
        "................",
        "....KKKKKKKK....",
        "..KKjGGGGGGKK...",
        ".KjGGGGGGGGGGK..",
        ".KjGGWWGGGGGGGK.",
        ".KjGGWWGGGGGGGK.",
        ".KjGGWWGGGGGGGK.",
        ".KGjGGGGGGGGGGK.",
        ".KGjjGGGGGGGGGK.",
        ".KGjjggggggggGK.",
        "..KGgggggggGGK..",
        "..KKggggGGGGK...",
        "...KKKKKKKKKK...",
        "....KGGGGGGGK...",
        "................",
    ],
    # ---------------- 骷髅 (骨白+亮部高光+暗部+黑眼窝+牙+肋骨, 全身骨架) ----------------
    "skeleton": [
        "................",
        "................",
        "....########....",
        "...##88777788##.",
        "..#8877777788#..",
        ".#8877KK88KK788#",
        ".#8877KK88KK788#",
        ".#8877777777788#",
        "..#8888888888#..",
        "..#8889K9K888#..",
        "....########....",
        "...##888888##...",
        "..#8888888888#..",
        "..#88K8888K88#..",
        "..##88888888##..",
        "................",
    ],
    # ---------------- 哥布林 (绿皮小个子, 大尖耳, 红眼, 破衣) ----------------
    "goblin": [
        "................",
        "....K.....K.....",
        "...KKKKKKKKK....",
        "..KKjGGGGGGGK...",
        "..KjGGGGGGGGGK..",
        ".KjGGGRRRRGjGGK.",
        ".KjGGGRRRRGjGGK.",
        ".KjGGGGGGGGGGGK.",
        ".KKGGGGGGGGGGKK.",
        "..KJGGGGGGGGJK..",
        "..KJGGGGGGGGJK..",
        "...KnnnnnnnnK...",
        "..KnnnnnnnnnnK..",
        "..KKnnnnnnnnKK..",
        "................",
        "................",
    ],
    # ---------------- 僵尸 (绿腐皮, 暗部, 血眼, 破衫) ----------------
    "zombie": [
        "................",
        "................",
        "....KKKKKKKK....",
        "...KGGGGGGGGK...",
        "..KGGGGGGGGGGK..",
        ".KGGGGRRRRGGGGK.",
        ".KGGGGRRRRGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGGGggggggggGK.",
        ".KggggggggggggK.",
        "..KGGGGGGGGGGK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    # ---------------- 战斧 (铁斧头高光+暗部+木柄, Minecraft 风格) ----------------
    "battle_axe": [
        "................",
        "....KKKK........",
        "...KSSSSKK......",
        "...KSSSSSKK.....",
        "..KSSSSSSSKK....",
        "..KSSSSSSSSK....",
        "..KSSSSSSSSK....",
        "...KSSSSSSSK....",
        "....KSSSSSK.....",
        ".....KSSSK......",
        "......KSK.......",
        ".....KNNK.......",
        "....KNNNNK......",
        "...KNNNNNNK.....",
        "...KKNNNNKK.....",
        "....KKKKKK......",
    ],
}

def check(name, art, width=16):
    errs = []
    for i, row in enumerate(art):
        if len(row) != width:
            errs.append(f"  行{i}: 长度{len(row)} != {width}: '{row}'")
    known = set(R.PIXEL_COLORS.keys()) | {'.', ' '}
    unknown = set()
    for row in art:
        unknown |= set(row) - known
    if unknown:
        errs.append(f"  未知字符(不在色板): {sorted(unknown)}")
    if errs:
        print(f"[{name}] 有问题:")
        for e in errs: print(e)
        return False
    print(f"[{name}] OK ({len(art)}行x{width}列)")
    return True


if __name__ == "__main__":
    ok = True
    for name, art in DESIGNS.items():
        ok &= check(name, art)
    print("全部通过" if ok else "有错误")
