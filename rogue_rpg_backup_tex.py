#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肉鸽勇士 —— RPG 风格的肉鸽回合制游戏 (鼠标操作)
路线与 UI 与「肉鸽试炼」一致, 但玩法为 RPG: 等级/技能/武器/药水/蓝量.

核心系统:
  - 地图: 分层节点, 节点之间不完全连通, 用线连接 (Canvas 绘制)
         节点类型比例 宝藏:事件:小怪:精英:商店 = 1:2:4:1:1 + 关底 boss
  - 角色: 等级 / 经验 / 生命 HP / 蓝量 MP
  - 技能: 由等级解锁, 释放消耗蓝量; 武器也能带来技能
  - 武器: 提升属性, 部分强力武器带被动
  - 药水: 战斗内使用的消耗品
  - 战斗: 回合制, 攻击 / 防御 / 技能 / 药水
本版本为第一层(floor 1) 完整可玩.
"""

import os
import pickle
import random
import sys

import tkinter as tk
from tkinter import font as tkfont

# ============================================================
# 主题配色 (与肉鸽试炼 GUI 一致)
# ============================================================
COLOR_BG      = "#1e1e2e"
COLOR_PANEL   = "#2a2a3e"
COLOR_PANEL2  = "#35354d"
COLOR_BORDER  = "#4a4a6a"
COLOR_TEXT     = "#e6e6f0"
COLOR_SUB      = "#9a9ab0"
COLOR_ACCENT   = "#c792ea"
COLOR_HP       = "#f7768e"
COLOR_MP       = "#7dcfff"
COLOR_GOLD     = "#e0af68"
COLOR_OK       = "#9ece6a"
COLOR_BAD      = "#f7768e"
COLOR_BTN      = "#3b3b55"
COLOR_BTN_HOV  = "#4a4a6a"
COLOR_SELECT   = "#7aa2f7"
COLOR_CARD     = "#31314a"

NODE_COLOR = {
    "monster":  COLOR_BAD,
    "divine":   "#ffd75e",
    "elite":    "#ff9e64",
    "treasure": COLOR_GOLD,
    "event":    COLOR_SELECT,
    "shop":     COLOR_OK,
    "blacksmith": "#82aaff",
    "abyss":    "#ff79c6",
    "abyss_elite": "#ff79c6",
    "abyss_core": "#ff79c6",
    "boss":     "#bb9af7",
    "start":    COLOR_ACCENT,
}
NODE_ICON = {
    "monster":  "⚔",
    "divine":   "✨",
    "elite":    "☠",
    "treasure": "💰",
    "event":    "❔",
    "shop":     "🛒",
    "blacksmith": "🔨",
    "abyss":    "🌀",
    "abyss_elite": "🌀",
    "abyss_core": "🌀",
    "boss":     "👑",
    "start":    "⛺",
}
NODE_LABEL = {
    "monster":  "小怪",
    "divine":   "神灵使者",
    "elite":    "精英",
    "treasure": "宝藏",
    "event":    "事件",
    "shop":     "商店",
    "blacksmith": "铁匠铺",
    "abyss":    "异界",
    "abyss_elite": "异界精英",
    "abyss_core": "异界核心",
    "boss":     "关底Boss",
    "start":    "营地",
}

FONT_MAIN  = ("Microsoft YaHei UI", 11)
FONT_TITLE = ("Microsoft YaHei UI", 15, "bold")
FONT_BIG   = ("Microsoft YaHei UI", 20, "bold")
FONT_MONO  = ("Consolas", 11)

# ============================================================
# 像素画系统: 用单字符网格定义 Minecraft 风格彩色像素贴图.
# 每个字符 = 一个像素方块, '.' 表示透明(不绘制).
# 渲染函数 pixel_canvas() 把字符网格逐像素画成彩色方块.
# ============================================================
PIXEL_COLORS = {
    # 灰阶
    "K": "#1a1a1a",   # 黑色(描边)
    "D": "#3c3c3c",   # 深灰
    "L": "#9c9c9c",   # 浅灰
    "W": "#ffffff",   # 白色
    "S": "#c8c8d0",   # 银
    # 红
    "R": "#e04040",   # 红
    "r": "#8a1c1c",   # 深红
    "A": "#5a1010",   # 暗红
    # 橙 / 黄 / 金
    "O": "#f0952a",   # 橙
    "Y": "#f2d130",   # 黄
    "F": "#ffc84d",   # 金
    # 绿
    "G": "#4fc04a",   # 绿
    "g": "#1e7a28",   # 深绿
    "V": "#3f6a24",   # 橄榄绿
    # 青 / 青绿 / 冰蓝
    "C": "#38c8c8",   # 青
    "c": "#1e7a7a",   # 深青
    "T": "#54e8c0",   # 青绿
    "I": "#a8e4ff",   # 冰蓝
    # 蓝
    "B": "#4a6cf0",   # 蓝
    "b": "#27439c",   # 深蓝
    # 紫
    "P": "#a854e0",   # 紫
    "p": "#5c2490",   # 深紫
    "Q": "#3a2470",   # 暗影紫
    # 粉 / 品红
    "M": "#f07aaa",   # 粉
    "m": "#b03a6e",   # 深粉
    # 棕 / 肤色
    "N": "#8a5a2c",   # 棕
    "n": "#5c3a1a",   # 深棕
    "E": "#f0b080",   # 浅肤色
    "e": "#c08650",   # 深肤色
}

PIXEL_DEFAULT_SCALE = 8   # 战斗/图鉴里每像素方块的大小(px)
PIXEL_PAD = 4             # 贴图周围留白(px)


def pixel_canvas(parent, art, bg=COLOR_PANEL, scale=PIXEL_DEFAULT_SCALE):
    """把像素画 art(字符网格列表) 渲染为一个 tk.Canvas 并返回.

    每个字符对应一个 scale×scale 的彩色方块; '.' / 空格 / 未知字符视为透明.
    """
    rows = list(art or [])
    if not rows:
        return None
    ncols = max(len(r) for r in rows)
    w = ncols * scale + PIXEL_PAD * 2
    h = len(rows) * scale + PIXEL_PAD * 2
    cv = tk.Canvas(parent, width=w, height=h, bg=bg, highlightthickness=0)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            col = PIXEL_COLORS.get(ch)
            if col is None:
                continue
            cv.create_rectangle(PIXEL_PAD + x * scale, PIXEL_PAD + y * scale,
                                PIXEL_PAD + (x + 1) * scale, PIXEL_PAD + (y + 1) * scale,
                                fill=col, outline="")
    return cv

# ============================================================
# 数据: 武器
# ============================================================
# 武器: 提升属性; 附带技能; 部分带被动.
# 分类: cat = sword(剑)/axe(斧)/staff(法杖)/hammer(锤)/dagger(匕首)
#        /greatsword(重剑)/spear(长矛)
# 等级体系: 共 4 级 (tier1~4), 4级为最高/神器级.
#   tier1: 初始;  tier2: 普通高级;  tier3: 精英/中级掉落;
#   tier4: 顶级武器 + 神器 (由最高等武器 + Boss材料在背包合成, 也直接作为顶级掉落).
# 匕首: 连击(hits)技能, 高级匕首耗蓝少; 重剑: 攻击高, 耗蓝大且带冷却(cooldown);
# 长矛: 攻击高且兼顾连突, 技能附带小冷却.
WEAPON_LIB = {
    # ----- tier1 (初始) -----
    "iron_sword": dict(
        name="铁剑", tier=1, atk=4, hp=0, mp=0, cat="sword",
        passive="", skill="cleave",
        desc="冒险者的起点, 朴实无华. 攻击+4",
        art=[
            ".......KK........",
            "......KSSK.......",
            "......KSSK.......",
            "......KSSK.......",
            "......KSSK.......",
            ".......KSSK......",
            ".......KSSK......",
            ".......KSSK......",
            "........KSSK.....",
            "........KSSK.....",
            ".........KSSK....",
            ".........KKKK....",
            "......KKKKKKK....",
            "....KKFFFFKKK....",
            "...KnnnnnnnnnK...",
            "...KKKKKKKKKKK...",
        ]),
    # ----- tier2 -----
    "battle_axe": dict(
        name="战斧", tier=2, atk=7, hp=10, mp=0, cat="axe",
        passive="", skill="whirlwind",
        desc="沉重战斧, 攻击+7 生命+10. 附带技能: 旋风斩",
        art=[
            "   _",
            "  / \\",
            " |   |",
            "  \\_/",
            "   |",
            "   |",
            "   ▓",
        ]),
    "magic_staff": dict(
        name="奥术法杖", tier=2, atk=3, hp=0, mp=25, cat="staff",
        passive="mana_regen", skill="fireball",
        desc="凝聚魔力, 攻击+3 蓝量+25. 每回合回复2蓝",
        art=[
            "   o",
            "   |",
            "   |",
            "   |",
            "  / \\",
            " /   \\",
            "▓     ▓",
        ]),
    "steel_dagger": dict(
        name="钢匕首", tier=2, atk=6, hp=0, mp=0, cat="dagger",
        passive="", skill="double_stab",
        desc="轻巧迅捷, 攻击+6. 技能连刺耗蓝极少",
        art=[
            "   ▓",
            "   |",
            "   |",
            "   |",
            "  / \\",
            " /   \\",
            "▓     ▓",
        ]),
    "claymore": dict(
        name="大剑", tier=2, atk=12, hp=15, mp=0, cat="greatsword",
        passive="", skill="power_swing",
        desc="厚重宽刃, 攻击+12 生命+15. 重斩耗蓝大, 两回合一次",
        art=[
            "    ▄",
            "   ▄▄",
            "   █",
            "   █",
            "   █",
            "   ▓",
            "   ▓",
        ]),
    "hunter_spear": dict(
        name="猎枪", tier=2, atk=9, hp=0, mp=0, cat="spear",
        passive="", skill="spear_thrust",
        desc="猎人惯用的长枪, 攻击+9. 附带技能: 突刺连击",
        art=[
            "   ▸",
            "    |",
            "    |",
            "    |",
            "    |",
            "    ▓",
            "    ▓",
        ]),
    # ----- tier3 (中级/精英掉落) -----
    "war_hammer": dict(
        name="战锤", tier=3, atk=10, hp=28, mp=0, cat="hammer",
        passive="", skill="quake",
        desc="精工战锤, 攻击+10 生命+28. 附带技能: 大地震击",
        art=[
            "  ▄▄▄▄",
            "  ████",
            "   |",
            "   |",
            "   |",
            "   ▓",
            "   ▓",
        ]),
    "blood_dagger": dict(
        name="血刃", tier=4, atk=16, hp=10, mp=12, cat="dagger",
        passive="", skill="blood_stab", ail=("bleed", 2),
        desc="饮尽敌血而愈发锋利的匕首(加强后为神器级), 攻击+16 生命+10 蓝量+12. 连击使敌人流血",
        art=[
            "   ▓",
            "   |",
            "  /|",
            " / |",
            "|  |",
            " \\ |",
            "  \\▓",
        ]),
    "steel_spear": dict(
        name="龙骨枪", tier=3, atk=14, hp=5, mp=5, cat="spear",
        passive="", skill="spear_storm",
        desc="以龙骨为柄的强枪, 攻击+14 生命+5 蓝量+5. 附带技能: 龙枪连突",
        art=[
            "   ▸▸",
            "    |",
            "    |",
            "    |",
            "    |",
            "    ▓",
            "    ▓",
        ]),
    # ----- tier4 (顶级 + 神器; 原tier3武器加强后并入此级) -----
    "giant_hammer": dict(
        name="巨人战锤", tier=4, atk=14, hp=55, mp=0, cat="hammer",
        passive="strong_body", skill="quake",
        desc="传说战锤(加强), 攻击+14 生命+55. 附带技能: 大地震击",
        art=[
            "  ▄▄▄▄",
            "  ████",
            "   |",
            "   |",
            "   |",
            "   ▓",
            "   ▓",
        ]),
    "venom_dagger": dict(
        name="淬毒匕首", tier=4, atk=12, hp=5, mp=15, cat="dagger",
        passive="", skill="venom_stab",
        desc="淬满剧毒(加强), 攻击+12 生命+5 蓝量+15. 三连击耗蓝少",
        art=[
            "   ▓",
            "   |",
            "  /|",
            " / |",
            "|  |",
            " \\ |",
            "  \\▓",
        ]),
    "giant_blade": dict(
        name="巨剑", tier=4, atk=21, hp=30, mp=0, cat="greatsword",
        passive="strong_body", skill="colossal_cleave",
        desc="开山巨剑(加强), 攻击+21 生命+30. 横扫无视格挡, 两回合一次",
        art=[
            "   ▄▄▄",
            "   ███",
            "    █",
            "    █",
            "    █",
            "    ▓",
            "    ▓",
        ]),
    # ----- tier4 (顶级 + 神器, 由最高等武器 + Boss材料在背包合成) -----
    "assassin_dagger": dict(
        name="刺客匕首", tier=4, atk=11, hp=5, mp=12, cat="dagger",
        passive="", skill="assassinate",
        desc="致命连击, 攻击+11 生命+5 蓝量+12. 四连击",
        art=[
            "  ▓",
            "  |",
            "  |",
            "  |",
            " / \\",
            "▓   ▓",
            "     ",
        ]),
    "war_greatsword": dict(
        name="战争巨剑", tier=4, atk=19, hp=25, mp=0, cat="greatsword",
        passive="strong_body", skill="rend_earth",
        desc="裂地神兵, 攻击+19 生命+25. 裂地斩无视格挡, 两回合一次",
        art=[
            "   ▄▄▄▄",
            "    ███",
            "     █",
            "     █",
            "     █",
            "     ▓",
            "     ▓",
        ]),
    "god_hammer": dict(
        name="泰坦神锤", tier=4, atk=18, hp=60, mp=0, cat="hammer",
        passive="strong_body", skill="titan_quake", ail=("stun", 1),
        desc="由巨人战锤与龙鳞重铸的传说之锤, 攻击+18 生命+60. 重锤震慑, 攻击令敌人眩晕; 大地崩裂, 两回合一次",
        art=[
            "   █████",
            "  ███████",
            "   █████",
            "     |",
            "     |",
            "     ▓",
            "     ▓",
        ]),
    "god_greatsword": dict(
        name="破灭重剑", tier=4, atk=26, hp=40, mp=10, cat="greatsword",
        passive="strong_body", skill="world_cleave", ail=("bleed", 3),
        desc="由战争巨剑与龙鳞锻造的神兵, 攻击+26 生命+40 蓝量+10. 撕裂伤口, 攻击令敌人流血; 裂地灭世, 两回合一次",
        art=[
            "    ▄▄▄▄▄",
            "     █████",
            "      ███",
            "      ███",
            "      ███",
            "      ▓",
            "      ▓",
        ]),
    "god_dagger": dict(
        name="深渊匕影", tier=4, atk=20, hp=20, mp=20, cat="dagger",
        passive="guard_start", skill="shadow_assassinate", ail=("poison", 2),
        desc="由刺客匕首与巫妖之魂淬炼, 攻击+20 生命+20 蓝量+20. 淬毒割裂, 攻击令敌人中毒; 暗影五连击",
        art=[
            "  ▓",
            "  ▓",
            "  ▓",
            " / \\",
            "▓   ▓",
            " ███",
            "     ",
        ]),
    # ----- 新增长矛神器: 永恒之枪 (tier4) -----
    "gungnir": dict(
        name="永恒之枪", tier=4, atk=24, hp=15, mp=15, cat="spear",
        passive="guard_start", skill="gungnir_bolt", ail=("bleed", 2),
        desc="北欧神话中的神器之枪, 投出必中要害. 攻击+24 生命+15 蓝量+15. 贯穿撕裂, 攻击令敌人流血; 永恒贯穿, 两回合一次",
        art=[
            "     ▸▸",
            "      |",
            "      |",
            "      |",
            "      |",
            "      ▓",
            "      ▓",
        ]),
    # ----- 新增锤类神器: 雷霆碎星锤 (tier4) -----
    "god_hammer2": dict(
        name="雷霆碎星锤", tier=4, atk=22, hp=70, mp=10, cat="hammer",
        passive="strong_body", skill="storm_hammer", ail=("burn", 2),
        desc="凝聚风暴之力的雷神之锤, 攻击+22 生命+70 蓝量+10. 雷火灼烧, 攻击令敌人燃烧; 天雷崩落, 两回合一次",
        art=[
            "    █████",
            "  ██ ███ ██",
            "   ███████",
            "      |",
            "      |",
            "      ▓",
            "      ▓",
        ]),
    # ----- 新增匕首神器: 冥府毒牙 (tier4) -----
    "god_dagger2": dict(
        name="冥府毒牙", tier=4, atk=21, hp=15, mp=22, cat="dagger",
        passive="mana_regen", skill="shadow_dance", ail=("poison", 3),
        desc="淬以冥河之毒的双刃匕首, 攻击+21 生命+15 蓝量+22. 剧毒侵蚀, 攻击令敌人中毒; 六段影袭",
        art=[
            "  ▓▓",
            "   ▓",
            "   ▓",
            "  /|",
            " / |",
            "▓  ▓",
            "    ",
        ]),
    # ----- 新增 tier4 异常武器 (能造成 燃烧/冰冻/中毒/流血) -----
    "flame_blade": dict(
        name="烈焰之刃", tier=4, atk=20, hp=15, mp=8, cat="greatsword",
        passive="", skill="flame_slash", ail=("burn", 2),
        desc="燃烧着不灭之焰的巨刃, 攻击+20 生命+15 蓝量+8. 攻击令敌人燃烧",
        art=[
            "  /▄▄\\",
            "  ████",
            "   ██",
            "   ██",
            "   ██",
            "   ▓",
            "   ▓",
        ]),
    "frost_saber": dict(
        name="冰霜之刃", tier=4, atk=18, hp=20, mp=15, cat="sword",
        passive="", skill="frost_slash", ail=("freeze", 1),
        desc="凝结寒霜之力的利刃, 攻击+18 生命+20 蓝量+15. 攻击累积寒气, 第三次冰冻敌人",
        art=[
            "   ▄▄",
            "  /|",
            " / |",
            "|  |",
            "|  |",
            " \\ |",
            "  \\▓",
        ]),
    "toxic_blade": dict(
        name="剧毒之刃", tier=4, atk=17, hp=10, mp=18, cat="dagger",
        passive="", skill="toxic_stab", ail=("poison", 3),
        desc="浸满致命剧毒的匕首, 攻击+17 生命+10 蓝量+18. 连击使敌人中毒",
        art=[
            "  ▓",
            "  |",
            " /|",
            "/ |",
            "| |",
            " \\▓",
            "  ▓",
        ]),
    # ----- 超神器 (神器 + tier4异常武器 + 第三层掉落物 合成, 北欧神话武器) -----
    "super_mjolnir": dict(
        name="妙尔尼尔", tier=5, atk=30, hp=80, mp=20, cat="hammer",
        passive="strong_body", skill="mjolnir_bolt",
        skills=["mjolnir_bolt", "mjolnir_judgement"], ail=("burn", 2),
        desc="雷神之锤·妙尔尼尔, 以雷霆碎星锤与烈焰之刃熔铸的至高神器. 攻击+30 生命+80 蓝量+20. 雷神之怒眩晕万物, 雷霆审判对目标上回合处于眩晕时造成巨额伤害, 各两回合一次",
        art=[
            "   █████",
            "  ███ ███",
            "   █████",
            "     |",
            "     |",
            "     ▓",
            "     ▓",
        ]),
    "super_tyrfing": dict(
        name="提尔锋", tier=5, atk=36, hp=50, mp=10, cat="greatsword",
        passive="strong_body", skill="tyrfing_curse",
        skills=["tyrfing_curse"], ail=("bleed", 3),
        desc="受诅咒的魔剑·提尔锋, 以破灭重剑与血刃熔铸. 攻击+36 生命+50 蓝量+10. 提尔锋之咒令双方流血, 被攻击时反噬敌血, 两回合一次",
        art=[
            "   ▄▄▄▄▄",
            "    ████",
            "     ██",
            "     ██",
            "     ██",
            "     ▓",
            "     ▓",
        ]),
    "super_laevateinn": dict(
        name="莱瓦汀", tier=5, atk=32, hp=40, mp=35, cat="staff",
        passive="mana_regen", skill="laevateinn_brand",
        skills=["laevateinn_brand", "laevateinn_detonate"], ail=("burn", 3),
        desc="烈焰魔杖·莱瓦汀, 以永恒之枪与烈焰之刃熔铸. 攻击+32 生命+40 蓝量+35. 烈焰烙印施加永久烧伤, 焚天引爆倾泻毁灭之力",
        art=[
            "    ▄▄",
            "    ██",
            "    ██",
            "   ████",
            "   ████",
            "     ▓",
            "     ▓",
        ]),
    "super_dainsleif": dict(
        name="达因斯莱夫", tier=5, atk=34, hp=45, mp=30, cat="dagger",
        passive="", skill="dainsleif_dance",
        skills=["dainsleif_dance"], ail=("perm_poison", 3),
        desc="杀人魔剑·达因斯莱夫, 以深渊匕影与剧毒之刃熔铸. 攻击+34 生命+45 蓝量+30. 索命连刺以毒养毒, 毒改为永久毒伤(不因引爆消失), 三度出手便得额外回合",
        art=[
            "   ▓▓",
            "   ▓▓",
            "   ▓▓",
            "  / |",
            " /  |",
            "▓   ▓",
            "    ",
        ]),
}

# 神器武器 id 集合 (仅能通过合成获得, 不直接掉落)
ARTIFACT_WEAPONS = {"god_hammer", "god_hammer2", "god_greatsword", "god_dagger",
                    "god_dagger2", "gungnir"}

# 超神器武器 id 集合 (神器 + tier4异常武器 + 第三层掉落物 合成, 不直接掉落)
SUPER_ARTIFACT_WEAPONS = {"super_mjolnir", "super_tyrfing",
                          "super_laevateinn", "super_dainsleif"}

# ============================================================
# 数据: 技能
# ============================================================
# 技能: kind + value. 战斗中解释.
# 基础技能 (等级解锁); 武器技能 (装备即得)
SKILL_LIB = {
    # ----- 基础技能 (等级解锁) -----
    "attack":    dict(name="攻击",   mp=0,  kind="dmg", value=0,
                      desc="普通攻击, 造成 攻击力 伤害"),
    "defend":    dict(name="防御",   mp=0,  kind="block", value=8,
                      desc="获得 8 点格挡"),
    # 前期强控
    "stun_strike": dict(name="震慑一击", mp=12, kind="dmg", value=10, ail=("stun", 1),
                        desc="消耗12蓝, 造成 10+攻击 伤害并眩晕敌人一回合"),
    "frost_lock":  dict(name="寒冰禁锢", mp=14, kind="dmg", value=14, ail=("freeze", 3),
                        desc="消耗14蓝, 造成 14+攻击 伤害并立即冰冻敌人一回合"),
    # 中期辅助
    "heal":      dict(name="治疗术", mp=12, kind="heal", value=35,
                      desc="消耗12蓝, 回复 35 生命"),
    "inspire":   dict(name="鼓舞号令", mp=16, kind="aid", value=25, block=12,
                      desc="消耗16蓝, 回复 25 生命并获得 12 格挡"),
    # 后期百分比终结技
    "execute":     dict(name="处决",   mp=22, kind="execute", value=20,
                        desc="消耗22蓝, 无视格挡造成敌人最大生命 20% 的伤害"),
    "execute_big": dict(name="终极处决", mp=34, kind="execute", value=35,
                        desc="消耗34蓝, 无视格挡造成敌人最大生命 35% 的伤害"),
    # ----- 武器技能 -----
    "cleave":    dict(name="顺劈斩", mp=8,  kind="dmg", value=12,
                      desc="铁剑技能, 消耗8蓝, 造成 12+攻击 伤害"),
    "whirlwind": dict(name="旋风斩", mp=12, kind="dmg", value=20,
                      desc="战斧技能, 消耗12蓝, 造成 20+攻击 伤害"),
    "fireball":  dict(name="火球术", mp=12, kind="dmg", value=26,
                      desc="法杖技能, 消耗12蓝, 造成 26+攻击 伤害"),
    "quake":     dict(name="大地震击", mp=18, kind="pierce", value=36,
                      desc="战锤技能, 消耗18蓝, 无视格挡造成 36+攻击 伤害"),
    # ----- 匕首技能 (连击, 耗蓝少; 每次命中都附加部分攻击力) -----
    "double_stab": dict(name="连刺", mp=5, kind="combo", hits=2, value=8,
                        desc="匕首技能, 消耗5蓝, 连刺2次, 每次命中附带攻击力"),
    "venom_stab":  dict(name="淬毒连击", mp=6, kind="combo", hits=3, value=8,
                        desc="匕首技能, 消耗6蓝, 三连击, 每次命中附带攻击力"),
    "assassinate": dict(name="终结连击", mp=7, kind="combo", hits=4, value=9,
                        desc="匕首技能, 消耗7蓝, 四连击, 每次命中附带攻击力"),
    # ----- 长矛技能 (连突, 攻击高, 附带攻击力) -----
    "spear_thrust": dict(name="突刺连击", mp=6, kind="combo", hits=2, value=11,
                         desc="长矛技能, 消耗6蓝, 突刺2次, 每次命中附带攻击力"),
    "spear_storm":  dict(name="龙枪连突", mp=8, kind="combo", hits=3, value=11,
                         desc="长矛技能, 消耗8蓝, 三连突, 每次命中附带攻击力"),
    "gungnir_bolt": dict(name="永恒贯穿", mp=30, kind="pierce", value=48, cooldown=2,
                         desc="神器技能, 消耗30蓝, 无视格挡造成高额伤害并附带攻击力, 两回合一次"),
    # ----- 重剑技能 (耗蓝大, 两回合一次) -----
    "power_swing":    dict(name="重斩", mp=20, kind="dmg", value=30, cooldown=2,
                           desc="重剑技能, 消耗20蓝, 造成 30+攻击 伤害, 两回合一次"),
    "colossal_cleave": dict(name="巨剑横扫", mp=28, kind="pierce", value=40, cooldown=2,
                            desc="重剑技能, 消耗28蓝, 无视格挡 40+攻击 伤害, 两回合一次"),
    "rend_earth":     dict(name="裂地斩", mp=35, kind="pierce", value=55, cooldown=2,
                           desc="重剑技能, 消耗35蓝, 无视格挡 55+攻击 伤害, 两回合一次"),
    # ----- 神器技能 (神器专属) -----
    "titan_quake":    dict(name="大地崩裂", mp=30, kind="pierce", value=60, cooldown=2,
                           desc="神器技能, 消耗30蓝, 无视格挡 60+攻击 伤害, 两回合一次"),
    "world_cleave":   dict(name="裂地灭世", mp=40, kind="pierce", value=75, cooldown=2,
                           desc="神器技能, 消耗40蓝, 无视格挡 75+攻击 伤害, 两回合一次"),
    "shadow_assassinate": dict(name="暗影连刺", mp=10, kind="combo", hits=5, value=10,
                               desc="神器技能, 消耗10蓝, 暗影五连击, 每次命中附带攻击力"),
    "storm_hammer":   dict(name="天雷崩落", mp=34, kind="pierce", value=66, cooldown=2,
                           desc="神器技能, 消耗34蓝, 无视格挡 66+攻击 伤害, 两回合一次"),
    "shadow_dance":   dict(name="冥河影袭", mp=12, kind="combo", hits=6, value=10,
                           desc="神器技能, 消耗12蓝, 六段影袭, 每次命中附带攻击力"),
    # ----- 新增 tier4 异常武器技能 -----
    "blood_stab":    dict(name="血刃连刺", mp=7, kind="combo", hits=4, value=9,
                          desc="血刃技能, 消耗7蓝, 四连击, 每次命中附带攻击力并令敌人流血"),
    "flame_slash":   dict(name="烈焰斩", mp=24, kind="dmg", value=34, cooldown=2,
                          desc="烈焰之刃技能, 消耗24蓝, 造成 34+攻击 伤害并燃烧敌人, 两回合一次"),
    "frost_slash":   dict(name="寒霜斩", mp=20, kind="dmg", value=30,
                          desc="冰霜之刃技能, 消耗20蓝, 造成 30+攻击 伤害并累积寒气"),
    "toxic_stab":    dict(name="剧毒连刺", mp=8, kind="combo", hits=4, value=8,
                          desc="剧毒之刃技能, 消耗8蓝, 四连击, 每次命中附带攻击力并使敌人中毒"),
    # ----- 超神器技能 (北欧神话武器) -----
    "mjolnir_bolt":   dict(name="雷神之怒", mp=26, kind="pierce", value=130, cooldown=2,
                           empowered="burn",
                           desc="妙尔尼尔技能一, 消耗26蓝, 无视格挡 130+攻击 伤害并燃烧敌人. 对燃烧目标伤害+50%. 直接眩晕对手, 两回合一次"),
    "mjolnir_judgement": dict(name="雷霆审判", mp=32, kind="pierce", value=90, cooldown=2,
                              desc="妙尔尼尔技能二, 消耗32蓝, 无视格挡 90+攻击 伤害. 目标上回合处于眩晕状态时造成巨额伤害(6倍), 两回合一次"),
    "tyrfing_curse":  dict(name="提尔锋之咒", mp=24, kind="pierce", value=125, cooldown=2,
                           empowered="bleed",
                           desc="提尔锋技能, 消耗24蓝, 无视格挡 125+攻击 伤害并给双方上大量流血. 对流血目标伤害+50%. 之后被攻击时给敌人上等量流血, 两回合一次"),
    "laevateinn_brand": dict(name="烈焰烙印", mp=20, kind="pierce", value=95, cooldown=2,
                             empowered="burn",
                             desc="莱瓦汀技能一, 消耗20蓝, 无视格挡 95+攻击 伤害并给对方上巨额永久烧伤(每回合自动扩大30层, 攻击时结算并再扩大20层). 对燃烧目标伤害+50%, 两回合一次"),
    "laevateinn_detonate": dict(name="焚天引爆", mp=12, kind="detonate_burn", value=0,
                                desc="莱瓦汀技能二, 消耗12蓝, 引爆敌人身上所有永久烧伤, 每层造成 3 点伤害并清空"),
    "dainsleif_dance": dict(name="索命连刺", mp=12, kind="combo", hits=7, value=13,
                            empowered="perm_poison",
                            desc="达因斯莱夫技能, 消耗12蓝, 七连击, 每段命中附带当前永久毒伤层数伤害并使敌人永久中毒. 对中毒目标伤害+50%. 使用3次技能后获得额外回合"),
    # ----- 副手武器技能 -----
    "offhand_flame":  dict(name="灼热符文", mp=10, kind="amplify",
                           desc="副手·烈焰符主动, 消耗10蓝, 使敌人燃烧及永久燃烧层数×1.5 并立即结算一次燃烧伤害"),
    "offhand_frost":  dict(name="寒霜符文", mp=9,  kind="dmg", value=12,
                           desc="副手·冰霜符技能, 消耗9蓝, 造成 12+攻击 伤害并累积寒气"),
    "offhand_venom":  dict(name="剧毒符文", mp=9,  kind="amplify",
                           desc="副手·剧毒符主动, 消耗9蓝, 使敌人中毒及永久毒伤层数×1.5 并立即结算一次中毒伤害"),
    "offhand_blood":  dict(name="血祭", mp=10, kind="amplify",
                           desc="副手·血圣杯主动, 消耗10蓝, 使敌人流血层数×1.5 并立即结算一次流血伤害"),
    "offhand_warhorn": dict(name="战号齐鸣", mp=8, kind="buff_atk", value=4, atk_mult=4.0, duration=2,
                            desc="副手·战号主动, 消耗8蓝, 攻击×4 持续两回合"),
}

# 等级解锁: level -> 基础技能id (前期强控 / 中期辅助 / 后期百分比终结技)
LVL_SKILLS = {
    1: ["attack", "defend"],
    2: ["stun_strike"],      # 前期强控
    4: ["frost_lock"],       # 前期强控
    6: ["heal"],             # 中期辅助
    8: ["inspire"],          # 中期辅助
    10: ["execute"],         # 后期百分比终结技 (20%)
    15: ["execute_big"],     # 后期百分比终结技 (35%)
}

# ============================================================
# 数据: 饰品
# ============================================================
# 饰品: 提升 攻击/生命/蓝量; 部分带被动. 被动复用武器被动 id + 新增.
TRINKET_LIB = {
    "power_ring": dict(
        name="力量戒指", tier=1, atk=3, hp=0, mp=0, passive="",
        desc="攻击+3",
        art=["  ▄▄",
             " ████",
             "  ██"]),
    "vital_amulet": dict(
        name="生命护符", tier=1, atk=0, hp=25, mp=0, passive="",
        desc="生命+25",
        art=["  ██",
             " ████",
             "  ██"]),
    "mana_orb": dict(
        name="魔力宝珠", tier=1, atk=0, hp=0, mp=20, passive="",
        desc="蓝量+20",
        art=["  ╭╮",
             " (oo)",
             "  ╰╯"]),
    "swift_band": dict(
        name="迅捷手环", tier=2, atk=0, hp=0, mp=0, passive="mana_regen",
        desc="每回合回复2蓝",
        art=[" ○○",
             "████",
             " ○○"]),
    "guard_charm": dict(
        name="守护护符", tier=2, atk=0, hp=10, mp=0, passive="guard_start",
        desc="战斗开始获得4点格挡, 生命+10",
        art=[" ╭─╮",
             " │◆│",
             " ╰─╯"]),
    "lucky_clover": dict(
        name="幸运四叶草", tier=2, atk=0, hp=0, mp=0, passive="coin_bonus",
        desc="获得的金币 +25%",
        art=["  ✿",
             " ✿✿",
             "  ✿"]),
    # ----- Boss 专属饰品 -----
    "dragon_amulet": dict(
        name="龙鳞护符", tier=3, atk=5, hp=30, mp=5, passive="guard_start",
        desc="远古巨龙掉落的护符, 攻击+5 生命+30 蓝量+5. 战斗开始获得4格挡",
        art=["  ▄▄▄",
             " █🐲█",
             "  ███"]),
    "lich_ring": dict(
        name="亡魂戒指", tier=3, atk=5, hp=5, mp=25, passive="mana_regen",
        desc="巫妖王掉落的戒指, 攻击+5 生命+5 蓝量+25. 每回合回复2蓝",
        art=["  ▄▄▄",
             " █💀█",
             "  ███"]),
    # ----- 神灵护身符 (仅能合成, 被击败后半血复活一次) -----
    "divine_amulet": dict(
        name="神灵护身符", tier=3, atk=3, hp=25, mp=0, passive="divine_revive",
        desc="以神灵碎片与秘银熔铸的护符, 被击败后以半血复活一次. 攻击+3 生命+25",
        art=["  ╭─╮",
             " │🌟│",
             "  ╰─╯"]),
    # ----- 新生护符 (仅能合成, 开启第四层神界的关键) -----
    "reborn_amulet": dict(
        name="新生护符", tier=4, atk=6, hp=40, mp=20, passive="divine_revive",
        desc="以异界旋涡与神灵碎片熔铸的护符, 蕴含新生之力. 攻击+6 生命+40 蓝量+20. 被击败后以半血复活一次",
        art=["  ╭─╮",
             " │🌀│",
             "  ╰─╯"]),
}

# 被动效果名
PASSIVE_NAME = {
    "mana_regen": "每回合回复2蓝",
    "strong_body": "生命力强健",
    "guard_start": "战斗开始获得4格挡",
    "coin_bonus": "获得金币+25%",
    "divine_revive": "被击败后以半血复活一次",
}

# ============================================================
# 数据: 副手武器 (新装备栏)
# ============================================================
# 副手武器: 提供技能; 其属性 (攻击/生命/蓝量) 以 1/3 计入角色 (取整).
# 从商店/掉落可获得; 副手武器能造成异常时, 其技能也会附加异常.
OFFHAND_LIB = {
    "offhand_flame": dict(
        name="烈焰符", atk=12, hp=6, mp=10, skill="offhand_flame", ail=("burn", 1),
        passive="offhand_burn",
        desc="铭刻火焰符文的副手护符, 提供技能【灼热符文】. 被动: 每次攻击附加燃烧5层; 主动: 燃烧(含永久)×1.5 并立即结算. 属性仅以1/3计入"),
    "offhand_frost": dict(
        name="冰霜符", atk=10, hp=8, mp=12, skill="offhand_frost", ail=("freeze", 1),
        desc="铭刻寒霜符文的副手护符, 提供技能【寒霜符文】. 属性仅以1/3计入"),
    "offhand_venom": dict(
        name="剧毒符", atk=11, hp=4, mp=14, skill="offhand_venom", ail=("poison", 2),
        passive="offhand_poison",
        desc="铭刻剧毒符文的副手护符, 提供技能【剧毒符文】. 被动: 每次攻击附加中毒5层; 主动: 中毒(含永久)×1.5 并立即结算. 属性仅以1/3计入"),
    "offhand_blood": dict(
        name="血圣杯", atk=13, hp=12, mp=8, skill="offhand_blood", ail=("bleed", 2),
        passive="offhand_bleed",
        desc="盛满鲜血的圣杯, 提供技能【血祭】. 被动: 每次攻击附加流血5层; 主动: 流血×1.5 并立即结算. 属性仅以1/3计入"),
    "offhand_warhorn": dict(
        name="战号", atk=9, hp=10, mp=0, skill="offhand_warhorn", ail=None,
        passive="offhand_warhorn",
        desc="激励士气的战斗号角, 提供技能【战号齐鸣】. 被动: 技能伤害×1.1; 主动: 攻击×4 持续两回合. 属性仅以1/3计入"),
}

# 异常效果显示文本 (供图鉴/装备界面)
def ail_desc(ail):
    """异常效果显示文本. ail: (kind, stacks) 或 None."""
    if not ail:
        return ""
    kind, n = ail
    t = {"burn": "燃烧", "poison": "中毒", "bleed": "流血", "perm_poison": "永久毒伤",
         "freeze": "冰冻(累积3次)", "stun": "眩晕", "perm_burn": "永久烧伤"}[kind]
    return f"异常: {t}×{n}"

# ============================================================
# 数据: 材料 (用于高等级武器合成)
# ============================================================
# tier: 1 普通(小怪) / 2 中级(精英) / 3 高级(Boss专属)
# 小怪掉 tier1, 精英掉 tier1-2, Boss 掉 tier1-3 + 专属材料
MATERIAL_LIB = {
    "iron":             dict(name="铁锭",       tier=1, icon="⛏",
                             desc="最基础的锻造材料"),
    "coal":             dict(name="煤炭",       tier=1, icon="⬛",
                             desc="锻造熔炉的燃料"),
    "bronze":           dict(name="青铜",       tier=1, icon="🟤",
                             desc="廉价而坚固的合金"),
    "fire_shard":       dict(name="火焰碎片",   tier=1, icon="🔥",
                             desc="蕴含火元素之力"),
    "water_shard":      dict(name="冰霜碎片",   tier=1, icon="❄",
                             desc="蕴含水元素之力"),
    "lightning_shard":  dict(name="雷电碎片",   tier=2, icon="⚡",
                             desc="蕴含雷元素之力"),
    "wind_shard":       dict(name="疾风碎片",   tier=2, icon="🌪",
                             desc="蕴含风元素之力"),
    "mithril":          dict(name="秘银",       tier=2, icon="✨",
                             desc="轻而坚固的稀有金属"),
    "divine_shard":     dict(name="神灵碎片",   tier=2, icon="🌟",
                             desc="蕴含神性之力的碎片 (神灵使者掉落)"),
    "steel":            dict(name="精钢",       tier=2, icon="⚙",
                             desc="经过反复锻打的坚韧钢材"),
    "obsidian":         dict(name="黑曜石",     tier=2, icon="🪨",
                             desc="火山岩凝成的尖锐结晶"),
    "shadow_shard":     dict(name="暗影碎片",   tier=3, icon="🌑",
                             desc="蕴含暗影之力, 精英/Boss掉落"),
    "dragon_scale":     dict(name="龙鳞",       tier=3, icon="🐲",
                             desc="远古巨龙掉落的鳞片 (Boss专属)"),
    "lich_soul":        dict(name="巫妖之魂",   tier=3, icon="💀",
                             desc="巫妖王凝结的灵魂 (Boss专属)"),
    "dragonbone":       dict(name="龙骨",       tier=3, icon="🦴",
                             desc="冥龙骸骨, 蕴含不朽之力 (冥界Boss掉落)"),
    "soul_ash":         dict(name="灵魂灰烬",   tier=3, icon="🕯",
                             desc="冥界亡魂燃尽的灰烬 (冥界精英/Boss掉落)"),
    "nether_core":      dict(name="幽冥核心",   tier=3, icon="🔮",
                             desc="冥界深处的能量核心 (冥界深处Boss掉落)"),
    "adamantite":       dict(name="坚钢",       tier=3, icon="💎",
                             desc="传说中最坚硬的金属 (锻造高级材料)"),
    "abyss_vortex":     dict(name="异界旋涡",   tier=3, icon="🌀",
                             desc="异界核心凝成的混沌旋涡, 蕴含新生之力 (离开异界获得)"),
}

# 各 tier 的材料 id 池 (供随机掉落)
MATERIAL_POOL = {
    1: ["iron", "coal", "bronze", "fire_shard", "water_shard"],
    2: ["lightning_shard", "wind_shard", "mithril", "steel", "obsidian"],
    3: ["shadow_shard", "dragonbone", "soul_ash", "adamantite"],
}

# ============================================================
# 数据: 合成配方 (神器 = 最高等武器 + Boss专属材料)
# ============================================================
# weapon: 作为原料消耗的最高等武器; mats: {material_id: 数量}
# 产出为该配方 key 对应的神器武器 (见 WEAPON_LIB)
CRAFT_LIB = {
    "god_hammer": dict(
        name="泰坦神锤",
        weapon="giant_hammer",
        mats={"dragon_scale": 1, "shadow_shard": 2, "iron": 2},
        desc="以巨人战锤为基, 熔入龙鳞与暗影之力, 铸成撼地神锤",
    ),
    "god_hammer2": dict(
        name="雷霆碎星锤",
        weapon="giant_hammer",
        mats={"lightning_shard": 3, "adamantite": 1, "soul_ash": 2},
        desc="以巨人战锤为基, 汇聚风暴之雷与灵魂之力, 锻出碎星之锤",
    ),
    "god_greatsword": dict(
        name="破灭重剑",
        weapon="war_greatsword",
        mats={"dragon_scale": 1, "mithril": 2, "iron": 3},
        desc="以战争巨剑为基, 融龙鳞与秘银, 锻出灭世神兵",
    ),
    "god_dagger": dict(
        name="深渊匕影",
        weapon="assassin_dagger",
        mats={"lich_soul": 1, "lightning_shard": 2, "shadow_shard": 2},
        desc="以刺客匕首为基, 淬巫妖之魂与雷电暗影, 凝出深渊匕影",
    ),
    "god_dagger2": dict(
        name="冥府毒牙",
        weapon="assassin_dagger",
        mats={"nether_core": 1, "soul_ash": 2, "obsidian": 3},
        desc="以刺客匕首为基, 浸冥河之毒与幽冥核心, 淬出冥府毒牙",
    ),
    "gungnir": dict(
        name="永恒之枪",
        weapon="steel_spear",
        mats={"divine_shard": 2, "dragonbone": 1},
        desc="以龙骨枪为基, 融入神灵碎片与冥界龙骨, 铸成必中之枪",
    ),
}

# ============================================================
# 数据: 超神器合成配方 (神器 + tier4异常武器 + 第三层掉落物)
# ============================================================
# artifact: 作为原料消耗的神器武器; weapon: 作为原料的 tier4 异常武器;
# mats: 第三层掉落物 (nether_core / soul_ash / dragonbone / abyss_vortex)
# 产出为该配方 key 对应的超神器 (见 WEAPON_LIB)
SUPER_ARTIFACT_LIB = {
    "super_mjolnir": dict(
        name="妙尔尼尔",
        artifact="god_hammer2",
        weapon="flame_blade",
        mats={"nether_core": 1, "soul_ash": 2},
        desc="以雷霆碎星锤为基, 熔入烈焰之刃与幽冥核心, 锻出雷神之锤·妙尔尼尔",
    ),
    "super_tyrfing": dict(
        name="提尔锋",
        artifact="god_greatsword",
        weapon="blood_dagger",
        mats={"soul_ash": 1, "dragonbone": 1},
        desc="以破灭重剑为基, 淬以血刃与灵魂灰烬, 铸成受诅咒的魔剑·提尔锋",
    ),
    "super_laevateinn": dict(
        name="莱瓦汀",
        artifact="gungnir",
        weapon="flame_blade",
        mats={"dragonbone": 1, "nether_core": 1},
        desc="以永恒之枪为基, 融烈焰之刃与冥界龙骨, 锻出烈焰魔杖·莱瓦汀",
    ),
    "super_dainsleif": dict(
        name="达因斯莱夫",
        artifact="god_dagger",
        weapon="toxic_blade",
        mats={"abyss_vortex": 1, "soul_ash": 1},
        desc="以深渊匕影为基, 淬剧毒之刃与异界旋涡, 铸成杀人魔剑·达因斯莱夫",
    ),
}

# ============================================================
# 数据: 饰品合成配方 (仅能通过合成获得, 不直接掉落/出售)
# ============================================================
# mats: {material_id: 数量}; 产出为该配方 key 对应的饰品 (见 TRINKET_LIB)
TRINKET_CRAFT_LIB = {
    "divine_amulet": dict(
        name="神灵护身符",
        mats={"divine_shard": 2, "mithril": 1},
        desc="以神灵碎片与秘银熔铸, 佩戴者被击败后以半血复活一次",
    ),
    "reborn_amulet": dict(
        name="新生护符",
        mats={"abyss_vortex": 1, "divine_shard": 1},
        desc="以异界旋涡与神灵碎片熔铸, 蕴含新生之力, 是踏入神界的钥匙",
    ),
}

# ============================================================
# 数据: 药水
# ============================================================
POTION_LIB = {
    "hp":     dict(name="治疗药水", desc="回复 30 生命", kind="heal", value=30),
    "mp":     dict(name="蓝量药水", desc="回复 50 蓝量", kind="mp", value=50),
    "atk":    dict(name="力量药水", desc="本场战斗攻击+5", kind="buff_atk", value=5),
    "big_hp": dict(name="大治疗药水", desc="回复 60 生命", kind="heal", value=60),
}

# ============================================================
# 数据: 职业 (闯关前选择, 提供初始增益)
# ============================================================
# atk: 攻击加成  hp: 生命加成(可为负)  mp: 蓝量加成
# block: 每场战斗开始获得的格挡  level_atk: 每次升级额外攻击
CLASS_LIB = {
    "warrior": dict(
        name="战士", icon="⚔",
        atk=3, hp=20, mp=0, block=0, level_atk=0,
        desc="攻守均衡的近战勇士",
    ),
    "paladin": dict(
        name="圣骑士", icon="🛡",
        atk=0, hp=40, mp=0, block=4, level_atk=0,
        desc="坚不可摧的神圣守护者",
    ),
    "berserker": dict(
        name="狂战士", icon="🔥",
        atk=10, hp=-10, mp=0, block=0, level_atk=2,
        desc="以血换伤的疯狂战士",
    ),
    "rune_warrior": dict(
        name="符文战士", icon="✨",
        atk=2, hp=0, mp=20, block=0, level_atk=0,
        desc="铭刻符文的魔剑士",
    ),
    "tester": dict(
        name="测试员", icon="🧪",
        atk=99999, hp=99999, mp=0, block=0, level_atk=0,
        desc="无敌的测试用职业, 秒杀一切",
    ),
    "tester_all": dict(
        name="测试员(全武器)", icon="🧪",
        atk=0, hp=999999, mp=0, block=0, level_atk=0,
        desc="全武器测试职业: 攻击无加成, 生命+999999, 初始等级20, 拥有全部超神器、新生护符与全副手武器",
    ),
}

# ============================================================
# 数据: 怪物
# ============================================================
MONSTER_ART = {
    "slime": [
        "................",
        ".....KKKKKK.....",
        "...KKGGGGGGKK...",
        "..KGGGGGGGGGGK..",
        ".KGGWWKGGGGGGGK.",
        ".KGGWWKGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        "..KGGGGGGGGGGK..",
        "..KGGGGGGGGGGK..",
        "...KGgggggggGK..",
        "...KGGgggGGGGK..",
        "....KKKKKKKK....",
        "................",
    ],
    "rat": [
        "................",
        "......KKKK......",
        "....KKNNNNKK....",
        "...KNNNNNNNNK...",
        "..KNNNWNNWNNNK..",
        "..KNNNWNNWNNNK..",
        "..KNKNNNNNNKNK..",
        "..KNNNNNNNNNNK..",
        "...KNNNKKNNNK...",
        "...KNnNNNNnNK...",
        "..KNNnNKKNnNNK..",
        "..KNNNNNNNNNNK..",
        "...KKKKKKKKKK...",
        "................",
        "................",
        "................",
    ],
    "skeleton": [
        "  .-.__.-.",
        "  | o  o |",
        "  |  ||  |",
        "  \\ \\/ /",
    ],
    "goblin": [
        "   ,---.",
        "  / o o \\",
        " (  \\ /  )",
        "  (  v  )",
    ],
    "wolf": [
        "   /\\_/\\",
        "  ( o.o )",
        "   >   <",
        "  ( █████ )",
    ],
    "ogre": [
        "   ._____.",
        "  /  o o  \\",
        "  |    |   |",
        "   \\_____/",
    ],
    "golem": [
        "   .#####.",
        "  .# o o #.",
        "  #   |   #",
        "  ########",
    ],
    "knight": [
        "   __/\\___",
        "  |  o o  |",
        "  |   |   |",
        "  |  ███  |",
    ],
    "dragon": [
        "    /\\    /\\",
        "   /  \\__/  \\",
        "  /    ██    \\",
        " |  ████████  |",
    ],
    "lich": [
        "    .-~~~-.",
        "   | o   o |",
        "   |   |   |",
        "   |  \\_/  |",
    ],
    # ----- 冥界 (第二层) -----
    "ghost": [
        "   ( .  . )",
        "  (   |   )",
        "  (  \\_/  )",
        "   ~~|~~|~~",
    ],
    "banshee": [
        "   \\  o  /",
        "  --(   )--",
        "     | |",
        "    /   \\",
    ],
    "wraith": [
        "    \\  /",
        "  .--o--.",
        "  |  |  |",
        "   \\/ \\/",
    ],
    "deathspider": [
        "   /  \\  /  \\",
        "   \\  oo  /",
        "   /  oo  \\",
        "   \\  ||  /",
    ],
    "zombie": [
        "   o  .  o",
        "  /   |   \\",
        "   \\  |  /",
        "  (  |||  )",
    ],
    "reaper": [
        "    |\\  /|",
        "    | oo |",
        "     |  |",
        "    /|  |\\",
        "   /  \\/  \\",
    ],
    "hellhound": [
        "   /\\_/\\",
        "  ( o.o )",
        "   > vv <",
        "  ( ~~~~ )",
    ],
    "bone_giant": [
        "   .__|__.",
        "  |  o o  |",
        "  |   |   |",
        "  |  |||  |",
        "  \\_/\\_/\\_/",
    ],
    "hell_king": [
        "   /\\  |  /\\",
        "  /  \\ o /  \\",
        " |    | |    |",
        "  \\  /\\_/\\  /",
        "   \\/     \\/",
    ],
    # ----- 冥界深处 (第三层) -----
    "soul_eater": [
        "   ( o  o )",
        "  (   ||   )",
        "   \\  \\/  /",
        "    /\\/\\/\\",
    ],
    "void_demon": [
        "   .@@@@@.",
        "  @ o   o @",
        "  @   |   @",
        "   \\_____/",
        "   /\\   /\\",
    ],
    "abyss_ghoul": [
        "   o  .  o",
        "  (   |   )",
        "  (   |   )",
        "   \\/\\/\\/",
    ],
    "cursed_knight": [
        "   .-|||-.",
        "  | o   o |",
        "  |  ---  |",
        "  |  |||  |",
        "   \\_____/",
    ],
    "nether_imp": [
        "   \\   /",
        "    o o",
        "   > 0 <",
        "   /   \\",
    ],
    "dread_lord": [
        "   \\  .  /",
        "  --( o )--",
        "     | |",
        "    /   \\",
        "   /     \\",
    ],
    "abyss_wyrm": [
        "   ~~~~~~~",
        "   o  o  o",
        "    |    |",
        "   ~~~~~~~",
    ],
    "tormentor": [
        "   .-ooo-.",
        "  | o   o |",
        "  |  \\ /  |",
        "   \\_____/",
        "   /\\   /\\",
    ],
    "nether_overlord": [
        "   /\\  @  /\\",
        "  /  \\ o /  \\",
        " |    o o    |",
        "  \\  /   \\  /",
        "   \\/  |  \\/",
        "      / \\",
    ],
    # ----- 异界特殊精英 (两种) -----
    "void_mirror": [
        "    ◇◇◇",
        "   ◇ o o ◇",
        "   ◇  |  ◇",
        "    ◇◇◇",
        "   /\\   /\\",
    ],
    "abyss_devourer": [
        "   .@@@@@.",
        "  @ o   o @",
        "  @  --   @",
        "   \\/\\_\\/",
        "   /     \\",
    ],
    # ----- 神灵使者 (特殊小怪) -----
    "divine_messenger": [
        "   ✦   ✦",
        "    ◇◇◇",
        "   ◇ o o ◇",
        "   ◇  |  ◇",
        "    ◇▽◇",
    ],
    # ----- 神界 (第四层) -----
    "light_spirit": [
        "   ✦ ✦ ✦",
        "    ◇◇◇",
        "   ◇ o o ◇",
        "    ◇▽◇",
    ],
    "angel": [
        "   __/\\__",
        "  | o  o |",
        "   \\ == /",
        "    /\\/\\",
    ],
    "holy_knight": [
        "   __/\\___",
        "  |  o o  |",
        "  |   +   |",
        "  |  ███  |",
    ],
    "oracle": [
        "    ( . )",
        "  --( o )--",
        "     | |",
        "    /   \\",
    ],
    "celestial_warrior": [
        "   /\\   /\\",
        "  |  o o  |",
        "   \\  +  /",
        "    /||\\",
    ],
    "seraphim": [
        "  ✦ /\\ ✦",
        "  /  o o  \\",
        " |   |   |",
        "  \\  ▽  /",
    ],
    "judgement_knight": [
        "   __/\\___",
        "  |  o o  |",
        "  |   ⚖   |",
        "  |  ███  |",
        "   \\/ \\/",
    ],
    "temple_guardian": [
        "   .#####.",
        "  .# o o #.",
        "  #   +   #",
        "  ########",
        "   /\\ /\\",
    ],
    "supreme_god": [
        "    ✦  ✦",
        "  ◇ o o ◇",
        " ◇   |   ◇",
        "  ◇  ▽  ◇",
        "    ◇ ◇",
    ],
}

# 怪物: (hp, atk, acts, exp, gold_reward, art, desc)
# acts: 行动池, 战斗中随机选
# 按楼层分组: floor1=地表  floor2=冥界  floor3=冥界深处
FLOOR_MONSTERS = {
    1: {
        "normal": [
            dict(name="史莱姆", key="slime", hp=32,  atk=6,  acts=("attack",),
                 exp=40, gold=18, art=MONSTER_ART["slime"], desc="黏糊糊的低等魔物."),
            dict(name="大老鼠", key="rat", hp=28,  atk=7,  acts=("attack", "double"),
                 exp=42, gold=20, art=MONSTER_ART["rat"], desc="敏捷的啮齿魔物, 双爪扑击."),
            dict(name="骷髅兵", key="skeleton", hp=38, atk=6, acts=("attack", "defend"),
                 exp=45, gold=22, art=MONSTER_ART["skeleton"], desc="会格挡的不死士兵."),
            dict(name="哥布林", key="goblin", hp=42, atk=8, acts=("attack", "buff"),
                 exp=50, gold=25, art=MONSTER_ART["goblin"], desc="凶狠的小个子强盗, 会自我强化."),
            dict(name="座狼", key="wolf", hp=36,  atk=8,  acts=("attack", "double"),
                 exp=48, gold=24, art=MONSTER_ART["wolf"], desc="嗜血的野兽, 行动迅捷."),
        ],
        "elite": [
            dict(name="食人魔", key="ogre", hp=85,  atk=12, acts=("attack", "smash", "buff", "blood_rage"),
                 exp=140, gold=70, art=MONSTER_ART["ogre"], desc="力大无穷的精英, 重击可穿透格挡, 陷入狂暴时以伤换命."),
            dict(name="石魔像", key="golem", hp=100, atk=9,  acts=("defend", "attack", "smash", "stone_spikes"),
                 exp=150, gold=75, art=MONSTER_ART["golem"], desc="皮糙肉厚的精英, 常驻格挡, 能震裂大地施放地刺."),
            dict(name="黑骑士", key="knight", hp=90,  atk=11, acts=("attack", "defend", "smash", "charge"),
                 exp=155, gold=78, art=MONSTER_ART["knight"], desc="堕落骑士, 攻守兼备, 冲锋势不可挡."),
        ],
        "boss": [
            dict(name="远古巨龙", key="dragon", hp=170, atk=15, acts=("attack", "smash", "breath", "buff"),
                 exp=500, gold=200, art=MONSTER_ART["dragon"], desc="塔顶之主, 龙息灼烧万物."),
            dict(name="巫妖王", key="lich", hp=150, atk=13, acts=("attack", "double", "smash", "summon_buff"),
                 exp=500, gold=200, art=MONSTER_ART["lich"], desc="不朽的巫妖, 魔法阴冷彻骨."),
        ],
    },
    2: {
        "normal": [
            dict(name="幽灵", key="ghost", hp=46,  atk=9,  acts=("attack", "drain"),
                 exp=90, gold=40, art=MONSTER_ART["ghost"], desc="穿行于冥界的虚影, 能汲取生命."),
            dict(name="女妖", key="banshee", hp=42, atk=10, acts=("attack", "wail"),
                 exp=92, gold=42, art=MONSTER_ART["banshee"], desc="凄厉哀嚎, 令敌人心神溃散."),
            dict(name="怨灵", key="wraith", hp=50,  atk=9,  acts=("attack", "drain", "defend"),
                 exp=95, gold=44, art=MONSTER_ART["wraith"], desc="执念不散的怨魂, 攻守皆备."),
            dict(name="冥蛛", key="deathspider", hp=45, atk=11, acts=("attack", "double"),
                 exp=90, gold=40, art=MONSTER_ART["deathspider"], desc="八足织网的毒蛛, 连扑致残."),
            dict(name="僵尸", key="zombie", hp=60,  atk=9,  acts=("attack", "buff"),
                 exp=88, gold=38, art=MONSTER_ART["zombie"], desc="僵硬而不灭的行尸, 越战越勇."),
        ],
        "elite": [
            dict(name="死神", key="reaper", hp=150, atk=15, acts=("attack", "smash", "scythe", "soul_reap"),
                 exp=260, gold=130, art=MONSTER_ART["reaper"], desc="挥舞镰刀的死神, 收割灵魂并侵蚀你的战意."),
            dict(name="地狱犬", key="hellhound", hp=130, atk=14, acts=("attack", "double", "breath", "hell_bite"),
                 exp=250, gold=125, art=MONSTER_ART["hellhound"], desc="三首地狱凶犬, 爪牙与吐息皆致命, 地狱撕咬汲取魔力."),
            dict(name="骨巨魔", key="bone_giant", hp=180, atk=12, acts=("defend", "attack", "smash", "bone_pierce"),
                 exp=270, gold=135, art=MONSTER_ART["bone_giant"], desc="巨大骨骸堆砌的魔像, 坚不可摧, 骨刺突刺令人胆寒."),
        ],
        "boss": [
            dict(name="冥界之王", key="hell_king", hp=320, atk=19, acts=("attack", "smash", "scythe", "summon_buff"),
                 exp=950, gold=380, art=MONSTER_ART["hell_king"], desc="统治冥界的君主, 威压诸魂."),
        ],
    },
    3: {
        "normal": [
            dict(name="噬魂者", key="soul_eater", hp=70,  atk=13, acts=("attack", "drain", "buff"),
                 exp=170, gold=75, art=MONSTER_ART["soul_eater"], desc="吞噬灵魂的深渊魔物."),
            dict(name="虚空恶魔", key="void_demon", hp=64, atk=14, acts=("attack", "double", "smash"),
                 exp=175, gold=78, art=MONSTER_ART["void_demon"], desc="来自虚空裂隙的恶魔, 凶悍狂暴."),
            dict(name="深渊食尸鬼", key="abyss_ghoul", hp=82, atk=13, acts=("attack", "drain", "defend"),
                 exp=172, gold=76, art=MONSTER_ART["abyss_ghoul"], desc="沉沦于深渊的食尸鬼."),
            dict(name="诅咒骑士", key="cursed_knight", hp=72, atk=15, acts=("attack", "smash", "defend"),
                 exp=180, gold=80, art=MONSTER_ART["cursed_knight"], desc="身负永世诅咒的堕落骑士."),
            dict(name="炼狱小鬼", key="nether_imp", hp=60, atk=16, acts=("attack", "double", "buff"),
                 exp=168, gold=74, art=MONSTER_ART["nether_imp"], desc="炼狱中蹦跳的狡诈小鬼."),
        ],
        "elite": [
            dict(name="恐惧领主", key="dread_lord", hp=230, atk=20, acts=("attack", "smash", "scythe", "wail", "dread_gaze"),
                 exp=480, gold=240, art=MONSTER_ART["dread_lord"], desc="深渊中的恐惧之主, 恐惧凝视侵蚀你的战意."),
            dict(name="深渊巨虫", key="abyss_wyrm", hp=280, atk=17, acts=("defend", "attack", "breath", "smash", "acid_spit"),
                 exp=490, gold=245, art=MONSTER_ART["abyss_wyrm"], desc="盘踞深渊的巨型蠕虫, 腐液侵蚀你的防御."),
            dict(name="折磨者", key="tormentor", hp=240, atk=19, acts=("attack", "double", "smash", "buff", "blood_rage"),
                 exp=500, gold=250, art=MONSTER_ART["tormentor"], desc="以痛苦为乐的深渊刑罚者, 狂暴起来更加致命."),
        ],
        "boss": [
            dict(name="冥界主宰", key="nether_overlord", hp=520, atk=25, acts=("attack", "smash", "breath", "scythe", "summon_buff"),
                 exp=1800, gold=700, art=MONSTER_ART["nether_overlord"], desc="冥界深处的至高主宰, 万灵俯首."),
        ],
    },
    4: {
        "normal": [
            dict(name="光之精灵", key="light_spirit", hp=78,  atk=16, acts=("attack", "buff"),
                 exp=240, gold=110, art=MONSTER_ART["light_spirit"], desc="神界漂浮的圣光精灵, 会自我强化."),
            dict(name="天使", key="angel", hp=85,  atk=17, acts=("attack", "defend"),
                 exp=250, gold=115, art=MONSTER_ART["angel"], desc="神界下位的守护天使, 攻守有度."),
            dict(name="圣光骑士", key="holy_knight", hp=92,  atk=18, acts=("attack", "defend", "smash"),
                 exp=260, gold=120, art=MONSTER_ART["holy_knight"], desc="沐浴圣光的骑士, 圣剑无坚不摧."),
            dict(name="神谕者", key="oracle", hp=80, atk=17, acts=("attack", "wail"),
                 exp=255, gold=118, art=MONSTER_ART["oracle"], desc="传达神谕的先知, 其声摄人心魄."),
            dict(name="天界战士", key="celestial_warrior", hp=88, atk=19, acts=("attack", "double", "buff"),
                 exp=265, gold=122, art=MONSTER_ART["celestial_warrior"], desc="身经百战的天界勇士, 勇猛绝伦."),
        ],
        "elite": [
            dict(name="炽天使", key="seraphim", hp=340, atk=23, acts=("attack", "smash", "breath", "buff", "holy_smite"),
                 exp=620, gold=310, art=MONSTER_ART["seraphim"], desc="六翼炽天使, 圣焰焚尽一切, 圣光制裁治愈自身."),
            dict(name="神罚骑士", key="judgement_knight", hp=360, atk=24, acts=("attack", "defend", "scythe", "smash", "charge"),
                 exp=640, gold=320, art=MONSTER_ART["judgement_knight"], desc="执行神罚的骑士, 审判之镰无情, 冲锋势不可挡."),
            dict(name="圣殿守卫", key="temple_guardian", hp=390, atk=22, acts=("defend", "attack", "smash", "buff", "stone_spikes"),
                 exp=650, gold=325, art=MONSTER_ART["temple_guardian"], desc="镇守圣殿的巨像, 坚不可摧, 地刺贯穿护甲."),
        ],
        "boss": [
            dict(name="至高神", key="supreme_god", hp=680, atk=31, acts=("attack", "smash", "breath", "scythe", "summon_buff"),
                 exp=2600, gold=1100, art=MONSTER_ART["supreme_god"], desc="神界的至高主宰, 真最终Boss, 万神之巅."),
        ],
    },
}

# 兼容旧引用: 全部怪物库 + 一层怪物池 (供图鉴/旧逻辑使用)
def monster_lib():
    """返回全部怪物的合并字典 (key -> data)."""
    merged = {}
    for f, groups in FLOOR_MONSTERS.items():
        for kind, lst in groups.items():
            for m in lst:
                merged[m["key"]] = m
    return merged

MONSTER_POOL = {
    "normal": [m["key"] for m in FLOOR_MONSTERS[1]["normal"]],
    "elite":  [m["key"] for m in FLOOR_MONSTERS[1]["elite"]],
}

# 各楼层显示名称 (用于图鉴/状态)
FLOOR_NAME = {1: "地表之塔", 2: "冥界", 3: "冥界深处", 4: "神界"}

# ============================================================
# 异界特殊精英 (隐藏层第一节点必定为其中之一, 二选一)
# 数值与第二层相似, 机制特殊 (虚空镜像/异界吞噬者)
# ============================================================
ABYSS_ELITES = {
    "void_mirror": dict(
        name="虚空镜像", key="void_mirror", hp=160, atk=14,
        acts=("attack", "mirror", "split", "smash"),
        exp=300, gold=150, art=MONSTER_ART["void_mirror"],
        desc="异界的诡秘造物, 会折射你的攻击并分裂幻影.", special=True,
    ),
    "abyss_devourer": dict(
        name="异界吞噬者", key="abyss_devourer", hp=180, atk=13,
        acts=("attack", "mana_drain", "devour", "smash"),
        exp=320, gold=160, art=MONSTER_ART["abyss_devourer"],
        desc="潜伏异界的贪婪之物, 吸噬魔力与生命.", special=True,
    ),
}

# ============================================================
# 异界隐藏层地图生成 (路线 1,3,2, 无垂直通路)
# ============================================================
# 隐藏层结构: 4 个阶段, 节点数分别为 1,3,2,1
#   阶段1: 特殊精英怪 (异界主题, 二选一)
#   阶段2: 3 个节点 (小怪/精英/宝藏/事件 混合)
#   阶段3: 2 个节点, 必定为商店 (最后两个节点)
#   阶段4: 1 个节点, 异界核心, 到达即返回主世界并获得异界旋涡
ABYSS_STAGE_NODES = [1, 3, 2, 1]
ABYSS_STAGE_KINDS = [["abyss_elite"],
                     ["monster", "treasure", "event"],
                     ["shop", "shop"],
                     ["abyss_core"]]


def generate_abyss_map(rng):
    """生成异界隐藏层地图.
    返回 (nodes, edges, ordered):
      nodes: dict node_id -> kind; node id 用 (stage, index)
      edges: list of (from, to)
      ordered: 布局顺序
    隐藏层为 1,3,2,1 四阶段, 无垂直通路, 阶段4 为异界核心.
    """
    nodes = {}
    for s, kinds in enumerate(ABYSS_STAGE_KINDS):
        ks = list(kinds)
        if s > 0:
            rng.shuffle(ks)
        for i, k in enumerate(ks):
            nodes[(s, i)] = k
    edges = []
    # 阶段间完全连通 (隐藏层规模小, 保证顺畅推进)
    for s in range(len(ABYSS_STAGE_KINDS) - 1):
        cur = [(s, i) for i in range(len(ABYSS_STAGE_KINDS[s]))]
        nxt = [(s + 1, i) for i in range(len(ABYSS_STAGE_KINDS[s + 1]))]
        for src in cur:
            for t in nxt:
                if (src, t) not in edges:
                    edges.append((src, t))
    ordered = []
    for s in range(len(ABYSS_STAGE_KINDS)):
        ordered.extend((s, i) for i in range(len(ABYSS_STAGE_KINDS[s])))
    return nodes, edges, ordered

# ============================================================
# 地图生成 (一层): 7阶段分层 DAG, 节点不完全连通
# 精英/商店分布在阶段5-7, 且可多路径到达
# ============================================================
# 阶段节点数 (不含起点与 boss 终点)
# 节点类型计数: 小怪13 事件5 宝藏3 精英4 商店3 铁匠铺3 异界1  (共32, 4×8)
# 分配到 8 个阶段, 每阶段 4 节点 (4行8列):
#   阶段1: 小怪+事件+小怪+宝藏
#   阶段2: 小怪+小怪+事件+宝藏
#   阶段3: 小怪+精英+小怪+事件
#   阶段4: 小怪+小怪+铁匠铺+商店
#   阶段5: 小怪+精英+小怪+异界
#   阶段6: 小怪+事件+商店+铁匠铺
#   阶段7: 精英+小怪+铁匠铺+事件
#   阶段8: 精英+小怪+宝藏+商店
STAGE_NODES = [4, 4, 4, 4, 4, 4, 4, 4]
STAGE_KINDS = [["monster", "event", "monster", "treasure"],
               ["monster", "monster", "event", "treasure"],
               ["monster", "elite", "monster", "event"],
               ["monster", "monster", "blacksmith", "shop"],
               ["monster", "elite", "monster", "abyss"],
               ["monster", "event", "shop", "blacksmith"],
               ["elite", "monster", "blacksmith", "event"],
               ["elite", "monster", "treasure", "shop"]]


def generate_map(rng):
    """生成一层的主地图结构 (4×8).
    返回 (nodes, edges, ordered, vertical):
      nodes: dict node_id -> kind; node id 用 (stage, index) 表示, 起点为 start, 终点为 boss
      edges: list of (from_node_id, to_node_id)   (水平前进连线)
      ordered: 布局顺序的节点 id 列表
      vertical: 垂直通路边集合 (同一阶段相邻行的收费通道), 元素为 (a, b)
    连接规则:
      - 营地延伸4条路到阶段1; 阶段间保证可达, 连接数量约为原来一半 (稀疏地图)
      - 所有连线两端节点的竖向距离不超过1 (连线不会斜跨过远)
      - 精英/商店/铁匠铺/异界节点从上一阶段相邻节点连入, 保留多路径可达
      - 约70%的节点生成一条垂直通路 (连到正上方或正下方), 走垂直通路需支付金币
      - 异界(abyss)节点为进入隐藏层的入口, 本身不提供垂直通路
    """
    nodes = {}          # (stage,index) -> kind
    nodes["start"] = "start"
    for s, kinds in enumerate(STAGE_KINDS):
        # 阶段内打乱类型顺序, 让每次地图略有不同
        ks = list(kinds)
        rng.shuffle(ks)
        for i, k in enumerate(ks):
            nodes[(s, i)] = k
    # boss 终点
    total_stages = len(STAGE_KINDS)
    boss_id = "boss"
    nodes[boss_id] = "boss"

    # 将约 1/3 的小怪节点替换为「神灵使者」节点
    monster_ids = [nid for nid, k in nodes.items() if k == "monster"]
    rng.shuffle(monster_ids)
    divine_count = len(monster_ids) // 3
    for nid in monster_ids[:divine_count]:
        nodes[nid] = "divine"

    edges = []          # list of (src, dst), 水平前进连线
    vertical = set()    # 垂直通路 (同阶段相邻行), 走此通道需付费

    def stage_children(s):
        """第 s 阶段的节点 id 列表."""
        return [(s, i) for i in range(len(STAGE_KINDS[s]))]

    # 营地 -> 阶段1 所有节点 (延伸 4 条路)
    for c in stage_children(0):
        edges.append(("start", c))

    # 阶段 i -> 阶段 i+1: 减少连接 (约为原来一半), 且连线两端节点竖向距离≤1
    for s in range(total_stages - 1):
        cur = stage_children(s)
        nxt = stage_children(s + 1)
        # 保证下一阶段每个节点至少一个入度 (可达), 且竖向距离≤1
        for t in nxt:
            ti = t[1]
            near = [src for src in cur if abs(src[1] - ti) <= 1]
            if near:
                src = rng.choice(near)
                if (src, t) not in edges:
                    edges.append((src, t))
        # 精英/商店/铁匠铺/异界: 上一阶段竖向距离≤1的节点连入, 保留多路径可达
        for t in nxt:
            if nodes[t] in ("elite", "shop", "blacksmith", "abyss"):
                ti = t[1]
                for src in cur:
                    if abs(src[1] - ti) <= 1:
                        if (src, t) not in edges:
                            edges.append((src, t))

    # 最后阶段 -> boss
    for c in stage_children(total_stages - 1):
        edges.append((c, boss_id))

    # 垂直通路: 精确控制约70%的节点 (非异界入口) 拥有垂直通路
    candidate = []
    for s in range(total_stages):
        n = len(STAGE_KINDS[s])
        for i in range(n):
            nid = (s, i)
            if nodes[nid] == "abyss":
                continue  # 异界入口不提供垂直通路
            candidate.append(nid)
    rng.shuffle(candidate)
    target = int(len(candidate) * 0.7)     # 目标: 约70%的节点有垂直通路
    covered = set()                         # 已有垂直通路的节点
    for nid in candidate:
        if len(covered) >= target:
            break
        if nid in covered:
            continue
        s, i = nid
        n = len(STAGE_KINDS[s])
        neighbors = []
        if i > 0:
            neighbors.append((s, i - 1))
        if i < n - 1:
            neighbors.append((s, i + 1))
        if not neighbors:
            continue
        other = rng.choice(neighbors)
        vertical.add(tuple(sorted((nid, other))))
        covered.add(nid)
        covered.add(other)

    # 记录节点总数/顺序便于布局
    ordered = ["start"]
    for s in range(total_stages):
        ordered.extend(stage_children(s))
    ordered.append(boss_id)
    return nodes, edges, ordered, vertical


# ============================================================
# 角色
# ============================================================
class Player:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.max_hp = 60
        self.hp = 60
        self.max_mp = 30
        self.mp = 30
        self.atk = 6            # 基础攻击
        self.weapon = "iron_sword"
        self.offhand = None      # 副手武器 (id 或 None)
        self.accessory = None   # 饰品 (id 或 None)
        self.gold = 40
        self.potions = ["hp", "hp", "mp"]
        self.bag = []           # 背包: 持有的武器 id 列表 (不含当前装备)
        self.offhands = []      # 副手栏: 持有的副手武器 id 列表 (不含当前装备)
        self.trinkets = []      # 饰品栏: 持有的饰品 id 列表 (不含当前装备)
        self.materials = {}     # 材料: {material_id: 数量} (用于合成)
        self.block = 0          # 战斗中格挡
        self.battle_atk_bonus = 0
        self.weapon_hp_bonus = 0   # 武器提供的生命上限加成
        self.weapon_mp_bonus = 0   # 武器提供的蓝量上限加成
        self.trinket_hp_bonus = 0  # 饰品提供的生命上限加成
        self.trinket_mp_bonus = 0  # 饰品提供的蓝量上限加成
        self.offhand_hp_bonus = 0  # 副手武器提供的生命上限加成 (1/3)
        self.offhand_mp_bonus = 0  # 副手武器提供的蓝量上限加成 (1/3)
        self.max_action = 15       # 行动力上限 (每层)
        self.action = 15           # 当前行动力
        self.player_class = None   # 职业 (CLASS_LIB 的 key)
        self.class_block = 0       # 职业提供的每场战斗初始格挡
        self.battle_atk_mult = 1.0        # 攻击倍率 (战号主动: ×4)
        self.battle_atk_mult_remaining = 0  # 攻击倍率剩余回合数
        self.all_skills = False       # 打靶模式: 解锁全部升级技能

    def apply_class(self, cid):
        """选择职业, 应用初始增益 (攻击/生命/蓝量/格挡)."""
        c = CLASS_LIB[cid]
        self.player_class = cid
        if c["atk"]:
            self.atk += c["atk"]
        if c["hp"]:
            self.max_hp = max(1, self.max_hp + c["hp"])
            self.hp = max(1, self.hp + c["hp"])
        if c["mp"]:
            self.max_mp = max(1, self.max_mp + c["mp"])
            self.mp = max(1, self.mp + c["mp"])
        if c["block"]:
            self.class_block = c["block"]
        # 测试员(全武器): 等级20, 初始获得所有超神器与新生护符
        if cid == "tester_all":
            for _ in range(19):   # 1级 -> 20级 (每级 生命+12 蓝量+8)
                self.level += 1
                self.max_hp += 12
                self.max_mp += 8
            self.hp = self.max_hp
            self.mp = self.max_mp
            for wid in SUPER_ARTIFACT_WEAPONS:
                self.add_weapon_to_bag(wid)
            self.add_trinket("reborn_amulet")
            for oid in OFFHAND_LIB:   # 全副手武器
                self.add_offhand_to_bag(oid)

    # ---- 饰品 ----
    @property
    def trinket_data(self):
        return TRINKET_LIB[self.accessory] if self.accessory else None

    def add_material(self, mid, n=1):
        """把 n 个材料放入背包."""
        if mid in MATERIAL_LIB and n > 0:
            self.materials[mid] = self.materials.get(mid, 0) + n
            return True
        return False

    def has_materials(self, mats):
        """mats: {mid: count} 是否全部足够."""
        for mid, cnt in mats.items():
            if self.materials.get(mid, 0) < cnt:
                return False
        return True

    def consume_materials(self, mats):
        """消耗一组材料 (假设已用 has_materials 校验)."""
        for mid, cnt in mats.items():
            self.materials[mid] = max(0, self.materials.get(mid, 0) - cnt)
            if self.materials[mid] == 0:
                del self.materials[mid]

    def add_trinket(self, tid):
        """把一件饰品放入饰品栏 (若非当前装备且未持有)."""
        if tid == self.accessory or tid in self.trinkets:
            return False
        self.trinkets.append(tid)
        return True

    def equip_trinket(self, tid):
        """更换饰品, 调整饰品带来的生命/蓝量上限加成. 旧饰品回到饰品栏."""
        if tid is None or tid == self.accessory:
            return self.accessory
        # 目标饰品须为持有 (从饰品栏取出装备)
        if tid in self.trinkets:
            self.trinkets.remove(tid)
        # 旧饰品放回饰品栏
        old = self.accessory
        if old is not None and old not in self.trinkets:
            self.trinkets.append(old)
        old_hp, old_mp = self.trinket_hp_bonus, self.trinket_mp_bonus
        new_hp = TRINKET_LIB[tid]["hp"]
        new_mp = TRINKET_LIB[tid]["mp"]
        self.accessory = tid
        self.trinket_hp_bonus, self.trinket_mp_bonus = new_hp, new_mp
        d_hp, d_mp = new_hp - old_hp, new_mp - old_mp
        if d_hp:
            self.max_hp = max(20, self.max_hp + d_hp)
            self.hp = min(self.max_hp, self.hp + max(0, d_hp))
        if d_mp:
            self.max_mp = max(10, self.max_mp + d_mp)
            self.mp = min(self.max_mp, self.mp + max(0, d_mp))
        return tid

    def equip_weapon(self, wid):
        """更换武器, 调整由武器带来的生命/蓝量上限加成."""
        old_hp, old_mp = self.weapon_hp_bonus, self.weapon_mp_bonus
        new_hp = WEAPON_LIB[wid]["hp"]
        new_mp = WEAPON_LIB[wid]["mp"]
        self.weapon = wid
        self.weapon_hp_bonus, self.weapon_mp_bonus = new_hp, new_mp
        d_hp, d_mp = new_hp - old_hp, new_mp - old_mp
        if d_hp:
            self.max_hp = max(20, self.max_hp + d_hp)
            self.hp = min(self.max_hp, self.hp + max(0, d_hp))
        if d_mp:
            self.max_mp = max(10, self.max_mp + d_mp)
            self.mp = min(self.max_mp, self.mp + max(0, d_mp))
        return wid

    # ---- 副手武器 ----
    @property
    def offhand_data(self):
        oid = getattr(self, "offhand", None)
        return OFFHAND_LIB[oid] if oid else None

    @property
    def offhand_skill(self):
        return self.offhand_data["skill"] if self.offhand_data else None

    def offhand_atk(self):
        """副手武器攻击加成 (属性以 1/3 计入)."""
        return self.offhand_data["atk"] // 3 if self.offhand_data else 0

    def offhand_mp(self):
        return self.offhand_data["mp"] // 3 if self.offhand_data else 0

    def add_offhand_to_bag(self, oid):
        """把一件副手武器放入副手栏 (若非当前装备)."""
        if not hasattr(self, "offhands"):
            self.offhands = []
        if oid == getattr(self, "offhand", None):
            return False
        if oid not in self.offhands:
            self.offhands.append(oid)
        return True

    def equip_offhand(self, oid):
        """更换副手武器, 调整由副手带来的生命/蓝量上限加成 (1/3)."""
        old_hp, old_mp = self.offhand_hp_bonus, self.offhand_mp_bonus
        if oid:
            new_hp = OFFHAND_LIB[oid]["hp"] // 3
            new_mp = OFFHAND_LIB[oid]["mp"] // 3
        else:
            new_hp = new_mp = 0
        self.offhand = oid
        self.offhand_hp_bonus, self.offhand_mp_bonus = new_hp, new_mp
        d_hp, d_mp = new_hp - old_hp, new_mp - old_mp
        if d_hp:
            self.max_hp = max(20, self.max_hp + d_hp)
            self.hp = min(self.max_hp, self.hp + max(0, d_hp))
        if d_mp:
            self.max_mp = max(10, self.max_mp + d_mp)
            self.mp = min(self.max_mp, self.mp + max(0, d_mp))
        return oid

    def add_weapon_to_bag(self, wid):
        """把一把武器放入背包 (若非当前装备)."""
        if wid == self.weapon:
            return False
        self.bag.append(wid)
        return True

    def reward_gold(self, base):
        """获得金币 (幸运四叶草被动 +25%)."""
        m = 1.25 if "coin_bonus" in self.passives else 1.0
        g = int(base * m)
        self.gold += g
        return g

    # ---- 属性计算 (含武器/饰品/被动) ----
    @property
    def weapon_data(self):
        return WEAPON_LIB[self.weapon]

    @property
    def weapon_skill(self):
        return self.weapon_data["skill"]

    @property
    def weapon_skills(self):
        """当前武器提供的所有技能 id (支持多技能武器)."""
        w = self.weapon_data
        if w.get("skills"):
            return list(w["skills"])
        return [w["skill"]]

    def weapon_atk(self):
        return self.weapon_data["atk"]

    def trinket_atk(self):
        return self.trinket_data["atk"] if self.trinket_data else 0

    def trinket_mp(self):
        return self.trinket_data["mp"] if self.trinket_data else 0

    def total_atk(self):
        base = (self.atk + self.weapon_atk() + self.trinket_atk()
                + self.offhand_atk() + self.battle_atk_bonus)
        mult = getattr(self, "battle_atk_mult", 1.0)
        return int(base * mult) if mult != 1.0 else base

    @property
    def passives(self):
        p = []
        if self.weapon_data["passive"]:
            p.append(self.weapon_data["passive"])
        if self.trinket_data and self.trinket_data["passive"]:
            p.append(self.trinket_data["passive"])
        return p

    # ---- 经验 / 等级 ----
    def exp_needed(self):
        return 60 + (self.level - 1) * 50

    def gain_exp(self, amount):
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_needed():
            self.exp -= self.exp_needed()
            self.level += 1
            # 升级成长: 生命+12, 蓝量+8
            self.max_hp += 12
            self.max_mp += 8
            self.hp = self.max_hp
            self.mp = self.max_mp
            # 职业额外成长 (如狂战士每次升级额外攻击)
            cdata = CLASS_LIB.get(getattr(self, "player_class", None))
            if cdata and cdata.get("level_atk"):
                self.atk += cdata["level_atk"]
            leveled = True
        return leveled

    def unlocked_skills(self):
        """当前可用的技能 id 列表 (基础+主武器所有技能+副手). 打靶模式解锁全部升级技能."""
        ids = []
        for lv, sk in sorted(LVL_SKILLS.items()):
            if self.all_skills or self.level >= lv:
                ids.extend(sk)
        for ws in self.weapon_skills:
            if ws not in ids:
                ids.append(ws)
        oh = self.offhand_skill
        if oh and oh not in ids:
            ids.append(oh)
        return ids

    def skills_data(self):
        return [(sid, SKILL_LIB[sid]) for sid in self.unlocked_skills()]


# ============================================================
# 战斗
# ============================================================
class Enemy:
    def __init__(self, data):
        self.name = data["name"]
        self.key = data.get("key", "?")
        self.hp = data["hp"]
        self.max_hp = data["hp"]
        self.atk = data["atk"]
        self.acts = data["acts"]
        self.exp = data["exp"]
        self.gold = data["gold"]
        self.art = data["art"]
        self.desc = data["desc"]
        self.block = 0
        self.bonus_atk = 0
        self.last_hits = []   # 最近一次受击的各段伤害 (用于界面显示伤害数字)
        self.can_revive = False  # 神灵使者: 被击杀后半血复活一次
        self.revived = False     # 是否已复活过
        # 异常状态 (由武器附加)
        self.burn = 0        # 燃烧层数: 回合初造成 层数 伤害
        self.poison = 0      # 中毒层数: 回合初造成 层数 伤害
        self.bleed = 0       # 流血层数: 敌人攻击时额外受到 层数 伤害
        self.freeze = False  # 冰冻: 停止行动一回合
        self.cold = 0        # 寒冷累积 (冰冻类武器): 第3次冰冻
        self.stun = False    # 眩晕: 停止行动一回合 (妙尔尼尔, 与冰冻独立可共存)
        self.was_stunned = False  # 上回合是否处于眩晕状态 (雷霆审判巨额伤害触发条件)
        self.perm_burn = 0   # 永久烧伤层数 (莱瓦汀): 回合初伤害, 不参与毒火爆炸清除
        self.perm_poison = 0 # 永久毒伤层数 (达因斯莱夫): 回合初伤害, 不因引爆消失
        self.frozen_msg = "" # 冰冻时显示的文字

    @property
    def ail_text(self):
        """异常状态摘要 (供界面显示)."""
        parts = []
        if self.burn:
            parts.append(f"🔥{self.burn}")
        if self.perm_burn:
            parts.append(f"♨{self.perm_burn}")
        if self.poison:
            parts.append(f"☠{self.poison}")
        if self.perm_poison:
            parts.append(f"♨☠{self.perm_poison}")
        if self.bleed:
            parts.append(f"🩸{self.bleed}")
        if self.freeze:
            parts.append("❄冰冻")
        elif self.cold:
            parts.append(f"❄寒冷{self.cold}/3")
        if self.stun:
            parts.append("⚡眩晕")
        return "  ".join(parts)

    @property
    def alive(self):
        return self.hp > 0

    def total_atk(self):
        return self.atk + self.bonus_atk


class RpgCombat:
    """一次战斗. player 为持久 Player 对象 (战斗中改 hp/mp/block/battle_atk_bonus)."""
    def __init__(self, player, enemy, rng):
        self.player = player
        self.enemy = enemy
        self.rng = rng
        self.log = []
        # 战斗开始重置临时状态
        player.block = 0
        player.battle_atk_bonus = 0
        player.battle_atk_mult = 1.0
        player.battle_atk_mult_remaining = 0
        # 职业提供的每场战斗初始格挡 (如圣骑士 +4)
        player.block += getattr(player, "class_block", 0)
        # 技能冷却: {sid: 剩余冷却回合}; 0 表示可用
        self.skill_cd = {}
        # ---- 超神器战斗状态 ----
        self.next_stun = False     # 妙尔尼尔: 用过技能后, 下次普攻眩晕并暴击
        self.tyrfing_counter = False  # 提尔锋: 用过技能后, 被攻击时给敌人上等量流血
        self.skill_uses = 0        # 达因斯莱夫: 技能使用计数 (3次触发额外回合)
        self.extra_turn = False    # 额外回合标记 (达因斯莱夫 3次技能后触发)
        # 被动: mana_regen 每回合回蓝
        self.regen_mp = 2 * player.passives.count("mana_regen")
        self.buff_cast_round = False  # 战号: 施放当回合不扣减攻击倍率持续时间
        # 被动: guard_start 战斗开始获得格挡
        if "guard_start" in player.passives:
            player.block += 4
        # 被动: strong_body 生命上限 (已通过武器/饰品直接加)
        # 被动: coin_bonus 在获得金币处处理

    def _damage(self, target_block, target_hp, amount):
        """扣血, 先扣格挡. 返回剩余格挡."""
        if target_block >= amount:
            return target_block - amount, target_hp
        remainder = amount - target_block
        return 0, target_hp - remainder

    def skill_ready(self, sid):
        """技能是否可用 (无冷却且蓝量足够)."""
        sk = SKILL_LIB[sid]
        cd = self.skill_cd.get(sid, 0)
        if cd > 0:
            return False
        return self.player.mp >= sk["mp"]

    def tick_cooldowns(self):
        """每经过一个回合, 技能冷却递减."""
        for sid in list(self.skill_cd):
            self.skill_cd[sid] = max(0, self.skill_cd[sid] - 1)

    # ---- 异常系统 ----
    def _apply_ailment(self, target, ail, msg_out):
        """对敌人施加异常状态. ail: (kind, stacks). 返回日志文本."""
        if not ail:
            return ""
        kind, stacks = ail
        if kind == "burn":
            target.burn += stacks
            return f"🔥 {target.name} 燃烧层数+{stacks}!"
        elif kind == "perm_burn":
            # 永久烧伤: 不随时间衰减, 不参与毒火爆炸清除
            target.perm_burn += stacks
            return f"♨ {target.name} 被烙上永久烧伤! (永久烧伤×{target.perm_burn})"
        elif kind == "poison":
            target.poison += stacks
            return f"☠ {target.name} 中毒层数+{stacks}!"
        elif kind == "perm_poison":
            target.perm_poison += stacks
            return f"☠ {target.name} 中上永久剧毒! (永久毒伤×{target.perm_poison})"
        elif kind == "bleed":
            target.bleed += stacks
            return f"🩸 {target.name} 流血层数+{stacks}!"
        elif kind == "stun":
            target.stun = True
            return f"⚡ {target.name} 被眩晕! (无法行动一回合)"
        elif kind == "freeze":
            # 累积制: 第一/二次使敌人寒冷, 第三次冰冻
            target.cold += stacks
            if target.cold >= 3:
                target.freeze = True
                target.cold = 0
                return f"❄ {target.name} 寒气积累, 被彻底冰冻! (无法行动一回合)"
            return f"❄ {target.name} 寒冷 ({target.cold}/3)"
        return ""

    # ---- 玩家行动 ----
    def player_attack(self):
        e = self.enemy
        dmg = self.player.total_atk()
        e.block, e.hp = self._damage(e.block, e.hp, dmg)
        e.last_hits = [dmg]
        msg = f"你挥动武器, 造成 {dmg} 伤害."
        wdata = self.player.weapon_data
        ail = wdata.get("ail")
        if ail and e.alive:
            msg += " " + self._apply_ailment(e, ail, None)
        # 副手被动: 每次攻击附加对应属性减益5层 (烈焰/剧毒/血圣杯)
        odata = self.player.offhand_data
        if odata and odata.get("passive") and e.alive:
            p_kind = odata["passive"]
            if p_kind == "offhand_burn":
                msg += " " + self._apply_ailment(e, ("burn", 5), None)
            elif p_kind == "offhand_poison":
                msg += " " + self._apply_ailment(e, ("poison", 5), None)
            elif p_kind == "offhand_bleed":
                msg += " " + self._apply_ailment(e, ("bleed", 5), None)
        # 大剑超神器 (提尔锋): 攻击流血敌人时吸血15并扩大流血层数 1.2 倍
        if self.player.weapon == "super_tyrfing" and e.alive and e.bleed > 0:
            self.player.hp = min(self.player.max_hp, self.player.hp + 15)
            old = e.bleed
            e.bleed = int(old * 1.2)
            msg += f" 🩸 提尔锋吸食敌血, 回复15生命, 流血层数 {old}→{e.bleed}!"
        return msg

    def player_defend(self):
        self.player.block += 8
        return f"你举盾防御, 获得 8 点格挡."

    def _has_ailment(self, kind):
        """敌人是否带有指定异常 (供对异常目标增伤)."""
        e = self.enemy
        if kind == "burn":
            return e.burn > 0 or e.perm_burn > 0
        if kind == "poison":
            return e.poison > 0
        if kind == "perm_poison":
            return e.perm_poison > 0
        if kind == "bleed":
            return e.bleed > 0
        if kind == "freeze":
            return e.freeze
        if kind == "stun":
            return e.stun
        return False

    def _after_skill(self, sid, msg):
        """技能施放后的通用处理 (达因斯莱夫额外回合)."""
        if sid == "dainsleif_dance":
            self.skill_uses += 1
            if self.skill_uses >= 3:
                self.extra_turn = True
                self.skill_uses = 0
                msg += " ⏳ 索命连刺三度出手! 获得额外回合!"
        return msg

    def _offhand_amplify(self, elem, skname):
        """副手主动: 使对方对应减益(含永久)×1.5 并立即结算一次. 返回日志文本."""
        e = self.enemy
        if elem == "burn":
            e.burn = int(e.burn * 1.5)
            e.perm_burn = int(e.perm_burn * 1.5)
            dmg = e.burn + e.perm_burn
            e.hp -= dmg
            e.last_hits = [dmg]
            return (f"你施展【{skname}】, 烈焰助燃! 燃烧×{e.burn} 永久燃烧×{e.perm_burn},"
                    f" 立即结算 {dmg} 伤害!")
        elif elem == "poison":
            e.poison = int(e.poison * 1.5)
            e.perm_poison = int(e.perm_poison * 1.5)
            dmg = e.poison + e.perm_poison
            e.hp -= dmg
            e.last_hits = [dmg]
            return (f"你施展【{skname}】, 剧毒扩散! 中毒×{e.poison} 永久毒伤×{e.perm_poison},"
                    f" 立即结算 {dmg} 伤害!")
        elif elem == "bleed":
            e.bleed = int(e.bleed * 1.5)
            dmg = e.bleed
            e.hp -= dmg
            e.last_hits = [dmg]
            return f"你施展【{skname}】, 鲜血沸腾! 流血×{e.bleed}, 立即结算 {dmg} 伤害!"
        elif elem == "freeze":
            e.cold = int(e.cold * 1.5)
            if e.cold >= 3:
                e.freeze = True
                e.cold = 0
                return f"你施展【{skname}】, 寒气急剧凝聚, 立即将敌人彻底冰冻!"
            return f"你施展【{skname}】, 寒气凝聚! (寒冷 {e.cold}/3)"
        return f"你施展【{skname}】."

    def player_skill(self, sid):
        sk = SKILL_LIB[sid]
        if self.player.mp < sk["mp"]:
            return "no_mp"
        if self.skill_cd.get(sid, 0) > 0:
            return "cooldown"
        # 莱瓦汀引爆: 无永久烧伤则不消耗蓝
        if sk["kind"] == "detonate_burn" and self.enemy.perm_burn <= 0:
            return "no_burn"
        self.player.mp -= sk["mp"]
        # 带冷却的技能: 施放后进入冷却
        if sk.get("cooldown"):
            self.skill_cd[sid] = sk["cooldown"]  # 用后需隔 cooldown-1 回合
        p = self.player
        e = self.enemy
        val = sk.get("value", 0)
        kind = sk["kind"]
        base_atk = p.total_atk()
        # 异常附加: 武器技能带武器异常, 副手技能带副手异常
        ail = None
        if sid in p.weapon_skills:
            ail = WEAPON_LIB[p.weapon].get("ail")
        elif sid == p.offhand_skill:
            ail = (OFFHAND_LIB[p.offhand].get("ail") if p.offhand else None)
        # 对异常目标增伤 (超神器): 目标带有对应异常时伤害+50%
        mult = 1.0
        empowered_txt = ""
        if sk.get("empowered") and self._has_ailment(sk["empowered"]):
            mult = 1.5
            empowered_txt = "命中要害! "
        # 妙尔尼尔二技能: 目标上回合处于眩晕状态时造成巨额伤害 (6倍)
        if sid == "mjolnir_judgement" and getattr(e, "was_stunned", False):
            mult = 6
            empowered_txt = "天雷滚滚, 对眩晕目标降下审判! "
        # 副手被动 (战号): 技能伤害×1.1
        sk_mult = 1.1 if (p.offhand_data and p.offhand_data.get("passive") == "offhand_warhorn") else 1.0
        def calc(v):
            return int((v + base_atk) * mult * sk_mult)
        if kind == "dmg":
            dmg = calc(val)
            e.block, e.hp = self._damage(e.block, e.hp, dmg)
            e.last_hits = [dmg]
            msg = f"你施展【{sk['name']}】,{empowered_txt}造成 {dmg} 伤害."
            if e.alive:
                if ail:
                    msg += " " + self._apply_ailment(e, ail, None)
                if sk.get("ail"):
                    msg += " " + self._apply_ailment(e, sk["ail"], None)
            return self._after_skill(sid, msg)
        elif kind == "amplify":
            # 副手主动: 使对方对应减益(含永久)×1.5 并立即结算一次
            elem = {"offhand_flame": "burn", "offhand_venom": "poison",
                    "offhand_blood": "bleed"}.get(sid, "burn")
            return self._after_skill(sid, self._offhand_amplify(elem, sk['name']))
        elif kind == "pierce":
            dmg = calc(val)
            e.hp -= dmg
            e.last_hits = [dmg]
            msg = f"你施展【{sk['name']}】,{empowered_txt}无视格挡造成 {dmg} 伤害!"
            # 超神器特殊机制
            if sid == "mjolnir_bolt":
                if e.alive:
                    msg += " " + self._apply_ailment(e, ("stun", 1), None)
                msg += " ⚡ 雷神之力轰顶, 直接眩晕对手!"
            elif sid == "mjolnir_judgement":
                if e.alive:
                    msg += " ⚡ 雷霆审判落下!"
            elif sid == "tyrfing_curse":
                self.tyrfing_counter = True
                if e.alive:
                    msg += " " + self._apply_ailment(e, ("bleed", 8), None)
                msg += " 🩸 诅咒蔓延, 之后被攻击时将反噬敌血!"
            elif sid == "laevateinn_brand":
                if e.alive:
                    msg += " " + self._apply_ailment(e, ("perm_burn", 30), None)
            if ail and e.alive:
                msg += " " + self._apply_ailment(e, ail, None)
            return self._after_skill(sid, msg)
        elif kind == "combo":
            # 连击: 多次命中, 每次命中附加部分攻击力
            total = 0
            hits_done = 0
            hit_list = []
            for _ in range(sk["hits"]):
                if not e.alive:
                    break
                per_hit = val + base_atk // 2
                if mult > 1.0:
                    per_hit = int(per_hit * mult)
                if sid == "dainsleif_dance":
                    per_hit += e.perm_poison  # 每段附加当前永久毒伤层数伤害
                e.block, e.hp = self._damage(e.block, e.hp, per_hit)
                total += per_hit
                hits_done += 1
                hit_list.append(per_hit)
                if sid == "dainsleif_dance" and e.alive:
                    self._apply_ailment(e, ("perm_poison", 1), None)  # 每段上永久毒
            e.last_hits = hit_list
            seg = " + ".join(str(h) for h in hit_list)
            msg = f"你施展【{sk['name']}】,{empowered_txt}连击 {hits_done} 次 ({seg}) 共造成 {total} 伤害!"
            if ail and e.alive:
                msg += " " + self._apply_ailment(e, ail, None)
            return self._after_skill(sid, msg)
        elif kind == "detonate_burn":
            # 莱瓦汀: 引爆永久烧伤
            if e.perm_burn <= 0:
                return "no_burn"
            dmg = e.perm_burn * 3
            e.hp -= dmg
            e.perm_burn = 0
            e.last_hits = [dmg]
            return self._after_skill(sid, f"你施展【{sk['name']}】, 引爆 {dmg//3} 层永久烧伤, 造成 {dmg} 伤害!")
        elif kind == "execute":
            # 后期百分比终结技: 造成敌人最大生命 value% 的无视格挡伤害
            dmg = int(e.max_hp * val / 100)
            e.hp -= dmg
            e.last_hits = [dmg]
            return self._after_skill(sid, f"你施展【{sk['name']}】, 处决敌人 {val}% 最大生命, 造成 {dmg} 伤害!")
        elif kind == "aid":
            # 中期辅助: 回复生命并获得格挡
            before = self.player.hp
            self.player.hp = min(self.player.max_hp, self.player.hp + val)
            self.player.block += sk.get("block", 0)
            return (f"你施展【{sk['name']}】, 回复 {self.player.hp - before} 生命,"
                    f" 获得 {sk.get('block', 0)} 点格挡.")
        elif kind == "heal":
            before = self.player.hp
            self.player.hp = min(self.player.max_hp, self.player.hp + val)
            return f"你施展【{sk['name']}】, 回复 {self.player.hp - before} 生命."
        elif kind == "block":
            self.player.block += val
            return f"你施展【{sk['name']}】, 获得 {val} 点格挡."
        elif kind == "buff_atk":
            if sk.get("atk_mult"):
                # 战号主动: 攻击×4 持续两回合
                self.player.battle_atk_mult = sk["atk_mult"]
                self.player.battle_atk_mult_remaining = sk.get("duration", 2)
                self.buff_cast_round = True   # 施放当回合不扣减
                return f"你吹响【{sk['name']}】, 攻击×{sk['atk_mult']:.0f} 持续{sk.get('duration',2)}回合!"
            self.player.battle_atk_bonus += val
            return f"你施展【{sk['name']}】, 攻击+{val}."
        return "..."

    def player_potion(self, pid):
        pot = POTION_LIB[pid]
        kind = pot["kind"]
        if kind == "heal":
            before = self.player.hp
            self.player.hp = min(self.player.max_hp, self.player.hp + pot["value"])
            return f"你喝下【{pot['name']}】, 回复 {self.player.hp - before} 生命."
        elif kind == "mp":
            before = self.player.mp
            self.player.mp = min(self.player.max_mp, self.player.mp + pot["value"])
            return f"你喝下【{pot['name']}】, 回复 {self.player.mp - before} 蓝量."
        elif kind == "buff_atk":
            self.player.battle_atk_bonus += pot["value"]
            return f"你喝下【{pot['name']}】, 攻击+{pot['value']}."
        return "..."

    def player_rest(self):
        """休息: 回复 30 蓝量, 获得 2 点格挡."""
        before = self.player.mp
        self.player.mp = min(self.player.max_mp, self.player.mp + 30)
        self.player.block += 2
        return f"你稍作休息, 回复 {self.player.mp - before} 蓝量, 获得 2 点格挡."

    # ---- 敌人行动 ----
    def enemy_turn(self):
        """敌人行动. 返回日志 (含异常结算)."""
        e = self.enemy
        e.block = 0
        logs = []
        # 回合初: 燃烧/中毒/永久烧伤 结算 (每层造成层数伤害)
        logs += self._enemy_start_of_turn()
        if not e.alive:
            return logs
        # 冰冻: 停止行动一回合
        if e.freeze:
            e.freeze = False
            logs.append(f"❄ {e.name} 被冰冻, 无法行动!")
            logs += self._enemy_end_of_turn()
            return logs
        # 眩晕: 停止行动一回合 (与冰冻独立可共存)
        if e.stun:
            e.stun = False
            e.was_stunned = True   # 记录: 上回合处于眩晕状态 (雷霆审判巨额伤害触发)
            logs.append(f"⚡ {e.name} 眩晕未消, 无法行动!")
            logs += self._enemy_end_of_turn()
            return logs
        # 正常行动 (本回合未眩晕)
        e.was_stunned = False
        act = self.rng.choice(e.acts)
        logs += self._enemy_act(act)
        # 流血: 敌人攻击时额外受到层数伤害
        if act in ("attack", "double", "smash", "breath", "scythe", "drain", "devour",
                   "charge", "blood_rage", "stone_spikes", "soul_reap", "hell_bite",
                   "bone_pierce", "dread_gaze", "acid_spit", "holy_smite",
                   "mirror", "mana_drain"):
            logs += self._enemy_bleed()
        # 回合末: 毒火共存则爆炸
        logs += self._enemy_end_of_turn()
        return logs

    def _enemy_start_of_turn(self):
        """回合初: 燃烧/中毒/永久烧伤/永久毒伤 每层造成层数伤害; 永久燃烧每回合自动扩大30层."""
        e = self.enemy
        logs = []
        if e.burn > 0:
            dmg = e.burn
            e.hp -= dmg
            logs.append(f"🔥 {e.name} 正被燃烧! 受到 {dmg} 伤害 (燃烧×{e.burn}).")
        if e.perm_burn > 0:
            old = e.perm_burn
            e.hp -= old
            e.perm_burn = old + 30   # 永久燃烧每回合自动扩大30层
            logs.append(f"♨ {e.name} 被永久烧伤炙烤! 受到 {old} 伤害.")
            logs.append(f"♨ 永久燃烧自噬蔓延, 层数 {old}→{e.perm_burn}!")
        if e.perm_poison > 0:
            dmg = e.perm_poison
            e.hp -= dmg
            logs.append(f"☠ {e.name} 永久剧毒侵蚀! 受到 {dmg} 伤害 (永久毒伤×{e.perm_poison}).")
        if e.poison > 0:
            dmg = e.poison
            e.hp -= dmg
            logs.append(f"☠ {e.name} 中毒发作! 受到 {dmg} 伤害 (中毒×{e.poison}).")
        return logs

    def _enemy_bleed(self):
        """流血: 敌人攻击时额外受到层数伤害; 永久燃烧: 施放攻击时结算一次燃烧伤害并再扩大20层."""
        e = self.enemy
        logs = []
        if e.bleed > 0:
            dmg = e.bleed
            e.hp -= dmg
            logs.append(f"🩸 {e.name} 撕裂的伤口流血不止, 受到 {dmg} 伤害!")
        if e.perm_burn > 0:
            old = e.perm_burn
            e.hp -= old
            e.perm_burn = old + 20   # 施放攻击时永久燃烧再扩大20层
            logs.append(f"♨ {e.name} 攻击时灼焰焚身, 受到 {old} 伤害!")
            logs.append(f"♨ 烈焰随攻击蔓延, 永久燃烧 {old}→{e.perm_burn}!")
        return logs

    def _enemy_end_of_turn(self):
        """回合末: 毒火共存则引爆, 消耗掉毒与火."""
        e = self.enemy
        logs = []
        if e.burn > 0 and e.poison > 0:
            dmg = (e.burn + e.poison) * 2
            e.hp -= dmg
            e.burn = 0
            e.poison = 0
            logs.append(f"🔥☠ 毒火交融! {e.name} 体内发生爆炸, 受到 {dmg} 伤害!")
        return logs

    def _enemy_act(self, act):
        e = self.enemy
        logs = []
        hp_before = self.player.hp
        if act == "attack":
            dmg = self.enemy.total_atk()
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            logs.append(f"{self.enemy.name} 攻击, 造成 {dmg} 伤害.")
        elif act == "double":
            dmg = self.enemy.total_atk()
            total = 0
            for _ in range(2):
                self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
                total += dmg
            logs.append(f"{self.enemy.name} 双重攻击, 造成 {total} 伤害!")
        elif act == "defend":
            self.enemy.block += 6
            logs.append(f"{self.enemy.name} 防御, 获得 6 点格挡.")
        elif act == "smash":
            dmg = self.enemy.total_atk() + 4
            self.player.hp -= dmg
            self.player.block = 0
            logs.append(f"{self.enemy.name} 重击! 无视格挡造成 {dmg} 伤害!")
        elif act == "buff":
            self.enemy.bonus_atk += 3
            logs.append(f"{self.enemy.name} 怒吼, 攻击+3!")
        elif act == "breath":
            dmg = self.enemy.total_atk()
            self.player.hp -= dmg
            logs.append(f"{self.enemy.name} 龙息! 造成 {dmg} 伤害并灼烧你!")
        elif act == "summon_buff":
            self.enemy.bonus_atk += 2
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + 10)
            logs.append(f"{self.enemy.name} 汲取亡魂, 攻击+2 回复10生命.")
        elif act == "drain":
            dmg = self.enemy.total_atk() + 2
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            heal = min(self.enemy.max_hp, self.enemy.hp + dmg // 2)
            self.enemy.hp = heal
            logs.append(f"{self.enemy.name} 汲取生命, 造成 {dmg} 伤害并回复 {dmg // 2} 生命!")
        elif act == "wail":
            dmg = self.enemy.total_atk() + 3
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.player.battle_atk_bonus = max(-6, self.player.battle_atk_bonus - 2)
            logs.append(f"{self.enemy.name} 凄厉哀嚎, 造成 {dmg} 伤害并削弱你的攻击!")
        elif act == "scythe":
            dmg = self.enemy.total_atk() + 8
            self.player.hp -= dmg
            self.player.block = 0
            logs.append(f"{self.enemy.name} 挥舞死神镰刀! 无视格挡造成 {dmg} 伤害!")
        # ----- 新增精英独特技能 (加强精英怪) -----
        elif act == "charge":
            # 冲锋: 高伤害, 无视格挡
            dmg = self.enemy.total_atk() + 10
            self.player.hp -= dmg
            self.player.block = 0
            logs.append(f"{self.enemy.name} 冲锋! 势不可挡, 无视格挡造成 {dmg} 伤害!")
        elif act == "blood_rage":
            # 嗜血狂暴: 造成伤害并回复自身
            dmg = self.enemy.total_atk() + 4
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + dmg // 2)
            logs.append(f"{self.enemy.name} 陷入嗜血狂暴! 造成 {dmg} 伤害并回复 {dmg // 2} 生命!")
        elif act == "stone_spikes":
            # 地刺: 无视格挡并击碎你的格挡
            dmg = self.enemy.total_atk() + 6
            self.player.hp -= dmg
            self.player.block = 0
            logs.append(f"{self.enemy.name} 震裂大地, 地刺贯穿! 无视格挡造成 {dmg} 伤害!")
        elif act == "soul_reap":
            # 灵魂收割: 造成伤害并侵蚀你的攻击
            dmg = self.enemy.total_atk() + 6
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.player.battle_atk_bonus = max(-8, self.player.battle_atk_bonus - 3)
            logs.append(f"{self.enemy.name} 收割你的灵魂! 造成 {dmg} 伤害并削弱你的攻击!")
        elif act == "hell_bite":
            # 地狱撕咬: 造成伤害并汲取你的蓝量
            dmg = self.enemy.total_atk() + 4
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            drain_mp = min(self.player.mp, 10)
            self.player.mp -= drain_mp
            logs.append(f"{self.enemy.name} 地狱撕咬! 造成 {dmg} 伤害并汲取 {drain_mp} 蓝量!")
        elif act == "bone_pierce":
            # 骨刺突刺: 高额无视格挡伤害
            dmg = self.enemy.total_atk() + 8
            self.player.hp -= dmg
            self.player.block = 0
            logs.append(f"{self.enemy.name} 骨刺突刺! 无视格挡造成 {dmg} 伤害!")
        elif act == "dread_gaze":
            # 恐惧凝视: 造成伤害并大幅削弱攻击
            dmg = self.enemy.total_atk() + 5
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.player.battle_atk_bonus = max(-10, self.player.battle_atk_bonus - 4)
            logs.append(f"{self.enemy.name} 以恐惧凝视你! 造成 {dmg} 伤害并侵蚀你的战意!")
        elif act == "acid_spit":
            # 腐液喷射: 造成伤害并腐蚀你的格挡
            dmg = self.enemy.total_atk() + 6
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.player.block = 0
            logs.append(f"{self.enemy.name} 喷射腐液! 造成 {dmg} 伤害并腐蚀你的防御!")
        elif act == "holy_smite":
            # 圣光制裁: 造成伤害并治愈自身
            dmg = self.enemy.total_atk() + 7
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + 15)
            logs.append(f"{self.enemy.name} 降下圣光制裁! 造成 {dmg} 伤害并回复 15 生命!")
        # ----- 异界特殊精英行动 -----
        elif act == "mirror":
            # 虚空镜像: 造成基于玩家攻击力的反伤, 并降低玩家攻击
            dmg = max(4, self.player.total_atk() // 2)
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.player.battle_atk_bonus = max(-8, self.player.battle_atk_bonus - 3)
            logs.append(f"{self.enemy.name} 虚空折射! 反射 {dmg} 伤害并侵蚀你的攻击!")
        elif act == "split":
            # 虚空镜像分裂: 本回合攻击提升且下次攻击翻倍 (用bonus表示)
            self.enemy.bonus_atk += 4
            logs.append(f"{self.enemy.name} 分裂幻影! 攻击+4, 准备下一击!")
        elif act == "mana_drain":
            # 异界吞噬者: 吸取玩家蓝量
            drain_mp = min(self.player.mp, 8)
            self.player.mp -= drain_mp
            dmg = max(4, self.enemy.total_atk() - 3)
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            logs.append(f"{self.enemy.name} 吸噬魔力! 造成 {dmg} 伤害并汲取 {drain_mp} 蓝量!")
        elif act == "devour":
            # 异界吞噬者: 吞噬造成大量伤害并回复
            dmg = self.enemy.total_atk() + 6
            self.player.block, self.player.hp = self._damage(self.player.block, self.player.hp, dmg)
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + 12)
            logs.append(f"{self.enemy.name} 深渊吞噬! 造成 {dmg} 伤害并回复12生命!")
        # 提尔锋流血反击: 被攻击时给敌人上等于受到伤害的流血层数
        if getattr(self, "tyrfing_counter", False) and self.player.hp < hp_before:
            dealt = hp_before - self.player.hp
            if dealt > 0 and self.enemy.alive:
                self.enemy.bleed += dealt
                logs.append(f"🩸 提尔锋的诅咒反噬! {self.enemy.name} 因攻击你而流血 {dealt} 层!")
        return logs


# ============================================================
# 事件 (一层用)
# ============================================================
def event_factory(rng):
    events = [
        {
            "title": "被遗忘的祭坛",
            "text": "一座古老祭坛上摆着一瓶泛着紫光的药剂.",
            "choices": [
                ("饮下药剂 (随机增益或代价)", "mystery_potion"),
                ("砸碎祭坛 (获得金币)", "gold", {"value": 35}),
                ("离开", "leave"),
            ],
        },
        {
            "title": "垂死的冒险者",
            "text": "一名重伤的冒险者向你求助.",
            "choices": [
                ("救治他 (消耗1瓶药水, 获得经验)", "save_adventurer"),
                ("搜刮他的财物 (获得金币)", "gold", {"value": 30}),
                ("离开", "leave"),
            ],
        },
        {
            "title": "篝火与旅人",
            "text": "暖和的篝火旁坐着一位旅人, 愿意与你分享.",
            "choices": [
                ("一起烤火 (回复20生命)", "heal", {"value": 20}),
                ("听旅人讲故事 (获得经验)", "exp", {"value": 60}),
                ("离开", "leave"),
            ],
        },
        {
            "title": "诡异的水池",
            "text": "池水泛着幽光, 倒映着未来的战斗.",
            "choices": [
                ("饮一口 (随机效果)", "pool_gamble"),
                ("离开", "leave"),
            ],
        },
    ]
    return rng.choice(events)


# ============================================================
# 主应用 (Tkinter, 鼠标操作)
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚔ 肉鸽勇士 · Roguelite RPG")
        root.configure(bg=COLOR_BG)
        root.geometry("980x700")
        root.minsize(860, 640)

        self.rng = random.Random()
        self.player = Player()
        self.node_state = {}   # node_id -> "done"/"current"
        self.map_nodes = {}
        self.map_edges = []
        self.map_vertical = set()   # 主地图垂直通路边集合 (走此通道需付费)
        self.map_order = []
        self.current_node = "start"
        self.prev_node = None      # 上一个节点 (用于返回)
        self.floor = 1
        self.combat = None
        self.battle_log = []
        self.divine_fight = False   # 当前是否为神灵使者战
        self._player_revived = False  # 本场战斗是否已触发神灵护身符复活
        # 异界(隐藏层)状态
        self.in_abyss = False      # 当前是否在异界隐藏层内
        self.abyss_entry = None    # 异界入口节点 (主地图的 (stage,index))

        # 打靶模式状态 (靶场沙盒, 测量平均每回合伤害)
        self.target_mode = False       # 是否处于打靶模式
        self.target_attack = 50        # 靶子每回合攻击伤害 x (可调整)
        self.target_total_damage = 0   # 累计对靶子造成的伤害
        self.target_turns = 0          # 已进行的回合数
        self.target_avg = 0.0          # 平均每回合伤害
        self.target_prev_hp = None     # 上一回合靶子血量 (用于计算单回合伤害)
        self.target_saved_state = None # 进入靶场前保存的玩家状态 (退出时恢复)

        # 界面导航栈 (Esc 返回上一界面)
        self._view_stack = []
        self._cur_fn = None

        self._build_layout()
        # 键盘快捷键: Esc 返回上一界面, Z 存档
        root.bind("<Escape>", lambda e: self.on_esc())
        root.bind("<KeyPress-z>", lambda e: self.on_save())
        root.bind("<KeyPress-Z>", lambda e: self.on_save())
        self.show_menu()

    # ---------------- 布局 ----------------
    def _build_layout(self):
        self.status_bar = tk.Frame(self.root, bg=COLOR_PANEL, height=44)
        self.status_bar.pack(side="top", fill="x")
        self.status_bar.pack_propagate(False)
        self.status_label = tk.Label(self.status_bar, bg=COLOR_PANEL, fg=COLOR_TEXT,
                                     font=FONT_MAIN, anchor="w", padx=12)
        self.status_label.pack(fill="both", expand=True)

        self.content = tk.Frame(self.root, bg=COLOR_BG)
        self.content.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.action_bar = tk.Frame(self.root, bg=COLOR_PANEL, height=58)
        self.action_bar.pack(side="bottom", fill="x")
        self.action_bar.pack_propagate(False)
        self.action_inner = tk.Frame(self.action_bar, bg=COLOR_PANEL)
        self.action_inner.pack(fill="both", expand=True, padx=8, pady=6)

    def _clear_content(self):
        # 清除全局鼠标滚轮绑定 (避免残留引用已销毁的画布)
        try:
            self.root.unbind_all("<MouseWheel>")
        except Exception:
            pass
        for w in self.content.winfo_children():
            w.destroy()

    def _clear_actions(self):
        for w in self.action_inner.winfo_children():
            w.destroy()

    def _btn(self, parent, text, cmd, color=COLOR_BTN, fg=COLOR_TEXT, font=FONT_MAIN,
             width=None, padx=12, pady=6):
        b = tk.Button(parent, text=text, command=cmd, bg=color, fg=fg,
                      activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                      relief="flat", font=font, bd=0, cursor="hand2", padx=padx, pady=pady)
        if width:
            b.configure(width=width)
        b.pack(side="left", padx=4, pady=2)
        b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
        b.bind("<Leave>", lambda e, w=b, c=color: w.configure(bg=c))
        return b

    def _label(self, text, parent=None, fg=COLOR_TEXT, font=FONT_MAIN, bg=COLOR_BG):
        p = parent or self.content
        return tk.Label(p, text=text, bg=bg, fg=fg, font=font, justify="left", anchor="w")

    def _panel(self, parent=None, bg=COLOR_PANEL):
        p = parent or self.content
        return tk.Frame(p, bg=bg, highlightbackground=COLOR_BORDER, highlightthickness=1)

    def _update_status(self):
        p = self.player
        wdata = p.weapon_data
        cls_txt = ""
        if getattr(p, "player_class", None):
            cls_txt = CLASS_LIB[p.player_class]["name"] + "    "
        txt = (f"{cls_txt}第 {self.floor} 层    "
               f"⚡ 行动力 {p.action}/{p.max_action}   "
               f"Lv{p.level}  经验 {p.exp}/{p.exp_needed()}   "
               f"❤ {p.hp}/{p.max_hp}   "
               f"✦ {p.mp}/{p.max_mp}   "
               f"🗡 攻击 {p.total_atk()}   "
               f"🔨 {wdata['name']}   "
               f"💰 {p.gold}")
        if getattr(self, "_hint", None):
            txt += "    " + self._hint
            self._hint = None
        self.status_label.configure(text=txt)

    # ---------------- 界面导航 (Esc 返回) ----------------
    def _push_view(self, new_fn):
        """进入新界面时记录返回栈 (避免同一界面重绘重复压栈)."""
        if getattr(self, "_cur_fn", None) is not None and self._cur_fn != new_fn:
            self._view_stack.append(self._cur_fn)
        self._cur_fn = new_fn

    def on_esc(self):
        """Esc: 返回上一界面."""
        if self._view_stack:
            fn = self._view_stack.pop()
            self._cur_fn = fn
            if self._clear_actions_safe():
                fn()
        else:
            self._set_hint("没有可返回的上一界面")

    def _clear_actions_safe(self):
        try:
            self._clear_actions()
            return True
        except Exception:
            return False

    # ---------------- 存档 (Z 键) ----------------
    def _save_path(self):
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "rogue_rpg_save.dat")

    def on_save(self):
        """Z: 保存当前进度."""
        try:
            state = {
                "player": self.player,
                "floor": self.floor,
                "rng": self.rng.getstate(),
                "map_nodes": self.map_nodes,
                "map_edges": self.map_edges,
                "map_order": self.map_order,
                "map_vertical": self.map_vertical,
                "node_state": self.node_state,
                "current_node": self.current_node,
                "prev_node": self.prev_node,
                "in_abyss": getattr(self, "in_abyss", False),
                "abyss_entry": getattr(self, "abyss_entry", None),
                "main_map_nodes": getattr(self, "main_map_nodes", None),
                "main_map_edges": getattr(self, "main_map_edges", None),
                "main_map_vertical": getattr(self, "main_map_vertical", None),
                "main_map_order": getattr(self, "main_map_order", None),
                "main_node_state": getattr(self, "main_node_state", None),
                "main_prev_node": getattr(self, "main_prev_node", None),
                "shop_state": self._shop_state() if hasattr(self, "_shop_items") else None,
            }
            with open(self._save_path(), "wb") as f:
                pickle.dump(state, f)
            self._set_hint("💾 已存档! (按 Z 再次存档)")
        except Exception as e:
            self._set_hint(f"存档失败: {e}")

    def _shop_state(self):
        return (self._shop_items, self._shop_trinkets, self._shop_potions, self._shop_offhands)

    def save_exists(self):
        return os.path.exists(self._save_path())

    def load_game(self):
        """读取存档并恢复进度."""
        try:
            with open(self._save_path(), "rb") as f:
                st = pickle.load(f)
        except Exception:
            return False
        self.player = st["player"]
        self.floor = st["floor"]
        self.rng.setstate(st["rng"])
        self.map_nodes = st["map_nodes"]
        self.map_edges = st["map_edges"]
        self.map_order = st["map_order"]
        self.map_vertical = st.get("map_vertical", set())
        self.node_state = st["node_state"]
        self.current_node = st["current_node"]
        self.prev_node = st["prev_node"]
        self.in_abyss = st.get("in_abyss", False)
        self.abyss_entry = st.get("abyss_entry", None)
        self.main_map_nodes = st.get("main_map_nodes", None)
        self.main_map_edges = st.get("main_map_edges", None)
        self.main_map_vertical = st.get("main_map_vertical", None)
        self.main_map_order = st.get("main_map_order", None)
        self.main_node_state = st.get("main_node_state", None)
        self.main_prev_node = st.get("main_prev_node", None)
        if st.get("shop_state"):
            self._shop_items, self._shop_trinkets, self._shop_potions, self._shop_offhands = st["shop_state"]
        self.combat = None
        self._view_stack = []
        self._cur_fn = None
        self.show_map()
        return True

    def _set_hint(self, text):
        """在状态栏显示一条临时提示 (下一次刷新状态时显示一次后清除)."""
        self._hint = text
        try:
            self._update_status()
        except Exception:
            pass

    # ---------------- 主菜单 ----------------
    def show_menu(self):
        self._push_view(self.show_menu)
        self._clear_content()
        self._clear_actions()
        self._update_status()

        wrap = tk.Frame(self.content, bg=COLOR_BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="⚔ 肉 鸽 勇 士", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_BIG).pack(pady=(0, 4))
        tk.Label(wrap, text="Roguelite RPG", bg=COLOR_BG, fg=COLOR_SUB,
                 font=FONT_MAIN).pack(pady=(0, 24))

        items = [("开始冒险", self.start_new)]
        if self.save_exists():
            items.insert(0, ("继续游戏", self.load_game))
        items += [
            ("🎯 打靶模式", self.start_target_mode),
            ("武器图鉴", self.show_weapon_codex),
            ("技能图鉴", self.show_skill_codex),
            ("怪物图鉴", self.show_monster_codex),
            ("饰品图鉴", self.show_trinket_codex),
            ("副手图鉴", self.show_offhand_codex),
            ("材料图鉴", self.show_material_codex),
            ("药水图鉴", self.show_potion_codex),
        ]
        for text, cmd in items:
            b = tk.Button(wrap, text=text, command=cmd, bg=COLOR_BTN, fg=COLOR_TEXT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                          relief="flat", font=("Microsoft YaHei UI", 12), bd=0,
                          cursor="hand2", width=16, pady=7)
            b.pack(pady=4)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))
        tk.Label(wrap, text="快捷键:  Z = 存档   ·   Esc = 返回上一界面",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(10, 0))

    def start_new(self):
        seed = "".join(random.choice("0123456789abcdef") for _ in range(6))
        self.rng = random.Random(seed)
        self.player = Player()
        self.floor = 1
        self.show_class_select()

    def show_class_select(self):
        """闯关前选择职业, 获得初始增益."""
        self._push_view(self.show_class_select)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="⚔ 选择你的职业", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(12, 4))
        tk.Label(self.content, text="每种职业拥有不同的初始增益, 一旦选择无法更改",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 10))

        # 滚动容器 (职业较多, 可用滚轮或拉动条滚动选择)
        canvas, scroller, scroll = self._scroll_container()

        for cid, c in CLASS_LIB.items():
            row = self._panel(scroller)
            row.pack(fill="x", padx=60, pady=5)
            inner = tk.Frame(row, bg=COLOR_PANEL)
            inner.pack(padx=14, pady=8, fill="x")
            title = tk.Frame(inner, bg=COLOR_PANEL)
            title.pack(anchor="w")
            tk.Label(title, text=f"{c['icon']} {c['name']}", bg=COLOR_PANEL,
                     fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")
            tk.Label(title, text="   " + self._class_buff_text(c), bg=COLOR_PANEL,
                     fg=COLOR_GOLD, font=FONT_MAIN).pack(side="left", padx=10)
            tk.Label(inner, text="   " + c["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", pady=(2, 0))
            b = tk.Button(inner, text="选 择", bg=COLOR_OK, fg=COLOR_TEXT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          padx=20, pady=4,
                          command=lambda cid=cid: self.choose_class(cid))
            b.pack(anchor="e", pady=(4, 0))
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_OK))

        self._btn(self.action_inner, "← 返回主菜单", self.show_menu, color=COLOR_BTN)

    def _class_buff_text(self, c):
        parts = []
        if c["atk"]:
            parts.append(f"攻击+{c['atk']}")
        if c["hp"]:
            sign = "+" if c["hp"] > 0 else ""
            parts.append(f"生命{sign}{c['hp']}")
        if c["mp"]:
            parts.append(f"蓝量+{c['mp']}")
        if c["block"]:
            parts.append(f"格挡+{c['block']}")
        if c["level_atk"]:
            parts.append(f"升级攻击+{c['level_atk']}")
        return "  ".join(parts)

    def choose_class(self, cid):
        self.player.apply_class(cid)
        self._set_hint(f"已选择职业: {CLASS_LIB[cid]['name']}")
        self.show_intro()

    def show_intro(self):
        self._push_view(self.show_intro)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        self._show_node_legend()
        self._btn(self.action_inner, "开始冒险 ▶", self.begin_floor,
                  color=COLOR_OK, font=FONT_TITLE, padx=24, pady=8)

    def _show_node_legend(self):
        wrap = tk.Frame(self.content, bg=COLOR_BG)
        wrap.pack(expand=True)
        tk.Label(wrap, text="攀爬这座塔, 依次通过连通的节点, 击败关底Boss!",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_MAIN).pack(pady=8)
        tk.Label(wrap, text="⚡ 每走一步(前进/返回/回城)消耗 1 点行动力",
                 bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_MAIN).pack(pady=(0, 4))
        tk.Label(wrap, text="· 走过的节点会变成「空」, 再次进入不再触发任何效果",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack()
        tk.Label(wrap, text="· 可返回上一节点, 或回城🏕 回到营地",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 4))
        tk.Label(wrap, text="· 金色虚线为垂直通路, 上下移动需支付金币",
                 bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_MAIN).pack()
        tk.Label(wrap, text="· 异界🌀为通往隐藏层的入口",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 4))
        tk.Label(wrap, text="⚠ 行动力耗尽仍未到关底, 将直面强化Boss!",
                 bg=COLOR_BG, fg=COLOR_BAD, font=FONT_MAIN).pack(pady=(0, 8))
        for key in ["monster", "divine", "elite", "treasure", "event", "shop", "blacksmith", "abyss", "boss"]:
            row = tk.Frame(wrap, bg=COLOR_BG)
            row.pack(pady=2)
            tk.Label(row, text=NODE_ICON[key], bg=COLOR_BG, fg=NODE_COLOR[key],
                     font=("Consolas", 14)).pack(side="left", padx=6)
            tk.Label(row, text=f"  {NODE_LABEL[key]}", bg=COLOR_BG, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(side="left")
            desc = {
                "monster": "普通战斗",
                "divine": "特殊战斗, 掉落神灵碎片",
                "elite": "高难战斗, 丰厚奖励",
                "treasure": "金币与装备",
                "event": "抉择与机缘",
                "shop": "购买装备与药水",
                "blacksmith": "购买锻造材料",
                "abyss": "通往隐藏层",
                "boss": "关底首领",
            }[key]
            tk.Label(row, text=desc, bg=COLOR_BG, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(side="left", padx=10)

    # ---------------- 地图 ----------------
    def begin_floor(self):
        self.map_nodes, self.map_edges, self.map_order, self.map_vertical = generate_map(self.rng)
        self.node_state = {nid: ("done" if nid == "start" else "todo") for nid in self.map_order}
        self.current_node = "start"
        self.prev_node = None
        self.in_abyss = False
        self.abyss_entry = None
        self.show_map()

    def show_map(self):
        self._push_view(self.show_map)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        # 异界隐藏层地图标题
        if self.in_abyss:
            tk.Label(self.content, text="🌀 异 界 隐 藏 层", bg=COLOR_BG, fg="#ff79c6",
                     font=FONT_TITLE).pack(pady=(4, 0))
            tk.Label(self.content, text="1-3-2-1 的短路线, 无法回头, 到达第四阶段即返回主世界!",
                     bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 2))
        self._render_map_canvas()
        # 提示
        p = self.player
        if self.in_abyss:
            tip = "🌀 异界中行动不消耗行动力"
        else:
            tip = f"⚡ 剩余行动力 {p.action} · 每走一步(前进或返回)消耗 1 点"
        tk.Label(self.content, text=tip, bg=COLOR_BG, fg=COLOR_SUB,
                 font=FONT_MAIN).pack(pady=(6, 0))
        self._btn(self.action_inner, "查看状态 ▶", self.show_character_sheet, color=COLOR_BTN)
        self._btn(self.action_inner, "🎒 背包", self.show_bag, color=COLOR_BTN)
        self._btn(self.action_inner, "⚔ 装备", self.show_equip, color=COLOR_BTN)
        if not self.in_abyss:
            # 主地图: 可返回上一节点 / 回城 (消耗 1 行动值)
            if self.prev_node is not None and p.action > 0 and self.prev_node != self.current_node:
                self._btn(self.action_inner, "← 返回上一节点 (-1⚡)", self.go_back,
                          color=COLOR_SELECT, padx=16, pady=6)
            if self.current_node != "start" and p.action > 0:
                self._btn(self.action_inner, "🏕 回城 (-1⚡)", self.go_home,
                          color=COLOR_GOLD, padx=16, pady=6)
        else:
            # 异界隐藏层: 无回头路
            tk.Label(self.content, text="🌀 异界中无法返回或回城, 只能前进, 到达第四阶段即返回!",
                     bg=COLOR_BG, fg="#ff79c6", font=FONT_MAIN).pack(pady=(2, 0))
        if p.action <= 0 and not self.in_abyss:
            # 行动力耗尽: 被迫直面强化Boss
            tk.Label(self.content, text="⚠ 行动力已耗尽! 无法再前进, 只能直面强化Boss!",
                     bg=COLOR_BG, fg=COLOR_BAD, font=FONT_TITLE).pack(pady=(8, 0))
            self._btn(self.action_inner, "👑 直面强化Boss ⚠", self.start_strong_boss,
                      color=COLOR_BAD, font=FONT_TITLE, padx=20, pady=8)

    def _render_map_canvas(self):
        """用 Canvas 绘制地图: 节点方块 + 连接线."""
        nodes = self.map_nodes
        edges = self.map_edges
        p_action = self.player.action

        # 计算布局坐标: 阶段 -> 列 x, 节点 -> 行 y
        pos = {}
        # 找出阶段分组
        from collections import OrderedDict
        stages = OrderedDict()
        for nid, kind in nodes.items():
            if nid == "start":
                stages.setdefault(-1, []).append(nid)
            elif nid == "boss":
                stages.setdefault(99, []).append(nid)
            else:
                s, i = nid
                stages.setdefault(s, []).append(nid)
        stage_order = sorted(stages.keys())
        # x 坐标
        total = len(stage_order)
        x0, x1 = 70, 910
        for idx, s in enumerate(stage_order):
            n = len(stages[s])
            if total == 1:
                xs = [x0]
            else:
                xs = [x0 + (x1 - x0) * idx / (total - 1)] * n
            ys = []
            for j in range(n):
                if n == 1:
                    y = 300
                else:
                    y = 120 + 320 * j / (n - 1)
                ys.append(y)
            for j, nid in enumerate(stages[s]):
                pos[nid] = (xs[j], ys[j])

        cw, ch = 980, 470
        # 计算覆盖所有节点(含最底部节点底边)的内容高度, 超出可视高度时用滚动条查看
        for nid in nodes:
            _x, _y = pos[nid]
            ch = max(ch, _y + 48)
        # 地图放在可滚动容器内: 窗口空间不足时出现右侧滚动条, 可滚动查看下方节点
        map_wrap = tk.Frame(self.content, bg=COLOR_BG)
        map_wrap.pack(pady=4, fill="both", expand=True)
        canvas = tk.Canvas(map_wrap, width=cw, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(map_wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        canvas.configure(height=min(ch, 470), scrollregion=(0, 0, cw, ch))
        # 地图鼠标滚轮滚动 (与主内容滚轮绑定分开处理, 不冲突)
        def _map_wheel(event):
            try:
                canvas.yview_scroll(int(-event.delta / 120), "units")
            except Exception:
                pass
        canvas.bind("<MouseWheel>", _map_wheel)
        map_wrap.bind("<MouseWheel>", _map_wheel)

        # 画连接线 (水平前进线)
        for src, dst in edges:
            (x1_, y1_) = pos[src]
            (x2_, y2_) = pos[dst]
            src_ok = (src == self.current_node or dst == self.current_node)
            dst_done = self.node_state.get(dst) == "done"
            linecolor = COLOR_SELECT if src_ok else (COLOR_SUB if not dst_done else COLOR_BORDER)
            canvas.create_line(x1_, y1_, x2_, y2_, fill=linecolor, width=2)
        # 画垂直通路 (需支付金币)
        vcost = self.vertical_cost()
        for a, b in self.map_vertical:
            (x1_, y1_) = pos[a]
            (x2_, y2_) = pos[b]
            on_cur = (a == self.current_node or b == self.current_node)
            color = COLOR_GOLD if on_cur else "#6a5a3a"
            canvas.create_line(x1_, y1_, x2_, y2_, fill=color, width=2, dash=(4, 3))
            mx, my = (x1_ + x2_) / 2, (y1_ + y2_) / 2
            canvas.create_text(mx, my, text=f"{vcost}💰", fill=COLOR_GOLD,
                               font=("Microsoft YaHei UI", 8))

        # 画节点
        # 节点 tag 须用无空格无括号的安全串 (Tk 按空白拆分 tag)
        def _safe_tag(nid):
            if nid == "start":
                return "nd_start"
            if nid == "boss":
                return "nd_boss"
            s, i = nid
            return f"nd_{s}_{i}"

        for nid, kind in nodes.items():
            x, y = pos[nid]
            state = self.node_state.get(nid, "todo")
            cx = x + 34
            cy = y + 24
            # 该节点所有图形共用一个 tag, 便于整块点击
            node_tag = _safe_tag(nid)
            # 已走过的(除营地)节点显示为空
            is_empty = (state == "done" and nid != "start")
            # 节点方块
            if nid == self.current_node:
                fill = COLOR_CARD
            elif is_empty:
                fill = COLOR_PANEL2
            else:
                fill = COLOR_PANEL
            tag_rect = canvas.create_rectangle(x, y, x + 68, y + 48,
                                               fill=fill,
                                               outline=NODE_COLOR[kind],
                                               width=2 if nid == self.current_node else 1,
                                               tags=node_tag)
            if is_empty:
                # 空节点: 显示"空"而非原类型
                canvas.create_text(cx, cy, text="· 空 ·", fill=COLOR_SUB,
                                   font=("Microsoft YaHei UI", 10),
                                   tags=node_tag)
            else:
                canvas.create_text(cx, cy - 8, text=NODE_ICON[kind],
                                   fill=NODE_COLOR[kind], font=("Consolas", 14),
                                   tags=node_tag)
                canvas.create_text(cx, cy + 12, text=NODE_LABEL[kind],
                                   fill=COLOR_TEXT, font=("Microsoft YaHei UI", 8),
                                   tags=node_tag)
            # 已走过打勾
            if state == "done" and not is_empty:
                canvas.create_text(cx + 30, cy - 12, text="✓", fill=COLOR_OK,
                                   font=("Microsoft YaHei UI", 10, "bold"),
                                   tags=node_tag)
            # 当前节点
            if nid == self.current_node:
                canvas.create_text(x + 34, y - 8, text="▸ 当前", fill=COLOR_ACCENT,
                                   font=("Microsoft YaHei UI", 9, "bold"),
                                   tags=node_tag)
            # 可点击: 与当前节点有边相连 (可前进到未走过, 或返回已走过)
            if self._is_next(nid) and (p_action > 0 or self.in_abyss):
                # 绑定到统一 tag: 点方块或点文字都能触发
                canvas.tag_bind(node_tag, "<Button-1>",
                                lambda e, n=nid: self.on_node_click(n))
                canvas.tag_bind(node_tag, "<Enter>",
                                lambda e, t=tag_rect: canvas.itemconfig(t, width=3))
                canvas.tag_bind(node_tag, "<Leave>",
                                lambda e, t=tag_rect: canvas.itemconfig(t, width=1))
                # 已走过的空节点标注"返回"
                if state == "done":
                    canvas.create_text(cx + 34, cy + 24, text="↩ 返回",
                                       fill=COLOR_SELECT,
                                       font=("Microsoft YaHei UI", 8),
                                       tags=node_tag)

    def _is_next(self, nid):
        """nid 是否为当前节点可直接到达的相邻节点 (水平或垂直通路, 双向通行)."""
        for src, dst in self.map_edges:
            if (src == self.current_node and dst == nid) or \
               (dst == self.current_node and src == nid):
                return True
        pair = tuple(sorted((self.current_node, nid), key=lambda x: str(x)))
        return pair in self.map_vertical

    def _is_vertical(self, nid):
        """从当前节点到 nid 是否为垂直通路 (需支付金币)."""
        if self.current_node == nid:
            return False
        pair = tuple(sorted((self.current_node, nid), key=lambda x: str(x)))
        return pair in self.map_vertical

    def vertical_cost(self):
        """垂直通路通行费用 (按层递增)."""
        return 10 + 5 * self.floor

    def on_node_click(self, nid):
        if not self._is_next(nid):
            return
        # 异界中行动不消耗行动力
        if not self.in_abyss and self.player.action <= 0:
            return  # 行动力耗尽, 只能打强化Boss
        # 异界: 到达第四阶段(最后阶段)立即返回主世界
        if self.in_abyss and isinstance(nid, tuple) and nid[0] >= len(ABYSS_STAGE_KINDS) - 1:
            self.exit_abyss()
            return
        # 垂直通路需支付金币
        if self._is_vertical(nid):
            cost = self.vertical_cost()
            if self.player.gold < cost:
                self._set_hint(f"金币不足! 垂直通路需 {cost} 金币")
                return
            self.player.gold -= cost
        # 异界中行动不消耗行动力
        if not self.in_abyss:
            self.player.action -= 1          # 消耗 1 点行动力
        self.prev_node = self.current_node   # 记录上一节点 (供返回)
        self.current_node = nid
        # 已走过的(空)节点: 仅移动, 不触发效果
        if self.node_state.get(nid) == "done":
            self.show_map()
            return
        kind = self.map_nodes[nid]
        if kind == "monster":
            self.start_battle(monster=True)
        elif kind == "divine":
            self.start_divine_battle()
        elif kind == "elite":
            self.start_battle(monster=False)
        elif kind == "abyss_elite":
            self.start_abyss_elite_battle()
        elif kind == "treasure":
            self.show_treasure()
        elif kind == "event":
            self.show_event()
        elif kind == "shop":
            self.show_shop()
        elif kind == "blacksmith":
            self.show_blacksmith()
        elif kind == "abyss":
            self.show_abyss_gate()
        elif kind == "boss":
            self.start_battle(monster=False, boss=True)
        else:
            self.show_map()

    def go_back(self):
        """返回上一个节点, 消耗 1 点行动值, 不触发任何效果."""
        p = self.player
        if self.prev_node is None or p.action <= 0:
            return
        if self.prev_node == self.current_node:
            return
        p.action -= 1                       # 消耗 1 点行动值
        # 当前节点标为已完成(空)
        if self.current_node in self.node_state:
            self.node_state[self.current_node] = "done"
        # 返回上一个节点 (已是走过的空节点, 不触发效果)
        back = self.prev_node
        self.prev_node = self.current_node  # 反转, 便于再返回
        self.current_node = back
        self.node_state[back] = "done"
        self.show_map()

    def go_home(self):
        """回城: 消耗 1 点行动值, 回到营地, 不触发任何效果."""
        p = self.player
        if p.action <= 0:
            return
        if self.current_node == "start":
            return
        p.action -= 1
        # 当前节点标为已完成(空)
        if self.current_node in self.node_state:
            self.node_state[self.current_node] = "done"
        # 回到营地
        self.prev_node = self.current_node
        self.current_node = "start"
        self.node_state["start"] = "done"
        self.show_map()

    def after_node(self):
        """节点结束, 标记完成(空)并返回地图."""
        if self.current_node in self.node_state:
            self.node_state[self.current_node] = "done"
        # 异界隐藏层打到底 -> 返回主地图
        if self.in_abyss and self._abyss_cleared():
            self.exit_abyss()
            return
        self.show_map()

    def start_strong_boss(self):
        """行动力耗尽时提前直面强化Boss."""
        self.start_battle(monster=False, boss=True, strong=True)

    # ---------------- 战斗 ----------------
    def _make_enemy(self, monster, boss=False, strong=False):
        # 根据当前楼层选择怪物池 (1=地表 2=冥界 3=冥界深处 4=神界)
        fgroup = FLOOR_MONSTERS.get(min(self.floor, 4), FLOOR_MONSTERS[4])
        if boss:
            pool = fgroup["boss"]
        elif monster:
            pool = fgroup["normal"]
        else:
            pool = fgroup["elite"]
        data = self.rng.choice(pool)
        e = Enemy(data)
        e.key = data["key"]  # 记录种类 (供 Boss 专属掉落判断)
        # 层数缩放: 每层更强
        scale = 1.0 + (self.floor - 1) * 0.35
        e.hp = int(e.hp * scale)
        e.max_hp = e.hp
        e.atk = int(e.atk * scale)
        # 强化Boss (行动力耗尽被迫决战): 属性大幅提升
        if strong:
            e.name = "强化·" + e.name
            e.hp = int(e.max_hp * 1.6)
            e.max_hp = e.hp
            e.atk = int(e.atk * 1.5)
            e.exp = int(e.exp * 2)
            e.gold = int(e.gold * 2)
        return e

    def _make_divine_enemy(self):
        """生成神灵使者: 属性取同层小怪均值, 随层数增强, 与同层怪接近."""
        fgroup = FLOOR_MONSTERS.get(min(self.floor, 4), FLOOR_MONSTERS[4])
        pool = fgroup["normal"]
        n = len(pool)
        avg_hp = sum(m["hp"] for m in pool) // n
        avg_atk = sum(m["atk"] for m in pool) // n
        avg_exp = sum(m["exp"] for m in pool) // n
        avg_gold = sum(m["gold"] for m in pool) // n
        data = dict(
            name="神灵使者", key="divine_messenger",
            hp=avg_hp, atk=avg_atk,
            acts=("attack", "smash", "double"),
            exp=avg_exp, gold=avg_gold,
            art=MONSTER_ART["divine_messenger"],
            desc="降临人间的神之使者, 被击杀后会以半血姿态复活.",
        )
        e = Enemy(data)
        e.key = "divine_messenger"
        e.can_revive = True
        # 层数缩放 (与普通小怪一致, 随层数增强)
        scale = 1.0 + (self.floor - 1) * 0.35
        e.hp = int(e.hp * scale)
        e.max_hp = e.hp
        e.atk = int(e.atk * scale)
        return e

    def start_battle(self, monster, boss=False, strong=False):
        enemy = self._make_enemy(monster, boss, strong)
        self.combat = RpgCombat(self.player, enemy, self.rng)
        self.battle_log = []
        self.boss_fight = boss
        self.strong_boss = strong
        self.divine_fight = False
        self._player_revived = False
        self.render_battle()

    def start_abyss_elite_battle(self):
        """异界特殊精英战 (隐藏层第一节点, 二选一)."""
        key = self.rng.choice(list(ABYSS_ELITES.keys()))
        data = ABYSS_ELITES[key]
        e = Enemy(data)
        e.key = data["key"]
        e.special = True
        # 数值与第二层相似, 层数越高略增强
        scale = 1.0 + (self.floor - 2) * 0.25
        e.hp = int(e.hp * max(1.0, scale))
        e.max_hp = e.hp
        e.atk = int(e.atk * max(1.0, scale))
        self.combat = RpgCombat(self.player, e, self.rng)
        self.battle_log = []
        self.boss_fight = False
        self.strong_boss = False
        self.divine_fight = False
        self._player_revived = False
        self.render_battle()

    def start_divine_battle(self):
        """神灵使者战: 特殊小怪, 被击杀后半血复活一次."""
        enemy = self._make_divine_enemy()
        self.combat = RpgCombat(self.player, enemy, self.rng)
        self.battle_log = []
        self.boss_fight = False
        self.strong_boss = False
        self.divine_fight = True
        self._player_revived = False
        self.render_battle()

    def render_battle(self):
        self._push_view(self.render_battle)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        c = self.combat
        e = c.enemy

        if self.boss_fight:
            ttl = "☠ 强化关底首领战 (行动力耗尽)" if getattr(self, "strong_boss", False) else "👑 关底首领战"
            tk.Label(self.content, text=ttl, bg=COLOR_BG, fg=COLOR_ACCENT,
                     font=FONT_TITLE).pack(pady=(2, 4))
        elif getattr(self, "divine_fight", False):
            tk.Label(self.content, text="✨ 神灵使者战", bg=COLOR_BG, fg="#ffd75e",
                     font=FONT_TITLE).pack(pady=(2, 4))
        elif getattr(c.enemy, "special", False):
            tk.Label(self.content, text="🌀 异界特殊精英战", bg=COLOR_BG, fg="#ff79c6",
                     font=FONT_TITLE).pack(pady=(2, 4))

        # 敌人区
        enemy_frame = tk.Frame(self.content, bg=COLOR_BG)
        enemy_frame.pack(fill="x", padx=10)
        self._render_enemy(enemy_frame, e)

        # 战斗日志 (多行, 显示玩家行动与敌人反击)
        log_txt = "\n".join(self.battle_log) if self.battle_log else ""
        self.battle_log_label = tk.Label(self.content, text=log_txt, bg=COLOR_BG,
                                         fg=COLOR_TEXT, font=FONT_MAIN, justify="left",
                                         anchor="w")
        self.battle_log_label.pack(pady=(6, 2), padx=16)

        # 玩家状态
        self._render_player_status()

        # 行动区 (底部)
        self._render_actions()

    def _render_enemy(self, parent, e):
        panel = tk.Frame(parent, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER,
                         highlightthickness=1)
        panel.pack(fill="x", pady=3)
        artbox = tk.Frame(panel, bg=COLOR_PANEL)
        artbox.pack(side="left", padx=(8, 12))
        art_txt = "\n".join(e.art)
        tk.Label(artbox, text=art_txt, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MONO, justify="left").pack()
        info = tk.Frame(panel, bg=COLOR_PANEL)
        info.pack(side="left", padx=6, pady=6)
        name = e.name
        if e.block:
            name += f"   ⛨{e.block}"
        if e.bonus_atk:
            name += f"   ⚡+{e.bonus_atk}"
        tk.Label(info, text=name, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w")
        self._render_hpbar(info, e)
        # 异常状态显示
        if e.ail_text:
            tk.Label(info, text="  " + e.ail_text, bg=COLOR_PANEL, fg="#ff79c6",
                     font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", pady=(2, 0))
        # 显示最近一次受击的各段伤害 (伤害数字)
        if e.last_hits:
            dmg_txt = "  ".join(f"-{d}" for d in e.last_hits)
            tk.Label(info, text=dmg_txt, bg=COLOR_PANEL, fg=COLOR_BAD,
                     font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(2, 0))

    def _render_hpbar(self, parent, e):
        bar = tk.Canvas(parent, width=280, height=18, bg=COLOR_PANEL, highlightthickness=0)
        bar.pack(anchor="w", pady=(4, 2))
        ratio = max(0, min(1, e.hp / e.max_hp))
        fw = int(280 * ratio)
        color = COLOR_OK if ratio > 0.5 else (COLOR_GOLD if ratio > 0.25 else COLOR_HP)
        bar.create_rectangle(2, 2, 2 + fw, 16, fill=color, outline="")
        bar.create_text(140, 10, text=f"{e.hp} / {e.max_hp}", fill=COLOR_TEXT,
                        font=("Microsoft YaHei UI", 8))

    def _render_player_status(self):
        p = self.player
        panel = self._panel()
        panel.pack(fill="x", padx=10, pady=6)
        row = tk.Frame(panel, bg=COLOR_PANEL)
        row.pack(padx=12, pady=6)
        tk.Label(row, text=f"Lv.{p.level}", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 13, "bold")).pack(side="left", padx=(0, 12))
        tk.Label(row, text=f"❤ {p.hp}/{p.max_hp}", bg=COLOR_PANEL, fg=COLOR_HP,
                 font=FONT_MAIN).pack(side="left", padx=8)
        tk.Label(row, text=f"✦ {p.mp}/{p.max_mp}", bg=COLOR_PANEL, fg=COLOR_MP,
                 font=FONT_MAIN).pack(side="left", padx=8)
        if p.block:
            tk.Label(row, text=f"⛨ {p.block}", bg=COLOR_PANEL, fg=COLOR_SELECT,
                     font=FONT_MAIN).pack(side="left", padx=8)
        if p.battle_atk_bonus:
            tk.Label(row, text=f"⚡+{p.battle_atk_bonus}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=FONT_MAIN).pack(side="left", padx=8)
        wd = p.weapon_data
        tk.Label(row, text=f"🗡 攻击 {p.total_atk()}", bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MAIN).pack(side="right", padx=8)
        tk.Label(row, text=f"🔨 {wd['name']}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                 font=FONT_MAIN).pack(side="right", padx=8)
        if p.trinket_data:
            tk.Label(row, text=f"◆ {p.trinket_data['name']}", bg=COLOR_PANEL,
                     fg=COLOR_ACCENT, font=FONT_MAIN).pack(side="right", padx=8)
        if p.offhand_data:
            tk.Label(row, text=f"✦ {p.offhand_data['name']}", bg=COLOR_PANEL,
                     fg="#ff79c6", font=FONT_MAIN).pack(side="right", padx=8)

    def _render_actions(self):
        c = self.combat
        p = self.player
        # 主行动按钮
        self._btn(self.action_inner, "⚔ 攻击", self.battle_attack, color=COLOR_BAD)
        self._btn(self.action_inner, "🛡 防御", self.battle_defend, color=COLOR_SELECT)
        self._btn(self.action_inner, "☕ 休息", self.battle_rest, color=COLOR_OK)
        # 技能按钮 (打开技能面板弹窗)
        n_skill = len([s for s, _ in p.skills_data() if s not in ("attack", "defend")])
        self._btn(self.action_inner, f"✦ 技能 ({n_skill})", self._open_skill_panel, color=COLOR_BTN)
        # 药水 (同种合并显示, 如 蓝量药水*3)
        for pid, cnt in self._potion_counts().items():
            pot = POTION_LIB[pid]
            label = f"🧪 {pot['name']}" + (f"*{cnt}" if cnt > 1 else "")
            self._btn(self.action_inner, label,
                      lambda pid=pid: self.battle_potion(pid), color=COLOR_GOLD)

    def _open_skill_panel(self):
        """弹出技能面板: 列出所有可用技能, 点击施放."""
        c = self.combat
        p = self.player
        win = tk.Toplevel(self.root)
        win.title("✦ 技能")
        win.configure(bg=COLOR_BG)
        win.geometry("600x680")
        win.transient(self.root)
        win.grab_set()
        win.attributes("-topmost", True)
        tk.Label(win, text="✦ 选择技能", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(10, 4))
        tk.Label(win, text=f"蓝量 {p.mp}/{p.max_mp}", bg=COLOR_BG, fg=COLOR_MP,
                 font=FONT_MAIN).pack(pady=(0, 8))

        canvas, inner, scroll = self._scroll_container_into(win)

        for sid, sk in p.skills_data():
            if sid in ("attack", "defend"):
                continue
            cost = sk["mp"]
            ready = c.skill_ready(sid)
            cd = c.skill_cd.get(sid, 0)
            src = "武器"
            if sid in p.weapon_skills:
                src = "武器"
            elif sid == p.offhand_skill:
                src = "副手"
            else:
                src = "Lv"
            # 状态标记
            if cd > 0:
                status = f"  ⏳冷却 {cd}"
                color = "#3a3a55"
            elif p.mp < cost:
                status = f"  ({cost}✦) 蓝不足"
                color = "#3a3a55"
            else:
                status = f"  ({cost}✦)"
                color = COLOR_BTN
            row = tk.Frame(inner, bg=color, highlightbackground=COLOR_BORDER,
                           highlightthickness=1)
            row.pack(fill="x", padx=10, pady=3)
            title_txt = f"  {sk['name']}{status}   [{src}]"
            if sk.get("cooldown"):
                title_txt += "  (两回合一次)"
            elif sk.get("hits"):
                title_txt += f"  (连击x{sk['hits']})"
            tk.Label(row, text=title_txt, bg=color, fg=COLOR_TEXT,
                     font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            tk.Label(row, text="     " + sk["desc"], bg=color, fg=COLOR_SUB,
                     font=FONT_MAIN, wraplength=500, justify="left").pack(anchor="w", padx=10, pady=(1, 3))
            if ready:
                b = tk.Button(row, text="施 放", bg=COLOR_OK, fg=COLOR_TEXT, relief="flat",
                              font=FONT_MAIN, bd=0, cursor="hand2", padx=14, pady=3,
                              command=lambda s=sid: self._cast_from_panel(win, s))
                b.pack(anchor="e", padx=10, pady=(0, 5))

        tk.Button(win, text="✖ 关闭", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=18, pady=4,
                  command=win.destroy).pack(pady=(6, 10))

    def _cast_from_panel(self, win, sid):
        """从技能面板施放技能后关闭面板."""
        win.destroy()
        self.battle_skill(sid)

    # 玩家行动执行 -> 敌人反击 -> 检查胜负 -> 回玩家回合
    def _do_action(self, msg):
        self.battle_log = [msg]
        # 技能冷却递减 (每回合)
        if self.combat:
            self.combat.tick_cooldowns()
        # 玩家击杀敌人: 神灵使者会半血复活一次
        if not self.combat.enemy.alive:
            if self._try_revive_enemy():
                return
            self._after_combat_tick()
            return
        # 额外回合 (达因斯莱夫 3次技能后触发): 跳过敌人回合, 玩家再行动
        if getattr(self.combat, "extra_turn", False):
            self.combat.extra_turn = False
            self.battle_log.append("⏳ 你获得额外回合!")
            self._after_combat_tick()
            return
        # 敌人回合
        enemy_logs = self.combat.enemy_turn()
        self.battle_log += enemy_logs
        self._after_combat_tick()

    def _try_revive_enemy(self):
        """神灵使者被击杀后半血复活一次."""
        e = self.combat.enemy
        if getattr(e, "can_revive", False) and not getattr(e, "revived", False):
            e.revived = True
            e.hp = max(1, e.max_hp // 2)
            e.block = 0
            e.bonus_atk = 0
            e.last_hits = []
            self.battle_log.append(f"✨ {e.name} 被击杀, 但神性之力涌动, 以半血姿态复活了!")
            self.render_battle()
            return True
        return False

    def _try_revive_player(self):
        """神灵护身符被动: 玩家被击败后半血复活一次."""
        if "divine_revive" in self.player.passives and not getattr(self, "_player_revived", False):
            self._player_revived = True
            self.player.hp = max(1, self.player.max_hp // 2)
            self.battle_log.append("✨ 神灵护身符闪耀, 你以半血姿态复活了!")
            self.render_battle()
            return True
        return False

    def _after_combat_tick(self):
        c = self.combat
        # 战号攻击倍率持续时间结算 (施放当回合不扣减)
        if self.combat and getattr(self.combat, "buff_cast_round", False):
            self.combat.buff_cast_round = False
        elif self.player.battle_atk_mult_remaining > 0:
            self.player.battle_atk_mult_remaining -= 1
            if self.player.battle_atk_mult_remaining <= 0:
                self.player.battle_atk_mult = 1.0
        # 打靶模式: 靶子与玩家血量超厚, 倒下即重置, 持续测量 DPS
        if getattr(self, "target_mode", False):
            if c.enemy.hp <= 0:
                c.enemy.hp = c.enemy.max_hp
                c.enemy.block = 0
                self.battle_log.append("🎯 靶子被打烂, 靶场立刻重置!")
            if self.player.hp <= 0:
                self.player.hp = self.player.max_hp
                self.player.block = 0
                self.battle_log.append("💀 你被靶子打倒, 靶场立刻将你救起!")
            # 回蓝 (被动)
            if self.combat.regen_mp > 0:
                self.player.mp = min(self.player.max_mp, self.player.mp + self.combat.regen_mp)
            self._track_target_dps()
            self.render_target_battle()
            return
        if not c.enemy.alive:
            self.battle_victory()
            return
        if self.player.hp <= 0:
            if self._try_revive_player():
                return
            self.player.hp = 0
            self.battle_defeat()
            return
        # 回蓝 (被动)
        if self.combat.regen_mp > 0:
            self.player.mp = min(self.player.max_mp, self.player.mp + self.combat.regen_mp)
        self.render_battle()

    def _track_target_dps(self):
        """打靶模式: 累计对靶子造成的伤害并更新平均每回合伤害."""
        if not getattr(self, "target_mode", False) or not self.combat:
            return
        e = self.combat.enemy
        if self.target_prev_hp is None:
            self.target_prev_hp = e.hp
            return
        dmg = self.target_prev_hp - e.hp
        if dmg < 0:
            dmg = 0
        self.target_prev_hp = e.hp
        self.target_total_damage += dmg
        self.target_turns += 1
        self.target_avg = self.target_total_damage / max(1, self.target_turns)

    # ---------------- 打靶模式 (靶场沙盒) ----------------
    def start_target_mode(self):
        """进入打靶模式: 靶子每回合攻击 x 点, 双方血量 99999999, 测量平均每回合伤害."""
        p = self.player
        # 保存进入靶场前的玩家状态 (退出时恢复)
        self.target_saved_state = dict(
            max_hp=p.max_hp, hp=p.hp, max_mp=p.max_mp, mp=p.mp,
            weapon=p.weapon, offhand=p.offhand, accessory=p.accessory,
            weapon_hp_bonus=p.weapon_hp_bonus, weapon_mp_bonus=p.weapon_mp_bonus,
            trinket_hp_bonus=p.trinket_hp_bonus, trinket_mp_bonus=p.trinket_mp_bonus,
            offhand_hp_bonus=p.offhand_hp_bonus, offhand_mp_bonus=p.offhand_mp_bonus,
            bag=list(p.bag), offhands=list(p.offhands), trinkets=list(p.trinkets),
            all_skills=p.all_skills,
        )
        self.target_mode = True
        self.target_attack = 50
        self.target_total_damage = 0
        self.target_turns = 0
        self.target_avg = 0.0
        self.target_prev_hp = None
        # 双方血量设为 99999999, 能量(蓝量)无限, 解锁全部升级技能
        p.max_hp = 99999999
        p.hp = 99999999
        p.max_mp = 999999999
        p.mp = 999999999
        p.all_skills = True
        # 生成靶子敌人
        e = Enemy(dict(
            name="练习靶子", key="dummy", hp=99999999, atk=self.target_attack,
            acts=("attack",), exp=0, gold=0,
            art=["  ████████",
                 "  ████████",
                 "  ██▉  ██▉",
                 "   ▀▀▀▀▀▀▀"],
            desc="只会攻击的练习靶子, 每回合对你造成 x 点伤害.",
        ))
        e.max_hp = 99999999
        self.combat = RpgCombat(p, e, self.rng)
        self.battle_log = []
        self.boss_fight = False
        self.divine_fight = False
        self._player_revived = False
        self.render_target_battle()

    def render_target_battle(self):
        self._push_view(self.render_target_battle)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        c = self.combat
        e = c.enemy

        tk.Label(self.content, text="🎯 打靶模式", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(2, 4))

        # 敌人区 (靶子)
        enemy_frame = tk.Frame(self.content, bg=COLOR_BG)
        enemy_frame.pack(fill="x", padx=10)
        self._render_enemy(enemy_frame, e)

        # 打靶专属控制面板: DPS 统计 + x 调整 + 装备/退出
        ctl = self._panel()
        ctl.pack(fill="x", padx=10, pady=4)
        avg_txt = f"{self.target_avg:.1f}"
        tk.Label(ctl, text=(f"  累计伤害 {self.target_total_damage}   回合数 {self.target_turns}   "
                            f"平均每回合 {avg_txt}"),
                 bg=COLOR_PANEL, fg=COLOR_GOLD,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        row = tk.Frame(ctl, bg=COLOR_PANEL)
        row.pack(anchor="w", padx=16, pady=(0, 6))
        tk.Label(row, text=f"靶子攻击伤害 x = {self.target_attack}", bg=COLOR_PANEL,
                 fg=COLOR_TEXT, font=FONT_MAIN).pack(side="left", padx=(0, 10))
        tk.Button(row, text="-10", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=10, pady=2,
                  command=lambda: self.target_adjust_x(-10)).pack(side="left", padx=2)
        tk.Button(row, text="-1", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=10, pady=2,
                  command=lambda: self.target_adjust_x(-1)).pack(side="left", padx=2)
        tk.Button(row, text="+1", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=10, pady=2,
                  command=lambda: self.target_adjust_x(1)).pack(side="left", padx=2)
        tk.Button(row, text="+10", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=10, pady=2,
                  command=lambda: self.target_adjust_x(10)).pack(side="left", padx=2)
        tk.Button(row, text="🎒 切换武器/副手/饰品", bg=COLOR_SELECT, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=12, pady=2,
                  command=self.target_equip).pack(side="left", padx=8)
        tk.Button(row, text="↩ 退出靶场", bg=COLOR_BAD, fg=COLOR_TEXT, relief="flat",
                  font=FONT_MAIN, bd=0, cursor="hand2", padx=12, pady=2,
                  command=self.exit_target_mode).pack(side="left", padx=8)

        # 战斗日志
        log_txt = "\n".join(self.battle_log) if self.battle_log else ""
        self.battle_log_label = tk.Label(self.content, text=log_txt, bg=COLOR_BG,
                                         fg=COLOR_TEXT, font=FONT_MAIN, justify="left",
                                         anchor="w")
        self.battle_log_label.pack(pady=(6, 2), padx=16)

        # 玩家状态
        self._render_player_status()

        # 行动区
        self._render_target_actions()

    def _render_target_actions(self):
        c = self.combat
        p = self.player
        self._btn(self.action_inner, "⚔ 攻击", self.battle_attack, color=COLOR_BAD)
        self._btn(self.action_inner, "🛡 防御", self.battle_defend, color=COLOR_SELECT)
        self._btn(self.action_inner, "☕ 休息", self.battle_rest, color=COLOR_OK)
        n_skill = len([s for s, _ in p.skills_data() if s not in ("attack", "defend")])
        self._btn(self.action_inner, f"✦ 技能 ({n_skill})", self._open_skill_panel, color=COLOR_BTN)
        for pid, cnt in self._potion_counts().items():
            pot = POTION_LIB[pid]
            label = f"🧪 {pot['name']}" + (f"*{cnt}" if cnt > 1 else "")
            self._btn(self.action_inner, label,
                      lambda pid=pid: self.battle_potion(pid), color=COLOR_GOLD)

    def target_adjust_x(self, delta):
        """调整靶子每回合攻击伤害 x."""
        self.target_attack = max(0, self.target_attack + delta)
        if self.combat:
            self.combat.enemy.atk = self.target_attack
        self.render_target_battle()

    def _force_target_hp(self):
        self.player.max_hp = 99999999
        self.player.hp = 99999999
        self.player.max_mp = 999999999
        self.player.mp = 999999999
        self.player.all_skills = True

    def target_equip(self):
        """靶场装备切换: 可自由装备任意武器/副手/饰品 (无需持有)."""
        self._push_view(self.target_equip)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="🎯 靶场 · 自由切换装备", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(8, 4))
        tk.Label(self.content, text="可装备任意武器 / 副手 / 饰品 (靶场提供全图鉴, 无需持有)",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 6))

        canvas, inner, scroll = self._scroll_container()

        # 武器
        wpn = self._panel(inner)
        wpn.pack(fill="x", padx=10, pady=3)
        tk.Label(wpn, text="— 武器 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        for wid, w in WEAPON_LIB.items():
            row = tk.Frame(wpn, bg=COLOR_PANEL)
            row.pack(fill="x", padx=16, pady=1)
            rowi = tk.Frame(row, bg=COLOR_PANEL)
            rowi.pack(side="left", fill="x", expand=True, anchor="w")
            _sn = "、".join(SKILL_LIB[s]["name"] for s in w.get("skills", [w["skill"]]))
            txt = (f"🔨 {w['name']}  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}"
                   f"  技能:{_sn}")
            if w.get("ail"):
                txt += f"  ⚠{ail_desc(w['ail'])}"
            tk.Label(rowi, text=txt, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(anchor="w")
            cur = " [当前]" if p.weapon == wid else ""
            tk.Button(row, text="装备" + cur, bg=(COLOR_OK if p.weapon == wid else COLOR_BTN),
                      fg=COLOR_TEXT, relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                      padx=8, pady=2,
                      command=lambda wid=wid: self.target_equip_weapon(wid)).pack(side="right")

        # 副手
        ohs = self._panel(inner)
        ohs.pack(fill="x", padx=10, pady=3)
        tk.Label(ohs, text="— 副手 (属性按1/3计入) —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        for oid, o in OFFHAND_LIB.items():
            row = tk.Frame(ohs, bg=COLOR_PANEL)
            row.pack(fill="x", padx=16, pady=1)
            rowi = tk.Frame(row, bg=COLOR_PANEL)
            rowi.pack(side="left", fill="x", expand=True, anchor="w")
            sk = SKILL_LIB[o["skill"]]
            txt = (f"✦ {o['name']}  攻击+{o['atk']//3} 生命+{o['hp']//3} 蓝量+{o['mp']//3}"
                   f"  技能:{sk['name']}")
            if o.get("ail"):
                txt += f"  ⚠{ail_desc(o['ail'])}"
            tk.Label(rowi, text=txt, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(anchor="w")
            cur = " [当前]" if p.offhand == oid else ""
            tk.Button(row, text="装备" + cur, bg=(COLOR_OK if p.offhand == oid else COLOR_BTN),
                      fg=COLOR_TEXT, relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                      padx=8, pady=2,
                      command=lambda oid=oid: self.target_equip_offhand(oid)).pack(side="right")

        # 饰品
        trk = self._panel(inner)
        trk.pack(fill="x", padx=10, pady=3)
        tk.Label(trk, text="— 饰品 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        for tid, t in TRINKET_LIB.items():
            row = tk.Frame(trk, bg=COLOR_PANEL)
            row.pack(fill="x", padx=16, pady=1)
            rowi = tk.Frame(row, bg=COLOR_PANEL)
            rowi.pack(side="left", fill="x", expand=True, anchor="w")
            txt = f"◆ {t['name']}  攻击+{t['atk']} 生命+{t['hp']} 蓝量+{t['mp']}"
            if t.get("passive"):
                txt += f"  被动:{PASSIVE_NAME.get(t['passive'], t['passive'])}"
            tk.Label(rowi, text=txt, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(anchor="w")
            cur = " [当前]" if p.accessory == tid else ""
            tk.Button(row, text="装备" + cur, bg=(COLOR_OK if p.accessory == tid else COLOR_BTN),
                      fg=COLOR_TEXT, relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                      padx=8, pady=2,
                      command=lambda tid=tid: self.target_equip_trinket(tid)).pack(side="right")

        self._btn(self.action_inner, "↩ 返回靶场", self.render_target_battle, color=COLOR_BTN)

    def target_equip_weapon(self, wid):
        self.player.equip_weapon(wid)
        self._force_target_hp()
        self.render_target_battle()

    def target_equip_offhand(self, oid):
        self.player.equip_offhand(oid)
        self._force_target_hp()
        self.render_target_battle()

    def target_equip_trinket(self, tid):
        self.player.equip_trinket(tid)
        self._force_target_hp()
        self.render_target_battle()

    def exit_target_mode(self):
        """退出靶场, 恢复进入前的玩家状态."""
        s = self.target_saved_state or {}
        p = self.player
        for k in ("max_hp", "hp", "max_mp", "mp", "weapon", "offhand", "accessory",
                  "weapon_hp_bonus", "weapon_mp_bonus", "trinket_hp_bonus", "trinket_mp_bonus",
                  "offhand_hp_bonus", "offhand_mp_bonus", "all_skills"):
            if k in s:
                setattr(p, k, s[k])
        if "bag" in s:
            p.bag = list(s["bag"])
        if "offhands" in s:
            p.offhands = list(s["offhands"])
        if "trinkets" in s:
            p.trinkets = list(s["trinkets"])
        self.target_mode = False
        self.target_saved_state = None
        self.combat = None
        self.show_menu()

    def battle_attack(self):
        self._target_start_round()
        msg = self.combat.player_attack()
        self._do_action(msg)

    def _target_start_round(self):
        """打靶模式: 记录本回合开始时靶子血量 (须在玩家行动前调用)."""
        if getattr(self, "target_mode", False) and self.combat:
            self.target_prev_hp = self.combat.enemy.hp

    def battle_defend(self):
        self._target_start_round()
        msg = self.combat.player_defend()
        self._do_action(msg)

    def battle_skill(self, sid):
        self._target_start_round()
        msg = self.combat.player_skill(sid)
        if msg == "no_mp":
            self._set_log("蓝量不足!")
            return
        if msg == "cooldown":
            self._set_log("技能冷却中, 还需等待!")
            return
        if msg == "no_burn":
            self._set_log("敌人身上没有永久烧伤, 无法引爆!")
            return
        self._do_action(msg)

    def battle_potion(self, pid):
        if pid not in self.player.potions:
            return
        self.player.potions.remove(pid)   # 用一瓶减一
        self._target_start_round()
        msg = self.combat.player_potion(pid)
        self._do_action(msg)

    def battle_rest(self):
        self._target_start_round()
        msg = self.combat.player_rest()
        self._do_action(msg)

    def _potion_counts(self):
        """按药水类型计数, 保持插入顺序 (用于合并显示)."""
        counts = {}
        for pid in self.player.potions:
            counts[pid] = counts.get(pid, 0) + 1
        return counts

    def _set_log(self, text):
        if hasattr(self, "battle_log_label"):
            self.battle_log_label.configure(text="  " + text, fg=COLOR_SUB)

    def battle_victory(self):
        c = self.combat
        e = c.enemy
        g = self.player.reward_gold(e.gold)
        leveled = self.player.gain_exp(e.exp)
        # 精英/首领/小怪掉落 (材料 + 装备等)
        drop = ""
        if self.boss_fight:
            drop = self._boss_drop()
        elif getattr(self, "divine_fight", False):
            drop = self._divine_drop()
        elif self.map_nodes.get(self.current_node) == "elite":
            drop = self._elite_drop()
        elif self.map_nodes.get(self.current_node) == "abyss_elite":
            drop = self._elite_drop() + " + " + self._drop_specific_material(
                self.rng.choice(["soul_ash", "shadow_shard", "nether_core"]), 1)
        else:
            drop = self._normal_drop()

        self._clear_content()
        self._clear_actions()
        self._update_status()
        lines = [f"🏆 胜利!  击败了 {e.name}"]
        lines.append(f"💰 获得 {g} 金币   ✦ 经验 +{e.exp}")
        if leveled:
            p = self.player
            lines.append(f"⬆ 升级到 Lv.{p.level}!  生命+12  蓝量+8 (已回满)")
        if drop:
            lines.append("🎁 " + drop)
        panel = self._panel()
        panel.pack(expand=True)
        for ln in lines:
            tk.Label(panel, text=ln, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_TITLE).pack(pady=4)
        if self.boss_fight:
            self._btn(self.action_inner, "击败Boss! 进入下一层 ▶", self.boss_clear, color=COLOR_OK)
        else:
            self._btn(self.action_inner, "继续 ▶", self.after_node, color=COLOR_OK)

    def _drop_materials(self, count, max_tier):
        """随机掉落 count 个材料 (tier <= max_tier), 返回日志文本."""
        if count <= 0:
            return ""
        gained = []
        for _ in range(count):
            tier = self.rng.randint(1, max_tier)
            mid = self.rng.choice(MATERIAL_POOL[tier])
            self.player.add_material(mid)
            gained.append(MATERIAL_LIB[mid]["name"])
        return "掉落材料: " + ", ".join(gained)

    def _elite_drop(self):
        # 精英必定掉武器 + 饰品 + 材料 (含中级) + 药水 (副手仅商店第二层后可得)
        parts = []
        parts.append(self._offer_random_weapon("精英掉落"))
        parts.append(self._offer_random_trinket("精英掉落"))
        parts.append(self._drop_materials(self.rng.randint(2, 3), 2))
        if self.rng.random() < 0.5:
            pid = self.rng.choice(["hp", "mp", "atk"])
            self.player.potions.append(pid)
            parts.append(f"掉落药水: {POTION_LIB[pid]['name']}")
        return " + ".join(p for p in parts if p)

    def _boss_drop(self):
        # boss 必定掉 高级武器 + 饰品 + 大量材料(含高级) + 专属装备 + 专属材料 (副手仅商店第二层后可得)
        parts = ["大治疗药水"]
        self.player.potions.append("big_hp")
        parts.append(self._offer_random_weapon("Boss掉落", tier_min=3))
        parts.append(self._offer_random_trinket("Boss掉落", tier_min=2))
        parts.append(self._drop_materials(self.rng.randint(4, 5), 3))
        # 专属掉落: 由当前 boss 所在楼层决定
        fl = min(self.floor, 4)
        if fl == 4:
            # 神界 Boss (至高神): 掉神灵碎片 + 坚钢
            parts.append(self._drop_specific_material("divine_shard", 2))
            parts.append(self._drop_specific_material("adamantite", 1))
        elif fl == 3:
            # 冥界深处 Boss: 掉幽冥核心
            parts.append(self._drop_specific_material("nether_core", 1))
            parts.append(self._drop_specific_material("soul_ash", 1))
        elif fl == 2:
            # 冥界 Boss: 掉龙骨 + 灵魂灰烬
            parts.append(self._drop_specific_material("dragonbone", 1))
            parts.append(self._drop_specific_material("soul_ash", 1))
        else:
            # 地表 Boss (远古巨龙 / 巫妖王)
            boss_key = self.combat.enemy.key
            if boss_key == "lich":
                parts.append(self._drop_specific_material("lich_soul", 1))
                self.player.add_trinket("lich_ring")
                parts.append("获得Boss专属饰品【亡魂戒指】")
            else:  # dragon
                parts.append(self._drop_specific_material("dragon_scale", 1))
                self.player.add_trinket("dragon_amulet")
                parts.append("获得Boss专属饰品【龙鳞护符】")
        return " + ".join(parts)

    def _drop_specific_material(self, mid, n):
        """掉落指定材料 n 个, 返回日志文本."""
        self.player.add_material(mid, n)
        return f"获得专属材料【{MATERIAL_LIB[mid]['name']}】×{n}"

    def _normal_drop(self):
        # 小怪: 必掉材料 (1-2个 tier1), 概率掉武器/饰品/药水 (副手仅商店第二层后可得)
        parts = [self._drop_materials(self.rng.randint(1, 2), 1)]
        r = self.rng.random()
        if r < 0.18:
            parts.append(self._offer_random_weapon("小怪掉落"))
        elif r < 0.32:
            parts.append(self._offer_random_trinket("小怪掉落"))
        if self.rng.random() < 0.25:
            pid = self.rng.choice(["hp", "mp", "atk"])
            self.player.potions.append(pid)
            parts.append(f"掉落药水: {POTION_LIB[pid]['name']}")
        return " + ".join(p for p in parts if p)

    def _divine_drop(self):
        # 神灵使者: 必掉神灵碎片 + 常规小怪掉落
        parts = [self._drop_specific_material("divine_shard", 1)]
        parts.append(self._normal_drop())
        return " + ".join(p for p in parts if p)

    def _offer_random_weapon(self, source, tier_min=1, force_better=False):
        """随机给一把武器, 存入背包 (不自动装备). 神器/超神器仅能通过合成获得, 不直接掉落."""
        pool = [w for w in WEAPON_LIB
                if WEAPON_LIB[w]["tier"] >= tier_min
                and w not in ARTIFACT_WEAPONS and w not in SUPER_ARTIFACT_WEAPONS]
        pick = self.rng.choice(pool)
        w = WEAPON_LIB[pick]
        self.player.add_weapon_to_bag(pick)
        return f"获得武器【{w['name']}】(已存入背包)"

    def _offer_random_trinket(self, source, tier_min=1):
        """随机给一件饰品, 存入饰品栏 (不自动装备). 排除Boss专属/仅合成饰品."""
        pool = [t for t in TRINKET_LIB
                if TRINKET_LIB[t]["tier"] >= tier_min
                and t not in ("dragon_amulet", "lich_ring", "divine_amulet", "reborn_amulet")]
        tid = self.rng.choice(pool)
        t = TRINKET_LIB[tid]
        self.player.add_trinket(tid)
        return f"获得饰品【{t['name']}】(已存入饰品栏)"

    def _offer_random_offhand(self, source):
        """随机给一件副手武器, 存入副手栏 (不自动装备)."""
        oid = self.rng.choice(list(OFFHAND_LIB.keys()))
        o = OFFHAND_LIB[oid]
        self.player.add_offhand_to_bag(oid)
        return f"获得副手【{o['name']}】(已存入副手栏)"

    def _apply_weapon_hp(self):
        """武器生命加成已在 equip_weapon 中处理, 保留占位."""
        pass

    def boss_clear(self):
        """击败Boss: 第四层Boss视为真结局通关; 第三层需持新生护符进入第四层."""
        if self.floor >= 4:
            self.show_true_ending()
        elif self.floor == 3:
            if self._has_reborn_amulet():
                self.next_floor()
            else:
                self.show_victory()
        else:
            self.next_floor()

    def _has_reborn_amulet(self):
        """是否持有新生护符 (装备中或饰品栏)."""
        p = self.player
        return p.accessory == "reborn_amulet" or "reborn_amulet" in p.trinkets

    def next_floor(self):
        """进入下一层: 行动力重置, 回复部分状态, 重新生成地图, 敌人更强."""
        self.floor += 1
        # 新层商店重新进货 (第2层起商店出售 tier4 非神器)
        for attr in ("_shop_items", "_shop_trinkets", "_shop_potions"):
            if hasattr(self, attr):
                delattr(self, attr)
        p = self.player
        p.action = p.max_action
        p.hp = min(p.max_hp, p.hp + 30)
        p.mp = min(p.max_mp, p.mp + 20)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text=f"🏆 击败Boss! 进入第 {self.floor} 层",
                 bg=COLOR_BG, fg=COLOR_OK, font=FONT_BIG).pack(pady=14)
        tk.Label(self.content, text=f"行动力已重置为 {p.max_action}, 回复 30 生命 20 蓝量. 敌人更强了!",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_MAIN).pack()
        self._btn(self.action_inner, "进入新层 ▶", self.begin_floor, color=COLOR_OK)

    def show_victory(self):
        """通关(未达成真结局): 击败第三层Boss."""
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🏆 通 关!", bg=COLOR_BG, fg=COLOR_OK,
                 font=FONT_BIG).pack(pady=16)
        tk.Label(self.content, text="你击败了第三层的关底Boss!",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE).pack(pady=6)
        tk.Label(self.content, text="但真正的试炼尚未结束——以「异界旋涡」与「神灵碎片」合成「新生护符」, 方能踏入神界.",
                 bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_MAIN).pack(pady=4)
        tk.Label(self.content, text="感谢游玩 ⚔ Roguelite RPG",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=4)
        self._btn(self.action_inner, "返回主菜单", self.show_menu, color=COLOR_OK)

    def show_true_ending(self):
        """真结局: 击败第四层神界Boss."""
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🏆 你已通关达成真结局!", bg=COLOR_BG, fg=COLOR_OK,
                 font=FONT_BIG).pack(pady=16)
        tk.Label(self.content, text="你击败了神界的至高神, 完成了肉鸽勇士的真结局试炼!",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE).pack(pady=6)
        tk.Label(self.content, text="感谢游玩 ⚔ Roguelite RPG",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=4)
        self._btn(self.action_inner, "返回主菜单", self.show_menu, color=COLOR_OK)

    def battle_defeat(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="☠ 你倒下了...", bg=COLOR_BG, fg=COLOR_BAD,
                 font=FONT_BIG).pack(pady=16)
        self._btn(self.action_inner, "返回主菜单", self.show_menu, color=COLOR_BTN)

    # ---------------- 角色状态 ----------------
    def show_character_sheet(self):
        self._push_view(self.show_character_sheet)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        wd = p.weapon_data
        td = p.trinket_data
        tk.Label(self.content, text="🗡 角色状态", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=8)

        # 滚动容器 (内容过长时可用鼠标滚轮/拉动条拉到底部)
        canvas, inner, scroll = self._scroll_container()

        panel = self._panel(inner)
        panel.pack(fill="x", padx=10, pady=4)
        atk_str = f"基础{p.atk} + 武器{wd['atk']}"
        if td and td["atk"]:
            atk_str += f" + 饰品{td['atk']}"
        if p.offhand_data and p.offhand_data["atk"]:
            atk_str += f" + 副手{p.offhand_data['atk']//3}"
        if p.battle_atk_bonus:
            atk_str += f" + 临时{p.battle_atk_bonus}"
        rows = []
        if getattr(p, "player_class", None):
            c = CLASS_LIB[p.player_class]
            rows.append(f"职业     {c['icon']} {c['name']}")
        rows += [
            f"等级     Lv.{p.level}    经验 {p.exp}/{p.exp_needed()}",
            f"生命     ❤ {p.hp} / {p.max_hp}",
            f"蓝量     ✦ {p.mp} / {p.max_mp}",
            f"攻击     🗡 {p.total_atk()}  ({atk_str})",
            f"金币     💰 {p.gold}",
        ]
        for r in rows:
            tk.Label(panel, text=r, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)

        # 武器
        wp = self._panel(inner)
        wp.pack(fill="x", padx=10, pady=4)
        tk.Label(wp, text=f"🔨 当前武器: {wd['name']}   (攻击+{wd['atk']}, 生命+{wd['hp']}, 蓝量+{wd['mp']})",
                 bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        tk.Label(wp, text="   " + wd["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                 font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
        if wd["passive"]:
            pname = PASSIVE_NAME.get(wd["passive"], wd["passive"])
            tk.Label(wp, text=f"  被动: {pname}", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        # 饰品
        tp = self._panel(inner)
        tp.pack(fill="x", padx=10, pady=4)
        if td:
            tk.Label(tp, text=f"◆ 当前饰品: {td['name']}   (攻击+{td['atk']}, 生命+{td['hp']}, 蓝量+{td['mp']})",
                     bg=COLOR_PANEL, fg=COLOR_ACCENT, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
            tk.Label(tp, text="   " + td["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
            if td["passive"]:
                tk.Label(tp, text=f"  被动: {PASSIVE_NAME.get(td['passive'], td['passive'])}",
                         bg=COLOR_PANEL, fg=COLOR_ACCENT, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
        else:
            tk.Label(tp, text="◆ 饰品: 未装备", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        if p.trinkets:
            tk.Label(tp, text=f"  饰品栏: 持有 {len(p.trinkets)} 件 (可到「装备/背包」更换)",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        # 副手
        od = p.offhand_data
        op = self._panel(inner)
        op.pack(fill="x", padx=10, pady=4)
        if od:
            sk = SKILL_LIB[od["skill"]]
            tk.Label(op, text=f"✦ 当前副手: {od['name']}   (攻击+{od['atk']//3}, 生命+{od['hp']//3}, 蓝量+{od['mp']//3}, 属性按1/3计入)",
                     bg=COLOR_PANEL, fg="#ff79c6", font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
            tk.Label(op, text=f"  提供技能: {sk['name']} ({sk['mp']}✦) — {sk['desc']}",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
        else:
            tk.Label(op, text="✦ 副手: 未装备", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        if p.offhands:
            tk.Label(op, text=f"  副手栏: 持有 {len(p.offhands)} 件 (可到「装备/背包」更换)",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        # 技能
        sp = self._panel(inner)
        sp.pack(fill="x", padx=10, pady=4)
        tk.Label(sp, text="技能", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        for sid, sk in p.skills_data():
            cost = f" ({sk['mp']}✦)" if sk["mp"] else ""
            if sid in p.weapon_skills:
                src = "武器"
            elif sid == p.offhand_skill:
                src = "副手"
            else:
                src = "Lv解锁"
            extra = ""
            if sk.get("cooldown"):
                extra = f"  [两回合一次]"
            elif sk.get("hits"):
                extra = f"  [连击x{sk['hits']}]"
            tk.Label(sp, text=f"  {sk['name']}{cost}  —  {sk['desc']}{extra}",
                     bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        # 药水
        pp = self._panel(inner)
        pp.pack(fill="x", padx=10, pady=4)
        tk.Label(pp, text="药水", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if not p.potions:
            tk.Label(pp, text="  ( 空 )", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
        for pid, cnt in self._potion_counts().items():
            pot = POTION_LIB[pid]
            label = pot['name'] + (f" ×{cnt}" if cnt > 1 else "")
            tk.Label(pp, text=f"  🧪 {label}  —  {pot['desc']}",
                     bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        self._btn(self.action_inner, "← 返回地图", self.show_map, color=COLOR_BTN)
        self._btn(self.action_inner, "🎒 背包", self.show_bag, color=COLOR_BTN)
        self._btn(self.action_inner, "⚔ 装备", self.show_equip, color=COLOR_BTN)

    # ---------------- 宝藏 ----------------
    def show_treasure(self):
        self._push_view(self.show_treasure)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="💰 宝 藏", bg=COLOR_BG, fg=COLOR_GOLD,
                 font=FONT_TITLE).pack(pady=10)
        gold = self.rng.randint(40, 70)
        g = self.player.reward_gold(gold)
        lines = [f"你打开沉重的宝箱... 获得 {g} 金币!"]
        # 可能得药水/武器/饰品 (副手仅商店第二层后可得, 宝藏不再掉落)
        r = self.rng.random()
        extra = ""
        if r < 0.4:
            pid = self.rng.choice(["hp", "mp", "atk"])
            self.player.potions.append(pid)
            extra = f"发现一瓶{POTION_LIB[pid]['name']}!"
        elif r < 0.6:
            extra = self._offer_random_weapon("宝藏")
        elif r < 0.8:
            extra = self._offer_random_trinket("宝藏")
        if extra:
            lines.append(extra)
        panel = self._panel()
        panel.pack(expand=True)
        for ln in lines:
            tk.Label(panel, text=ln, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_TITLE).pack(pady=4)
        self._btn(self.action_inner, "继续 ▶", self.after_node, color=COLOR_OK)

    # ---------------- 事件 ----------------
    def show_event(self):
        self._push_view(self.show_event)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        ev = event_factory(self.rng)
        self._current_event = ev
        tk.Label(self.content, text="❔ 事 件", bg=COLOR_BG, fg=COLOR_SELECT,
                 font=FONT_TITLE).pack(pady=(8, 6))
        tk.Label(self.content, text=ev["title"], bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(0, 10))
        text_panel = self._panel()
        text_panel.pack(fill="x", padx=20, pady=4)
        tk.Label(text_panel, text=ev["text"], bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MAIN, wraplength=680, justify="left").pack(padx=14, pady=10)
        cho_panel = tk.Frame(self.content, bg=COLOR_BG)
        cho_panel.pack(pady=12)
        for label, kind, *rest in ev["choices"]:
            param = rest[0] if rest else {}
            b = tk.Button(cho_panel, text=label, bg=COLOR_BTN, fg=COLOR_TEXT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          command=lambda k=kind, p=param: self.resolve_event(k, p),
                          width=48, pady=7, anchor="w")
            b.pack(pady=4)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    def resolve_event(self, kind, param):
        p = self.player
        result = ""
        if kind == "mystery_potion":
            r = self.rng.random()
            if r < 0.5:
                p.hp = min(p.max_hp, p.hp + 25)
                result = "暖流涌动, 回复 25 生命."
            elif r < 0.8:
                p.mp = min(p.max_mp, p.mp + 20)
                result = "魔力充盈, 回复 20 蓝量."
            else:
                p.hp = max(1, p.hp - 15)
                result = "药剂反噬, 损失 15 生命!"
        elif kind == "save_adventurer":
            if p.potions:
                p.potions.pop(0)
                leveled = p.gain_exp(80)
                result = "你耗费一瓶药水救治了他, 获得 80 经验."
                if leveled:
                    result += f" 升级到 Lv.{p.level}!"
            else:
                p.hp = max(1, p.hp - 12)
                result = "你没有药水, 只能眼睁睁看他离去, 心情沉重 -12 生命."
        elif kind == "heal":
            p.hp = min(p.max_hp, p.hp + param["value"])
            result = f"回复 {param['value']} 生命."
        elif kind == "exp":
            leveled = p.gain_exp(param["value"])
            result = f"获得 {param['value']} 经验."
            if leveled:
                result += f" 升级到 Lv.{p.level}!"
        elif kind == "gold":
            p.gold += param["value"]
            result = f"获得 {param['value']} 金币."
        elif kind == "pool_gamble":
            r = self.rng.random()
            if r < 0.5:
                p.hp = min(p.max_hp, p.hp + 20)
                result = "清冽泉水治愈了你, 回复 20 生命."
            elif r < 0.8:
                p.mp = min(p.max_mp, p.mp + 20)
                result = "魔力涌动, 回复 20 蓝量."
            else:
                p.hp = max(1, p.hp - 20)
                result = "池水剧毒! 损失 20 生命."
        elif kind == "leave":
            result = "你转身离开."
        self._show_event_result(result)

    def _show_event_result(self, text):
        self._push_view(self._show_event_result)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="❔ 事件结果", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=16)
        panel = self._panel()
        panel.pack(expand=True)
        tk.Label(panel, text=text, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MAIN, wraplength=640, justify="center").pack(padx=20, pady=14)
        self._btn(self.action_inner, "继续 ▶", self.after_node, color=COLOR_OK)

    # ---------------- 商店 ----------------
    def show_shop(self):
        self._push_view(self.show_shop)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="🛒 商 店", bg=COLOR_BG, fg=COLOR_OK,
                 font=FONT_TITLE).pack(pady=8)
        tk.Label(self.content, text=f"💰 你的金币: {p.gold}", bg=COLOR_BG,
                 fg=COLOR_GOLD, font=FONT_TITLE).pack(pady=(0, 8))

        # 商品: 武器 + 副手 + 饰品 + 药水
        if not hasattr(self, "_shop_items"):
            # 商店出售 tier2~tier3 武器; 第2层及以上额外出售 tier4 非神器 (不含神器/超神器)
            max_tier = 4 if self.floor >= 2 else 3
            wpn_pool = [w for w in WEAPON_LIB
                        if 2 <= WEAPON_LIB[w]["tier"] <= max_tier
                        and w not in ARTIFACT_WEAPONS and w not in SUPER_ARTIFACT_WEAPONS]
            self._shop_items = self.rng.sample(wpn_pool, min(3, len(wpn_pool)))
            # 副手仅在第2层及以后的商店才可购买
            if self.floor >= 2:
                self._shop_offhands = self.rng.sample(
                    list(OFFHAND_LIB.keys()), min(2, len(OFFHAND_LIB)))
            else:
                self._shop_offhands = []
            self._shop_trinkets = self.rng.sample(
                [t for t in TRINKET_LIB if TRINKET_LIB[t]["tier"] <= 2],
                min(2, len([t for t in TRINKET_LIB if TRINKET_LIB[t]["tier"] <= 2])))
            self._shop_potions = self.rng.sample(list(POTION_LIB.keys()), 3)
            self._shop_price = {"battle_axe": 70, "magic_staff": 70, "giant_hammer": 120,
                                "steel_dagger": 65, "venom_dagger": 100, "assassin_dagger": 150,
                                "claymore": 75, "giant_blade": 110, "war_greatsword": 160,
                                "hunter_spear": 80, "steel_spear": 130,
                                "war_hammer": 105, "blood_dagger": 95,
                                "flame_blade": 175, "frost_saber": 160, "toxic_blade": 170}
            self._offhand_price = {"offhand_flame": 90, "offhand_frost": 85,
                                   "offhand_venom": 90, "offhand_blood": 95,
                                   "offhand_warhorn": 80}
            self._trinket_price = {"power_ring": 45, "vital_amulet": 45, "mana_orb": 45,
                                   "swift_band": 70, "guard_charm": 70, "lucky_clover": 70}
            self._potion_price = {"hp": 20, "mp": 15, "atk": 25, "big_hp": 45}

        panel = self._panel()
        panel.pack(fill="x", padx=20, pady=4)
        tk.Label(panel, text="— 武器 (购买后存入背包) —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        for wid in self._shop_items:
            w = WEAPON_LIB[wid]
            price = self._shop_price.get(wid, 70)
            own = (p.weapon == wid)
            txt = f"  {w['name']}  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}   {price}金币"
            if w.get("ail"):
                txt += f"  ⚠{ail_desc(w['ail'])}"
            if own:
                txt += "  (已装备)"
            b = tk.Button(panel, text=txt, bg=COLOR_BTN, fg=COLOR_TEXT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          width=60, pady=4, anchor="w",
                          command=lambda wid=wid, pr=price: self.buy_weapon(wid, pr))
            b.pack(pady=2, padx=8)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))
        tk.Label(panel, text="— 副手 (购买后存入副手栏, 属性按1/3计入) —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        if not self._shop_offhands:
            tk.Label(panel, text="  (副手仅在第2层及以后的商店出售)", bg=COLOR_PANEL,
                     fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        for oid in self._shop_offhands:
            o = OFFHAND_LIB[oid]
            price = self._offhand_price[oid]
            own = (p.offhand == oid)
            sk = SKILL_LIB[o["skill"]]
            txt = (f"  ✦ {o['name']}  攻击+{o['atk']//3} 生命+{o['hp']//3} 蓝量+{o['mp']//3}"
                   f"  技能:{sk['name']}   {price}金币")
            if own:
                txt += "  (已装备)"
            b = tk.Button(panel, text=txt, bg=COLOR_BTN, fg=COLOR_ACCENT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_ACCENT,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          width=64, pady=4, anchor="w",
                          command=lambda oid=oid, pr=price: self.buy_offhand(oid, pr))
            b.pack(pady=2, padx=8)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))
        tk.Label(panel, text="— 饰品 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        for tid in self._shop_trinkets:
            t = TRINKET_LIB[tid]
            price = self._trinket_price[tid]
            txt = f"  ◆ {t['name']}  攻击+{t['atk']} 生命+{t['hp']} 蓝量+{t['mp']}   {price}金币"
            if t["passive"]:
                txt += f"  [{PASSIVE_NAME[t['passive']]}]"
            b = tk.Button(panel, text=txt, bg=COLOR_BTN, fg=COLOR_ACCENT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_ACCENT,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          width=60, pady=4, anchor="w",
                          command=lambda tid=tid, pr=price: self.buy_trinket(tid, pr))
            b.pack(pady=2, padx=8)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))
        tk.Label(panel, text="— 药水 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        for pid in self._shop_potions:
            pot = POTION_LIB[pid]
            price = self._potion_price[pid]
            b = tk.Button(panel, text=f"  🧪 {pot['name']}  {pot['desc']}   {price}金币",
                          bg=COLOR_BTN, fg=COLOR_GOLD,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_GOLD,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          width=60, pady=4, anchor="w",
                          command=lambda pid=pid, pr=price: self.buy_potion(pid, pr))
            b.pack(pady=2, padx=8)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))
        tk.Label(self.content, text="", bg=COLOR_BG, font=FONT_MAIN).pack()
        self._btn(self.action_inner, "离开商店 ▶", self.after_node, color=COLOR_OK)
        self._btn(self.action_inner, "🎒 背包", self.show_bag, color=COLOR_BTN)

    def _shop_notice(self, text):
        self._clear_actions()
        tk.Label(self.action_inner, text="  " + text, bg=COLOR_PANEL, fg=COLOR_OK,
                 font=FONT_MAIN).pack(side="left", padx=8)
        self._btn(self.action_inner, "继续浏览", self.show_shop, color=COLOR_BTN)

    def buy_weapon(self, wid, price):
        if self.player.gold < price:
            self._shop_notice("金币不足!")
            return
        self.player.gold -= price
        self.player.add_weapon_to_bag(wid)
        self._shop_notice(f"已购买【{WEAPON_LIB[wid]['name']}】并存入背包!")

    def buy_trinket(self, tid, price):
        if self.player.gold < price:
            self._shop_notice("金币不足!")
            return
        self.player.gold -= price
        self.player.add_trinket(tid)
        self._shop_notice(f"已购买【{TRINKET_LIB[tid]['name']}】并存入饰品栏!")

    def buy_offhand(self, oid, price):
        if self.floor < 2:
            self._shop_notice("副手仅在第2层及以后的商店出售!")
            return
        if self.player.gold < price:
            self._shop_notice("金币不足!")
            return
        self.player.gold -= price
        self.player.add_offhand_to_bag(oid)
        self._shop_notice(f"已购买【{OFFHAND_LIB[oid]['name']}】并存入副手栏!")

    def buy_potion(self, pid, price):
        if self.player.gold < price:
            self._shop_notice("金币不足!")
            return
        self.player.gold -= price
        self.player.potions.append(pid)
        self._shop_notice(f"购买了{POTION_LIB[pid]['name']}!")

    # ---------------- 铁匠铺 (购买锻造材料) ----------------
    # 铁匠铺材料售价: {material_id: 单价}
    BLACKSMITH_PRICE = {
        "iron": 15, "coal": 10, "bronze": 12, "fire_shard": 20, "water_shard": 20,
        "lightning_shard": 35, "wind_shard": 30, "mithril": 40, "steel": 38, "obsidian": 36,
        "shadow_shard": 80, "dragonbone": 120, "soul_ash": 100, "adamantite": 150,
    }

    def show_blacksmith(self):
        self._push_view(self.show_blacksmith)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="🔨 铁 匠 铺", bg=COLOR_BG, fg="#82aaff",
                 font=FONT_TITLE).pack(pady=8)
        tk.Label(self.content, text=f"💰 你的金币: {p.gold}   铁匠愿出售各种锻造材料",
                 bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_TITLE).pack(pady=(0, 8))
        if getattr(self, "_blacksmith_notice", None):
            tk.Label(self.content, text="  ✓ " + self._blacksmith_notice, bg=COLOR_BG,
                     fg=COLOR_OK, font=FONT_MAIN).pack(pady=(0, 6))
            self._blacksmith_notice = None

        canvas, inner, scroll = self._scroll_container()

        # 每类材料一行
        # 按 tier 分组显示
        for tier in (1, 2, 3):
            tier_name = {1: "普通材料", 2: "中级材料", 3: "高级材料"}[tier]
            group = tk.Frame(inner, bg=COLOR_BG)
            group.pack(fill="x", padx=8, pady=4)
            tk.Label(group, text=f"— {tier_name} —", bg=COLOR_BG, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=4)
            for mid in [m for m, d in MATERIAL_LIB.items()
                        if d["tier"] == tier and m in self.BLACKSMITH_PRICE]:
                m = MATERIAL_LIB[mid]
                price = self.BLACKSMITH_PRICE[mid]
                own = p.materials.get(mid, 0)
                txt = f"  {m['icon']} {m['name']} ×1   {price}金币   (持有{own})"
                row = tk.Frame(group, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER,
                               highlightthickness=1)
                row.pack(fill="x", pady=2, padx=4)
                tk.Label(row, text=txt, bg=COLOR_PANEL, fg=COLOR_GOLD,
                         font=FONT_MAIN).pack(side="left", padx=10, pady=4)
                b = tk.Button(row, text="购买", bg=COLOR_OK, fg=COLOR_TEXT, relief="flat",
                              font=FONT_MAIN, bd=0, cursor="hand2", padx=10, pady=2,
                              command=lambda mid=mid, pr=price: self.buy_material(mid, pr))
                b.pack(side="right", padx=10)
                b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
                b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_OK))

        self._btn(self.action_inner, "离开铁匠铺 ▶", self.after_node, color=COLOR_OK)
        self._btn(self.action_inner, "🎒 背包", self.show_bag, color=COLOR_BTN)

    def buy_material(self, mid, price):
        p = self.player
        if p.gold < price:
            self._set_blacksmith_notice("金币不足!")
            return
        p.gold -= price
        p.add_material(mid, 1)
        self._set_blacksmith_notice(f"购买了【{MATERIAL_LIB[mid]['name']}】×1 (已放入背包)")
        self.show_blacksmith()

    def _set_blacksmith_notice(self, text):
        self._blacksmith_notice = text

    # ---------------- 异界 (隐藏层) ----------------
    def abyss_enter_cost(self):
        """进入异界隐藏层的费用 (按层递增)."""
        return 50 + 20 * self.floor

    def show_abyss_gate(self):
        """异界入口界面: 支付金币后进入隐藏层."""
        self._push_view(self.show_abyss_gate)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        cost = self.abyss_enter_cost()
        tk.Label(self.content, text="🌀 异 界 之 门", bg=COLOR_BG, fg="#ff79c6",
                 font=FONT_TITLE).pack(pady=12)
        tk.Label(self.content, text="一扇泛着幽光的传送门, 通往未知的隐藏层.",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_MAIN).pack(pady=(0, 4))
        tk.Label(self.content, text=f"隐藏层为 1-3-2-1 的短路线, 没有回头路, 必须一路打到尽头!",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 4))
        tk.Label(self.content, text=f"第一关是特殊的异界精英, 到达第四阶段即返回主世界, 并获得【异界旋涡】.",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 4))
        tk.Label(self.content, text=f"💰 开启传送门需要 {cost} 金币 (你现有 {p.gold})",
                 bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_TITLE).pack(pady=(12, 8))

        can = p.gold >= cost
        self._btn(self.action_inner, "🌀 支付并进入异界", self.enter_abyss,
                  color=COLOR_OK if can else "#2a2a3e")
        self._btn(self.action_inner, "离开", self.after_node, color=COLOR_BTN)

    def enter_abyss(self):
        """支付金币, 保存主地图状态并进入异界隐藏层."""
        cost = self.abyss_enter_cost()
        if self.player.gold < cost:
            self._set_hint(f"金币不足! 需要 {cost} 金币")
            return
        self.player.gold -= cost
        entry = self.current_node  # 异界入口节点 (主地图上的 abyss 节点)
        # 保存主地图状态 (用于返回)
        self.main_map_nodes = self.map_nodes
        self.main_map_edges = self.map_edges
        self.main_map_vertical = self.map_vertical
        self.main_map_order = self.map_order
        self.main_node_state = dict(self.node_state)
        self.main_prev_node = self.prev_node
        # 生成异界隐藏层
        self.map_nodes, self.map_edges, self.map_order = generate_abyss_map(self.rng)
        self.map_vertical = set()
        self.node_state = {nid: "todo" for nid in self.map_order}
        self.current_node = self.map_order[0]   # 第一节点 = 特殊异界精英
        self.prev_node = None
        self.in_abyss = True
        self.abyss_entry = entry
        # 第一节点必为特殊精英怪, 立即开战
        self.start_abyss_elite_battle()

    def exit_abyss(self):
        """异界隐藏层打到底, 标记异界入口完成, 返回主地图."""
        # 异界入口节点在主地图上标记为已完成
        entry = self.abyss_entry
        self.map_nodes = self.main_map_nodes
        self.map_edges = self.main_map_edges
        self.map_vertical = self.main_map_vertical
        self.map_order = self.main_map_order
        self.node_state = self.main_node_state
        self.prev_node = self.main_prev_node
        self.current_node = entry
        if entry in self.node_state:
            self.node_state[entry] = "done"
        self.in_abyss = False
        self.abyss_entry = None
        # 离开异界: 获得新道具「异界旋涡」
        self.player.add_material("abyss_vortex", 1)
        self._set_hint("🌀 异界之旅结束, 你获得【异界旋涡】, 已返回主地图")
        self.show_map()

    def _abyss_cleared(self):
        """异界隐藏层是否已经打到底 (所有节点完成)."""
        return all(self.node_state.get(nid) == "done" for nid in self.map_order)

    # ---------------- 背包 ----------------
    def show_bag(self):
        """背包: 查看持有的武器, 可卖出或装备."""
        self._push_view(self.show_bag)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="🎒 背 包", bg=COLOR_BG, fg=COLOR_GOLD,
                 font=FONT_TITLE).pack(pady=8)
        tk.Label(self.content, text=f"💰 金币: {p.gold}   背包武器: {len(p.bag)} 件",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 8))
        if getattr(self, "_bag_notice", None):
            tk.Label(self.content, text="  ✓ " + self._bag_notice, bg=COLOR_BG,
                     fg=COLOR_OK, font=FONT_MAIN).pack(pady=(0, 6))
            self._bag_notice = None

        # 滚动容器 (内容过长时可用鼠标滚轮/拉动条拉到底部)
        canvas, inner, scroll = self._scroll_container()

        if not p.bag:
            tk.Label(inner, text="( 背包空空如也, 击败精英/Boss或从商店可获得武器 )",
                     bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=20)
        else:
            for wid in list(p.bag):
                w = WEAPON_LIB[wid]
                row = self._panel(inner)
                row.pack(fill="x", padx=10, pady=3)
                rowi = tk.Frame(row, bg=COLOR_PANEL)
                rowi.pack(padx=10, pady=4)
                _sn = "、".join(SKILL_LIB[s]["name"] for s in w.get("skills", [w["skill"]]))
                txt = (f"🔨 {w['name']}  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}"
                       f"  技能:{_sn}")
                if w.get("ail"):
                    txt += f"  ⚠{ail_desc(w['ail'])}"
                tk.Label(rowi, text=txt, bg=COLOR_PANEL, fg=COLOR_TEXT,
                         font=FONT_MAIN).pack(anchor="w")
                bbar = tk.Frame(rowi, bg=COLOR_PANEL)
                bbar.pack(anchor="w", pady=(2, 0))
                tk.Button(bbar, text="⚔ 装备", bg=COLOR_OK, fg=COLOR_TEXT, relief="flat",
                          font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                          command=lambda wid=wid: self.equip_from_bag(wid)).pack(side="left", padx=2)
                tk.Button(bbar, text="💰 卖出 (+{})".format(self._sell_price(wid)),
                          bg=COLOR_BTN, fg=COLOR_GOLD, relief="flat",
                          font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                          command=lambda wid=wid: self.sell_weapon(wid)).pack(side="left", padx=2)

        # 副手栏
        osp = self._panel(inner)
        osp.pack(fill="x", padx=10, pady=3)
        tk.Label(osp, text="— 副手 ({} 件, 属性按1/3计入) —".format(len(p.offhands)),
                 bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if not p.offhands and not p.offhand_data:
            tk.Label(osp, text="  ( 暂无副手, 可从商店购买或击败精英/Boss获得 )",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        else:
            if p.offhand_data:
                self._bag_offhand_row(osp, p.offhand, equipped=True)
            for oid in list(p.offhands):
                self._bag_offhand_row(osp, oid, equipped=False)

        # 饰品栏
        tsp = self._panel(inner)
        tsp.pack(fill="x", padx=10, pady=3)
        tk.Label(tsp, text="— 饰品 ({} 件) —".format(len(p.trinkets)),
                 bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if not p.trinkets and not p.trinket_data:
            tk.Label(tsp, text="  ( 暂无饰品, 可从商店购买或击败精英/Boss获得 )",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        else:
            if p.trinket_data:
                self._bag_trinket_row(tsp, p.accessory, equipped=True)
            for tid in list(p.trinkets):
                self._bag_trinket_row(tsp, tid, equipped=False)

        # 材料栏 (用于合成)
        msp = self._panel(inner)
        msp.pack(fill="x", padx=10, pady=3)
        tk.Label(msp, text="— 材料 (用于合成) —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if not p.materials:
            tk.Label(msp, text="  ( 暂无材料, 击败怪物可掉落: 铁锭/元素碎片等 )",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        else:
            for mid, cnt in sorted(p.materials.items(), key=lambda kv: -MATERIAL_LIB[kv[0]]["tier"]):
                m = MATERIAL_LIB[mid]
                tier_txt = {1: "普通", 2: "中级", 3: "高级"}[m["tier"]]
                tk.Label(msp, text=f"  {m['icon']} {m['name']} ×{cnt}   [{tier_txt}]  {m['desc']}",
                         bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        self._btn(self.action_inner, "← 返回", self.show_character_sheet, color=COLOR_BTN)
        self._btn(self.action_inner, "⚔ 装备", self.show_equip, color=COLOR_BTN)
        self._btn(self.action_inner, "🔨 合成", self.show_craft, color=COLOR_ACCENT)

    def _sell_price(self, wid):
        return WEAPON_LIB[wid]["tier"] * 30

    def sell_weapon(self, wid):
        if wid in self.player.bag:
            self.player.bag.remove(wid)
            g = self._sell_price(wid)
            self.player.gold += g
            self._set_shop_like_notice(f"卖出了【{WEAPON_LIB[wid]['name']}】, 获得 {g} 金币")
            self.show_bag()

    def equip_from_bag(self, wid):
        """从背包装备武器 (把当前武器放回背包)."""
        p = self.player
        if wid in p.bag:
            old = p.weapon
            p.bag.remove(wid)
            # 当前武器放回背包 (若不在背包且不是初始铁剑)
            if old not in p.bag:
                p.bag.append(old)
            p.equip_weapon(wid)
            self._set_shop_like_notice(f"已装备【{WEAPON_LIB[wid]['name']}】")
            self.show_bag()

    def _set_shop_like_notice(self, text):
        """在操作区显示一条临时提示 (简单方式: 存入状态)."""
        self._bag_notice = text

    def _sell_trinket_price(self, tid):
        return TRINKET_LIB[tid]["tier"] * 20

    def _bag_trinket_row(self, parent, tid, equipped):
        t = TRINKET_LIB[tid]
        inner = tk.Frame(parent, bg=COLOR_PANEL)
        inner.pack(anchor="w", padx=16, pady=2)
        txt = f"  ◆ {t['name']}  攻击+{t['atk']} 生命+{t['hp']} 蓝量+{t['mp']}"
        if t["passive"]:
            txt += f"  [{PASSIVE_NAME[t['passive']]}]"
        if equipped:
            txt += "  (已装备)"
        tk.Label(inner, text=txt, bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=FONT_MAIN).pack(side="left", padx=2)
        bbar = tk.Frame(inner, bg=COLOR_PANEL)
        bbar.pack(side="left", padx=6)
        if not equipped:
            tk.Button(bbar, text="⚔ 装备", bg=COLOR_OK, fg=COLOR_TEXT, relief="flat",
                      font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                      command=lambda tid=tid: self.equip_trinket_from(tid)).pack(side="left", padx=2)
            tk.Button(bbar, text="💰 卖出 (+{})".format(self._sell_trinket_price(tid)),
                      bg=COLOR_BTN, fg=COLOR_GOLD, relief="flat",
                      font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                      command=lambda tid=tid: self.sell_trinket(tid)).pack(side="left", padx=2)

    def sell_trinket(self, tid):
        if tid in self.player.trinkets:
            self.player.trinkets.remove(tid)
            g = self._sell_trinket_price(tid)
            self.player.gold += g
            self._set_shop_like_notice(f"卖出了【{TRINKET_LIB[tid]['name']}】, 获得 {g} 金币")
            self.show_bag()

    # ---- 副手武器 (背包/装备) ----
    def _sell_offhand_price(self, oid):
        return OFFHAND_LIB[oid]["atk"] * 3

    def _bag_offhand_row(self, parent, oid, equipped):
        o = OFFHAND_LIB[oid]
        sk = SKILL_LIB[o["skill"]]
        inner = tk.Frame(parent, bg=COLOR_PANEL)
        inner.pack(anchor="w", padx=16, pady=2)
        txt = (f"  ✦ {o['name']}  攻击+{o['atk']//3} 生命+{o['hp']//3} 蓝量+{o['mp']//3}"
               f"  技能:{sk['name']}")
        if equipped:
            txt += "  (已装备)"
        tk.Label(inner, text=txt, bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=FONT_MAIN).pack(side="left", padx=2)
        bbar = tk.Frame(inner, bg=COLOR_PANEL)
        bbar.pack(side="left", padx=6)
        if not equipped:
            tk.Button(bbar, text="⚔ 装备", bg=COLOR_OK, fg=COLOR_TEXT, relief="flat",
                      font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                      command=lambda oid=oid: self.equip_offhand_from(oid)).pack(side="left", padx=2)
            tk.Button(bbar, text="💰 卖出 (+{})".format(self._sell_offhand_price(oid)),
                      bg=COLOR_BTN, fg=COLOR_GOLD, relief="flat",
                      font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                      command=lambda oid=oid: self.sell_offhand(oid)).pack(side="left", padx=2)

    def equip_offhand_from(self, oid):
        p = self.player
        if oid in p.offhands:
            old = p.offhand
            p.offhands.remove(oid)
            if old is not None and old not in p.offhands:
                p.offhands.append(old)
            p.equip_offhand(oid)
            self._set_shop_like_notice(f"已装备副手【{OFFHAND_LIB[oid]['name']}】")
        self.show_bag()

    def sell_offhand(self, oid):
        if oid in self.player.offhands:
            self.player.offhands.remove(oid)
            g = self._sell_offhand_price(oid)
            self.player.gold += g
            self._set_shop_like_notice(f"卖出了【{OFFHAND_LIB[oid]['name']}】, 获得 {g} 金币")
            self.show_bag()

    # ---------------- 合成系统 ----------------
    CAT_CN = {"sword": "剑", "axe": "斧", "staff": "法杖", "hammer": "锤",
              "dagger": "匕首", "greatsword": "重剑", "spear": "长矛"}

    def show_craft(self):
        """合成界面: 用最高等武器 + 材料 合成神器, 也可合成饰品."""
        self._push_view(self.show_craft)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="🔨 合成", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=8)
        tk.Label(self.content, text="以最高等武器或材料为基, 熔入Boss掉落与神灵碎片, 铸成传说装备",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 8))
        canvas, inner, scroll = self._scroll_container()

        for rid, recipe in CRAFT_LIB.items():
            w = WEAPON_LIB[rid]
            base_w = WEAPON_LIB[recipe["weapon"]]
            sk = SKILL_LIB[w["skill"]]
            panel = self._panel(inner)
            panel.pack(fill="x", padx=10, pady=3)
            left = tk.Frame(panel, bg=COLOR_PANEL)
            left.pack(side="left", padx=8, pady=4)
            tk.Label(left, text="\n".join(w["art"]), bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=FONT_MONO, justify="left").pack()
            right = tk.Frame(panel, bg=COLOR_PANEL)
            right.pack(side="left", padx=6, pady=4, fill="x", expand=True)

            owned = (p.weapon == rid) or (rid in p.bag)
            title = f"[神器·{self.CAT_CN.get(w['cat'], w['cat'])}] {w['name']}"
            if owned:
                title += "  (已拥有)"
            tk.Label(right, text=title, bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(right, text=f"  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}",
                     bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
            tk.Label(right, text=f"  技能: {sk['name']} ({sk['mp']}✦) — {sk['desc']}",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN, wraplength=560,
                     justify="left").pack(anchor="w")
            # 原料
            has_base = (p.weapon == recipe["weapon"]) or (recipe["weapon"] in p.bag)
            base_state = "✓" if has_base else "✗"
            tk.Label(right, text=f"  原料武器: {base_state} {base_w['name']}",
                     bg=COLOR_PANEL, fg=(COLOR_OK if has_base else COLOR_BAD),
                     font=FONT_MAIN).pack(anchor="w")
            # 材料
            has_mats = p.has_materials(recipe["mats"])
            mat_txt = "  所需材料: "
            mat_parts = []
            for mid, cnt in recipe["mats"].items():
                m = MATERIAL_LIB[mid]
                have = p.materials.get(mid, 0)
                ok = have >= cnt
                mark = "✓" if ok else "✗"
                mat_parts.append(f"{mark}{m['name']}×{cnt}(有{have})")
            tk.Label(right, text=mat_txt + "  ".join(mat_parts),
                     bg=COLOR_PANEL, fg=(COLOR_OK if has_mats else COLOR_BAD),
                     font=FONT_MAIN).pack(anchor="w")
            tk.Label(right, text="  " + recipe["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w")

            if not owned:
                can = has_base and has_mats
                tk.Button(right, text="🔨 合成", bg=COLOR_OK if can else COLOR_BTN,
                          fg=COLOR_TEXT, relief="flat", font=FONT_MAIN, bd=0,
                          cursor="hand2", padx=12, pady=3,
                          command=lambda rid=rid: self.craft_item(rid)).pack(anchor="w", pady=(4, 2))

        # 超神器合成 (神器 + tier4异常武器 + 第三层掉落物, 北欧神话武器)
        tk.Label(inner, text="— 超神器合成 (北欧神话武器) —", bg=COLOR_BG, fg="#ff79c6",
                 font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(12, 2))
        tk.Label(inner, text="以神器为基, 熔入 tier4 异常武器 与 第三层掉落物, 铸成超神器",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 2))
        for rid, recipe in SUPER_ARTIFACT_LIB.items():
            w = WEAPON_LIB[rid]
            art_w = WEAPON_LIB[recipe["artifact"]]
            wpn_w = WEAPON_LIB[recipe["weapon"]]
            sk = SKILL_LIB[w["skill"]]
            panel = self._panel(inner)
            panel.pack(fill="x", padx=10, pady=3)
            left = tk.Frame(panel, bg=COLOR_PANEL)
            left.pack(side="left", padx=8, pady=4)
            tk.Label(left, text="\n".join(w["art"]), bg=COLOR_PANEL, fg="#ff79c6",
                     font=FONT_MONO, justify="left").pack()
            right = tk.Frame(panel, bg=COLOR_PANEL)
            right.pack(side="left", padx=6, pady=4, fill="x", expand=True)

            owned = (p.weapon == rid) or (rid in p.bag)
            title = f"[超神器·{self.CAT_CN.get(w['cat'], w['cat'])}] {w['name']}"
            if owned:
                title += "  (已拥有)"
            tk.Label(right, text=title, bg=COLOR_PANEL, fg="#ff79c6",
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(right, text=f"  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}",
                     bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
            for _sid in w.get("skills", [w["skill"]]):
                _sk = SKILL_LIB[_sid]
                tk.Label(right, text=f"  技能: {_sk['name']} ({_sk['mp']}✦) — {_sk['desc']}",
                         bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN, wraplength=560,
                         justify="left").pack(anchor="w")
            # 原料: 神器 + tier4异常武器
            def _have(wid):
                return (p.weapon == wid) or (wid in p.bag)
            has_art = _have(recipe["artifact"])
            has_wpn = _have(recipe["weapon"])
            tk.Label(right, text=f"  神器原料: {'✓' if has_art else '✗'} {art_w['name']}",
                     bg=COLOR_PANEL, fg=(COLOR_OK if has_art else COLOR_BAD),
                     font=FONT_MAIN).pack(anchor="w")
            tk.Label(right, text=f"  异常武器原料: {'✓' if has_wpn else '✗'} {wpn_w['name']}",
                     bg=COLOR_PANEL, fg=(COLOR_OK if has_wpn else COLOR_BAD),
                     font=FONT_MAIN).pack(anchor="w")
            # 材料 (第三层掉落物)
            has_mats = p.has_materials(recipe["mats"])
            mat_txt = "  所需材料: "
            mat_parts = []
            for mid, cnt in recipe["mats"].items():
                m = MATERIAL_LIB[mid]
                have = p.materials.get(mid, 0)
                ok = have >= cnt
                mark = "✓" if ok else "✗"
                mat_parts.append(f"{mark}{m['name']}×{cnt}(有{have})")
            tk.Label(right, text=mat_txt + "  ".join(mat_parts),
                     bg=COLOR_PANEL, fg=(COLOR_OK if has_mats else COLOR_BAD),
                     font=FONT_MAIN).pack(anchor="w")
            tk.Label(right, text="  " + recipe["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w")
            if not owned:
                can = has_art and has_wpn and has_mats
                tk.Button(right, text="🔨 合成", bg=COLOR_OK if can else COLOR_BTN,
                          fg=COLOR_TEXT, relief="flat", font=FONT_MAIN, bd=0,
                          cursor="hand2", padx=12, pady=3,
                          command=lambda rid=rid: self.craft_super(rid)).pack(anchor="w", pady=(4, 2))

        # 饰品合成
        tk.Label(inner, text="— 饰品合成 —", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(12, 2))
        for tid, recipe in TRINKET_CRAFT_LIB.items():
            t = TRINKET_LIB[tid]
            panel = self._panel(inner)
            panel.pack(fill="x", padx=10, pady=3)
            left = tk.Frame(panel, bg=COLOR_PANEL)
            left.pack(side="left", padx=8, pady=4)
            tk.Label(left, text="\n".join(t["art"]), bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=FONT_MONO, justify="left").pack()
            right = tk.Frame(panel, bg=COLOR_PANEL)
            right.pack(side="left", padx=6, pady=4, fill="x", expand=True)

            owned = (p.accessory == tid) or (tid in p.trinkets)
            title = f"[饰品] {t['name']}"
            if owned:
                title += "  (已拥有)"
            tk.Label(right, text=title, bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(right, text=f"  攻击+{t['atk']} 生命+{t['hp']} 蓝量+{t['mp']}",
                     bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
            if t["passive"]:
                tk.Label(right, text=f"  被动: {PASSIVE_NAME.get(t['passive'], t['passive'])}",
                         bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w")
            # 材料
            has_mats = p.has_materials(recipe["mats"])
            mat_txt = "  所需材料: "
            mat_parts = []
            for mid, cnt in recipe["mats"].items():
                m = MATERIAL_LIB[mid]
                have = p.materials.get(mid, 0)
                ok = have >= cnt
                mark = "✓" if ok else "✗"
                mat_parts.append(f"{mark}{m['name']}×{cnt}(有{have})")
            tk.Label(right, text=mat_txt + "  ".join(mat_parts),
                     bg=COLOR_PANEL, fg=(COLOR_OK if has_mats else COLOR_BAD),
                     font=FONT_MAIN).pack(anchor="w")
            tk.Label(right, text="  " + recipe["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w")
            if not owned:
                tk.Button(right, text="🔨 合成", bg=COLOR_OK if has_mats else COLOR_BTN,
                          fg=COLOR_TEXT, relief="flat", font=FONT_MAIN, bd=0,
                          cursor="hand2", padx=12, pady=3,
                          command=lambda tid=tid: self.craft_trinket(tid)).pack(anchor="w", pady=(4, 2))

        self._btn(self.action_inner, "← 返回背包", self.show_bag, color=COLOR_BTN)

    def craft_item(self, rid):
        """执行一次合成: 消耗原料武器 + 材料, 产出神器."""
        recipe = CRAFT_LIB[rid]
        p = self.player
        if (p.weapon == rid) or (rid in p.bag):
            self._set_shop_like_notice(f"已拥有【{WEAPON_LIB[rid]['name']}】, 无需重复合成")
            self.show_craft()
            return
        if not p.has_materials(recipe["mats"]):
            self._set_shop_like_notice("材料不足!")
            self.show_craft()
            return
        base = recipe["weapon"]
        # 原料武器须持有 (背包或当前装备). 若已装备则先卸下.
        if p.weapon == base:
            p.equip_weapon("iron_sword")
            p.bag.append(base)
        if base not in p.bag:
            self._set_shop_like_notice(f"缺少原料武器【{WEAPON_LIB[base]['name']}】!")
            self.show_craft()
            return
        p.bag.remove(base)
        p.consume_materials(recipe["mats"])
        p.add_weapon_to_bag(rid)
        self._set_shop_like_notice(f"合成成功! 获得神器【{WEAPON_LIB[rid]['name']}】(已存入背包)")
        self.show_craft()

    def craft_super(self, rid):
        """执行超神器合成: 消耗 神器 + tier4异常武器 + 第三层掉落物, 产出超神器."""
        recipe = SUPER_ARTIFACT_LIB[rid]
        p = self.player
        if (p.weapon == rid) or (rid in p.bag):
            self._set_shop_like_notice(f"已拥有【{WEAPON_LIB[rid]['name']}】, 无需重复合成")
            self.show_craft()
            return
        if not p.has_materials(recipe["mats"]):
            self._set_shop_like_notice("材料不足!")
            self.show_craft()
            return
        for key in ("artifact", "weapon"):
            base = recipe[key]
            # 原料武器须持有 (背包或当前装备). 若已装备则先卸下.
            if p.weapon == base:
                p.equip_weapon("iron_sword")
                p.bag.append(base)
            if base not in p.bag:
                self._set_shop_like_notice(f"缺少原料【{WEAPON_LIB[base]['name']}】!")
                self.show_craft()
                return
            p.bag.remove(base)
        p.consume_materials(recipe["mats"])
        p.add_weapon_to_bag(rid)
        self._set_shop_like_notice(f"合成成功! 获得超神器【{WEAPON_LIB[rid]['name']}】(已存入背包)")
        self.show_craft()

    def craft_trinket(self, tid):
        """执行一次饰品合成: 消耗材料, 产出饰品."""
        recipe = TRINKET_CRAFT_LIB[tid]
        p = self.player
        if (p.accessory == tid) or (tid in p.trinkets):
            self._set_shop_like_notice(f"已拥有【{TRINKET_LIB[tid]['name']}】, 无需重复合成")
            self.show_craft()
            return
        if not p.has_materials(recipe["mats"]):
            self._set_shop_like_notice("材料不足!")
            self.show_craft()
            return
        p.consume_materials(recipe["mats"])
        p.add_trinket(tid)
        self._set_shop_like_notice(f"合成成功! 获得饰品【{TRINKET_LIB[tid]['name']}】(已存入饰品栏)")
        self.show_craft()

    # ---------------- 装备系统 ----------------
    def show_equip(self):
        """装备系统: 更换武器与饰品."""
        self._push_view(self.show_equip)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="⚔ 装 备", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=8)
        if getattr(self, "_bag_notice", None):
            tk.Label(self.content, text="  ✓ " + self._bag_notice, bg=COLOR_BG,
                     fg=COLOR_OK, font=FONT_MAIN).pack(pady=(0, 6))
            self._bag_notice = None

        # 滚动容器 (内容过长时可用鼠标滚轮/拉动条拉到底部)
        canvas, inner, scroll = self._scroll_container()

        # 当前装备
        wd = p.weapon_data
        cur = self._panel(inner)
        cur.pack(fill="x", padx=10, pady=4)
        tk.Label(cur, text=f"当前武器: 🔨 {wd['name']}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                 font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if p.trinket_data:
            tk.Label(cur, text=f"当前饰品: ◆ {p.trinket_data['name']}",
                     bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(2, 6))
        else:
            tk.Label(cur, text="当前饰品: (无)", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(2, 6))
        if p.offhand_data:
            tk.Label(cur, text=f"当前副手: ✦ {p.offhand_data['name']}",
                     bg=COLOR_PANEL, fg="#ff79c6",
                     font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(2, 6))
        else:
            tk.Label(cur, text="当前副手: (无)", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(2, 6))

        # 武器列表: 背包武器 + 当前武器
        wp = self._panel(inner)
        wp.pack(fill="x", padx=10, pady=4)
        tk.Label(wp, text="— 武器 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        self._equip_weapon_button(wp, p.weapon, equipped=True)
        for wid in list(p.bag):
            self._equip_weapon_button(wp, wid, equipped=False)

        # 副手列表: 当前副手 + 持有的副手
        op = self._panel(inner)
        op.pack(fill="x", padx=10, pady=4)
        tk.Label(op, text="— 副手 (属性按1/3计入) —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if p.offhand_data:
            self._equip_offhand_button(op, p.offhand, equipped=True)
        for oid in list(p.offhands):
            self._equip_offhand_button(op, oid, equipped=False)
        if not p.offhand_data and not p.offhands:
            tk.Label(op, text="  ( 暂无副手, 可从商店购买或击败精英/Boss获得 )",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)

        # 饰品列表: 当前饰品 + 持有的饰品
        tp = self._panel(inner)
        tp.pack(fill="x", padx=10, pady=4)
        tk.Label(tp, text="— 饰品 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if p.trinket_data:
            self._equip_trinket_button(tp, p.accessory, equipped=True)
        for tid in list(p.trinkets):
            self._equip_trinket_button(tp, tid, equipped=False)
        if not p.trinket_data and not p.trinkets:
            tk.Label(tp, text="  ( 暂无饰品, 可从商店购买或击败精英/Boss获得 )",
                     bg=COLOR_PANEL, fg=COLOR_SUB, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)

        self._btn(self.action_inner, "← 返回", self.show_character_sheet, color=COLOR_BTN)
        self._btn(self.action_inner, "🎒 背包", self.show_bag, color=COLOR_BTN)

    def _equip_weapon_button(self, parent, wid, equipped):
        w = WEAPON_LIB[wid]
        _sn = "、".join(SKILL_LIB[s]["name"] for s in w.get("skills", [w["skill"]]))
        txt = f"  🔨 {w['name']}  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}  技能:{_sn}"
        if w.get("ail"):
            txt += f"  ⚠{ail_desc(w['ail'])}"
        if equipped:
            txt += "  (已装备)"
        b = tk.Button(parent, text=txt, bg=COLOR_OK if equipped else COLOR_BTN,
                      fg=COLOR_TEXT, activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                      relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                      width=64, pady=4, anchor="w",
                      command=lambda wid=wid: self.equip_from_bag(wid) if not equipped else None)
        b.pack(pady=2, padx=8)
        if not equipped:
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    def _equip_trinket_button(self, parent, tid, equipped):
        t = TRINKET_LIB[tid]
        txt = f"  ◆ {t['name']}  攻击+{t['atk']} 生命+{t['hp']} 蓝量+{t['mp']}"
        if t["passive"]:
            txt += f"  [{PASSIVE_NAME[t['passive']]}]"
        if equipped:
            txt += "  (已装备)"
        b = tk.Button(parent, text=txt, bg=COLOR_OK if equipped else COLOR_BTN,
                      fg=COLOR_ACCENT, activebackground=COLOR_BTN_HOV, activeforeground=COLOR_ACCENT,
                      relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                      width=64, pady=4, anchor="w",
                      command=lambda tid=tid: self.equip_trinket_from(tid) if not equipped else None)
        b.pack(pady=2, padx=8)
        if not equipped:
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    def equip_trinket_from(self, tid):
        self.player.equip_trinket(tid)
        self._set_shop_like_notice(f"已装备【{TRINKET_LIB[tid]['name']}】")
        self.show_equip()

    def _equip_offhand_button(self, parent, oid, equipped):
        o = OFFHAND_LIB[oid]
        sk = SKILL_LIB[o["skill"]]
        txt = (f"  ✦ {o['name']}  攻击+{o['atk']//3} 生命+{o['hp']//3} 蓝量+{o['mp']//3}"
               f"  技能:{sk['name']}")
        if equipped:
            txt += "  (已装备)"
        b = tk.Button(parent, text=txt, bg=COLOR_OK if equipped else COLOR_BTN,
                      fg="#ff79c6", activebackground=COLOR_BTN_HOV, activeforeground="#ff79c6",
                      relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                      width=64, pady=4, anchor="w",
                      command=lambda oid=oid: self.equip_offhand_from(oid) if not equipped else None)
        b.pack(pady=2, padx=8)
        if not equipped:
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    # ---------------- 图鉴 ----------------
    def show_weapon_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🔨 武器图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 8))
        CAT = {"sword": "剑", "axe": "斧", "staff": "法杖", "hammer": "锤",
               "dagger": "匕首", "greatsword": "重剑", "spear": "长矛"}
        canvas, inner, scroll = self._scroll_container()
        for wid, w in WEAPON_LIB.items():
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=3)
            left = tk.Frame(p, bg=COLOR_PANEL)
            left.pack(side="left", padx=8, pady=4)
            tk.Label(left, text="\n".join(w["art"]), bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MONO, justify="left").pack()
            right = tk.Frame(p, bg=COLOR_PANEL)
            right.pack(side="left", padx=6, pady=4)
            tk.Label(right,
                     text=f"[{CAT.get(w['cat'], w['cat'])}] {w['name']}  攻击+{w['atk']}  生命+{w['hp']}  蓝量+{w['mp']}",
                     bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(right, text="   " + w["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN, wraplength=520, justify="left").pack(anchor="w")
            if w["passive"]:
                pname = PASSIVE_NAME.get(w["passive"], w["passive"])
                tk.Label(right, text=f"  被动: {pname}", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                         font=FONT_MAIN).pack(anchor="w")
            if w.get("ail"):
                tk.Label(right, text=f"  ⚠ {ail_desc(w['ail'])}", bg=COLOR_PANEL, fg="#ff79c6",
                         font=FONT_MAIN).pack(anchor="w")
            for _sid in w.get("skills", [w["skill"]]):
                _sk = SKILL_LIB[_sid]
                _extra = ""
                if _sk.get("cooldown"):
                    _extra = "  [两回合一次]"
                elif _sk.get("hits"):
                    _extra = f"  [连击x{_sk['hits']}]"
                tk.Label(right, text=f"  武器技能: {_sk['name']} ({_sk['mp']}✦) — {_sk['desc']}{_extra}",
                         bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_trinket_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="◆ 饰品图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 8))
        canvas, inner, scroll = self._scroll_container()
        for tid, t in TRINKET_LIB.items():
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=3)
            left = tk.Frame(p, bg=COLOR_PANEL)
            left.pack(side="left", padx=8, pady=4)
            tk.Label(left, text="\n".join(t["art"]), bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=FONT_MONO, justify="left").pack()
            right = tk.Frame(p, bg=COLOR_PANEL)
            right.pack(side="left", padx=6, pady=4)
            tk.Label(right, text=f"◆ {t['name']}  攻击+{t['atk']}  生命+{t['hp']}  蓝量+{t['mp']}",
                     bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(right, text="   " + t["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN, wraplength=520, justify="left").pack(anchor="w")
            if t["passive"]:
                tk.Label(right, text=f"  被动: {PASSIVE_NAME.get(t['passive'], t['passive'])}",
                         bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_offhand_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="✦ 副手图鉴", bg=COLOR_BG, fg="#ff79c6",
                 font=FONT_TITLE).pack(pady=(6, 8))
        tk.Label(self.content, text="副手武器提供技能, 其属性以 1/3 计入角色 (攻击/生命/蓝量)",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 4))
        canvas, inner, scroll = self._scroll_container()
        for oid, o in OFFHAND_LIB.items():
            sk = SKILL_LIB[o["skill"]]
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=3)
            right = tk.Frame(p, bg=COLOR_PANEL)
            right.pack(side="left", padx=10, pady=6)
            tk.Label(right, text=f"✦ {o['name']}  攻击+{o['atk']//3}  生命+{o['hp']//3}  蓝量+{o['mp']//3} (1/3计入)",
                     bg=COLOR_PANEL, fg="#ff79c6",
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(right, text="   " + o["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN, wraplength=560, justify="left").pack(anchor="w")
            tk.Label(right, text=f"  提供技能: {sk['name']} ({sk['mp']}✦) — {sk['desc']}",
                     bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
            if o.get("ail"):
                tk.Label(right, text=f"  ⚠ {ail_desc(o['ail'])}", bg=COLOR_PANEL, fg="#ff79c6",
                         font=FONT_MAIN).pack(anchor="w")
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_material_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="⛏ 材料图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 4))
        tk.Label(self.content, text="怪物掉落, 用于合成神器 · 普通=小怪 中级=精英 高级=Boss",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 8))
        canvas, inner, scroll = self._scroll_container()
        for mid, m in MATERIAL_LIB.items():
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=3)
            tier_txt = {1: "普通", 2: "中级", 3: "高级"}[m["tier"]]
            tk.Label(p, text=f"  {m['icon']} {m['name']}  [{tier_txt}]",
                     bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=10, pady=(4, 0))
            tk.Label(p, text="   " + m["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_skill_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="✦ 技能图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 4))
        tk.Label(self.content, text="基础技能按等级解锁 · 武器技能随装备获得",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 8))
        canvas, inner, scroll = self._scroll_container()
        tk.Label(inner, text="— 基础技能 (等级解锁) —", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(4, 2))
        for lv, ids in sorted(LVL_SKILLS.items()):
            for sid in ids:
                sk = SKILL_LIB[sid]
                p = self._panel(inner)
                p.pack(fill="x", padx=10, pady=2)
                cost = f" ({sk['mp']}✦)" if sk["mp"] else ""
                tk.Label(p, text=f"Lv.{lv}  {sk['name']}{cost}",
                         bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w", padx=10, pady=(4, 0))
                tk.Label(p, text="   " + sk["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                         font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        tk.Label(inner, text="— 武器技能 —", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(8, 2))
        for wid, w in WEAPON_LIB.items():
            for _sid in w.get("skills", [w["skill"]]):
                _sk = SKILL_LIB[_sid]
                _extra = ""
                if _sk.get("cooldown"):
                    _extra = "  [两回合一次]"
                elif _sk.get("hits"):
                    _extra = f"  [连击x{_sk['hits']}]"
                p = self._panel(inner)
                p.pack(fill="x", padx=10, pady=2)
                tk.Label(p, text=f"{w['name']} → {_sk['name']} ({_sk['mp']}✦){_extra}",
                         bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w", padx=10, pady=(4, 0))
                tk.Label(p, text="   " + _sk["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                         font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        tk.Label(inner, text="— 副手技能 (副手武器提供, 属性按1/3计入) —", bg=COLOR_BG, fg="#ff79c6",
                 font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(8, 2))
        for oid, o in OFFHAND_LIB.items():
            sk = SKILL_LIB[o["skill"]]
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=2)
            tk.Label(p, text=f"{o['name']} → {sk['name']} ({sk['mp']}✦)",
                     bg=COLOR_PANEL, fg="#ff79c6", font=FONT_MAIN).pack(anchor="w", padx=10, pady=(4, 0))
            tk.Label(p, text="   " + sk["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_monster_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="👹 怪物图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 4))
        canvas, inner, scroll = self._scroll_container()
        kind_cn = {"normal": "小怪", "elite": "精英", "boss": "首领"}
        for fl in sorted(FLOOR_MONSTERS.keys()):
            tk.Label(inner, text=f"— 第{fl}层 · {FLOOR_NAME[fl]} —", bg=COLOR_BG,
                     fg=COLOR_GOLD, font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(10, 2))
            for kind in ("normal", "elite", "boss"):
                tk.Label(inner, text=f"  · {kind_cn[kind]}", bg=COLOR_BG, fg=COLOR_ACCENT,
                         font=("Microsoft YaHei UI", 11, "bold")).pack(pady=(4, 0))
                for m in FLOOR_MONSTERS[fl][kind]:
                    p = self._panel(inner)
                    p.pack(fill="x", padx=10, pady=2)
                    left = tk.Frame(p, bg=COLOR_PANEL)
                    left.pack(side="left", padx=8, pady=4)
                    tk.Label(left, text="\n".join(m["art"]), bg=COLOR_PANEL, fg=COLOR_TEXT,
                             font=FONT_MONO, justify="left").pack()
                    right = tk.Frame(p, bg=COLOR_PANEL)
                    right.pack(side="left", padx=6, pady=4)
                    tk.Label(right, text=f"{m['name']}  生命{m['hp']}  攻击{m['atk']}  经验{m['exp']}",
                             bg=COLOR_PANEL, fg=COLOR_TEXT,
                             font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
                    tk.Label(right, text="   " + m["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                             font=FONT_MAIN, wraplength=500, justify="left").pack(anchor="w")
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_potion_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🧪 药水图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 8))
        canvas, inner, scroll = self._scroll_container()
        for pid, pot in POTION_LIB.items():
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=3)
            tk.Label(p, text=f"🧪 {pot['name']}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=10, pady=(4, 0))
            tk.Label(p, text="   " + pot["desc"], bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def _scroll_container(self):
        """在主内容区创建滚动容器. 返回 (canvas, inner, scroll)."""
        return self._scroll_container_into(self.content, global_wheel=True)

    def _scroll_container_into(self, parent, global_wheel=False):
        """在指定父容器内创建滚动容器. 返回 (canvas, inner, scroll)."""
        canvas = tk.Canvas(parent, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLOR_BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        # 鼠标滚轮滚动支持
        def _on_wheel(event):
            try:
                canvas.yview_scroll(int(-event.delta / 120), "units")
            except Exception:
                pass
        if global_wheel:
            self.root.bind_all("<MouseWheel>", _on_wheel)
        else:
            canvas.bind("<MouseWheel>", _on_wheel)
        return canvas, inner, scroll


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
