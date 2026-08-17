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
    "elite":    "#ff9e64",
    "treasure": COLOR_GOLD,
    "event":    COLOR_SELECT,
    "shop":     COLOR_OK,
    "boss":     "#bb9af7",
    "start":    COLOR_ACCENT,
}
NODE_ICON = {
    "monster":  "⚔",
    "elite":    "☠",
    "treasure": "💰",
    "event":    "❔",
    "shop":     "🛒",
    "boss":     "👑",
    "start":    "⛺",
}
NODE_LABEL = {
    "monster":  "小怪",
    "elite":    "精英",
    "treasure": "宝藏",
    "event":    "事件",
    "shop":     "商店",
    "boss":     "关底Boss",
    "start":    "营地",
}

FONT_MAIN  = ("Microsoft YaHei UI", 11)
FONT_TITLE = ("Microsoft YaHei UI", 15, "bold")
FONT_BIG   = ("Microsoft YaHei UI", 20, "bold")
FONT_MONO  = ("Consolas", 11)

# ============================================================
# 数据: 武器
# ============================================================
# 武器: 提升属性; 附带技能; 部分带被动.
# 分类: cat = sword(剑)/axe(斧)/staff(法杖)/hammer(锤)/dagger(匕首)/greatsword(重剑)
# 匕首: 连击(hits)技能, 高级匕首耗蓝少; 重剑: 攻击高, 高级重剑耗蓝大且带冷却(cooldown)
WEAPON_LIB = {
    "iron_sword": dict(
        name="铁剑", tier=1, atk=4, hp=0, mp=0, cat="sword",
        passive="", skill="cleave",
        desc="冒险者的起点, 朴实无华. 攻击+4",
        art=[
            "   /|",
            "  / |",
            " /  |",
            "|   |",
            " \\  |",
            "  \\_|",
            "    ▓",
        ]),
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
    "giant_hammer": dict(
        name="巨人战锤", tier=3, atk=9, hp=35, mp=0, cat="hammer",
        passive="strong_body", skill="quake",
        desc="传说战锤, 攻击+9 生命+35. 附带技能: 大地震击",
        art=[
            "  ▄▄▄▄",
            "  ████",
            "   |",
            "   |",
            "   |",
            "   ▓",
            "   ▓",
        ]),
    # ----- 匕首 (连击, 耗蓝少) -----
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
    "venom_dagger": dict(
        name="淬毒匕首", tier=3, atk=8, hp=0, mp=8, cat="dagger",
        passive="", skill="venom_stab",
        desc="淬满剧毒, 攻击+8 蓝量+8. 三连击耗蓝少",
        art=[
            "   ▓",
            "   |",
            "  /|",
            " / |",
            "|  |",
            " \\ |",
            "  \\▓",
        ]),
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
    # ----- 重剑 (攻击高, 耗蓝大, 两回合一次) -----
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
    "giant_blade": dict(
        name="巨剑", tier=3, atk=15, hp=20, mp=0, cat="greatsword",
        passive="strong_body", skill="colossal_cleave",
        desc="开山巨剑, 攻击+15 生命+20. 横扫无视格挡, 两回合一次",
        art=[
            "   ▄▄▄",
            "   ███",
            "    █",
            "    █",
            "    █",
            "    ▓",
            "    ▓",
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
    # ----- 神器 (tier5, 由最高等武器 + Boss材料在背包合成) -----
    "god_hammer": dict(
        name="泰坦神锤", tier=5, atk=18, hp=60, mp=0, cat="hammer",
        passive="strong_body", skill="titan_quake",
        desc="由巨人战锤与龙鳞重铸的传说之锤, 攻击+18 生命+60. 大地崩裂, 两回合一次",
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
        name="破灭重剑", tier=5, atk=26, hp=40, mp=10, cat="greatsword",
        passive="strong_body", skill="world_cleave",
        desc="由战争巨剑与龙鳞锻造的神兵, 攻击+26 生命+40 蓝量+10. 裂地灭世, 两回合一次",
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
        name="深渊匕影", tier=5, atk=20, hp=20, mp=20, cat="dagger",
        passive="", skill="shadow_assassinate",
        desc="由刺客匕首与巫妖之魂淬炼, 攻击+20 生命+20 蓝量+20. 暗影五连击",
        art=[
            "  ▓",
            "  ▓",
            "  ▓",
            " / \\",
            "▓   ▓",
            " ███",
            "     ",
        ]),
}

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
    "heavy":     dict(name="重击",   mp=10, kind="dmg", value=16,
                      desc="消耗10蓝, 造成 16+攻击 伤害"),
    "heal":      dict(name="治疗术", mp=12, kind="heal", value=25,
                      desc="消耗12蓝, 回复 25 生命"),
    "burst":     dict(name="爆发",   mp=14, kind="dmg", value=22,
                      desc="消耗14蓝, 造成 22+攻击 伤害"),
    "pierce":    dict(name="破甲一击", mp=18, kind="pierce", value=30,
                      desc="消耗18蓝, 无视格挡造成 30+攻击 伤害"),
    "rage":      dict(name="狂暴",   mp=10, kind="buff_atk", value=4,
                      desc="消耗10蓝, 本场战斗攻击+4"),
    # ----- 武器技能 -----
    "cleave":    dict(name="顺劈斩", mp=8,  kind="dmg", value=12,
                      desc="铁剑技能, 消耗8蓝, 造成 12+攻击 伤害"),
    "whirlwind": dict(name="旋风斩", mp=12, kind="dmg", value=20,
                      desc="战斧技能, 消耗12蓝, 造成 20+攻击 伤害"),
    "fireball":  dict(name="火球术", mp=12, kind="dmg", value=26,
                      desc="法杖技能, 消耗12蓝, 造成 26+攻击 伤害"),
    "quake":     dict(name="大地震击", mp=18, kind="pierce", value=36,
                      desc="战锤技能, 消耗18蓝, 无视格挡造成 36+攻击 伤害"),
    # ----- 匕首技能 (连击, 耗蓝少) -----
    "double_stab": dict(name="连刺", mp=5, kind="combo", hits=2, value=9,
                        desc="匕首技能, 消耗5蓝, 连刺2次共18伤害"),
    "venom_stab":  dict(name="淬毒连击", mp=6, kind="combo", hits=3, value=9,
                        desc="匕首技能, 消耗6蓝, 三连击共27伤害"),
    "assassinate": dict(name="终结连击", mp=7, kind="combo", hits=4, value=10,
                        desc="匕首技能, 消耗7蓝, 四连击共40伤害"),
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
    "shadow_assassinate": dict(name="暗影连刺", mp=10, kind="combo", hits=5, value=12,
                               desc="神器技能, 消耗10蓝, 暗影五连击共60伤害"),
}

# 等级解锁: level -> 基础技能id
LVL_SKILLS = {
    1: ["attack", "defend"],
    2: ["heavy"],
    4: ["heal"],
    6: ["burst"],
    8: ["rage"],
    10: ["pierce"],
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
}

# 被动效果名
PASSIVE_NAME = {
    "mana_regen": "每回合回复2蓝",
    "strong_body": "生命力强健",
    "guard_start": "战斗开始获得4格挡",
    "coin_bonus": "获得金币+25%",
}

# ============================================================
# 数据: 材料 (用于高等级武器合成)
# ============================================================
# tier: 1 普通(小怪) / 2 中级(精英) / 3 高级(Boss专属)
# 小怪掉 tier1, 精英掉 tier1-2, Boss 掉 tier1-3 + 专属材料
MATERIAL_LIB = {
    "iron":             dict(name="铁锭",       tier=1, icon="⛏",
                             desc="最基础的锻造材料"),
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
    "shadow_shard":     dict(name="暗影碎片",   tier=3, icon="🌑",
                             desc="蕴含暗影之力, 精英/Boss掉落"),
    "dragon_scale":     dict(name="龙鳞",       tier=3, icon="🐲",
                             desc="远古巨龙掉落的鳞片 (Boss专属)"),
    "lich_soul":        dict(name="巫妖之魂",   tier=3, icon="💀",
                             desc="巫妖王凝结的灵魂 (Boss专属)"),
}

# 各 tier 的材料 id 池 (供随机掉落)
MATERIAL_POOL = {
    1: ["iron", "fire_shard", "water_shard"],
    2: ["lightning_shard", "wind_shard", "mithril"],
    3: ["shadow_shard"],
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
        mats={"dragon_scale": 1, "shadow_shard": 2},
        desc="以巨人战锤为基, 熔入龙鳞与暗影之力, 铸成撼地神锤",
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
}

# ============================================================
# 数据: 药水
# ============================================================
POTION_LIB = {
    "hp":     dict(name="治疗药水", desc="回复 30 生命", kind="heal", value=30),
    "mp":     dict(name="蓝量药水", desc="回复 25 蓝量", kind="mp", value=25),
    "atk":    dict(name="力量药水", desc="本场战斗攻击+5", kind="buff_atk", value=5),
    "big_hp": dict(name="大治疗药水", desc="回复 60 生命", kind="heal", value=60),
}

# ============================================================
# 数据: 怪物
# ============================================================
MONSTER_ART = {
    "slime": [
        "  ╭──────╮",
        " (  ██  ██  )",
        "  ( ██████ )",
        "   ╰──────╯",
    ],
    "rat": [
        "   /\\_/\\",
        "  ( o.o )",
        "   > ^ <",
        "  ( ██ ██ )",
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
}

# 怪物: (hp, atk, acts, exp, gold_reward, art, desc)
# acts: 行动池, 战斗中随机选
def monster_lib():
    return {
        "slime":   dict(name="史莱姆", hp=32,  atk=6,  acts=("attack",),
                        exp=40, gold=18, art=MONSTER_ART["slime"],
                        desc="黏糊糊的低等魔物."),
        "rat":     dict(name="大老鼠", hp=28,  atk=7,  acts=("attack", "double"),
                        exp=42, gold=20, art=MONSTER_ART["rat"],
                        desc="敏捷的啮齿魔物, 双爪扑击."),
        "skeleton":dict(name="骷髅兵", hp=38, atk=6,  acts=("attack", "defend"),
                        exp=45, gold=22, art=MONSTER_ART["skeleton"],
                        desc="会格挡的不死士兵."),
        "goblin":  dict(name="哥布林", hp=42,  atk=8,  acts=("attack", "buff"),
                        exp=50, gold=25, art=MONSTER_ART["goblin"],
                        desc="凶狠的小个子强盗, 会自我强化."),
        "wolf":    dict(name="座狼",   hp=36,  atk=8,  acts=("attack", "double"),
                        exp=48, gold=24, art=MONSTER_ART["wolf"],
                        desc="嗜血的野兽, 行动迅捷."),
        # 精英
        "ogre":    dict(name="食人魔", hp=85,  atk=12, acts=("attack", "smash", "buff"),
                        exp=140, gold=70, art=MONSTER_ART["ogre"],
                        desc="力大无穷的精英, 重击可穿透格挡."),
        "golem":   dict(name="石魔像", hp=100, atk=9,  acts=("defend", "attack", "smash"),
                        exp=150, gold=75, art=MONSTER_ART["golem"],
                        desc="皮糙肉厚的精英, 常驻格挡."),
        "knight":  dict(name="黑骑士", hp=90,  atk=11, acts=("attack", "defend", "smash"),
                        exp=155, gold=78, art=MONSTER_ART["knight"],
                        desc="堕落骑士, 攻守兼备."),
        # boss
        "dragon":  dict(name="远古巨龙", hp=170, atk=15, acts=("attack", "smash", "breath", "buff"),
                        exp=500, gold=200, art=MONSTER_ART["dragon"],
                        desc="塔顶之主, 龙息灼烧万物."),
        "lich":    dict(name="巫妖王", hp=150, atk=13, acts=("attack", "double", "smash", "summon_buff"),
                        exp=500, gold=200, art=MONSTER_ART["lich"],
                        desc="不朽的巫妖, 魔法阴冷彻骨."),
    }

MONSTER_POOL = {
    "normal": ["slime", "rat", "skeleton", "goblin", "wolf"],
    "elite":  ["ogre", "golem", "knight"],
}

# ============================================================
# 地图生成 (一层): 7阶段分层 DAG, 节点不完全连通
# 精英/商店分布在阶段5-7, 且可多路径到达
# ============================================================
# 阶段节点数 (不含起点与 boss 终点)
# 节点类型计数: 宝藏2 事件4 小怪8 精英2 商店2  (比例 1:2:4:1:1 放大)
# 分配到 7 个阶段 (阶段5-7 出现商店与精英):
#   阶段1(3): 小怪+事件+小怪        (营地延伸3条路)
#   阶段2(3): 小怪+小怪+事件
#   阶段3(2): 小怪+宝藏
#   阶段4(2): 小怪+小怪
#   阶段5(2): 精英+事件
#   阶段6(3): 商店+小怪+事件
#   阶段7(3): 精英+宝藏+商店
STAGE_NODES = [3, 3, 2, 2, 2, 3, 3]
STAGE_KINDS = [["monster", "event", "monster"],
               ["monster", "monster", "event"],
               ["monster", "treasure"],
               ["monster", "monster"],
               ["elite", "event"],
               ["shop", "monster", "event"],
               ["elite", "treasure", "shop"]]


def generate_map(rng):
    """生成一层的地图结构.
    返回 (nodes, edges):
      nodes: list of dict {kind, stage, index}
      edges: list of (from_node_id, to_node_id)
    node id = 阶段内节点索引, 用 (stage, index) 表示, 起点为 start.
    连接规则: 营地延伸3条路到阶段1; 节点间不完全连通;
    精英/商店节点必定从上一阶段的所有节点连入, 保证多路径可达.
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

    edges = []          # list of (src, dst), src/dst 为 (stage,index) 或 'start'/'boss'

    def stage_children(s):
        """第 s 阶段的节点 id 列表."""
        return [(s, i) for i in range(len(STAGE_KINDS[s]))]

    # 营地 -> 阶段1 所有节点 (延伸 3 条路)
    for c in stage_children(0):
        edges.append(("start", c))

    # 阶段 i -> 阶段 i+1: 不完全连通, 但有充足分支
    for s in range(total_stages - 1):
        cur = stage_children(s)
        nxt = stage_children(s + 1)
        rng.shuffle(cur)
        # 保证下一阶段每个节点至少一个入度 (可达)
        for j, t in enumerate(nxt):
            src = cur[j % len(cur)]
            if (src, t) not in edges:
                edges.append((src, t))
        # 每个源节点额外连到 1~全部 个下一阶段节点 (产生分支/多路径)
        for src in cur:
            for t in rng.sample(nxt, rng.randint(1, len(nxt))):
                if (src, t) not in edges:
                    edges.append((src, t))
        # 精英/商店: 上一阶段所有节点连入 -> 多个路径到达
        for t in nxt:
            if nodes[t] in ("elite", "shop"):
                for src in cur:
                    if (src, t) not in edges:
                        edges.append((src, t))

    # 阶段7 -> boss
    for c in stage_children(total_stages - 1):
        edges.append((c, boss_id))

    # 记录节点总数/顺序便于布局
    ordered = ["start"]
    for s in range(total_stages):
        ordered.extend(stage_children(s))
    ordered.append(boss_id)
    return nodes, edges, ordered


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
        self.accessory = None   # 饰品 (id 或 None)
        self.gold = 40
        self.potions = ["hp", "hp", "mp"]
        self.bag = []           # 背包: 持有的武器 id 列表 (不含当前装备)
        self.trinkets = []      # 饰品栏: 持有的饰品 id 列表 (不含当前装备)
        self.materials = {}     # 材料: {material_id: 数量} (用于合成)
        self.block = 0          # 战斗中格挡
        self.battle_atk_bonus = 0
        self.weapon_hp_bonus = 0   # 武器提供的生命上限加成
        self.weapon_mp_bonus = 0   # 武器提供的蓝量上限加成
        self.trinket_hp_bonus = 0  # 饰品提供的生命上限加成
        self.trinket_mp_bonus = 0  # 饰品提供的蓝量上限加成
        self.max_action = 15       # 行动力上限 (每层)
        self.action = 15           # 当前行动力

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

    def weapon_atk(self):
        return self.weapon_data["atk"]

    def trinket_atk(self):
        return self.trinket_data["atk"] if self.trinket_data else 0

    def trinket_mp(self):
        return self.trinket_data["mp"] if self.trinket_data else 0

    def total_atk(self):
        return self.atk + self.weapon_atk() + self.trinket_atk() + self.battle_atk_bonus

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
            leveled = True
        return leveled

    def unlocked_skills(self):
        """当前可用的技能 id 列表 (基础+武器)."""
        ids = []
        for lv, sk in sorted(LVL_SKILLS.items()):
            if self.level >= lv:
                ids.extend(sk)
        if self.weapon_skill not in ids:
            ids.append(self.weapon_skill)
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
        # 技能冷却: {sid: 剩余冷却回合}; 0 表示可用
        self.skill_cd = {}
        # 被动: mana_regen 每回合回蓝
        self.regen_mp = 2 * player.passives.count("mana_regen")
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

    # ---- 玩家行动 ----
    def player_attack(self):
        dmg = self.player.total_atk()
        self.enemy.block, self.enemy.hp = self._damage(self.enemy.block, self.enemy.hp, dmg)
        return f"你挥动武器, 造成 {dmg} 伤害."

    def player_defend(self):
        self.player.block += 8
        return f"你举盾防御, 获得 8 点格挡."

    def player_skill(self, sid):
        sk = SKILL_LIB[sid]
        if self.player.mp < sk["mp"]:
            return "no_mp"
        if self.skill_cd.get(sid, 0) > 0:
            return "cooldown"
        self.player.mp -= sk["mp"]
        # 带冷却的技能: 施放后进入冷却
        if sk.get("cooldown"):
            self.skill_cd[sid] = sk["cooldown"]  # 用后需隔 cooldown-1 回合
        val = sk["value"]
        kind = sk["kind"]
        if kind == "dmg":
            dmg = val + self.player.total_atk()
            self.enemy.block, self.enemy.hp = self._damage(self.enemy.block, self.enemy.hp, dmg)
            return f"你施展【{sk['name']}】, 造成 {dmg} 伤害."
        elif kind == "pierce":
            dmg = val + self.player.total_atk()
            self.enemy.hp -= dmg
            return f"你施展【{sk['name']}】, 无视格挡造成 {dmg} 伤害!"
        elif kind == "combo":
            # 连击: 多次命中, 每次造成 value 伤害 (不叠加攻击力)
            total = 0
            for _ in range(sk["hits"]):
                if not self.enemy.alive:
                    break
                self.enemy.block, self.enemy.hp = self._damage(self.enemy.block, self.enemy.hp, val)
                total += val
            return f"你施展【{sk['name']}】, 连击 {sk['hits']} 次共造成 {total} 伤害!"
        elif kind == "heal":
            before = self.player.hp
            self.player.hp = min(self.player.max_hp, self.player.hp + val)
            return f"你施展【{sk['name']}】, 回复 {self.player.hp - before} 生命."
        elif kind == "block":
            self.player.block += val
            return f"你施展【{sk['name']}】, 获得 {val} 点格挡."
        elif kind == "buff_atk":
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

    # ---- 敌人行动 ----
    def enemy_turn(self):
        """敌人行动. 返回日志."""
        self.enemy.block = 0
        act = self.rng.choice(self.enemy.acts)
        logs = []
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
        self.map_order = []
        self.current_node = "start"
        self.prev_node = None      # 上一个节点 (用于返回)
        self.floor = 1
        self.combat = None
        self.battle_log = []

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
        txt = (f"第 {self.floor} 层    "
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
                "node_state": self.node_state,
                "current_node": self.current_node,
                "prev_node": self.prev_node,
                "shop_state": self._shop_state() if hasattr(self, "_shop_items") else None,
            }
            with open(self._save_path(), "wb") as f:
                pickle.dump(state, f)
            self._set_hint("💾 已存档! (按 Z 再次存档)")
        except Exception as e:
            self._set_hint(f"存档失败: {e}")

    def _shop_state(self):
        return (self._shop_items, self._shop_trinkets, self._shop_potions)

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
        self.node_state = st["node_state"]
        self.current_node = st["current_node"]
        self.prev_node = st["prev_node"]
        if st.get("shop_state"):
            self._shop_items, self._shop_trinkets, self._shop_potions = st["shop_state"]
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
            ("武器图鉴", self.show_weapon_codex),
            ("技能图鉴", self.show_skill_codex),
            ("怪物图鉴", self.show_monster_codex),
            ("饰品图鉴", self.show_trinket_codex),
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
        tk.Label(wrap, text="⚠ 行动力耗尽仍未到关底, 将直面强化Boss!",
                 bg=COLOR_BG, fg=COLOR_BAD, font=FONT_MAIN).pack(pady=(0, 8))
        for key in ["monster", "elite", "treasure", "event", "shop", "boss"]:
            row = tk.Frame(wrap, bg=COLOR_BG)
            row.pack(pady=2)
            tk.Label(row, text=NODE_ICON[key], bg=COLOR_BG, fg=NODE_COLOR[key],
                     font=("Consolas", 14)).pack(side="left", padx=6)
            tk.Label(row, text=f"  {NODE_LABEL[key]}", bg=COLOR_BG, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(side="left")
            desc = {
                "monster": "普通战斗",
                "elite": "高难战斗, 丰厚奖励",
                "treasure": "金币与装备",
                "event": "抉择与机缘",
                "shop": "购买装备与药水",
                "boss": "关底首领",
            }[key]
            tk.Label(row, text=desc, bg=COLOR_BG, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(side="left", padx=10)

    # ---------------- 地图 ----------------
    def begin_floor(self):
        self.map_nodes, self.map_edges, self.map_order = generate_map(self.rng)
        self.node_state = {nid: ("done" if nid == "start" else "todo") for nid in self.map_order}
        self.current_node = "start"
        self.prev_node = None
        self.show_map()

    def show_map(self):
        self._push_view(self.show_map)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        self._render_map_canvas()
        # 提示
        p = self.player
        tip = f"⚡ 剩余行动力 {p.action} · 每走一步(前进或返回)消耗 1 点"
        tk.Label(self.content, text=tip, bg=COLOR_BG, fg=COLOR_SUB,
                 font=FONT_MAIN).pack(pady=(6, 0))
        self._btn(self.action_inner, "查看状态 ▶", self.show_character_sheet, color=COLOR_BTN)
        self._btn(self.action_inner, "🎒 背包", self.show_bag, color=COLOR_BTN)
        self._btn(self.action_inner, "⚔ 装备", self.show_equip, color=COLOR_BTN)
        # 返回上一节点 (消耗 1 行动值, 不触发效果)
        if self.prev_node is not None and p.action > 0 and self.prev_node != self.current_node:
            self._btn(self.action_inner, "← 返回上一节点 (-1⚡)", self.go_back,
                      color=COLOR_SELECT, padx=16, pady=6)
        # 回城 (消耗 1 行动值, 回到营地)
        if self.current_node != "start" and p.action > 0:
            self._btn(self.action_inner, "🏕 回城 (-1⚡)", self.go_home,
                      color=COLOR_GOLD, padx=16, pady=6)
        if p.action <= 0:
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
        canvas = tk.Canvas(self.content, width=cw, height=ch, bg=COLOR_BG,
                           highlightthickness=0)
        canvas.pack(pady=4)
        canvas.configure(scrollregion=(0, 0, cw, ch))

        # 画连接线
        for src, dst in edges:
            (x1_, y1_) = pos[src]
            (x2_, y2_) = pos[dst]
            src_ok = (src == self.current_node or dst == self.current_node)
            dst_done = self.node_state.get(dst) == "done"
            linecolor = COLOR_SELECT if src_ok else (COLOR_SUB if not dst_done else COLOR_BORDER)
            canvas.create_line(x1_, y1_, x2_, y2_, fill=linecolor, width=2)

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
            if self._is_next(nid) and p_action > 0:
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
        """nid 是否为当前节点可直接到达的相邻节点 (前进或返回均可, 连线双向通行)."""
        for src, dst in self.map_edges:
            if (src == self.current_node and dst == nid) or \
               (dst == self.current_node and src == nid):
                return True
        return False

    def on_node_click(self, nid):
        if not self._is_next(nid):
            return
        if self.player.action <= 0:
            return  # 行动力耗尽, 只能打强化Boss
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
        elif kind == "elite":
            self.start_battle(monster=False)
        elif kind == "treasure":
            self.show_treasure()
        elif kind == "event":
            self.show_event()
        elif kind == "shop":
            self.show_shop()
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
        self.show_map()

    def start_strong_boss(self):
        """行动力耗尽时提前直面强化Boss."""
        self.start_battle(monster=False, boss=True, strong=True)

    # ---------------- 战斗 ----------------
    def _make_enemy(self, monster, boss=False, strong=False):
        lib = monster_lib()
        if boss:
            key = self.rng.choice(["dragon", "lich"])
        elif monster:
            key = self.rng.choice(MONSTER_POOL["normal"])
        else:
            key = self.rng.choice(MONSTER_POOL["elite"])
        data = lib[key]
        e = Enemy(data)
        e.key = key  # 记录种类 (供 Boss 专属掉落判断)
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

    def start_battle(self, monster, boss=False, strong=False):
        enemy = self._make_enemy(monster, boss, strong)
        self.combat = RpgCombat(self.player, enemy, self.rng)
        self.battle_log = []
        self.boss_fight = boss
        self.strong_boss = strong
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

        # 敌人区
        enemy_frame = tk.Frame(self.content, bg=COLOR_BG)
        enemy_frame.pack(fill="x", padx=10)
        self._render_enemy(enemy_frame, e)

        # 战斗日志
        self.battle_log_label = self._label("")
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

    def _render_actions(self):
        c = self.combat
        p = self.player
        # 主行动按钮
        self._btn(self.action_inner, "⚔ 攻击", self.battle_attack, color=COLOR_BAD)
        self._btn(self.action_inner, "🛡 防御", self.battle_defend, color=COLOR_SELECT)
        # 技能按钮 (带蓝量显示, 冷却显示)
        for sid, sk in p.skills_data():
            if sid in ("attack", "defend"):
                continue  # 已有按钮
            cost = sk["mp"]
            ready = c.skill_ready(sid)
            if ready:
                self._btn(self.action_inner, f"{sk['name']} ({cost}✦)",
                          lambda s=sid: self.battle_skill(s), color=COLOR_BTN)
            elif c.skill_cd.get(sid, 0) > 0:
                # 冷却中
                self._btn(self.action_inner, f"{sk['name']} ⏳{c.skill_cd[sid]}",
                          lambda s=sid: self.battle_skill(s), color="#2a2a3e")
            else:
                # 蓝不足
                self._btn(self.action_inner, f"{sk['name']} ({cost}✦)",
                          lambda s=sid: self.battle_skill(s), color="#2a2a3e")
        # 药水
        for i, pid in enumerate(p.potions):
            pot = POTION_LIB[pid]
            self._btn(self.action_inner, f"🧪 {pot['name']}",
                      lambda i=i: self.battle_potion(i), color=COLOR_GOLD)

    # 玩家行动执行 -> 敌人反击 -> 检查胜负 -> 回玩家回合
    def _do_action(self, msg):
        self.battle_log = [msg]
        # 技能冷却递减 (每回合)
        if self.combat:
            self.combat.tick_cooldowns()
        # 若玩家行动已击杀怪物, 怪物不再反击, 直接胜利
        if not self.combat.enemy.alive:
            self._after_combat_tick()
            return
        # 敌人回合
        enemy_logs = self.combat.enemy_turn()
        self.battle_log += enemy_logs
        self._after_combat_tick()

    def _after_combat_tick(self):
        c = self.combat
        if not c.enemy.alive:
            self.battle_victory()
            return
        if self.player.hp <= 0:
            self.player.hp = 0
            self.battle_defeat()
            return
        # 回蓝 (被动)
        if self.combat.regen_mp > 0:
            self.player.mp = min(self.player.max_mp, self.player.mp + self.combat.regen_mp)
        self.render_battle()

    def battle_attack(self):
        msg = self.combat.player_attack()
        self._do_action(msg)

    def battle_defend(self):
        msg = self.combat.player_defend()
        self._do_action(msg)

    def battle_skill(self, sid):
        msg = self.combat.player_skill(sid)
        if msg == "no_mp":
            self._set_log("蓝量不足!")
            return
        if msg == "cooldown":
            self._set_log("技能冷却中, 还需等待!")
            return
        self._do_action(msg)

    def battle_potion(self, idx):
        pid = self.player.potions.pop(idx)
        msg = self.combat.player_potion(pid)
        self._do_action(msg)

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
        elif self.map_nodes.get(self.current_node) == "elite":
            drop = self._elite_drop()
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
        # 精英必定掉武器 + 饰品 + 材料 (含中级) + 药水
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
        # boss 必定掉 高级武器 + 饰品 + 大量材料(含高级) + 专属装备 + 专属材料
        parts = ["大治疗药水"]
        self.player.potions.append("big_hp")
        parts.append(self._offer_random_weapon("Boss掉落", tier_min=3))
        parts.append(self._offer_random_trinket("Boss掉落", tier_min=2))
        parts.append(self._drop_materials(self.rng.randint(4, 5), 3))
        # 专属掉落: 由当前 boss 决定
        boss_key = self.combat.enemy.key
        if boss_key == "lich":
            parts.append(self._drop_specific_material("lich_soul", 1))
            self.player.add_trinket("lich_ring")
            parts.append("获得Boss专属饰品【亡魂戒指】")
        else:  # dragon 默认
            parts.append(self._drop_specific_material("dragon_scale", 1))
            self.player.add_trinket("dragon_amulet")
            parts.append("获得Boss专属饰品【龙鳞护符】")
        return " + ".join(parts)

    def _drop_specific_material(self, mid, n):
        """掉落指定材料 n 个, 返回日志文本."""
        self.player.add_material(mid, n)
        return f"获得专属材料【{MATERIAL_LIB[mid]['name']}】×{n}"

    def _normal_drop(self):
        # 小怪: 必掉材料 (1-2个 tier1), 概率掉武器/饰品
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

    def _offer_random_weapon(self, source, tier_min=1, force_better=False):
        """随机给一把武器, 存入背包 (不自动装备). 神器(tier5)仅能通过合成获得, 不直接掉落."""
        pool = [w for w in WEAPON_LIB
                if WEAPON_LIB[w]["tier"] >= tier_min and WEAPON_LIB[w]["tier"] < 5]
        pick = self.rng.choice(pool)
        w = WEAPON_LIB[pick]
        self.player.add_weapon_to_bag(pick)
        return f"获得武器【{w['name']}】(已存入背包)"

    def _offer_random_trinket(self, source, tier_min=1):
        """随机给一件饰品, 存入饰品栏 (不自动装备). 排除Boss专属饰品."""
        pool = [t for t in TRINKET_LIB
                if TRINKET_LIB[t]["tier"] >= tier_min
                and t not in ("dragon_amulet", "lich_ring")]
        tid = self.rng.choice(pool)
        t = TRINKET_LIB[tid]
        self.player.add_trinket(tid)
        return f"获得饰品【{t['name']}】(已存入饰品栏)"

    def _apply_weapon_hp(self):
        """武器生命加成已在 equip_weapon 中处理, 保留占位."""
        pass

    def boss_clear(self):
        """击败Boss: 进入下一层. (进入下一层的条件即为打败Boss)"""
        self.next_floor()

    def next_floor(self):
        """进入下一层: 行动力重置, 回复部分状态, 重新生成地图, 敌人更强."""
        self.floor += 1
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

        panel = self._panel()
        panel.pack(fill="x", padx=20, pady=4)
        atk_str = f"基础{p.atk} + 武器{wd['atk']}"
        if td and td["atk"]:
            atk_str += f" + 饰品{td['atk']}"
        if p.battle_atk_bonus:
            atk_str += f" + 临时{p.battle_atk_bonus}"
        rows = [
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
        wp = self._panel()
        wp.pack(fill="x", padx=20, pady=4)
        tk.Label(wp, text=f"🔨 当前武器: {wd['name']}   (攻击+{wd['atk']}, 生命+{wd['hp']}, 蓝量+{wd['mp']})",
                 bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w", padx=16, pady=3)
        tk.Label(wp, text="   " + wd["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                 font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
        if wd["passive"]:
            pname = PASSIVE_NAME.get(wd["passive"], wd["passive"])
            tk.Label(wp, text=f"  被动: {pname}", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)

        # 饰品
        tp = self._panel()
        tp.pack(fill="x", padx=20, pady=4)
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

        # 技能
        sp = self._panel()
        sp.pack(fill="x", padx=20, pady=4)
        tk.Label(sp, text="技能", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        for sid, sk in p.skills_data():
            cost = f" ({sk['mp']}✦)" if sk["mp"] else ""
            if sid in WEAPON_LIB.get(p.weapon, {}).get("skill", ""):
                src = "武器"
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
        pp = self._panel()
        pp.pack(fill="x", padx=20, pady=4)
        tk.Label(pp, text="药水", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if not p.potions:
            tk.Label(pp, text="  ( 空 )", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=16, pady=1)
        for pid in p.potions:
            pot = POTION_LIB[pid]
            tk.Label(pp, text=f"  🧪 {pot['name']}  —  {pot['desc']}",
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
        # 可能得药水/武器/饰品
        r = self.rng.random()
        extra = ""
        if r < 0.4:
            pid = self.rng.choice(["hp", "mp", "atk"])
            self.player.potions.append(pid)
            extra = f"发现一瓶{POTION_LIB[pid]['name']}!"
        elif r < 0.65:
            extra = self._offer_random_weapon("宝藏")
        elif r < 0.85:
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

        # 商品: 武器 + 饰品 + 药水
        if not hasattr(self, "_shop_items"):
            wpn_pool = [w for w in WEAPON_LIB
                        if 2 <= WEAPON_LIB[w]["tier"] < 5]  # 不含神器(tier5), 神器仅靠合成
            self._shop_items = self.rng.sample(wpn_pool, min(3, len(wpn_pool)))
            self._shop_trinkets = self.rng.sample(
                [t for t in TRINKET_LIB if TRINKET_LIB[t]["tier"] <= 2],
                min(2, len([t for t in TRINKET_LIB if TRINKET_LIB[t]["tier"] <= 2])))
            self._shop_potions = self.rng.sample(list(POTION_LIB.keys()), 3)
            self._shop_price = {"battle_axe": 70, "magic_staff": 70, "giant_hammer": 120,
                                "steel_dagger": 65, "venom_dagger": 100, "assassin_dagger": 150,
                                "claymore": 75, "giant_blade": 110, "war_greatsword": 160}
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

    def buy_potion(self, pid, price):
        if self.player.gold < price:
            self._shop_notice("金币不足!")
            return
        self.player.gold -= price
        self.player.potions.append(pid)
        self._shop_notice(f"购买了{POTION_LIB[pid]['name']}!")

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
        if not p.bag:
            tk.Label(self.content, text="( 背包空空如也, 击败精英/Boss或从商店可获得武器 )",
                     bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=20)
        else:
            for wid in list(p.bag):
                w = WEAPON_LIB[wid]
                row = self._panel()
                row.pack(fill="x", padx=20, pady=3)
                inner = tk.Frame(row, bg=COLOR_PANEL)
                inner.pack(padx=10, pady=4)
                txt = (f"🔨 {w['name']}  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}"
                       f"  技能:{SKILL_LIB[w['skill']]['name']}")
                tk.Label(inner, text=txt, bg=COLOR_PANEL, fg=COLOR_TEXT,
                         font=FONT_MAIN).pack(anchor="w")
                bbar = tk.Frame(inner, bg=COLOR_PANEL)
                bbar.pack(anchor="w", pady=(2, 0))
                tk.Button(bbar, text="⚔ 装备", bg=COLOR_OK, fg=COLOR_TEXT, relief="flat",
                          font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                          command=lambda wid=wid: self.equip_from_bag(wid)).pack(side="left", padx=2)
                tk.Button(bbar, text="💰 卖出 (+{})".format(self._sell_price(wid)),
                          bg=COLOR_BTN, fg=COLOR_GOLD, relief="flat",
                          font=FONT_MAIN, bd=0, cursor="hand2", padx=8, pady=2,
                          command=lambda wid=wid: self.sell_weapon(wid)).pack(side="left", padx=2)

        # 饰品栏
        tsp = self._panel()
        tsp.pack(fill="x", padx=20, pady=3)
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
        msp = self._panel()
        msp.pack(fill="x", padx=20, pady=3)
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

    # ---------------- 合成系统 ----------------
    CAT_CN = {"sword": "剑", "axe": "斧", "staff": "法杖", "hammer": "锤",
              "dagger": "匕首", "greatsword": "重剑"}

    def show_craft(self):
        """合成界面: 用最高等武器 + Boss材料 合成神器 (入口在背包)."""
        self._push_view(self.show_craft)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        p = self.player
        tk.Label(self.content, text="🔨 武器合成", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=8)
        tk.Label(self.content, text="以最高等武器为基, 熔入Boss掉落的材料, 铸成传说神器",
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

        # 当前装备
        wd = p.weapon_data
        cur = self._panel()
        cur.pack(fill="x", padx=20, pady=4)
        tk.Label(cur, text=f"当前武器: 🔨 {wd['name']}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                 font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        if p.trinket_data:
            tk.Label(cur, text=f"当前饰品: ◆ {p.trinket_data['name']}",
                     bg=COLOR_PANEL, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(2, 6))
        else:
            tk.Label(cur, text="当前饰品: (无)", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=16, pady=(2, 6))

        # 武器列表: 背包武器 + 当前武器
        wp = self._panel()
        wp.pack(fill="x", padx=20, pady=4)
        tk.Label(wp, text="— 武器 —", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=16, pady=(6, 2))
        self._equip_weapon_button(wp, p.weapon, equipped=True)
        for wid in list(p.bag):
            self._equip_weapon_button(wp, wid, equipped=False)

        # 饰品列表: 当前饰品 + 持有的饰品
        tp = self._panel()
        tp.pack(fill="x", padx=20, pady=4)
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
        txt = f"  🔨 {w['name']}  攻击+{w['atk']} 生命+{w['hp']} 蓝量+{w['mp']}  技能:{SKILL_LIB[w['skill']]['name']}"
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

    # ---------------- 图鉴 ----------------
    def show_weapon_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🔨 武器图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 8))
        CAT = {"sword": "剑", "axe": "斧", "staff": "法杖", "hammer": "锤",
               "dagger": "匕首", "greatsword": "重剑"}
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
            sk = SKILL_LIB[w["skill"]]
            extra = ""
            if sk.get("cooldown"):
                extra = "  [两回合一次]"
            elif sk.get("hits"):
                extra = f"  [连击x{sk['hits']}]"
            tk.Label(right, text=f"  武器技能: {sk['name']} ({sk['mp']}✦) — {sk['desc']}{extra}",
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
            sk = SKILL_LIB[w["skill"]]
            extra = ""
            if sk.get("cooldown"):
                extra = "  [两回合一次]"
            elif sk.get("hits"):
                extra = f"  [连击x{sk['hits']}]"
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=2)
            tk.Label(p, text=f"{w['name']} → {sk['name']} ({sk['mp']}✦){extra}",
                     bg=COLOR_PANEL, fg=COLOR_GOLD, font=FONT_MAIN).pack(anchor="w", padx=10, pady=(4, 0))
            tk.Label(p, text="   " + sk["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_monster_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="👹 怪物图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 4))
        lib = monster_lib()
        canvas, inner, scroll = self._scroll_container()
        groups = [("小怪", MONSTER_POOL["normal"]), ("精英", MONSTER_POOL["elite"]),
                  ("首领", ["dragon", "lich"])]
        for title, keys in groups:
            tk.Label(inner, text=f"— {title} —", bg=COLOR_BG, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(8, 2))
            for k in keys:
                m = lib[k]
                p = self._panel(inner)
                p.pack(fill="x", padx=10, pady=3)
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
        canvas = tk.Canvas(self.content, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLOR_BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return canvas, inner, scroll


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
