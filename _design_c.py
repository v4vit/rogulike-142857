# -*- coding: utf-8 -*-
"""怪物像素贴图设计 (C批): 每个贴图 16行 x 16列, '.' 表示透明."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 色板键(与 rogue_rpg.PIXEL_COLORS 一致) + '.'(透明)
PALETTE = set("K#D0L7WS$&89RrAxXw4O%2YF!5GigjVh3CcTk~IBbUuPpQv@Mm;NnHJ6EeZ1.")

DESIGNS = {
    # ---------------- 深渊巨蟒 (盘绕蛇身+鳞片花纹, 三角头, 红眼, 吐芯) ----------------
    "abyss_wyrm": [
        "................",
        ".....KKKKKK.....",
        "....KjGGGGjK....",
        "....KGRRGGjK....",
        "....KGRRGGgK....",
        "....KKggGGKK....",
        ".....KxKxK......",
        ".....KggggK.....",
        "....KggggggK....",
        "...KjggggggjK...",
        "..KjggggggggjK..",
        "..KggggggggggK..",
        ".KggggCCCCggggK.",
        ".KgggcCCCCcgggK.",
        ".KggggCCCCggggK.",
        "..KKKKKKKKKKKK..",
    ],
    # ---------------- 折磨者 (暗红恶魔, 骨角, 银链, 绿幽光眼, 爪) ----------------
    "tormentor": [
        "................",
        "...8........8...",
        "...8K......K8...",
        "....KK....KK....",
        "..KKRRKKKKRRKK..",
        ".KRXRRKKKKRRXRK.",
        ".KRXRRKKKKRRXRK.",
        ".KRRjjRKKRjjRRK.",
        ".KKRRRKKKKRRRKK.",
        "..KXRRRRRRRRXK..",
        "..KRRwRRRRwRRK..",
        ".KRwwRRRRRRwwRK.",
        ".KS0wRRRRRRw0SK.",
        ".KSSwRRRRRRwSSK.",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    # ---------------- 地狱霸主 (巨型暗红霸主, 双大角, 金冠, 燃烧双眼) ----------------
    "nether_overlord": [
        "................",
        "..88........88..",
        "..8K888888888K..",
        "..KKFKKKKKKFKK..",
        ".KKKFKKKKKKFKKK.",
        "..KKKKKKKKKKKK..",
        "..KXRRKKKKRRXK..",
        ".KXR4RRKKRR4RXK.",
        ".KXR4RRKKRR4RXK.",
        ".KXRRRRRRRRRRXK.",
        "..KXRRRRRRRRXK..",
        "..KRRwwRRwwRRK..",
        ".KRwwRRRRRRwwRK.",
        ".KRwwRRRRRRwwRK.",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    # ---------------- 虚空之镜 (紫黑镜面, 亮紫反光, 钻石青核心, 异界诡谲) ----------------
    "void_mirror": [
        "................",
        "....KQQQQQQK....",
        "...KQppppppQK...",
        "..KQpvvPPvvpQK..",
        "..KpvPPkkPPvpK..",
        "..KpPPkCCkPPpK..",
        "..KpPPkCCkPPpK..",
        "..KpvPPkkPPvpK..",
        "..KQpvvPPvvpQK..",
        "...KQppppppQK...",
        "....KQQQQQQK....",
        "...KQ@@@@@@QK...",
        "..KQ@pppppp@QK..",
        "..KQ@pppppp@QK..",
        "..KKQQQQQQQQKK..",
        "................",
    ],
    # ---------------- 深渊吞噬者 (黑巨口, 骨獠牙, 深红内部, 两小发光眼) ----------------
    "abyss_devourer": [
        "................",
        "....KKKKKKKK....",
        "..KKKKKKKKKKKK..",
        ".KDDDRRKKRRDDDK.",
        ".KDDDRRKKRRDDDK.",
        ".KDDDKKKKKKDDDK.",
        ".KDDK888888KDDK.",
        ".KDDRRRRRRRRDDK.",
        ".KDDRRRRRRRRDDK.",
        ".KDDRARRRRARRDK.",
        ".KDDRRRRRRRRDDK.",
        ".KDDK888888KDDK.",
        ".KDDDKKKKKKDDDK.",
        ".KKKKKKKKKKKKKK.",
        "................",
        "................",
    ],
    # ---------------- 神灵使者 (金羽, 白圣躯, 金蓝光环, 庄严光辉) ----------------
    "divine_messenger": [
        "................",
        ".....YYYYYY.....",
        "....Y111111Y....",
        "....Y111111Y....",
        ".....YYYYYY.....",
        "....K111111K....",
        "...K11111111K...",
        "..K1uu1111uu1K..",
        ".F5K11111111K5F.",
        ".F55K111111K55F.",
        "..K5111111115K..",
        "..K1111111111K..",
        "..K1111YY1111K..",
        "..KK11111111KK..",
        "....KK1111KK....",
        "................",
    ],
    # ---------------- 光之精灵 (明亮光团, 柔和光芒, 发光金核, 圣洁) ----------------
    "light_spirit": [
        "................",
        ".......II.......",
        ".....IIIIII.....",
        "....IIWWWWII....",
        "...IWWWWWWWWI...",
        "..IWWWWWWWWWWI..",
        "..IWW11YY11WWI..",
        "..IWW1YFFY1WWI..",
        "..IWW11YY11WWI..",
        "..IWWWWWWWWWWI..",
        "...IWWWWWWWWI...",
        "....IIWWWWII....",
        ".....IIIIII.....",
        ".......II.......",
        "................",
        "................",
    ],
    # ---------------- 天使 (白翼, 金发, 白袍, 蓝眼, 光环) ----------------
    "angel": [
        "................",
        ".....YYYYYY.....",
        "....Y111111Y....",
        ".....YYYYYY.....",
        "...K11111111K...",
        "..K5555555555K..",
        "..K5uu1111uu5K..",
        "..K5111111115K..",
        "....K111111K....",
        ".77K11111111K77.",
        ".777K111111K777.",
        "..K1111111111K..",
        "..K1111YY1111K..",
        "..KK11111111KK..",
        "....KK1111KK....",
        "................",
    ],
    # ---------------- 圣骑士 (银甲, 金边, 十字头盔, 蓝披风, 盾) ----------------
    "holy_knight": [
        "................",
        "....KKKKKKKK....",
        "...K$7WWWW7$K...",
        "..K$7WKKKKW7$K..",
        "..K$7WKKKKW7$K..",
        "..K$7KKFFKK7$K..",
        "..K$$$$$$$$$$K..",
        ".KBB$$77WW$$BBK.",
        ".KBB$5$$$$5$BBK.",
        "..K$$$$$$$$$$K..",
        "..K$5$$$$$$5$K..",
        "..K$5$$FF$$5$K..",
        "..K$$$$$$$$$$K..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    # ---------------- 先知 (蓝袍, 白须, 水晶球, 神秘光芒, 智慧之眼) ----------------
    "oracle": [
        "................",
        "....KKKKKKKK....",
        "...KBBBBBBBBK...",
        "..KBBuuBBuuBBK..",
        "..KBBBBBBBBBBK..",
        "..KBB111111BBK..",
        "..KBB111111BBK..",
        "..KBB111111BBK..",
        "..KBBBBBBBBBBK..",
        "..KBBbbbbbbBBK..",
        "..KbbkkCCCkkbK..",
        "..KbbkkCCCkkbK..",
        "..KbbbbbbbbbbK..",
        "..KKbbbbbbbbKK..",
        "....KKKKKKKK....",
        "................",
    ],
    # ---------------- 天界战士 (金白甲, 蓝能量翼, 光环, 威严) ----------------
    "celestial_warrior": [
        "................",
        ".....YYYYYY.....",
        "....Y111111Y....",
        ".....YYYYYY.....",
        "....K$$$$$$K....",
        "...K$5WWWW5$K...",
        "..K$5WKKKKW5$K..",
        "..K$$$$$$$$$$K..",
        "..K5$$$$$$$$5K..",
        ".KuK$$$$$$$$KuK.",
        ".KuuK$5$$5$KuuK.",
        "..K$$$$$$$$$$K..",
        "..K$5$$$$$$5$K..",
        "..K$$$$$$$$$$K..",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    # ---------------- 炽天使 (金焰翼, 白袍, 多重光芒, 金光环, 光辉圣洁) ----------------
    "seraphim": [
        "................",
        ".....YYYYYY.....",
        "....Y111111Y....",
        ".....YYYYYY.....",
        "....K111111K....",
        "...K11111111K...",
        "..K1111111111K..",
        "..K1uu1111uu1K..",
        "..K1111111111K..",
        ".F4K11111111K4F.",
        ".F44K111111K44F.",
        ".F444K1111K444F.",
        "..K1111111111K..",
        "..KK11111111KK..",
        "....KK1111KK....",
        "................",
    ],
    # ---------------- 审判骑士 (银甲, 金饰, 黄金天秤, 蓝金配色, 头盔) ----------------
    "judgement_knight": [
        "................",
        "....KKKKKKKK....",
        "...K$7WWWW7$K...",
        "..K$7WKKKKW7$K..",
        "..K$7WKKKKW7$K..",
        "..K$7KKKKKK7$K..",
        "..K$$$$$$$$$$K..",
        "..K$$77WW77$$K..",
        "..K$5$$$$$$5$K..",
        "..K$$FF55FF$$K..",
        "..K$$F5$$5F$$K..",
        "..K$$$$$$$$$$K..",
        "..K$5$$$$$$5$K..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    # ---------------- 神殿守卫 (金雕像感, 岩石+黄金, 巨大, 蓝光眼) ----------------
    "temple_guardian": [
        "................",
        "....KKKKKKKK....",
        "...KNNNNNNNNK...",
        "..KNNN5NN5NNNK..",
        "..KNNuuNNuuNNK..",
        "..KNNNNNNNNNNK..",
        "..KNNF5NN5FNNK..",
        "...KNNNNNNNNK...",
        "..KNNNNNNNNNNK..",
        ".KNF5NNNNNN5FNK.",
        ".KNNNNNNNNNNNNK.",
        ".KNN5NNNNNN5NNK.",
        ".KNNNNNNNNNNNNK.",
        ".KKKKKKKKKKKKKK.",
        "................",
        "................",
    ],
    # ---------------- 至高神 (金冠, 白圣光, 蓝神性, 金射线, 光辉万丈) ----------------
    "supreme_god": [
        "................",
        "..F..F....F..F..",
        ".F...FKKKKF...F.",
        ".F...KFFFFK...F.",
        ".F...KFF55K...F.",
        ".F...K1111K...F.",
        "..F.Kuu11uuK.F..",
        "...K11111111K...",
        "..F.K111111K.F..",
        ".F..K111111K..F.",
        ".F..K111111K..F.",
        ".F..K111111K..F.",
        "..F.K111111K.F..",
        "....KKKKKKKK....",
        "................",
        "................",
    ],
}

def check(name, art, width=16):
    errs = []
    for i, row in enumerate(art):
        if len(row) != width:
            errs.append(f"  行{i}: 长度{len(row)} != {width}: '{row}'")
    unknown = set()
    for row in art:
        unknown |= set(row) - PALETTE
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
