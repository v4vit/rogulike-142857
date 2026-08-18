# -*- coding: utf-8 -*-
"""冥界/地狱主题怪物像素贴图设计(16x16) + 自检脚本."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 色板键集合(与 rogue_rpg.PIXEL_COLORS 完全一致, 保证全部合法)
R_PALETTE = {
    # 灰阶
    "K", "D", "L", "W", "S", "#", "0", "7", "$", "&",
    # 骨
    "8", "9",
    # 红
    "R", "r", "A", "x", "X", "w",
    # 橙 / 黄金 / 炽焰
    "O", "%", "2", "Y", "F", "!", "5", "4",
    # 绿
    "G", "i", "g", "j", "V", "h", "3",
    # 青 / 青绿 / 冰蓝
    "C", "c", "k", "~", "T", "I", "1",
    # 蓝
    "B", "b", "u", "U",
    # 紫
    "P", "p", "Q", "v", "@",
    # 粉
    "M", "m", ";",
    # 棕 / 肤
    "N", "n", "H", "J", "6", "E", "e", "Z",
}

# 用 "." 表示透明(不绘制). 每行必须正好 16 字符.
DESIGNS = {
    # ---------------- 死神 (黑长袍 + 兜帽骷髅 + 红光眼 + 斜握大镰刀) ----------------
    "reaper": [
        "....########....",
        "..K##########K..",
        "..K8888888888K..",
        "..K8888888888K..",
        "..K8RR8888RR8K..",
        "..K8RR8K8KRR8K..",
        "..K8888888888K..",
        "..K8888888888K..",
        "..K##########K..",
        "..KDDDDDDDDDDK..",
        "..KD&DDDDDDDDK..",
        "..KDD&DDDDDDDK..",
        "..KDDD&DDDDDDK..",
        "...KDDD&DDDDK...",
        "....KDDD&DDK....",
        ".....KDDD&K.....",
    ],
    # ---------------- 地狱犬 (深红黑毛 + 燃眼燃脊 + 獠牙 + 火焰鬃毛) ----------------
    "hellhound": [
        ".....KKKKKK.....",
        "....KXXXXXXK....",
        "...KX44K44XXK...",
        "..KX44K44K44XK..",
        "..KXKKKKKKKKXK..",
        "..KXKKKKKKKKXK..",
        "..KXKKKKKKKKXK..",
        "...KXKKKKKKXK...",
        "...KXRKKKKRXK...",
        "...KXRKKKKRXK...",
        "....KKKKKKKK....",
        "..KXXXXXXXXXXK..",
        "..K8XXXXXXXX8K..",
        "..KKKKKKKKKKKK..",
        "...KXXXXXXXXK...",
        "...KKKKKKKKKK...",
    ],
    # ---------------- 骨巨人 (巨型骷髅 + 黑眼窝 + 骨棒 + 暗部) ----------------
    "bone_giant": [
        "....########....",
        "..K8888888888K..",
        "..K8888888888K..",
        "..K8KK8888KK8K..",
        "..K8KK8888KK8K..",
        "..K8888888888K..",
        "..K8888888888K..",
        "..K8888888888K..",
        "..K##########K..",
        "..K8888888888K..",
        "..K8999999988K..",
        "..K88K9999K88K8.",
        "..K88K9999K88K8.",
        "..K88K9999K88K8.",
        "..K##########K8.",
        "..K8888888888K8.",
    ],
    # ---------------- 地狱之王 (深红黑龙魔王 + 金冠 + 骨角 + 燃眼) ----------------
    "hell_king": [
        "..K8K......K8K..",
        "...K8K....K8K...",
        ".KFFFFFFFFFFFK..",
        ".KF!FFFFFFFF!FK.",
        "..KFFFFFFFFFFK..",
        ".KXXXKKKKKKXXXK.",
        ".KXXXXXXXXXXXXK.",
        ".KXRRXXXXXXRRXK.",
        ".KXRRXXXXXXRRXK.",
        ".KXXXXXXXXXXXXK.",
        ".KXXXKKKKKKXXXK.",
        ".KXXXXXXXXXXXXK.",
        "..KXXXXXXXXXXK..",
        "...KXXXXXXXXK...",
        "....KXXXXXXK....",
        ".....KKKKKK.....",
    ],
    # ---------------- 噬魂者 (紫黑灵体 + 青绿幽光 + 大嘴吞魂 + 红眼) ----------------
    "soul_eater": [
        "................",
        "....@QQQQQQ@....",
        "...@QQkkkkQQ@...",
        "..@QQkkkkkkQQ@..",
        "..@QkkkkkkkkQ@..",
        "..@QkkRRRRkkQ@..",
        "..@QkkRRRRkkQ@..",
        "..@QkkkkkkkkQ@..",
        "..@QkkkkkkkkQ@..",
        "..@@QkkkkkkQ@@..",
        "...@@QQQQQQ@@...",
        "....@@QjjjQ@@...",
        ".....@@QjjQ@....",
        "......@@QQ@.....",
        ".......@@@......",
        "................",
    ],
    # ---------------- 虚空恶魔 (黑紫恶魔 + 角 + 燃红眼 + 裂嘴獠牙 + 翅) ----------------
    "void_demon": [
        "..@88@....@88@..",
        "..@88@....@88@..",
        "@QQ@@@@@@@@@@QQ@",
        "@QQPPPPPPPPPPQQ@",
        "@QPPPPPPPPPPPPQ@",
        "@QPPRRRRRRRRPPQ@",
        "@QPPRRRRRRRRPPQ@",
        "@QPPPPPPPPPPPPQ@",
        "@QPPPPPPKPPPPPQ@",
        "@QPPPPPKKKKPPPQ@",
        "@QPPPK8K8K8KPPQ@",
        "@QQPPPPPKKPPPQQ@",
        "@QQPPPPPPPPPPQQ@",
        "@QQPPPPPPPPPPQQ@",
        ".@QQQQQQQQQQQQ@.",
        "..@@@@@@@@@@@@..",
    ],
    # ---------------- 深渊食尸鬼 (暗绿腐尸 + 破衣 + 滴血大嘴 + 无神小眼) ----------------
    "abyss_ghoul": [
        "................",
        "...KKKKKKKK.....",
        "...KgggggggK....",
        "...KgggggggK....",
        "..KggKggggKggK..",
        "..KggKKKKKKggK..",
        "..KggKKKKKKggK..",
        "..KggggggggggK..",
        "..KggggggggggK..",
        "..KKGrrrrrrGKK..",
        "....GrrrrrrG....",
        "...K&GGGGGG&K...",
        "...K0&GGGG&0K...",
        "....KKKKKKKK....",
        ".....KGGGGK.....",
        ".....KKKKKK.....",
    ],
    # ---------------- 被诅咒骑士 (锈蚀黑甲 + 红锈 + 红眼缝 + 断剑 + 绿诅咒气) ----------------
    "cursed_knight": [
        "..j.......j.....",
        "...j.....j......",
        "....KKKKKKKK....",
        "....K######K....",
        "...K#0&&&&0#K...",
        "...K#0&&&&0#K...",
        "...K#wRRRRw#K...",
        "...K#wRRRRw#K...",
        "...KKKKKKKKK....",
        "..K#0&00&00&K...",
        "..K#00&&&000#K..",
        "..K#00&&&000#K..",
        "..K#0&&&00&0#K..",
        "...K#00&&00#K.S.",
        "....K#00&#K.S...",
        "....KKKKKKKK....",
    ],
    # ---------------- 地狱小鬼 (深红小恶魔 + 蝠翼 + 火尾 + 黄眼 + 獠牙) ----------------
    "nether_imp": [
        ".............K..",
        "..K..........KXK",
        "..KXK......KXXXK",
        "..KXXXK..KXXXXXK",
        ".....KXXXXXK....",
        "....KXXXXXXXK...",
        "....KXYYXXXKK...",
        "....KXYYXXXKK...",
        "....KXXXXXXXKK..",
        "....K8KXXXK8K...",
        ".....KKKKKKK....",
        "....KXXXXXXXX...",
        "....KXXXXXXXX...",
        "....KKKKKKKK!4..",
        ".....KXKKXK.....",
        ".....KKKKKK.....",
    ],
    # ---------------- 恐惧领主 (暗紫法袍 + 黑角王冠 + 燃橙眼 + 紫法能缠绕) ----------------
    "dread_lord": [
        "..v.......v.....",
        "..v@.....@v.....",
        "..KDDDDDDDDK....",
        "..KDDDDDDDDK....",
        "..KQQQQQQQQK....",
        "..KQQQQQQQQK....",
        "..KQOOOROOQK....",
        "..KQOOOROOQK....",
        "..KQQQQQQQQK....",
        "..KpQQQQQQQpK...",
        "..KpQQQQQQQpK...",
        ".KpPPQQQQQPPpK..",
        ".KpPPQQQQQPPpK..",
        ".KpPPPPPPPPPPpK.",
        "..KpPPPPPPPPpK..",
        "..KKKKKKKKKKKK..",
    ],
}


def check(name, art, width=16):
    errs = []
    for i, row in enumerate(art):
        if len(row) != width:
            errs.append(f"  行{i}: 长度{len(row)} != {width}: '{row}'")
    known = set(R_PALETTE) | {'.', ' '}
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
