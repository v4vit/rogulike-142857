#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肉鸽文字回合制卡牌游戏 —— 类杀戮尖塔（Slay the Spire）

核心系统：
  - 节点地图：多层爬塔，每层由 小怪/精英/宝藏/事件 四类节点按 3:1:1:2 比例随机生成
  - 卡牌战斗：手牌 / 能量 / 抽牌堆 / 弃牌堆 / 消耗，格挡机制
  - 角色成长：金币、商店/事件强化卡组、遗物
  - 纯文字交互，标准库实现，无第三方依赖
"""

import random
import os
import sys
import textwrap

# ============================================================
# 强制 UTF-8 输出, 避免中文 Windows 默认 GBK 编码导致
# 特殊符号(⚔☠💰❔◆等)无法打印而崩溃
# ============================================================
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ============================================================
# 全局工具 & UI 组件
# ============================================================

clear = lambda: os.system("cls" if os.name == "nt" else "clear")

def pause(msg="[ 按回车继续 ]"):
    print(f"\n  {msg}")
    try:
        input("")
    except EOFError:
        pass

def center(s, width=62):
    return s.center(width)

# ---------- 面板 (圆角边框) ----------
_BOX = dict(tl="╭", tr="╮", bl="╰", br="╯", h="─", v="│")

def box(lines, title=None, width=62):
    """绘制一个圆角边框面板, lines 为内部行列表."""
    if title:
        pad = (width - len(title) - 2) // 2
        if pad < 2:
            pad = 2
        left = _BOX["h"] * (pad - 1)
        right = _BOX["h"] * max(0, width - pad - len(title) - 1)
        top = _BOX["tl"] + left + " " + title + " " + right + _BOX["tr"]
    else:
        top = _BOX["tl"] + _BOX["h"] * (width - 2) + _BOX["tr"]
    print(top)
    for ln in lines:
        print(_BOX["v"] + " " + ln.ljust(width - 4) + " " + _BOX["v"])
    print(_BOX["bl"] + _BOX["h"] * (width - 2) + _BOX["br"])

def title_bar(text, sub=None, width=62):
    """顶部大标题."""
    print("╔" + "═" * (width - 2) + "╗")
    print("║" + center(text, width - 2) + "║")
    if sub:
        print("║" + center(sub, width - 2) + "║")
    print("╚" + "═" * (width - 2) + "╝")

def banner(title="◆ 肉 鸽 试 炼 ◆", sub="Roguelite Arena"):
    clear()
    title_bar(title, sub)

# ---------- 菜单 ----------
def menu_prompt(prompt="选择 > "):
    try:
        return input("  " + prompt).strip()
    except EOFError:
        return ""

# ---------- 血条 ----------
def hp_bar(current, maximum, width=18):
    """精致血条: 满血绿色? 无彩色则用实心/空心. 返回字符串."""
    if maximum <= 0:
        return ""
    ratio = current / maximum
    filled = int(width * ratio)
    # 按血量分段着色符号 (无彩色, 用不同符号表达健康度)
    if ratio > 0.5:
        mark = "█"
    elif ratio > 0.25:
        mark = "▓"
    else:
        mark = "▒"
    bar = mark * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{maximum}"

# ---------- 卡片 ----------
# 用带圈编号显示手牌/选项, 简洁美观
CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"]

def num(n):
    """1->①, 2->② ... 超出用 [n]."""
    if 1 <= n <= 9:
        return CIRCLED[n - 1]
    return f"[{n}]"

def card_tag(cid, index=None):
    """单行卡牌标签: ① 打击(1费)"""
    c = CARD_LIB[cid]
    idx = (num(index) + " ") if index else ""
    cost = "◆" * c["cost"] if c["cost"] else "0"
    return f"{idx}{c['name']} {cost}"

def card_info(cid):
    """卡牌详情多行(用于选择/图鉴)."""
    c = CARD_LIB[cid]
    return [f"{c['name']}   {c['type']}牌  {c['cost']}费",
            f"{c['desc']}"]

def wrap(s, width=56):
    return "\n".join(textwrap.wrap(s, width))

# ============================================================
# 卡牌定义
# ============================================================

# 每张卡: (id, 名称, 费用, 类型, 效果描述, 效果函数数据)
# 类型: 攻击 / 技能 / 能力
# 效果通过字典描述, 由战斗引擎解释
CARD_LIB = {
    # ----- 攻击牌 -----
    "strike":  dict(name="打击",   cost=1, type="攻击", desc="造成 6 点伤害",
                    kind="dmg", value=6),
    "bash":    dict(name="重击",   cost=2, type="攻击", desc="造成 8 点伤害",
                    kind="dmg", value=8),
    "cleave":  dict(name="顺劈",   cost=1, type="攻击", desc="造成 8 点伤害",
                    kind="dmg", value=8),
    "whirl":   dict(name="旋风斩", cost=2, type="攻击", desc="造成 9 点伤害",
                    kind="dmg", value=9),
    "heavy":   dict(name="重锤",   cost=2, type="攻击", desc="造成 14 点伤害",
                    kind="dmg", value=14),
    "stab":    dict(name="连刺",   cost=1, type="攻击", desc="造成 3 点伤害 ×2 次",
                    kind="dmg_multi", value=3, times=2),
    "warcry":  dict(name="战吼",   cost=1, type="技能", desc="获得 5 点格挡",
                    kind="block", value=5),
    "guard":   dict(name="格挡",   cost=1, type="技能", desc="获得 5 点格挡",
                    kind="block", value=5),
    "fortify": dict(name="坚守",   cost=2, type="技能", desc="获得 10 点格挡",
                    kind="block", value=10),
    "pommel":  dict(name="剑柄",   cost=1, type="攻击", desc="造成 6 点伤害，抽 1 张牌",
                    kind="dmg_draw", value=6, draw=1),
    "heal":    dict(name="急救",   cost=1, type="技能", desc="回复 5 点生命",
                    kind="heal", value=5),
    "vamp":    dict(name="吸血",   cost=1, type="攻击", desc="造成 5 点伤害，回复等量生命",
                    kind="dmg_lifesteal", value=5),
    "flurry":  dict(name="连击",   cost=1, type="攻击", desc="造成 4 点伤害 ×2 次，获得 3 点格挡",
                    kind="dmg_multi_block", value=4, times=2, block=3),
    "crush":   dict(name="粉碎",   cost=3, type="攻击", desc="造成 18 点伤害",
                    kind="dmg", value=18),
    "bigblow": dict(name="破甲一击", cost=2, type="攻击", desc="造成 10 点伤害，无视格挡",
                    kind="dmg_pierce", value=10),
    "regen":   dict(name="再生",   cost=1, type="技能", desc="获得 2 点再生（每回合回血）",
                    kind="regen", value=2),
    "strength":dict(name="狂暴",   cost=1, type="技能", desc="本场战斗获得 2 点力量",
                    kind="strength", value=2),
    "focus":   dict(name="专注",   cost=1, type="技能", desc="抽 2 张牌",
                    kind="draw", value=2),
    "fort":    dict(name="钢铁壁垒", cost=2, type="技能", desc="获得 12 点格挡",
                    kind="block", value=12),
}

# 初始卡组
STARTING_DECK = ["strike", "strike", "strike", "strike", "bash", "guard", "guard", "guard"]

# 卡池 (商店/事件可获得的卡)
SHOP_POOL = ["cleave", "whirl", "heavy", "stab", "fortify", "pommel", "heal",
             "vamp", "flurry", "crush", "bigblow", "regen", "strength", "focus", "fort"]

# 卡牌稀有度: ⭐普通 ⭐⭐稀有 ⭐⭐⭐史诗
CARD_RARITY = {
    "strike": "⭐", "bash": "⭐", "guard": "⭐", "warcry": "⭐", "cleave": "⭐",
    "fortify": "⭐", "regen": "⭐", "heal": "⭐",
    "whirl": "⭐⭐", "heavy": "⭐⭐", "stab": "⭐⭐", "pommel": "⭐⭐", "vamp": "⭐⭐",
    "flurry": "⭐⭐", "strength": "⭐⭐", "focus": "⭐⭐",
    "crush": "⭐⭐⭐", "bigblow": "⭐⭐⭐", "fort": "⭐⭐⭐",
}

# ============================================================
# 怪物定义
# ============================================================

# 像素画: 每个怪物一段 ASCII 像素形象 (行宽约 22, 6~7 行)
# 用等宽方块字符绘制, UTF-8 安全
MONSTER_ART = {
    "slime": """
      ╭──────╮
     (  ██  ██  )
      ( ██████ )
     (  ██  ██  )
      ╰──────╯
       ·  ·  ·
""",
    "rat": """
      /\_/\
     ( o.o )
      > ^ <
     /  █  \\
    ( ██ ██ )
     ~~~~~~~~
""",
    "skeleton": """
     .-.__.-.
     | o  o |
     |  ||  |
      \\ \\/ /
     /||  ||\\
     |||  |||
      U    U
""",
    "bat": """
      /\\   /\\
     /  \\_/  \\
    |   /\\   |
     \\ /  \\ /
      \\ ██ /
       /  \\
      /    \\
""",
    "goblin": """
      ,---.
     / o o \\
    (  \\ /  )
     (  v  )
    __|___|__
   /  |   |  \\
  (  /     \\  )
   \\/       \\/
""",
    "wolf": """
      /\\_/\\
     ( o.o )
      >   <
     /  █  \\
    ( █████ )
     ~~~~~~~~
""",
    "mushroom": """
      __
     (  )
      ||  ▓
      || ▓▓
     /    \\
     ▓▓▓▓▓▓
     ▓▓▓▓▓▓
""",
    "ogre": """
      ._____.
     /  o o  \\
    |    |    |
     \\  ===  /
      \\_____/
    /|       |\\
   / |  ███  | \\
  (  | █████ |  )
   \\_|_______|_/
""",
    "golem": """
      .#####.
     .# o o #.
     #   |   #
     #  ===  #
      #  █  #
     # █████ #
    .############.
    #   ####   #
    ##############
""",
    "berserker": """
       ___/\\___
      /  o o  \\
     /    |    \\
    (     █     )
     \\   ===   /
      \\_______/
     /|       |\\
    / |  ████  | \\
   |  |  ████  |  |
    \\_|_______|_/
""",
    "shaman": """
       __  __
      ( o)(o )
      (  \\/  )
       (  ▓ )
       /||||\\
      ( ▓▓▓▓ )
     /  ▓  ▓  \\
    |   ▓  ▓   |
""",
    "knight": """
      __/\\___
     |  o o  |
     |   |   |
     |  ===  |
     |  ███  |
    /|  █████ |\\
   ( | ███████ | )
    \\|_________|/
""",
    "dragon": """
       /\    /\\
      /  \\__/  \\
     /    ██    \\
    |  ████████  |
     \\   /||\\   /
      \\ /    \\ /
       V      V
    (  ██  ██  )
""",
    "lich": """
       .-~~~-.
      | o   o |
      |   |   |
      |  \\_/  |
     /|  ██  |\\
    | |  ████  | |
    | |  ████  | |
     \\|_______|/
""",
    "abyssal": """
       .-____-.
      /  o  o  \\
     |    __    |
     |  /    \\  |
      \\/  ██  \\/
     /\\  ████  /\\
    |  \\██████/  |
     \\__________/
""",
    "deathknight":
        """
      .-=====-.
     |  o  o   |
     |    |    |
     |   ===   |
     |   ███   |
    /|   █████  |\\
   | |  ███████ | |
    \\|_________|/
""",
    "titan":
        """
       .________.
      /  o    o  \\
     |     __    |
     |    /  \\   |
      \\  | ██ |  /
       \\ | ███ | /
        \\|█████|/
     /|   █████  |\\
    | |   █████  | |
     \\|________|/
""",
    "spider":
        """
       __\\/__
      (  oo  )
      (  ██  )
     /  /\\/\\  \\
    |  ██  ██  |
    (  ██  ██  )
      \\______/
""",
}

def monster_lib():
    return {
        # ----- 小怪 (弱) -----
        "slime":  dict(name="史莱姆", hp=30,  dmg=6,  block=0, act=("attack",),
                       reward=25, desc="黏糊糊的低等魔物，一跳一跳地靠近。",
                       art=MONSTER_ART["slime"], drop=""),
        "rat":    dict(name="大老鼠", hp=26,  dmg=7,  block=0, act=("attack", "double"),
                       reward=22, desc="敏捷的啮齿魔物，双爪扑击。",
                       art=MONSTER_ART["rat"], drop=""),
        "skeleton":dict(name="骷髅兵", hp=34, dmg=6,  block=3, act=("attack", "guard"),
                        reward=28, desc="会格挡的不死士兵，骸骨咔咔作响。",
                        art=MONSTER_ART["skeleton"], drop=""),
        "bat":    dict(name="暗影蝙蝠", hp=22, dmg=5, block=0, act=("attack", "double"),
                       reward=24, desc="时而单次攻击，时而双重俯冲。",
                       art=MONSTER_ART["bat"], drop=""),
        "goblin": dict(name="哥布林", hp=38,  dmg=8,  block=0, act=("attack",),
                       reward=30, desc="凶狠的小个子强盗，挥舞短刀。",
                       art=MONSTER_ART["goblin"], drop=""),
        "wolf":   dict(name="座狼", hp=32,  dmg=7,  block=0, act=("attack", "double"),
                       reward=29, desc="嗜血的野兽，结伴出没。",
                       art=MONSTER_ART["wolf"], drop=""),
        "mushroom":dict(name="毒蘑菇", hp=24, dmg=5, block=0, act=("attack", "poison"),
                       reward=26, desc="散播孢子的变异蘑菇。",
                       art=MONSTER_ART["mushroom"], drop=""),
        # ----- 精英怪 (强) -----
        "ogre":   dict(name="食人魔", hp=70,  dmg=11, block=0, act=("attack", "smash"),
                       reward=60, desc="力大无穷的精英，重击可穿透格挡。",
                       art=MONSTER_ART["ogre"], drop="铁块"),
        "golem":  dict(name="石魔像", hp=85,  dmg=8,  block=6, act=("guard", "attack"),
                       reward=65, desc="皮糙肉厚的精英，常驻格挡。",
                       art=MONSTER_ART["golem"], drop="魔法核心"),
        "berserker": dict(name="狂战士", hp=60, dmg=9, block=0, act=("attack", "double", "enrage"),
                          reward=62, desc="越战越勇的精英，会自我强化。",
                          art=MONSTER_ART["berserker"], drop="战斧"),
        "shaman": dict(name="暗影萨满", hp=55, dmg=6, block=0, act=("summon", "attack"),
                       reward=66, desc="会召唤幼蛛助战的精英。",
                       art=MONSTER_ART["shaman"], drop="巫毒图腾"),
        "knight": dict(name="黑骑士", hp=65, dmg=10, block=5, act=("attack", "guard", "smash"),
                       reward=68, desc="堕落骑士，攻守兼备。",
                       art=MONSTER_ART["knight"], drop="黑钢盾"),
        # ----- BOSS (分层) -----
        "dragon": dict(name="远古巨龙", hp=150, dmg=14, block=0, act=("attack", "smash", "breath"),
                       reward=150, desc="塔顶之主，呼吸吐息灼烧万物。",
                       art=MONSTER_ART["dragon"], tier=1, drop="龙之逆鳞"),
        "lich":   dict(name="巫妖王", hp=130, dmg=12, block=4, act=("attack", "summon", "double"),
                       reward=150, desc="不朽的巫妖，召唤爪牙不死不休。",
                       art=MONSTER_ART["lich"], tier=1, drop="巫妖命匣"),
        "abyssal":dict(name="深渊魔龙", hp=220, dmg=17, block=0, act=("attack", "smash", "breath", "double"),
                       reward=250, desc="来自深渊的古老魔龙，吐息毁天灭地。",
                       art=MONSTER_ART["abyssal"], tier=2, drop="深渊之心"),
        "deathknight": dict(name="死亡骑士", hp=200, dmg=15, block=6, act=("attack", "guard", "smash", "summon"),
                            reward=250, desc="从死亡中归来的骑士领主，召唤骸骨军团。",
                            art=MONSTER_ART["deathknight"], tier=2, drop="亡者之剑"),
        "titan":  dict(name="万古巨人", hp=260, dmg=16, block=8, act=("attack", "guard", "smash", "enrage"),
                       reward=260, desc="自远古时代便存在的巨人，一拳可碎山岳。",
                       art=MONSTER_ART["titan"], tier=3, drop="泰坦之核"),
    }

# 召唤物
SUMMON_LIB = {
    "spider": dict(name="幼蛛", hp=16, dmg=4, block=0, act=("attack",), reward=5,
                   desc="", art=MONSTER_ART["spider"], drop=""),
}

# 小怪/精英池
MONSTER_POOL = {
    "normal": ["slime", "rat", "skeleton", "bat", "goblin", "wolf", "mushroom"],
    "elite":  ["ogre", "golem", "berserker", "shaman", "knight"],
}

# 各层 BOSS 池: 第一层打 tier1, 更深层打 tier2, 更更深打 tier3
def boss_pool_for_floor(floor):
    if floor <= 1:
        return ["dragon", "lich"]
    elif floor <= 3:
        return ["abyssal", "deathknight"]
    else:
        return ["titan", "abyssal", "deathknight"]

# ============================================================
# 遗物
# ============================================================

RELIC_LIB = {
    "burning":  dict(name="燃烧之刃", desc="每场战斗开始获得 2 点力量"),
    "vial":     dict(name="生命药瓶", desc="每场战斗开始回复 5 点生命"),
    "boot":     dict(name="疾风之靴", desc="每场战斗开始抽 1 张额外手牌"),
    "coin":     dict(name="贪婪金袋", desc="击败敌人获得的金币 +50%"),
    "shield":   dict(name="守护者圣盾", desc="每场战斗开始获得 4 点格挡"),
    "heart":    dict(name="巨人之心", desc="最大生命 +10"),
    "tome":     dict(name="奥术秘典", desc="每场战斗额外获得 1 点能量"),
}

# ============================================================
# 事件
# ============================================================

# 事件返回 (text, choices) choices: [(选项文本, 效果类型, 参数)]
def event_factory(rng):
    events = [
        {
            "title": "被遗忘的祭坛",
            "text": "你发现一座古老祭坛，上面摆放着一把泛着紫光的短剑。",
            "choices": [
                ("献上 30 金币换取随机卡牌", "buy_card", {"cost": 30, "free": False}),
                ("徒手拔剑（可能受伤）", "risky_card", {}),
                ("离开", "leave", {}),
            ],
        },
        {
            "title": "迷雾中的旅人",
            "text": "一名蒙面旅人拦住去路，递给你两个瓶子。",
            "choices": [
                ("饮下金色药剂（回复 20 生命）", "heal", {"value": 20}),
                ("饮下红色药剂（赌博：可能获得力量或中毒）", "gamble", {}),
                ("婉言谢绝", "leave", {}),
            ],
        },
        {
            "title": "坍塌的宝库",
            "text": "一间崩塌的宝库，珠宝散落一地，但机关正在启动。",
            "choices": [
                ("冒险搜刮（获得 50 金币，可能触发陷阱）", "treasure_trap", {"gold": 50}),
                ("快速撤离（安全但一无所获）", "leave", {}),
            ],
        },
        {
            "title": "流浪铁匠",
            "text": "铁匠愿意为你强化一张牌。",
            "choices": [
                ("选择一张牌永久强化（伤害+3 或 格挡+3）", "upgrade", {}),
                ("购买一张随机牌（30 金币）", "buy_card", {"cost": 30, "free": False}),
                ("离开", "leave", {}),
            ],
        },
        {
            "title": "垂死的骑士",
            "text": "一名重伤的骑士请求你把他的遗物带给塔顶。",
            "choices": [
                ("接受委托（获得一件随机遗物）", "relic", {}),
                ("拒绝并搜刮他的财物（获得 25 金币）", "gold", {"value": 25}),
            ],
        },
        {
            "title": "诡异的水池",
            "text": "池水泛着幽光，倒映着未来的战斗。",
            "choices": [
                ("饮一口（随机效果）", "pool_gamble", {}),
                ("离开", "leave", {}),
            ],
        },
    ]
    return rng.choice(events)

# ============================================================
# 分支地图生成
# ============================================================

# 节点类型: 小怪(monster) / 精英(elite) / 宝藏(treasure) / 事件(event)
# 比例 3:1:1:2
NODE_TYPES = ["monster", "elite", "treasure", "event"]
NODE_WEIGHTS = [3, 1, 1, 2]

NODE_LABEL = {
    "monster":  "⚔ 小怪",
    "elite":    "☠ 精英",
    "treasure": "💰 宝藏",
    "event":    "❔ 事件",
}

def node_icon(kind):
    return {"monster": "⚔", "elite": "☠", "treasure": "💰", "event": "❔"}[kind]

def pick_node_kind(rng):
    return rng.choices(NODE_TYPES, weights=NODE_WEIGHTS, k=1)[0]

# 每层地图行数 (不含入口行)
MAP_ROWS = 5

def generate_floor(rng, rows=MAP_ROWS):
    """生成一层分支地图: rows 行, 每行 2~4 个节点, 比例 3:1:1:2.
    返回 [[node,...], ...], 玩家需在每行选择一个节点前进."""
    grid = []
    for _ in range(rows):
        n = rng.randint(2, 4)
        row = [pick_node_kind(rng) for _ in range(n)]
        grid.append(row)
    return grid

# ============================================================
# 战斗引擎
# ============================================================

class Combatant:
    def __init__(self, name, hp, max_hp, strength=0, block=0, regen=0, act=("attack",), dmg=0,
                 art=None, poison=0):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.strength = strength
        self.block = block
        self.regen = regen
        self.act = act
        self.dmg = dmg
        self.art = art
        self.poison = poison

    @property
    def alive(self):
        return self.hp > 0


class Combat:
    """一次战斗。hand 为玩家手牌列表(card id)。"""
    def __init__(self, player, enemies, rng, relics, energy=3):
        self.player = player
        self.enemies = enemies            # list of Combatant
        self.rng = rng
        self.relics = relics
        self.base_energy = energy
        self.energy = energy
        self.turn = 0
        # 抽牌/弃牌堆
        self.draw_pile = list(player.deck)
        self.discard = []
        self.hand = []
        self.shuffle_draw()

    def shuffle_draw(self):
        self.rng.shuffle(self.draw_pile)

    def draw(self, n):
        drawn = 0
        while drawn < n:
            if not self.draw_pile:
                if not self.discard:
                    break
                self.draw_pile = self.discard
                self.discard = []
                self.shuffle_draw()
            self.hand.append(self.draw_pile.pop())
            drawn += 1
        return drawn

    def apply_damage(self, target, amount):
        """扣血, 先扣格挡再扣生命。返回实际造成的生命伤害。"""
        if target.block >= amount:
            target.block -= amount
            return 0
        remainder = amount - target.block
        target.block = 0
        target.hp -= remainder
        return remainder

    # ---- 卡牌执行 ----
    def play_card(self, index):
        if index < 0 or index >= len(self.hand):
            return None
        cid = self.hand[index]
        card = CARD_LIB[cid]
        cost = card["cost"]
        if cost > self.energy:
            return "not_enough"
        self.energy -= cost
        self.hand.pop(index)

        # 目标选择: 只对攻击类需要选目标
        target = None
        if card["type"] == "攻击":
            target = self.pick_target()

        kind = card["kind"]
        if kind == "dmg":
            dmg = card["value"] + self.player.strength
            self.apply_damage(target, max(0, dmg))
        elif kind == "dmg_multi":
            for _ in range(card["times"]):
                dmg = card["value"] + self.player.strength
                self.apply_damage(target, max(0, dmg))
        elif kind == "dmg_draw":
            dmg = card["value"] + self.player.strength
            self.apply_damage(target, max(0, dmg))
            self.draw(card["draw"])
        elif kind == "dmg_lifesteal":
            dmg = card["value"] + self.player.strength
            dealt = self.apply_damage(target, max(0, dmg))
            self.player.hp = min(self.player.max_hp, self.player.hp + dealt)
        elif kind == "dmg_multi_block":
            for _ in range(card["times"]):
                dmg = card["value"] + self.player.strength
                self.apply_damage(target, max(0, dmg))
            self.player.block += card["block"]
        elif kind == "dmg_pierce":
            dmg = card["value"] + self.player.strength
            target.hp -= max(0, dmg)   # 无视格挡
        elif kind == "block":
            self.player.block += card["value"]
        elif kind == "heal":
            self.player.hp = min(self.player.max_hp, self.player.hp + card["value"])
        elif kind == "regen":
            self.player.regen += card["value"]
        elif kind == "strength":
            self.player.strength += card["value"]
        elif kind == "draw":
            self.draw(card["value"])
        elif kind == "block":
            self.player.block += card["value"]

        # 打出的牌进弃牌堆 (除消耗)
        self.discard.append(cid)
        return "ok"

    def pick_target(self):
        """文字界面选择目标(如果有多个敌人)。返回 Combatant。"""
        if len(self.enemies) == 1:
            return self.enemies[0]
        lines = []
        for i, e in enumerate(self.enemies):
            lines.append(f"{num(i+1)}  {e.name}   ❤ {hp_bar(e.hp, e.max_hp, 10)}")
        box(lines, title="选择目标", width=50)
        while True:
            try:
                sel = input("  选择 > ").strip()
                idx = int(sel) - 1
                if 0 <= idx < len(self.enemies):
                    return self.enemies[idx]
            except (ValueError, EOFError):
                pass
            print("  无效输入, 请重选。")

    # ---- 敌人行动 ----
    def enemy_turn(self, enemy):
        if not enemy.alive:
            return []
        logs = []
        # 回合开始: 重置格挡
        enemy.block = 0
        act = enemy.act
        # 简单行动选择
        action = self.rng.choice(act) if isinstance(act, (list, tuple)) else act

        if action == "attack":
            dmg = enemy.dmg + enemy.strength
            dealt = self.apply_damage(self.player, max(0, dmg))
            logs.append(f"{enemy.name} 攻击, 造成 {dmg} 点伤害(格挡后 -{dealt})")
        elif action == "double":
            dmg = enemy.dmg + enemy.strength
            total = 0
            for _ in range(2):
                total += self.apply_damage(self.player, max(0, dmg))
            logs.append(f"{enemy.name} 双重攻击, 造成 {dmg*2} 点伤害(格挡后 -{total})")
        elif action == "guard":
            enemy.block += 5
            logs.append(f"{enemy.name} 防御, 获得 5 点格挡")
        elif action == "smash":
            dmg = enemy.dmg + enemy.strength
            target_hp = self.player.hp
            self.player.hp -= max(0, dmg)   # 无视格挡
            self.player.block = 0
            logs.append(f"{enemy.name} 重击! 无视格挡造成 {dmg} 点伤害!")
        elif action == "enrage":
            enemy.strength += 2
            logs.append(f"{enemy.name} 狂暴, 力量 +2!")
        elif action == "summon":
            if len(self.enemies) < 3:
                s = SUMMON_LIB["spider"]
                self.enemies.append(Combatant(s["name"], s["hp"], s["hp"],
                                              block=s["block"], act=s["act"],
                                              dmg=s["dmg"], art=s["art"]))
                logs.append(f"{enemy.name} 召唤了幼蛛!")
            else:
                dmg = enemy.dmg + enemy.strength
                self.apply_damage(self.player, max(0, dmg))
                logs.append(f"{enemy.name} 攻击, 造成 {dmg} 点伤害")
        elif action == "breath":
            dmg = 6 + enemy.strength
            self.apply_damage(self.player, max(0, dmg))
            self.player.regen = 0
            logs.append(f"{enemy.name} 龙息, 造成 {dmg} 点伤害并打断再生")
        elif action == "poison":
            self.player.poison += 3
            logs.append(f"{enemy.name} 喷吐孢子, 你中毒了! (+3 中毒)")
        return logs

    def start_player_turn(self):
        # 玩家回合开始: 重置格挡, 回能量, 抽牌
        self.player.block = 0
        if self.player.regen > 0:
            self.player.hp = min(self.player.max_hp, self.player.hp + self.player.regen)
        # 中毒结算: 每回合开始受毒伤并递减
        if self.player.poison > 0:
            self.player.hp -= self.player.poison
            self.player.poison -= 1
        self.energy = self.base_energy + (1 if "tome" in self.relics else 0)
        # 弃掉旧手牌
        self.discard += self.hand
        self.hand = []
        bonus_draw = 1 if "boot" in self.relics else 0
        self.draw(5 + bonus_draw)

    def start_enemy_turn(self):
        # 敌人回合开始前, 玩家格挡保留到被攻击
        pass

    # ---- 战斗主循环 ----
    def run(self):
        # 战斗开始遗物
        if "burning" in self.relics:
            self.player.strength += 2
        if "shield" in self.relics:
            self.player.block += 4
        if "vial" in self.relics:
            self.player.hp = min(self.player.max_hp, self.player.hp + 5)

        self.start_player_turn()
        while True:
            self.turn += 1
            # --- 玩家回合 ---
            self.render()
            result = self.player_phase()
            if result == "dead":
                return "defeat"
            # 清理死亡敌人
            self.enemies = [e for e in self.enemies if e.alive]
            if not self.enemies:
                return "victory"

            # --- 敌人回合 ---
            logs = []
            for e in list(self.enemies):
                if e.alive:
                    logs += self.enemy_turn(e)
            box(["  " + l for l in logs], title="敌人行动", width=58)
            if not self.player.alive:
                return "defeat"
            pause()
            self.start_player_turn()

    def render(self):
        banner("⚔  战 斗 中", f"第 {self.turn} 回合")
        # ---- 敌人区 ----
        for e in self.enemies:
            print(self._enemy_block(e))
            print()
        # ---- 玩家状态 HUD ----
        p = self.player
        status = []
        if p.block:
            status.append(f"⛨ 格挡 {p.block}")
        if p.strength:
            status.append(f"⚡ 力量 {p.strength}")
        if p.regen:
            status.append(f"✚ 再生 {p.regen}")
        if p.poison:
            status.append(f"☣ 中毒 {p.poison}")
        status_str = "   ".join(status)
        hud_lines = [
            f"❤ {hp_bar(p.hp, p.max_hp, 20)}",
            f"◆ 能量  {'◆'*self.energy}{'◇'*max(0, self.base_energy-self.energy)}"
            + (f"  (+1 秘典)" if "tome" in self.relics else ""),
        ]
        if status_str:
            hud_lines.insert(0, status_str)
        box(hud_lines, title="你", width=58)
        # ---- 手牌区 ----
        if self.hand:
            hand_lines = []
            row = []
            for i, cid in enumerate(self.hand):
                row.append(card_tag(cid, i + 1))
            hand_lines.append("   ".join(row))
            box(hand_lines, title="手牌", width=58)
        else:
            box(["（ 无手牌 ）"], title="手牌", width=58)
        print()
        print("  指令: 输入卡牌编号出牌 · e 结束回合 · q 逃跑")

    def _enemy_block(self, e):
        """敌人块: 左像素画, 右名字+血条。多敌时上下排列."""
        art_lines = (e.art or "").strip("\n").splitlines() if e.art else []
        status = []
        if e.block:
            status.append(f"⛨{e.block}")
        if e.strength:
            status.append(f"⚡{e.strength}")
        status_str = ("  " + "  ".join(status)) if status else ""
        info_lines = [
            f"◈ {e.name}{status_str}",
            f"❤ {hp_bar(e.hp, e.max_hp, 14)}",
        ]
        # 补齐像素画行数
        h = max(len(art_lines), len(info_lines))
        art_lines += [""] * (h - len(art_lines))
        info_lines += [""] * (h - len(info_lines))
        out = []
        for a, i in zip(art_lines, info_lines):
            out.append(f"   {a:<20}{i}")
        return "\n".join(out)

    def player_phase(self):
        while True:
            try:
                cmd = input("  >>> ").strip().lower()
            except EOFError:
                cmd = "e"
            if cmd in ("q", "quit", "escape"):
                return "quit"
            if cmd in ("e", "end", ""):
                return "ok"
            if cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(self.hand):
                    result = self.play_card(idx)
                    if result == "not_enough":
                        print("  能量不足!")
                    self.enemies = [e for e in self.enemies if e.alive]
                    if not self.enemies:
                        return "victory"
                    if not self.player.alive:
                        return "dead"
                else:
                    print("  无效编号")
            else:
                print("  无效指令")

# ============================================================
# 主游戏流程
# ============================================================

class Game:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.floor = 1
        self.gold = 60
        self.relics = []
        self.deck = list(STARTING_DECK)
        self.hp = 70
        self.max_hp = 70
        self.base_energy = 3
        self.player = Combatant("你", self.hp, self.max_hp)
        self.player.deck = self.deck  # 共享卡组列表引用
        self.coin_mult = 1.0

    def apply_relic_effects(self):
        if "heart" in self.relics:
            self.max_hp += 10
            self.hp = self.max_hp

    def add_relic(self, rid):
        if rid not in self.relics:
            self.relics.append(rid)
            if rid == "heart":
                self.max_hp += 10
                self.hp = self.max_hp
        return RELIC_LIB[rid]

    def reward_gold(self, base):
        m = 1.5 if "coin" in self.relics else 1.0
        g = int(base * m)
        self.gold += g
        return g

    # ---------------- 地图流程 ----------------
    def run(self):
        self.apply_relic_effects()
        self.show_intro()
        while True:
            self.floor_map = generate_floor(self.rng)
            outcome = self.run_floor()
            if outcome == "dead":
                self.game_over(death=True)
                return
            if outcome == "quit":
                self.game_over(death=False)
                return
            # 打败 BOSS, 进入下一层
            self.floor += 1
            banner()
            box([f"✦ 你击败了本层首领, 进入第 {self.floor} 层 ✦"], width=58)
            self.heal_node()
            pause()

    def show_intro(self):
        banner("⚔  肉 鸽 试 炼", "Roguelite Arena")
        box([
            "你是一名落难的冒险者, 被困在永无止境的塔中。",
            "只有一层一层地向上攀爬, 才有机会逃出生天。",
        ], width=58)
        print()
        box([
            "  ⚔ 小怪    普通战斗, 温和的成长",
            "  ☠ 精英    高难战斗, 丰厚奖励",
            "  💰 宝藏   丰厚的金币与卡牌",
            "  ❔ 事件    抉择与机缘",
        ], title="节点类型", width=46)
        box([
            "每一行有多条路线, 选择其一向前推进",
            "战斗中: 输入卡牌编号出牌 · e 结束回合 · q 逃跑",
        ], title="提示", width=46)
        pause()

    def heal_node(self):
        heal = 10
        self.hp = min(self.max_hp, self.hp + heal)
        print(f"  你稍作休整, 回复 {heal} 点生命。")

    # ---------- HUD (顶部状态栏) ----------
    def hud(self):
        line = (f"第{self.floor}层   "
                f"❤ {self.hp}/{self.max_hp}   "
                f"💰 {self.gold}")
        if self.relics:
            line += "   ◆ " + " ".join(RELIC_LIB[r]["name"] for r in self.relics)
        box([line], width=58)

    def run_floor(self):
        grid = self.floor_map
        row = 0
        while row < len(grid):
            banner(f"⛰  第 {self.floor} 层", f"路线 {row+1} / {len(grid)}")
            self.hud()
            self.render_map(grid, row)
            print()
            # 让玩家在当前行选择一个节点
            choice = self.choose_node(grid[row])
            if choice is None:
                return "quit"
            kind = grid[row][choice]
            if kind == "monster":
                if not self.node_combat(monster=True): return "dead"
            elif kind == "elite":
                if not self.node_combat(monster=False): return "dead"
            elif kind == "treasure":
                self.node_treasure()
            elif kind == "event":
                self.node_event()
            row += 1
            # 每行后可选择是否休息
            if row < len(grid):
                if not self.rest_offer():
                    return "quit"
        # 层末 BOSS
        return self.boss_fight()

    def render_map(self, grid, current_row):
        """绘制分支地图(树状)。已走过 ✓ / 当前 ▸ / 未来 ·."""
        lines = []
        for r, row in enumerate(grid):
            # 每个节点加编号, 便于选择
            cell = " ".join(f"{node_icon(k)}{i+1}" for i, k in enumerate(row))
            if r < current_row:
                tag = "✓ "
            elif r == current_row:
                tag = "▸ "
            else:
                tag = "· "
            lines.append(tag + cell)
        lines.append("     ⛰ 塔顶 · 首领战")
        # 面板宽度 = 最宽内容 + 边框留白
        content_w = max(len(l) for l in lines) + 2
        box(lines, title="路线地图", width=max(content_w + 2, 30))

    def choose_node(self, row):
        """让玩家在当前行选择节点, 返回索引. 取消返回 None."""
        print("  选择前进路线:")
        for i, k in enumerate(row):
            print(f"    {num(i+1)}  {NODE_LABEL[k]}")
        while True:
            c = menu_prompt("选择 > ")
            if c.lower() in ("q", "quit"):
                return None
            try:
                idx = int(c) - 1
                if 0 <= idx < len(row):
                    return idx
            except ValueError:
                pass
            print("  无效输入, 请重新选择。")

    def rest_offer(self):
        print()
        box([
            f"{num(1)}  继续前进",
            f"{num(2)}  就地休息 (回复 10 生命, 但跳过下一路线)",
        ], title="休息", width=50)
        c = menu_prompt("选择 > ")
        if c == "2":
            self.hp = min(self.max_hp, self.hp + 10)
            print(f"  你休息片刻, 回复 10 点生命。")
            pause()
        return True

    # ---------------- 战斗节点 ----------------
    def node_combat(self, monster):
        lib = monster_lib()
        if monster:
            keys = MONSTER_POOL["normal"]
        else:
            keys = MONSTER_POOL["elite"]
        key = self.rng.choice(keys)
        data = lib[key]
        # 缩放强度
        scale = 1.0 + (self.floor - 1) * 0.25
        enemies = [Combatant(data["name"], int(data["hp"] * scale),
                             int(data["hp"] * scale), strength=0, block=data["block"],
                             act=data["act"], dmg=data["dmg"], art=data["art"])]
        if monster and self.floor > 1 and self.rng.random() < 0.3:
            # 可能两只小怪
            key2 = self.rng.choice(keys)
            d2 = lib[key2]
            enemies.append(Combatant(d2["name"], int(d2["hp"] * scale * 0.7),
                                     int(d2["hp"] * scale * 0.7), block=0,
                                     act=d2["act"], dmg=d2["dmg"], art=d2["art"]))
        self.player.hp = self.hp
        self.player.max_hp = self.max_hp
        self.player.block = 0
        self.player.strength = 0
        self.player.regen = 0
        self.player.poison = 0
        combat = Combat(self.player, enemies, self.rng, self.relics)
        result = combat.run()
        self.hp = self.player.hp
        if result == "quit":
            return "quit"
        if result == "defeat":
            return False
        # 胜利奖励
        gold = data["reward"]
        g = self.reward_gold(gold)
        lines = [f"🏆 胜利! 获得 {g} 金币"]
        if data.get("drop"):
            lines.append(f"💰 掉落: {data['drop']}")
        box(lines, width=46)
        if self.rng.random() < 0.35:
            self.offer_card_reward()
        pause()
        return True

    def boss_fight(self):
        lib = monster_lib()
        pool = boss_pool_for_floor(self.floor)
        key = self.rng.choice(pool)
        data = lib[key]
        # boss 随层数增强
        scale = 1.0 + max(0, (self.floor - 1)) * 0.15
        boss = Combatant(data["name"], int(data["hp"] * scale), int(data["hp"] * scale),
                         act=data["act"], dmg=int(data["dmg"] * scale), art=data["art"])
        self.player.hp = self.hp
        self.player.max_hp = self.max_hp
        self.player.block = 0
        self.player.strength = 0
        self.player.regen = 0
        self.player.poison = 0
        banner("👑  首 领 战", f"第 {self.floor} 层 BOSS")
        art = (data["art"] or "").strip("\n")
        w = max((len(l) for l in art.splitlines()), default=20)
        box([f"◈ {data['name']}"] + ["  " + l for l in art.splitlines()] + ["  " + data["desc"]],
            title=data["name"], width=w + 10)
        pause()
        combat = Combat(self.player, [boss], self.rng, self.relics)
        result = combat.run()
        self.hp = self.player.hp
        if result == "quit":
            return "quit"
        if result == "defeat":
            return "dead"
        g = self.reward_gold(data["reward"])
        lines = [f"🏆 击败首领! 获得 {g} 金币"]
        if data.get("drop"):
            lines.append(f"💰 掉落: {data['drop']}")
        box(lines, width=46)
        self.offer_card_reward()
        pause()
        return "next"

    # ---------------- 宝藏节点 ----------------
    def node_treasure(self):
        banner("💰  宝 藏")
        self.hud()
        box(["你打开沉重的宝箱..."], width=40)
        gained = []
        # 金币
        gold = self.rng.randint(40, 70)
        g = self.reward_gold(gold)
        gained.append(f"{g} 金币")
        # 卡牌
        if self.rng.random() < 0.6:
            self.offer_card_reward()
        # 可能遗物
        if self.rng.random() < 0.4 and len(self.relics) < 6:
            rid = self.rng.choice(list(RELIC_LIB.keys()))
            rel = self.add_relic(rid)
            gained.append(f"遗物「{rel['name']}」")
        box(["获得: " + ", ".join(gained)], width=46)
        pause()

    # ---------------- 事件节点 ----------------
    def node_event(self):
        banner("❔  事 件")
        self.hud()
        ev = event_factory(self.rng)
        box(wrap(ev["text"]).splitlines(), title=ev["title"], width=56)
        print()
        box([f"{num(i+1)}  {label}" for i, (label, _, _) in enumerate(ev["choices"])],
            title="抉择", width=52)
        c = menu_prompt("选择 > ")
        idx = -1
        try:
            idx = int(c) - 1
        except ValueError:
            idx = 0
        if idx < 0 or idx >= len(ev["choices"]):
            idx = 0
        label, kind, param = ev["choices"][idx]
        print(f"\n  → {label}")
        self.resolve_event(kind, param)
        pause()

    def resolve_event(self, kind, param):
        if kind == "buy_card":
            if self.gold >= param["cost"]:
                self.gold -= param["cost"]
                self.offer_card_reward(free=False, forced=True)
            else:
                print("  金币不足, 你悻悻离开。")
        elif kind == "risky_card":
            if self.rng.random() < 0.6:
                print("  你成功拔剑! 获得一张随机卡牌。")
                self.offer_card_reward(free=True, forced=True)
            else:
                dmg = self.rng.randint(6, 10)
                self.hp = max(1, self.hp - dmg)
                print(f"  短剑弹出, 划伤了你! 损失 {dmg} 生命。")
        elif kind == "heal":
            self.hp = min(self.max_hp, self.hp + param["value"])
            print(f"  回复 {param['value']} 点生命。")
        elif kind == "gamble":
            r = self.rng.random()
            if r < 0.5:
                self.player.strength += 2
                print("  药剂灼烧着你的血脉, 获得 2 点力量(本场战斗)。")
            elif r < 0.8:
                self.hp = min(self.max_hp, self.hp + 10)
                print("  暖流涌动, 回复 10 点生命。")
            else:
                self.hp = max(1, self.hp - 8)
                print("  药剂剧烈反噬, 损失 8 点生命!")
        elif kind == "treasure_trap":
            g = self.reward_gold(param["gold"])
            print(f"  搜刮到 {g} 金币!")
            if self.rng.random() < 0.35:
                dmg = self.rng.randint(5, 12)
                self.hp = max(1, self.hp - dmg)
                print(f"  但触发了机关! 损失 {dmg} 生命。")
        elif kind == "upgrade":
            self.offer_upgrade()
        elif kind == "relic":
            rid = self.rng.choice(list(RELIC_LIB.keys()))
            rel = self.add_relic(rid)
            print(f"  你郑重接过遗物【{rel['name']}】: {rel['desc']}")
        elif kind == "gold":
            g = self.reward_gold(param["value"])
            print(f"  获得 {g} 金币。")
        elif kind == "pool_gamble":
            r = self.rng.random()
            if r < 0.5:
                self.hp = min(self.max_hp, self.hp + 8)
                print("  清冽泉水治愈了你, 回复 8 生命。")
            else:
                self.hp = max(1, self.hp - 10)
                print("  池水剧毒! 损失 10 生命。")

    # ---------------- 卡牌奖励/商店 ----------------
    def offer_card_reward(self, free=True, forced=False):
        """从卡池随机给 3 选 1。free=False 表示要花金币。"""
        options = self.rng.sample(SHOP_POOL, 3)
        action = "加入卡组" if free else "购买"
        print()
        lines = []
        for i, cid in enumerate(options):
            c = CARD_LIB[cid]
            rarity = CARD_RARITY.get(cid, "⭐")
            lines.append(f"{num(i+1)}  {rarity} {c['name']}  ({c['cost']}费)  {c['type']}")
            lines.append(f"      {c['desc']}")
            lines.append("")
        box(lines[:-1], title=f"卡牌奖励 · 选择一张{action}", width=54)
        c = menu_prompt("选择 (0 跳过) > ")
        try:
            idx = int(c) - 1
        except ValueError:
            idx = -1
        if 0 <= idx < len(options):
            self.deck.append(options[idx])
            print(f"  ✦ 获得【{CARD_LIB[options[idx]]['name']}】!")
        else:
            print("  你选择不取卡牌。")

    def offer_upgrade(self):
        print("\n  选择一张牌强化 (伤害/格挡 +3):")
        for i, cid in enumerate(self.deck):
            print(f"    {num(i+1)}  {CARD_LIB[cid]['name']}")
        c = menu_prompt("选择 (0 跳过) > ")
        try:
            idx = int(c) - 1
        except ValueError:
            return
        if 0 <= idx < len(self.deck):
            cid = self.deck[idx]
            card = CARD_LIB[cid]
            if "value" in card:
                card["value"] += 3
            print(f"  ✦【{card['name']}】已强化! (+3)")
            pause()

    # ---------------- 结算 ----------------
    def game_over(self, death):
        banner("☠  游 戏 结 束" if death else "🏳  弃 塔 而 逃")
        title = f"你倒在了第 {self.floor} 层..." if death else "你选择放弃, 永远留在了塔中。"
        lines = [
            "  " + title,
            "",
            f"  攀爬层数   {self.floor}",
            f"  剩余金币   {self.gold}",
            f"  卡组数量   {len(self.deck)}",
        ]
        if self.relics:
            lines.append("  遗物       " + ", ".join(RELIC_LIB[r]["name"] for r in self.relics))
        box(lines, width=44)
        pause()


def main():
    banner("⚔  肉 鸽 试 炼", "Roguelite Arena")
    box([
        f"{num(1)}  开始游戏",
        f"{num(2)}  卡牌图鉴",
        f"{num(3)}  怪物图鉴",
        f"{num(4)}  遗物图鉴",
    ], title="主菜单", width=30)
    c = menu_prompt("选择 > ")
    if c == "2":
        show_cards()
    elif c == "3":
        show_monsters()
    elif c == "4":
        show_relics()
    else:
        seed = menu_prompt("随机种子 (留空随机) > ")
        rng = random.Random(seed) if seed else random.Random()
        game = Game(rng)
        game.run()


def show_cards():
    banner("🃏  卡牌图鉴")
    box(["稀有度: ⭐普通  ⭐⭐稀有  ⭐⭐⭐史诗"], width=54)
    groups = {"攻击": [], "技能": [], "能力": []}
    for cid, c in CARD_LIB.items():
        groups.setdefault(c["type"], []).append((cid, c))
    for gname, cards in groups.items():
        lines = []
        for i, (cid, c) in enumerate(cards):
            lines.append(f"{num(i+1)}  {CARD_RARITY.get(cid,'⭐')} {c['name']}  ({c['cost']}费)  {c['type']}")
            lines.append(f"      {c['desc']}")
        print()
        box(lines, title=f"{gname}牌", width=52)
    print()
    pause("图鉴浏览完毕, 按回车返回")
    main()

def show_monsters():
    banner("👹  怪物图鉴")
    lib = monster_lib()
    groups = [("小怪", MONSTER_POOL["normal"]), ("精英", MONSTER_POOL["elite"])]
    for title, keys in groups:
        print()
        _print_monster_group(lib, keys, title)
    print()
    boss_keys = [k for k, m in lib.items() if "tier" in m]
    _print_monster_group(lib, boss_keys, "首领")
    print()
    pause("图鉴浏览完毕, 按回车返回")
    main()

def _print_monster_group(lib, keys, title):
    for k in keys:
        m = lib[k]
        _print_monster_codex(m)

def _print_monster_codex(m):
    art = (m.get("art") or "").strip("\n")
    w = max((len(l) for l in art.splitlines()), default=16) + 4
    stats = f"{m['name']}   生命{m['hp']}  伤害{m['dmg']}"
    if m.get("block"):
        stats += f"  格挡{m['block']}"
    lines = ["  " + l for l in art.splitlines()] + ["  " + m["desc"]]
    if m.get("drop"):
        lines.append(f"  掉落: {m['drop']}")
    box(lines, title=stats, width=w + 6)

def show_relics():
    banner("◆  遗物图鉴")
    box([f"◆ {r['name']}  —  {r['desc']}" for r in RELIC_LIB.values()], title="遗物", width=54)
    print()
    pause("图鉴浏览完毕, 按回车返回")
    main()


if __name__ == "__main__":
    main()
