# -*- coding: utf-8 -*-
"""
无尽塔防 —— Python/tkinter 实现 (v3)
参考明日方舟出怪点机制：
  - 随机指定场上 5 个 3×3 格子作为出怪点，怪物从这些点出生。
  - 怪物自由索敌移动（无固定路线）。
索敌函数优先级：嘲讽塔 > 已有锁定目标(不更改) > 从近到远选最近目标。
怪物：红/绿/蓝/黄/黑 五色跳动圆球。怪物优先索敌塔，塔有生命值可被摧毁。
塔：主基地(2×2)、太阳能塔(1×1,产能量)、机枪塔(1×1,攻击)、嘲讽塔(1×1,吸引)。
PVZ式权重出怪，无尽模式。
"""
import tkinter as tk
import math
import random

# ============ 配置 ============
GRID = 40
CELL = 24
W = GRID * CELL                    # 地图区 960
PANEL_W = 220                      # 右侧信息栏宽
CANVAS_W = W + PANEL_W

MAX_ENERGY = 400
START_ENERGY = 300
SOLAR_RATE = 2.0                   # 能量/秒
GUN_DMG = 14
GUN_COOLDOWN = 0.5                 # DPS≈28
GUN_RANGE = 5 * CELL               # 射程 120px（已加强）
GEAR_COOLDOWN_FACTOR = 0.7         # 每个齿轮使机枪冷却 ×0.7
MAX_GEARS = 2                      # 一个机枪塔上最多种 2 个齿轮
BULLET_SPEED = 500                 # 子弹飞行 px/s
BULLET_LIFE = 2.0                  # 子弹最大存活秒（防滞留）
BASE_HP = 500
TAUNT_RANGE = 5 * CELL             # 嘲讽塔吸引范围(5格)

# 新塔机制配置
BOOM_DMG_FACTOR = 1.5              # 爆破单元伤害 = 1.5 × 红球血量
PRISM_DMG = 2.1                    # 光棱塔每次伤害（3帧/0.05s 一次）
PRISM_COOLDOWN = 0.05              # 光棱塔攻击间隔（3帧一次伤）
# 光棱塔 DPS = 42 = 机枪塔(28) × 1.5；一直锁定一个目标直到目标死亡/离开射程
PRISM_FOCUS_MAX = 2                # 一个光棱塔最多可装聚焦塔数
FOCUS_TARGETS = 1                  # 每个聚焦塔增加的攻击目标数
MISSILE_DMG = 45                   # 导弹塔伤害（削弱溅射）
MISSILE_COOLDOWN = 2.2             # 导弹塔发射间隔
MISSILE_LOCK = 0.6                 # 导弹锁定/追踪时间
MISSILE_EXPLODE_R = 2.5            # 导弹爆炸半径(格)
LIQUID_DMG = 12                    # 液氮塔范围攻击单次伤害
LIQUID_COOLDOWN = 2.5              # 液氮塔范围攻击间隔（2.5秒一次，较慢）
LIQUID_SLOW = 0.5                  # 减速倍率（液氮增益塔攻击减速目标）
LIQUID_SLOW_TIME = 2.0             # 减速持续(秒)
LIQUID_FREEZE_R = 4                # 液氮塔范围攻击半径 = 自身中心 4 格
LIQUID_AURA_R = 4                  # 液氮塔增益范围（4格内塔攻击减速）
LIQUID_FREEZE_TIME = 2.0           # 范围冰冻持续(秒)
HEAL_RATE = 8                      # 治疗塔每秒治疗量
HEAL_SHIELD = 40                   # 治疗塔给塔套的护盾值
ENERGY_GAIN = 120                  # 电能包一次性获得的能量
ENERGY_PACK_COOLDOWN = 15.0        # 电能包放置冷却(秒)

# 聚焦塔（叠在光棱塔上，增加攻击目标数）
FOCUS_COST = 45                    # 聚焦塔费用
FOCUS_MAX = 2                      # 一个光棱塔最多 2 个聚焦塔

# 迷你核弹单元（触碰/摧毁触发核爆 + 留下核辐射区域）
MININUKE_DMG_FACTOR = 4.0          # 核爆伤害 = 4 × 红球血量
MININUKE_EXPLODE_R = 3.5           # 核爆半径(格)
MININUKE_RADIATION_TIME = 6.0      # 核辐射区域持续时间(秒)
MININUKE_RADIATION_DPS = 28        # 核辐射区域 DPS（= 机枪塔 DPS），3帧一次伤
RADIATION_INTERVAL = 0.05          # 核辐射区域 3帧出一次伤

# 喷火器（锥形扇形火焰，3帧一次伤；范围内有液氮塔则喷减速火）
FLAMER_DPS_FACTOR = 1.3            # 喷火器对单 DPS = 1.3 × 机枪塔 DPS
FLAMER_DMG = 36.4 * 0.05           # 喷火器每次伤害（DPS=1.3×28=36.4，3帧0.05s一次）
FLAMER_COOLDOWN = 0.05             # 喷火器攻击间隔（3帧一次伤）
FLAMER_SLOW = 0.5                  # 减速火的减速倍率（与液氮塔一致）
FLAMER_SLOW_TIME = 2.0             # 减速火持续(秒)
FLAMER_HALF_ARC = 0.55             # 喷火器扇形半角(弧度)≈31.5°，总约63°

# 发射井（玉米加农炮式：右键选目标格子后持续射导弹）
SILO_MAX = 1                       # 发射井最多放置 1 个
SILO_COST = 150                    # 发射井费用
SILO_DMG_FACTOR = 2.0              # 发射井导弹伤害 = 导弹塔 × 2（攻击变为两倍）
SILO_EXPLODE_FACTOR = 1.5          # 发射井导弹爆炸半径 = 导弹塔 × 1.5

# 防御矩阵（弱嘲讽 4 格，种越多血量越多）
MATRIX_COST = 30                   # 防御矩阵费用
MATRIX_BASE_HP = 160               # 基础血量 = 嘲讽塔(320) 一半
MATRIX_HP_PER_MATRIX = 40          # 场上每多 1 个矩阵，所有矩阵血量上限 +40
MATRIX_TAUNT_RANGE = 4 * CELL      # 弱嘲讽范围(4格)

# 强化黑球传送范围（圆形半径，单位：格）
ELITE_BLACK_RADIUS = 2.7           # 范围圆半径(格)
ELITE_BLACK_PORT_DMG = 30          # 强化黑传送落地对目标塔造成的伤害（小幅削弱）
ELITE_BLACK_PORT_CD = 2.0          # 强化黑传送技能的冷却时间(秒)

# 出怪点数量与大小
NUM_SPAWN = 5
SPAWN_SIZE = 3                     # 每个出怪点 3×3
SPAWN_MIN_GAP = 9                  # 出怪点中心之间的最小间距(格)，避免扎堆
SPAWN_CORE_GAP = 13                # 出怪点中心离基地中心的最小间距(格)，避免刷到塔前

# 塔定义（含生命值）
TOWER_DEFS = {
    "solar":     {"name": "太阳能塔", "size": 2, "cost": 40, "hp": 120, "color": "#f0d94a",
                  "desc": "持续产出能量（2/秒），是建造其他塔的经济基础，多造可提升能量积累速度。"},
    "gun":       {"name": "机枪塔",   "size": 2, "cost": 60, "hp": 220, "color": "#4aa8f0",
                  "desc": "自动攻击射程内最靠左（最接近基地）的敌人，单体高频率输出（每次14伤害，0.5秒一发）。可加装齿轮提升攻速。无敌人时攻击射程内的裂隙出怪点。"},
    "taunt":     {"name": "嘲讽塔",   "size": 1, "cost": 80, "hp": 320, "color": "#f85149",
                  "desc": "吸引 5 格范围内所有怪物强制攻击它（无视其他锁定），用于把怪物火力集中到自己身上，保护主力输出塔。"},
    "gear":      {"name": "齿轮塔",   "size": 0, "cost": 45, "hp": 0,   "color": "#e3b341", "gear": True,
                  "desc": "只能叠放在机枪/导弹/液氮/发射井塔上（点其占用格），每个塔最多2个。每装1个使被加装塔冷却 ×0.7（攻速约提升43%）。"},
    "boom_unit": {"name": "爆破单元", "size": 1, "cost": 30, "hp": 60,  "color": "#ff9b3d",
                  "desc": "一次性地雷塔：被敌人触碰即引爆，对周围约2.2格范围造成 1.5× 当前红球血量的范围伤害，随后消失。"},
    "prism":     {"name": "光棱塔",   "size": 2, "cost": 90, "hp": 160, "color": "#d2a8ff", "range": 6 * CELL,
                  "desc": "射程6格，一直锁定目标持续激光攻击（3帧一次伤，DPS为机枪塔1.5倍），目标死亡或离开射程才切换。可叠放聚焦塔增加同时攻击的目标数。"},
    "missile":   {"name": "导弹塔",   "size": 2, "cost": 120, "hp": 160, "color": "#ff6b6b", "range": 12 * CELL, "gearable": True,
                  "desc": "超远射程（12格）追踪导弹：命中或超时爆炸，对半径2.5格内所有敌人造成60范围伤害。可加装齿轮提升发射频率。"},
    "liquid":    {"name": "液氮塔",   "size": 2, "cost": 70, "hp": 130, "color": "#8be9fd", "range": 4 * CELL, "gearable": True,
                  "desc": "范围攻击塔：每2.5秒对自身中心4格半径内所有敌人造成伤害并冰冻；同时给4格范围内友方塔提供减速增益，使其攻击均减速目标。"},
    "healer":    {"name": "治疗塔",   "size": 2, "cost": 60, "hp": 110, "color": "#50fa7b", "range": 4 * CELL,
                  "desc": "每秒治疗4格范围内其他塔 8 点生命，并为其维持 40 点护盾，延长防线寿命。"},
    "focus":     {"name": "聚焦塔",   "size": 0, "cost": FOCUS_COST, "hp": 0, "color": "#d2a8ff", "focus": True,
                  "desc": "只能叠放在光棱塔上（点其占用格），每个光棱塔最多2个。每装1个使光棱塔额外增加1个攻击目标（可同时锁定多敌）。"},
    "mininuke":  {"name": "迷你核弹单元", "size": 1, "cost": 35, "hp": 50, "color": "#f5a623",
                  "desc": "地雷式核弹：被怪物触碰或被摧毁时引爆，对半径3.5格造成 4× 当前红球血量核爆伤害，并留下持续6秒的核辐射区域（3帧一次伤，DPS与机枪塔持平）。"},
    "flamer":    {"name": "喷火器",   "size": 2, "cost": 90, "hp": 180, "color": "#ff7b00", "range": GUN_RANGE,
                  "desc": "朝射程内敌人喷射锥形火焰（扇形范围AOE，3帧一次伤，对单DPS为机枪塔1.3倍），火焰特效真实模拟现实喷火器。受液氮塔减速增益时喷出蓝色减速火。"},
    "silode":    {"name": "发射井",   "size": 3, "cost": SILO_COST, "hp": 220, "color": "#6b6b6b", "range": 14 * CELL, "gearable": True,
                  "desc": "占地3×3，全局仅能建造1座。先右键发射井进入锁定模式，再点击地图任意位置锁定目标点，之后持续向该点发射导弹（伤害为导弹塔2倍、爆炸半径1.5倍，可加装齿轮）。"},
    "matrix":    {"name": "防御矩阵", "size": 1, "cost": MATRIX_COST, "hp": MATRIX_BASE_HP, "color": "#7ee787",
                  "desc": "占地1×1的弱嘲讽塔：吸引4格范围内怪物强制攻击它，血量等于嘲讽塔一半，费用低。场上种得越多，所有防御矩阵血量上限越高（每多1个+40）。"},
    "energy":    {"name": "电能包",   "size": 1, "cost": 0,  "hp": 20,  "color": "#f1fa8c", "onetime": "energy",
                  "desc": "一次性道具：放置瞬间获得 120 能量并立即消失，用于紧急补充经济。"},
}
CORE_DEF = {"name": "主基地", "size": 2, "hp": BASE_HP, "color": "#c9a227"}

# 怪物定义（speed: 格/秒；hp_mult: 血量倍率；atk: 攻击力/秒）
# 强化球(elite=True)：红眼特效、带拖尾
MON_DEFS = {
    "red":    {"name": "红·标准", "color": "#f85149", "r": 9,  "speed": 1.1, "hp_mult": 1.0, "atk": 8,  "weight": 1, "revive": None,
               "desc": "基础单位：移速、血量、攻击均为基准值，数量多但威胁低。"},
    "green":  {"name": "绿·坦克", "color": "#3fb950", "r": 14, "speed": 0.7, "hp_mult": 2.0, "atk": 12, "weight": 3, "revive": None,
               "desc": "坦克型：体型大、血量2倍、移速慢（0.7格/秒），攻击力较高，适合用高输出塔集火。"},
    "blue":   {"name": "蓝·敏捷", "color": "#58a6ff", "r": 6,  "speed": 2.1, "hp_mult": 1.0, "atk": 10, "weight": 2, "revive": None,
               "desc": "敏捷型：移速极快（2.1格/秒）、体型小（难被命中），血量低，靠减速/冰冻克制。"},
    "yellow": {"name": "黄·复生", "color": "#f0d94a", "r": 9,  "speed": 1.1, "hp_mult": 1.0, "atk": 8,  "weight": 2, "revive": "red",
               "desc": "复生型：死亡后原地复活为一只红·标准，须优先处理或二次击杀。"},
    "black":  {"name": "黑·闪现", "color": "#1a1a1a", "r": 9,  "speed": 1.1, "hp_mult": 1.0, "atk": 14, "weight": 3, "revive": None,
               "desc": "闪现型：周期性瞬间移动到 10×10 格内最近塔旁直接攻击（每3秒一次），攻击力高，会绕过正面防线。"},
    "white":  {"name": "白·裂隙", "color": "#e6edf3", "r": 9,  "speed": 1.1, "hp_mult": 1.0, "atk": 8,  "weight": 1, "revive": None, "spawner": True,
               "desc": "裂隙型（第5波起每波50%概率出）：死亡后在其位置生成一个永久裂隙出怪点（可被机枪摧毁），裂隙会持续向外出怪。"},
    "bblack": {"name": "强·黑",  "color": "#1a1a1a", "r": 12, "speed": 1.1, "hp_mult": 2.0, "atk": 14, "weight": 1, "revive": None, "elite": True,
               "desc": "强化·黑（第5波起出现）：血量2倍。被攻击时会把周围2.7格内所有敌人一起传送向攻击目标，落地造成30伤害，成群时极具威胁。"},
    "byellow":{"name": "强·黄",  "color": "#f0d94a", "r": 12, "speed": 1.1, "hp_mult": 2.0, "atk": 8,  "weight": 1, "revive": "random", "elite": True,
               "desc": "强化·黄（第5波起出现）：血量2倍。死亡后复活为一只随机强化球（强黑/强黄/强绿/强蓝/强红，不会变强化白），会不断制造麻烦。"},
    "bgreen": {"name": "强·绿",  "color": "#3fb950", "r": 20, "speed": 0.7, "hp_mult": 24.0, "atk": 12, "weight": 1, "revive": None, "elite": True, "boom": True, "taunt": True,
               "desc": "强化·绿（第5波起出现）：血量翻倍、体型巨大，且自带嘲讽吸引范围内塔优先攻击它。死亡时爆炸，对周围2.5格内塔造成伤害，并分裂出两只普通绿。"},
    "bblue":  {"name": "强·蓝",  "color": "#58a6ff", "r": 8,  "speed": 3.15, "hp_mult": 1.0, "atk": 10, "weight": 1, "revive": None, "elite": True, "aura": True,
               "desc": "强化·蓝（第5波起出现）：移速极快，自带加速光环，将6格内友军移速提升至与自身一致，配合成群敌人会迅速突破防线。"},
    "bwhite": {"name": "强·白",  "color": "#e6edf3", "r": 11, "speed": 1.1, "hp_mult": 1.0, "atk": 8,  "weight": 0, "revive": None, "elite": True, "spawner": True, "summon": True,
               "desc": "强化·白（第5波起，每波的白/强白随机出）：红眼拖尾。活着时每2秒在自身范围内召唤一只普通怪；死亡后仍生成裂隙出怪点，比普通白更棘手。"},
    "bred":   {"name": "强·红",  "color": "#f85149", "r": 10, "speed": 2.1, "hp_mult": 2.0, "atk": 8,  "weight": 1, "revive": None, "elite": True, "ram": True,
               "desc": "强化·红（第5波起出现，金球也会把红球转化为它）：速度与强化蓝一致，冲撞到塔会造成大量伤害，是高速攻坚单位。"},
    "gold":   {"name": "金·核心", "color": "#f5c542", "r": 13, "speed": 0.3, "hp_mult": 12.0, "atk": 0,  "weight": 0, "revive": None, "gold": True,
               "desc": "金·核心（第5波起每两波出一个）：血量与强化绿相同、移动极慢。每3秒把自身范围内（除白与强化白和自己）的普通球转化为同色强化球，是精英制造者，务必优先击破。"},
    # ---- 三棱锥类敌人（第 6 波起出现） ----
    # 锥类：一边自转一边向前移动；cone=True 标记为锥类（金球转化、白球召唤均不作用于锥类）
    "rcone":  {"name": "红锥",   "color": "#ff6b6b", "r": 10, "speed": 1.0, "hp_mult": 1.0, "atk": 10, "weight": 2, "revive": None, "cone": True, "shoot": True,
               "desc": "锥类·远程（第6波起）：一边自转一边向前移动，发射光束远程攻击塔。"},
    "kcone":  {"name": "黑锥",   "color": "#2b2b2b", "r": 10, "speed": 1.0, "hp_mult": 1.0, "atk": 14, "weight": 2, "revive": None, "cone": True, "blink": True, "silence": True,
               "desc": "锥类·闪现（第6波起）：同黑球周期性闪现到塔旁，攻击时沉默目标塔使其无法攻击（嘲讽塔失去嘲讽）。"},
    "wcone":  {"name": "白锥",   "color": "#e6edf3", "r": 10, "speed": 0.0, "hp_mult": 1.0, "atk": 0,  "weight": 0, "revive": None, "cone": True, "summoner": True,
               "desc": "锥类·召唤（第6波起）：不移动，持续自扣血，并召唤球类与锥类敌人。"},
    "bconer": {"name": "强红锥", "color": "#ff6b6b", "r": 11, "speed": 1.4, "hp_mult": 2.0, "atk": 14, "weight": 1, "revive": None, "cone": True, "elite": True, "shoot": True, "shoot3": True,
               "desc": "强化·红锥：三次攻击每次一束，发射射程极远、伤害较高的光束攻击塔。"},
    "bconek": {"name": "强黑锥", "color": "#2b2b2b", "r": 12, "speed": 1.0, "hp_mult": 2.0, "atk": 14, "weight": 1, "revive": None, "cone": True, "elite": True, "blink": True, "silence": True, "area_silence": True, "cshield": 10,
               "desc": "强化·黑锥：3格范围沉默，带10层次数盾（需10次攻击击破）。"},
    "bconew": {"name": "强白锥", "color": "#e6edf3", "r": 11, "speed": 0.0, "hp_mult": 1.0, "atk": 0,  "weight": 0, "revive": None, "cone": True, "elite": True, "summoner": True, "summon_elite": True,
               "desc": "强化·白锥：不移动，自扣血，召唤强化球类与强化锥类敌人。"},
}
MON_KEYS = list(MON_DEFS.keys())
ELITE_MIN_WAVE = 5            # 强化球第 5 波起才出现

# 白球 / 强化白 / 强化绿 / 强化蓝 / 金球 机制配置
WHITE_MIN_WAVE = 5            # 第 5 波起每波必出 1 只白球或强化白
WHITE_ELITE_CHANCE = 0.5      # 每波出的那 1 只是强化白的概率
WSPAWN_HP = 180               # 白球死亡生成的出怪点血量（可被摧毁）
WSPAWN_INTERVAL = 2.0         # 白球出怪点独立出怪间隔(秒)
BWHITE_SUMMON_INTERVAL = 2.0  # 强化白召唤间隔(秒)，与裂隙出怪点一致
BWHITE_SUMMON_R = 2.2         # 强化白召唤范围(格)
BGREEN_EXPLODE_R = 2.5        # 强化绿死后爆炸半径(格)，对范围内塔造成伤害
BGREEN_TAUNT_R = 5            # 强化绿嘲讽半径(格)：范围内塔优先攻击它
BBLUE_AURA_R = 6              # 强化蓝加速光环半径(格)
BBLUE_BOOST = 2.0             # 光环内友军加速倍率（加强至两倍）
GOLD_MIN_WAVE = 5             # 第 5 波起，每两波必出一个金球
GOLD_TRANSFORM_INTERVAL = 3.0 # 金球转化间隔(秒)
GOLD_TRANSFORM_R = 3          # 金球转化范围(格)
BRED_RAM_DMG = 80             # 强化红撞塔一次性伤害
BRED_RAM_COOLDOWN = 1.5       # 强化红撞塔冷却(秒)
SPAWN_INTERVAL = 0.8          # 出怪间隔(秒/只)，已加强（原1.1）

# ===== 三棱锥类敌人机制配置 =====
CONE_MIN_WAVE = 6             # 第 6 波起锥类敌人出现（普通出怪池 + 新增锥类刷怪点）
CONE_SPAWN_MIN_DIST = 20      # 锥类刷怪点中心距主基地中心的最小距离(格)，避免刷在塔前
RCONE_RANGE = 6 * CELL        # 红锥光束射程(6格)
RCONE_COOLDOWN = 1.6          # 红锥光束攻击间隔(秒)
RCONE_BEAM_DMG = 14           # 红锥光束单次伤害
BRCONE_RANGE = 13 * CELL      # 强化红锥光束射程(极远,13格)
BRCONE_COOLDOWN = 1.2         # 强化红锥光束攻击间隔(秒)
BRCONE_BEAM_DMG = 34          # 强化红锥光束单次伤害(较高)
CONE_BEAM_SPEED = 420         # 锥光束飞行 px/s
CONE_SILENCE_TIME = 3.0       # 黑锥/强黑锥沉默持续时间(秒)
BCONEK_SILENCE_R = 3          # 强黑锥范围沉默半径(格)
BCONEK_SHIELD_CHARGES = 10    # 强黑锥次数盾层数（需10次攻击击破）
WCONE_DRAIN = 40              # 白锥每秒自扣血量
WCONE_SUMMON_INTERVAL = 2.0   # 白锥召唤间隔(秒)
WCONE_SUMMON_R = 2.2          # 白锥召唤范围(格)
WCONE_MIN_WAVE = 6            # 白锥/强白锥第 6 波起每波必出 1 只
WCONE_ELITE_CHANCE = 0.5      # 每波那 1 只是强化白锥的概率
HUNDRED_CONE_COUNT = 4        # 百球行中混入的锥类数量
CONE_EXTRA_BUDGET = 8         # 第 6 波起，因新增锥类刷怪点而提升的刷怪上限

# 百球行机制：第 10 波起，每 3 波在右边界涌出一大批单位
HUNDRED_MIN_WAVE = 10         # 第 10 波起触发
HUNDRED_PERIOD = 3            # 每 3 波触发一次（10,13,16...）
HUNDRED_BASE = 35             # 单位数基础 = (35 + 当前波次单位规模)/3
HUNDRED_DIV = 3               # 单位数量除以 3（减少为原来的 1/3）
HUNDRED_WARN_TIME = 3.0       # 触发前在屏幕中间的警告时长(秒)

# ============ 关卡模式 ============
# 每个关卡：初始能量、普通出怪点数量、10波单位数、出怪池、特殊规则
LEVELS = {
    "charge": {
        "name": "冲锋号令",
        "desc": "初始 200 能量。出怪仅有红/蓝/黑（带强化形态）及强化白、金。\n"
                "第 5、10 波触发百球行。独立刷怪点只出黑，第 5 波后只出强化黑。",
        "start_energy": 200,
        "spawn_points": 3,                 # 按无尽规则生成的普通出怪点数量
        "wave_units": [10, 20, 20, 30, 60, 40, 40, 70, 70, 100],  # 10 波单位数
        "mon_pool": ["red", "blue", "black"],       # 普通出怪池（红/蓝/黑）
        "elite_chance": 0.25,              # 红/蓝/黑 各为强化形态的概率
        "elite_white_gold_from": 6,        # 第 6 波起每波必出 1 强化白 + 1 金
        "hundred_waves": [5, 10],          # 触发百球行的波次
        "independent_spawn": {             # 主建筑周围的独立刷怪点
            "min_dist": 7, "max_dist": 12, # 离主基地 7~12 格
            "pre": "black",                # 第 5 波前（含）出黑
            "post": "bblack",              # 第 5 波后（第 6 波起）只出强化黑
            "interval": 3.0,               # 出怪间隔
        },
    },
}
LEVEL_ORDER = ["charge"]

CORE_C, CORE_R = 2, 19              # 主基地左上角(2×2)
BASE_EDGE_X = (CORE_C + CORE_DEF["size"]) * CELL   # 基地右缘 x = 96

def wave_budget(n): return 10 + 3 * n        # 刷怪量提高，每波增量提升
def wave_hp(n):     return 20 + 5 * n
def wave_speed(n):  return 1 + 0.02 * n

def random_mon_key(wave=1):
    """按权重随机出怪；白/强白/金球/白锥/强白锥走专门机制不在此池；
    第 5 波前不出强化球；第 6 波前不出锥类敌人"""
    keys = [k for k in MON_KEYS
            if k not in ("white", "bwhite", "gold", "wcone", "bconew")]
    if wave < CONE_MIN_WAVE:
        keys = [k for k in keys if not MON_DEFS[k].get("cone")]
    if wave < ELITE_MIN_WAVE:
        keys = [k for k in keys if not MON_DEFS[k].get("elite")]
    total = sum(MON_DEFS[k]["weight"] for k in keys)
    r = random.random() * total
    for k in keys:
        r -= MON_DEFS[k]["weight"]
        if r <= 0:
            return k
    return keys[0]

# 普通球 → 同色强化球 的映射（金球转化用）
ELITE_OF = {"red": "bred", "green": "bgreen", "blue": "bblue",
            "yellow": "byellow", "black": "bblack"}

def normal_summon_keys():
    """强化白召唤/裂隙出怪的普通怪池：排除白、强化白、金球、所有强化球与所有锥类"""
    return [k for k in MON_KEYS
            if k not in ("white", "bwhite", "gold")
            and not MON_DEFS[k].get("elite")
            and not MON_DEFS[k].get("cone")]

def _promote_monster(m):
    """金球把普通球提升为同色强化球（保留位置/朝向，重置为强化血量）。
    对锥类敌人无效（金球强化不作用于锥类）。"""
    if MON_DEFS[m["type"]].get("cone"):
        return False
    ntype = ELITE_OF.get(m["type"])
    if not ntype:
        return False
    m["type"] = ntype
    d = MON_DEFS[ntype]
    m["hp"] = wave_hp(S.wave) * d["hp_mult"]
    m["maxhp"] = m["hp"]
    m["r"] = d["r"]
    m["speed"] = d["speed"] * wave_speed(S.wave)
    m["atk"] = d["atk"]
    # 精英球补拖尾字段
    if "trail" not in m:
        m["trail"] = []
        m["trail_t"] = 0.0
    return True

# ============ 地图（无路线，可建区 + 基地 + 出怪点） ============
# 0可建 2基地 4出怪点区域(3×3,不可建)
grid = [[0] * GRID for _ in range(GRID)]
SPAWN_POINTS = []      # 每个出怪点的左上角格子 (r, c)

def gen_spawn_points(n=5):
    """生成 n 个彼此拉开间距、避开基地且远离基地的 3×3 出怪点。
    采用锚点网格 + 随机选格保证分散，并约束出怪点中心离基地中心 ≥SPAWN_CORE_GAP，
    避免刷到基地前/玩家塔区。返回左上角列表"""
    core_cr, core_cc = CORE_R + CORE_DEF["size"] // 2, CORE_C + CORE_DEF["size"] // 2
    # 锚点：以 12 格为间隔铺满地图，出怪点从这些锚点中随机抽取，天然相距≥12
    anchors = [(r, c) for r in range(4, GRID - 1, 12)
               for c in range(4, GRID - 1, 12)]
    random.shuffle(anchors)
    pts = []
    for (ar, ac) in anchors:
        if len(pts) >= n:
            break
        # 锚点周围 ±1 随机抖动，让布局更自然（仍保持≥10格间距）
        r = min(max(ar + random.randint(-1, 1), 0), GRID - SPAWN_SIZE)
        c = min(max(ac + random.randint(-1, 1), 0), GRID - SPAWN_SIZE)
        # 与基地重叠？
        overlap_core = (r < CORE_R + CORE_DEF["size"] + 1 and
                        r + SPAWN_SIZE > CORE_R - 1 and
                        c < CORE_C + CORE_DEF["size"] + 1 and
                        c + SPAWN_SIZE > CORE_C - 1)
        if overlap_core:
            continue
        # 出怪点中心格
        cr, cc = r + SPAWN_SIZE // 2, c + SPAWN_SIZE // 2
        # 离基地中心太近则跳过（避免刷到塔前）
        if (cr - core_cr) ** 2 + (cc - core_cc) ** 2 < SPAWN_CORE_GAP ** 2:
            continue
        pts.append((r, c))
    return pts

def init_map(n=None):
    global SPAWN_POINTS
    if n is None:
        n = NUM_SPAWN
    SPAWN_POINTS = gen_spawn_points(n)
    for r in range(CORE_R, CORE_R + CORE_DEF["size"]):
        for c in range(CORE_C, CORE_C + CORE_DEF["size"]):
            grid[r][c] = 2
    for (r, c) in SPAWN_POINTS:
        for dr in range(SPAWN_SIZE):
            for dc in range(SPAWN_SIZE):
                if grid[r + dr][c + dc] == 0:
                    grid[r + dr][c + dc] = 4
init_map()

def spawn_center(i):
    """第 i 个出怪点的中心像素坐标"""
    r, c = SPAWN_POINTS[i]
    return (c + SPAWN_SIZE / 2) * CELL, (r + SPAWN_SIZE / 2) * CELL

# ============ 状态 ============
class State:
    pass
S = State()
S.energy = START_ENERGY
S.wave = 1
S.paused = False
S.over = False
S.kills = 0
S.towers = []          # kind, c, r, size, x, y, hp, maxhp, cool
S.monsters = []        # type, x, y, hp, maxhp, r, speed, atk, bob, target, flash_cd
S.bullets = []         # x, y, target, life
S.missiles = []        # 导弹塔的追踪导弹（范围爆炸）
S.conebeams = []       # 红锥/强化红锥发射的光束（远程攻击塔）
S.radiations = []      # 迷你核弹留下的核辐射区域（持续伤害）
S.effects = []         # 视觉特效（范围圆/传送光效）
S.wspawns = []         # 白球生成的 1×1 出怪点（可被机枪摧毁、独立定时出怪）
S.white_pending = False  # 本波是否出 1 只白球/强化白
S.gold_pending = False   # 本波是否必出 1 只金球
S.wcone_pending = False  # 本波是否出 1 只白锥/强化白锥
S.conespawn = None       # 第 6 波起的锥类专用刷怪点
S.silo_locking = None    # 发射井锁定模式（当前等待选择目标点的发射井）
S.hundred_timer = 0.0    # 百球行来袭警告倒计时(秒)，>0 表示即将触发
S.energy_cd = 0.0        # 电能包放置冷却剩余时间(秒)
S.mode = "endless"       # 游戏模式：endless 无尽 / level 关卡
S.level = None           # 关卡配置（关卡模式下）
S.ispawn = None          # 关卡独立刷怪点（主基地周围，只出黑/强化黑）
S.spawn = {"total": 0, "acc": 0, "timer": 0, "interval": SPAWN_INTERVAL}
S.sel = None
S.time = 0

def core_tower():
    return next((t for t in S.towers if t["kind"] == "core"), None)

def remaining_field_weight():
    """场上剩余活怪的权重（无尽模式按权重计；关卡模式按单位数计，与 budget 单位一致）"""
    if S.mode == "level":
        return sum(1 for m in S.monsters if m["alive"])
    return sum(MON_DEFS[m["type"]]["weight"]
               for m in S.monsters if m["alive"])

def dist2(a, b):
    dx = a["x"] - b["x"]; dy = a["y"] - b["y"]
    return dx * dx + dy * dy

def in_sector(ox, oy, aim_angle, half_arc, rng, px, py):
    """判断点 (px,py) 是否在以 (ox,oy) 为顶点、aim_angle 方向、半角 half_arc、半径 rng 的扇形内"""
    dx = px - ox; dy = py - oy
    dist = math.hypot(dx, dy)
    if dist > rng or dist == 0:
        return False
    ang = math.atan2(dy, dx)
    diff = abs((ang - aim_angle + math.pi) % (2 * math.pi) - math.pi)
    return diff <= half_arc

# ============ 实体 ============
def spawn_monster(mtype, x=None, y=None, hp=None):
    d = MON_DEFS[mtype]
    if x is None:
        i = random.randrange(len(SPAWN_POINTS))
        x, y = spawn_center(i)
    hp = hp if hp is not None else wave_hp(S.wave) * d["hp_mult"]
    m = {
        "type": mtype, "x": x, "y": y,
        "hp": hp, "maxhp": hp, "r": d["r"], "speed": d["speed"] * wave_speed(S.wave),
        "atk": d["atk"], "bob": random.uniform(0, 6.28),
        "alive": True, "target": None, "flash_cd": random.uniform(1.0, 2.5),
        "boosted": False, "slow": 0.0, "frozen": 0.0,
    }
    if d.get("elite"):
        m["trail"] = []            # 拖尾残影，限长防卡顿
        m["trail_t"] = 0.0
    if d.get("cshield"):
        m["cshields"] = d["cshield"]   # 次数盾（强黑锥：25 层，每击消耗 1 层）
    return m

def can_build(c, r, size):
    for dr in range(size):
        for dc in range(size):
            rr, cc = r + dr, c + dc
            if rr < 0 or rr >= GRID or cc < 0 or cc >= GRID or grid[rr][cc] != 0:
                return False
    return True

def place_tower(kind, c, r):
    d = TOWER_DEFS[kind]
    if d.get("gear"):
        return place_gear_at(c, r)      # 齿轮塔走专用逻辑（叠在可加装塔上）
    if d.get("focus"):
        return place_focus_at(c, r)     # 聚焦塔走专用逻辑（叠在光棱塔上）
    # 发射井：全局仅能放置 1 个
    if kind == "silode" and any(t["kind"] == "silode" and not t.get("removed") for t in S.towers):
        log("发射井全局只能建造 1 座！", "warn"); return False
    # 电能包：有 15 秒放置冷却，冷却中不可放置
    if d.get("onetime") == "energy" and S.energy_cd > 0:
        log(f"⚡ 电能包冷却中（{S.energy_cd:.0f}秒）！", "warn")
        return False
    if S.energy < d["cost"]:
        log("能量不足！", "warn"); return False
    if not can_build(c, r, d["size"]):
        log("此处不可建造！", "warn"); return False
    S.energy -= d["cost"]
    for dr in range(d["size"]):
        for dc in range(d["size"]):
            grid[r + dr][c + dc] = 3
    t = {"kind": kind, "c": c, "r": r, "size": d["size"],
         "x": (c + d["size"] / 2) * CELL, "y": (r + d["size"] / 2) * CELL,
         "hp": d["hp"], "maxhp": d["hp"], "cool": 0, "shield": 0}
    if "range" in d:
        t["range"] = d["range"]
    if kind in ("gun", "missile", "liquid", "silode"):
        t["gears"] = 0
    if kind == "gun":
        t["range"] = GUN_RANGE
    if kind == "prism":
        t["locks"] = []       # 光棱塔锁定目标列表（聚焦塔可增加目标数）
        t["focuses"] = 0      # 光棱塔上装的聚焦塔数量
    if kind == "flamer":
        t["aim"] = 0.0        # 喷火器当前喷射方向角(弧度)
    if kind == "silode":
        t["lock_target"] = None   # 发射井锁定的目标点 (x, y)
    S.towers.append(t)
    log(f"建造 {d['name']}", "info")
    # 一次性塔：电能包放置即生效并消失（有 15 秒放置冷却）
    if d.get("onetime") == "energy":
        S.energy = min(MAX_ENERGY, S.energy + ENERGY_GAIN)
        S.energy_cd = ENERGY_PACK_COOLDOWN
        add_effect("boom", t["x"], t["y"], r=CELL * 1.5, color="#f1fa8c", life=0.6)
        remove_tower(t)
        log(f"⚡ 电能包 +{ENERGY_GAIN} 能量！(冷却 {ENERGY_PACK_COOLDOWN:.0f} 秒)", "info")
    return True

def place_gear_at(c, r):
    """齿轮塔：只能叠放在可加装塔（机枪/导弹/液氮）上，最多 MAX_GEARS 个。点击塔所占格子生效"""
    cost = TOWER_DEFS["gear"]["cost"]
    if S.energy < cost:
        log("能量不足！", "warn"); return False
    # 找到覆盖 (c, r) 的可加装塔
    base = None
    for t in S.towers:
        if t.get("removed"):
            continue
        d = TOWER_DEFS.get(t["kind"], {})
        if not (d.get("gearable") or t["kind"] == "gun"):
            continue
        if t["c"] <= c < t["c"] + t["size"] and t["r"] <= r < t["r"] + t["size"]:
            base = t
            break
    if base is None:
        log("齿轮塔只能种在机枪/导弹/液氮塔上！", "warn"); return False
    base.setdefault("gears", 0)
    if base["gears"] >= MAX_GEARS:
        log("该塔已装满齿轮（最多2个）！", "warn"); return False
    S.energy -= cost
    base["gears"] += 1
    log(f"⚙️ 加装齿轮 ({base['gears']}/{MAX_GEARS})，攻速提升!", "info")
    return True

def place_focus_at(c, r):
    """聚焦塔：只能叠放在光棱塔上，最多 FOCUS_MAX 个，每个增加 1 个攻击目标。点击塔所占格子生效"""
    cost = TOWER_DEFS["focus"]["cost"]
    if S.energy < cost:
        log("能量不足！", "warn"); return False
    # 找到覆盖 (c, r) 的光棱塔
    base = None
    for t in S.towers:
        if t.get("removed") or t["kind"] != "prism":
            continue
        if t["c"] <= c < t["c"] + t["size"] and t["r"] <= r < t["r"] + t["size"]:
            base = t
            break
    if base is None:
        log("聚焦塔只能种在光棱塔上！", "warn"); return False
    base.setdefault("focuses", 0)
    if base["focuses"] >= FOCUS_MAX:
        log("该光棱塔已装满聚焦塔（最多2个）！", "warn"); return False
    S.energy -= cost
    base["focuses"] += 1
    log(f"🎯 加装聚焦塔 ({base['focuses']}/{FOCUS_MAX})，攻击目标数提升!", "info")
    return True

def add_effect(etype, x, y, r=0, color="#bb88ff", life=0.6, **extra):
    """记录一个特效（范围圆/传送光效），由 draw_dynamic 绘制并随时间淡出。
    extra 可携带附加数据（如喷火器火焰的方向/扇形角）"""
    ef = {"type": etype, "x": x, "y": y, "r": r,
          "color": color, "life": life, "maxlife": life, "t": 0.0}
    if extra:
        ef["extra"] = extra
    S.effects.append(ef)

def _missile_explode(mi):
    """导弹命中/超时：对爆炸半径内所有怪物造成范围伤害，并波及裂隙出怪点。
    发射井导弹伤害×2、爆炸半径×1.5。"""
    if mi.get("is_silo"):
        dmg = MISSILE_DMG * SILO_DMG_FACTOR
        R = MISSILE_EXPLODE_R * CELL * SILO_EXPLODE_FACTOR
    else:
        dmg = MISSILE_DMG
        R = MISSILE_EXPLODE_R * CELL
    for m in S.monsters:
        if m["alive"] and dist2(m, mi) <= R * R:
            damage_monster(m, dmg)
            # 液氮塔增益：导弹爆炸命中的目标减速
            if mi.get("from") and mi["from"].get("frost"):
                m["slow"] = max(m["slow"], LIQUID_SLOW_TIME)
    # 波及爆炸半径内的白球裂隙出怪点（假刷怪点），可被导弹摧毁
    for w in S.wspawns:
        if w["alive"] and dist2(w, mi) <= R * R:
            w["hp"] -= dmg
            if w["hp"] <= 0:
                remove_wspawn(w)
    add_effect("boom", mi["x"], mi["y"], r=R,
               color="#ffb84d" if mi.get("is_silo") else "#ff6b6b", life=0.6)

def _elite_black_port(m):
    """强化黑被攻击：以自身为中心、半径 ELITE_BLACK_RADIUS 格的圆形范围内所有活球，
    一并传送到攻击目标（无目标则找最近塔）。伴随明显的范围圆与传送光效。"""
    R = ELITE_BLACK_RADIUS * CELL
    # 传送落点：优先用强化黑当前攻击目标（仍存活），否则找 10×10 格内最近塔
    best = m.get("target")
    if best is None or best.get("removed") or best["kind"] == "core":
        best = None
        gc, gr = int(m["x"] // CELL), int(m["y"] // CELL)
        bestd = float("inf")
        for t in S.towers:
            if t.get("removed") or t["kind"] == "core":
                continue
            tc, tr = t["c"] + t["size"] // 2, t["r"] + t["size"] // 2
            if abs(tc - gc) <= 5 and abs(tr - gr) <= 5:
                dd = (tc - gc) ** 2 + (tr - gr) ** 2
                if dd < bestd:
                    bestd = dd
                    best = t
    # 范围圆特效：显示被击半径
    add_effect("range", m["x"], m["y"], r=R, color="#bb66ff", life=0.7)
    if best is None:
        add_effect("boom", m["x"], m["y"], r=m["r"] * 2, color="#ff5555", life=0.4)
        log("⚫ 强化黑被击（无传送目标）!", "warn")
        return
    # 收集以自身为中心半径 R 圆形内的所有活球（含自身）
    group = [mm for mm in S.monsters
             if mm["alive"] and dist2(mm, m) <= R * R]
    if not group:
        group = [m]
    # 全部传送到塔边，并记录起点/落点光效
    for i, mm in enumerate(group):
        ang = math.atan2(mm["y"] - best["y"], mm["x"] - best["x"])
        dist = best["size"] * CELL / 2 + mm["r"] + 2
        add_effect("spark", mm["x"], mm["y"], r=mm["r"] * 2, color="#cc66ff", life=0.5)
        mm["x"] = best["x"] + math.cos(ang) * dist
        mm["y"] = best["y"] + math.sin(ang) * dist
        mm["target"] = best
    # 传送造成伤害
    best["hp"] -= ELITE_BLACK_PORT_DMG
    if best["hp"] <= 0:
        remove_tower(best)
    add_effect("boom", best["x"], best["y"], r=best["size"] * CELL / 2 + 14,
               color="#ffcc44", life=0.6)
    log(f"⚫ 强化黑被击，{len(group)} 球传送并造成 {ELITE_BLACK_PORT_DMG} 伤害!", "warn")

def spawn_wspawn(x, y):
    """白球死亡：在原地生成一个占地 1×1、可被机枪摧毁的独立出怪点"""
    c, r = int(x // CELL), int(y // CELL)
    if not (0 <= c < GRID and 0 <= r < GRID):
        return
    if grid[r][c] != 0:
        # 该格被占用（塔/其他出怪点），尝试就近找空格
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < GRID and 0 <= cc < GRID and grid[rr][cc] == 0:
                    r, c = rr, cc
                    break
            else:
                continue
            break
        else:
            log("白球出怪点无处生成！", "warn"); return
    grid[r][c] = 5          # 白球出怪点(1×1)，不可建、可被摧毁
    S.wspawns.append({"c": c, "r": r, "x": (c + 0.5) * CELL, "y": (r + 0.5) * CELL,
                      "hp": WSPAWN_HP, "maxhp": WSPAWN_HP, "alive": True,
                      "is_wspawn": True,
                      "timer": WSPAWN_INTERVAL, "interval": WSPAWN_INTERVAL})
    add_effect("boom", (c + 0.5) * CELL, (r + 0.5) * CELL, r=CELL * 1.2,
               color="#ffffff", life=0.7)
    if _game is not None:
        _game.redraw_static()
    log("🤍 白球死亡，生成 1×1 裂隙出怪点!", "warn")

def remove_wspawn(w):
    """白球出怪点被摧毁：清除其占用的格子与记录"""
    if not w.get("alive"):
        return
    w["alive"] = False
    if 0 <= w["r"] < GRID and 0 <= w["c"] < GRID and grid[w["r"]][w["c"]] == 5:
        grid[w["r"]][w["c"]] = 0
    if _game is not None:
        _game.redraw_static()
    add_effect("boom", w["x"], w["y"], r=CELL * 1.2, color="#ff7b72", life=0.5)
    log("🔧 白球裂隙出怪点被摧毁!", "info")

def _bgreen_explode(m):
    """强化绿死亡：爆炸对周围塔造成伤害，并生成两个普通绿"""
    R = BGREEN_EXPLODE_R * CELL
    # 对范围内所有塔(含基地)造成伤害
    for t in S.towers:
        if t.get("removed"):
            continue
        if dist2(m, t) <= R * R:
            t["hp"] -= 60
            if t["hp"] <= 0:
                remove_tower(t)
    # 生成两个普通绿
    for _ in range(2):
        nx = m["x"] + random.uniform(-16, 16)
        ny = m["y"] + random.uniform(-16, 16)
        g = spawn_monster("green", x=nx, y=ny)
        S.monsters.append(g)
    add_effect("boom", m["x"], m["y"], r=CELL * BGREEN_EXPLODE_R, color="#3fb950",
               life=0.6)
    add_effect("range", m["x"], m["y"], r=R, color="#7ee787", life=0.5)
    log("💥 强化绿爆炸! 生成两个普通绿", "warn")

def damage_monster(m, dmg):
    # 强黑锥次数盾：每次被攻击消耗 1 层，盾在时免疫本次伤害（需 25 次攻击击破）
    if m.get("cshields", 0) > 0:
        m["cshields"] -= 1
        add_effect("spark", m["x"], m["y"], r=m["r"] * 2, color="#9b59b6", life=0.25)
        if m["cshields"] <= 0:
            add_effect("boom", m["x"], m["y"], r=m["r"] * 2.2, color="#9b59b6",
                       life=0.5)
            log("🔺 强黑锥次数盾被击破!", "warn")
        return False   # 次数盾吸收本次伤害（不扣血、不算击杀）
    m["hp"] -= dmg
    # 强化黑传送技能：有 2 秒冷却，冷却中不触发
    if m["type"] == "bblack" and m["alive"] and m.get("port_cd", 0) <= 0:
        m["port_cd"] = ELITE_BLACK_PORT_CD
        _elite_black_port(m)
    if m["hp"] <= 0 and m["alive"]:
        m["alive"] = False
        S.kills += 1
        mtype = m["type"]
        d = MON_DEFS[mtype]
        # 白球死亡 → 生成裂隙出怪点
        if d.get("spawner"):
            spawn_wspawn(m["x"], m["y"])
        # 强化绿死亡 → 爆炸 + 两个普通绿
        if d.get("boom"):
            _bgreen_explode(m)
        # 复活逻辑
        rev = d["revive"]
        if rev == "random":
            # 强化黄死亡：复活为随机强化球（强黑/强黄/强绿/强蓝/强红），不会变强化白
            pool = [k for k in MON_KEYS
                    if MON_DEFS[k].get("elite") and k != "bwhite"]
            rev = random.choice(pool)
        if rev:
            rv = spawn_monster(rev, x=m["x"], y=m["y"], hp=m["maxhp"])
            rv["bob"] = m["bob"]
            S.monsters.append(rv)
        return True
    return False

def _boom_explode(t):
    """爆破单元爆炸（被触碰引爆或被摧毁引爆统一入口）：
    对周围 2.2 格内所有怪物造成 1.5× 当前红球血量的范围伤害"""
    red_hp = wave_hp(S.wave) * MON_DEFS["red"]["hp_mult"]
    boom_dmg = BOOM_DMG_FACTOR * red_hp
    R = CELL * 2.2
    for m in S.monsters:
        if m["alive"] and dist2(m, t) <= R * R:
            damage_monster(m, boom_dmg)
    add_effect("boom", t["x"], t["y"], r=R, color="#ff9b3d", life=0.6)
    log("💥 爆破单元引爆!", "warn")

def _mininuke_explode(t):
    """迷你核弹单元爆炸（触碰/摧毁统一入口）：
    对半径 3.5 格内所有怪物造成 4× 当前红球血量核爆伤害，并留下持续核辐射区域。"""
    red_hp = wave_hp(S.wave) * MON_DEFS["red"]["hp_mult"]
    nuke_dmg = MININUKE_DMG_FACTOR * red_hp
    R = MININUKE_EXPLODE_R * CELL
    for m in S.monsters:
        if m["alive"] and dist2(m, t) <= R * R:
            damage_monster(m, nuke_dmg)
    add_effect("boom", t["x"], t["y"], r=R, color="#f5a623", life=0.9)
    add_effect("range", t["x"], t["y"], r=R, color="#ffd77a", life=0.6)
    # 留下核辐射区域：持续一段时间，3帧一次伤，DPS = 机枪塔
    S.radiations.append({"x": t["x"], "y": t["y"],
                         "r": MININUKE_EXPLODE_R * CELL,
                         "life": MININUKE_RADIATION_TIME,
                         "maxlife": MININUKE_RADIATION_TIME,
                         "timer": 0.0, "interval": RADIATION_INTERVAL,
                         "dps": MININUKE_RADIATION_DPS,
                         "dmg": MININUKE_RADIATION_DPS * RADIATION_INTERVAL})
    log("☢️ 迷你核弹核爆！留下核辐射区域", "warn")

def update_radiations(dt):
    """核辐射区域：对范围内敌人 3帧一次伤（DPS = 机枪塔），随时间消散"""
    for rad in S.radiations:
        if rad["life"] <= 0:
            continue
        rad["life"] -= dt
        rad["timer"] -= dt
        if rad["timer"] <= 0:
            rad["timer"] = rad["interval"]
            for m in S.monsters:
                if m["alive"] and dist2(m, rad) <= rad["r"] ** 2:
                    damage_monster(m, rad["dmg"])
        # 核辐射视觉特效（脉冲绿/黄圆）
        if rad["life"] > 0:
            add_effect("aura", rad["x"], rad["y"], r=rad["r"] * (0.85 + 0.15 * (rad["life"] / rad["maxlife"])),
                       color="#d4ff57", life=0.12)
    S.radiations = [rad for rad in S.radiations if rad["life"] > 0]

def remove_tower(t):
    if not t.get("removed"):
        t["removed"] = True
        if t["kind"] == "core":
            # 基地血量归零 → 游戏失败
            game_over()
            return
        # 爆破单元/迷你核弹被摧毁（怪物攻击打爆）时同样引爆
        if t["kind"] == "boom_unit":
            _boom_explode(t)
        if t["kind"] == "mininuke":
            _mininuke_explode(t)
        for dr in range(t["size"]):
            for dc in range(t["size"]):
                rr, cc = t["r"] + dr, t["c"] + dc
                if 0 <= rr < GRID and 0 <= cc < GRID:
                    grid[rr][cc] = 0
        if t["kind"] != "core":
            S.towers = [x for x in S.towers if x is not t]
            if _game is not None:
                _game.redraw_static()
            log(f"{TOWER_DEFS.get(t['kind'], {}).get('name', '塔')} 被摧毁！", "warn")

# ============ 波次 ============
def level_wave_units(n):
    """关卡模式：第 n 波单位数（从关卡表读取，超出返回末值）"""
    if S.mode != "level" or not S.level:
        return wave_budget(n)
    table = S.level.get("wave_units", [])
    if n <= 0:
        return 0
    return table[n - 1] if n <= len(table) else table[-1]

def level_mon_key(wave):
    """关卡模式：从关卡出怪池随机出怪；红/蓝/黑各有概率为强化形态"""
    pool = S.level["mon_pool"]
    k = random.choice(pool)
    # 强化形态：红→强红, 蓝→强蓝, 黑→强黑
    if random.random() < S.level.get("elite_chance", 0.25):
        k = ELITE_OF.get(k, k)
    return k

def setup_independent_spawn():
    """关卡模式：在主建筑周围 7~12 格内随机生成一个独立刷怪点（只出黑/强化黑）"""
    if S.mode != "level" or not S.level or S.ispawn:
        return
    isp = S.level["independent_spawn"]
    min_d, max_d = isp["min_dist"], isp["max_dist"]
    core_cr, core_cc = CORE_R + CORE_DEF["size"] // 2, CORE_C + CORE_DEF["size"] // 2
    # 随机找一个距基地中心在 [min_d, max_d] 格的可建空格作为出怪点
    for _ in range(300):
        dr = random.randint(-max_d, max_d)
        dc = random.randint(-max_d, max_d)
        if abs(dr) + abs(dc) < min_d:
            continue
        r, c = core_cr + dr, core_cc + dc
        if not (0 <= r < GRID and 0 <= c < GRID):
            continue
        if grid[r][c] != 0:
            continue
        grid[r][c] = 4          # 复用出怪点标记（不可建）
        S.ispawn = {"r": r, "c": c, "x": (c + 0.5) * CELL, "y": (r + 0.5) * CELL,
                    "timer": 0.0, "interval": isp["interval"]}
        add_effect("boom", S.ispawn["x"], S.ispawn["y"], r=CELL * 2, color="#1a1a1a",
                   life=0.8)
        log("⚫ 独立强化黑刷怪点已生成！", "warn")
        return
    log("独立刷怪点无处生成！", "warn")

def update_independent_spawn(dt):
    """关卡模式：独立刷怪点定时出黑/强化黑（第 5 波后只出强化黑）"""
    if S.mode != "level" or not S.ispawn:
        return
    isp = S.ispawn
    isp["timer"] -= dt
    if isp["timer"] > 0:
        return
    isp["timer"] = isp["interval"]
    isp_cfg = S.level["independent_spawn"]
    k = isp_cfg["post"] if S.wave > 5 else isp_cfg["pre"]
    S.monsters.append(spawn_monster(k, x=isp["x"], y=isp["y"]))
    add_effect("spark", isp["x"], isp["y"], r=CELL * 0.7, color="#1a1a1a", life=0.4)

def setup_cone_spawn():
    """第 6 波起：在地图上随机生成一个锥类专用刷怪点（刷新机制与球类一致，
    锥类与球类共享刷怪上限）。位置需远离主基地（距基地中心至少 20 格）。"""
    if S.conespawn or S.wave < CONE_MIN_WAVE:
        return
    core_cr, core_cc = CORE_R + CORE_DEF["size"] // 2, CORE_C + CORE_DEF["size"] // 2
    for _ in range(600):
        r = random.randint(2, GRID - 3)
        c = random.randint(2, GRID - 3)
        # 避开基地、已有出怪点与基地周边（距基地中心至少 20 格）
        if grid[r][c] != 0:
            continue
        if (r - core_cr) ** 2 + (c - core_cc) ** 2 < CONE_SPAWN_MIN_DIST ** 2:
            continue
        x, y = (c + 0.5) * CELL, (r + 0.5) * CELL
        S.conespawn = {"r": r, "c": c, "x": x, "y": y}
        grid[r][c] = 4          # 复用出怪点标记（不可建）
        add_effect("boom", x, y, r=CELL * 2, color="#ff6b6b", life=0.8)
        log("🔺 锥类刷怪点已生成！（第6波起，远离基地）", "warn")
        if _game is not None:
            _game.redraw_static()
        return
    log("锥类刷怪点无处生成！", "warn")

def spawn_hundred_wave():
    """百球行：从地图右边界涌出一大批单位。
    数量 = (35 + 当前波次单位规模) / 3；恰好含 1 金球 + 1 强化白球。
    无尽模式单位规模用 wave_budget，关卡模式用关卡波次单位数。"""
    units = level_wave_units(S.wave)
    count = max(3, (HUNDRED_BASE + units) // HUNDRED_DIV)
    edge_x = GRID * CELL - 4          # 贴右边界
    # 恰好 1 金球 + 1 强化白球
    S.monsters.append(spawn_monster("gold", x=edge_x, y=random.uniform(0, GRID * CELL)))
    S.monsters.append(spawn_monster("bwhite", x=edge_x, y=random.uniform(0, GRID * CELL)))
    # 其余单位从出怪池随机（关卡模式用关卡出怪池，无尽用普通池；不占本波出怪权重）
    # 第 6 波起百球行中混入少量锥类（红/黑锥及强化锥）
    cone_left = HUNDRED_CONE_COUNT if S.wave >= CONE_MIN_WAVE else 0
    cone_pool = [k for k in ("rcone", "kcone", "bconer", "bconek")
                 if S.wave >= (ELITE_MIN_WAVE if MON_DEFS[k].get("elite") else CONE_MIN_WAVE)]
    for _ in range(max(0, count - 2)):
        if cone_left > 0 and cone_pool:
            cone_left -= 1
            k = random.choice(cone_pool)
        else:
            k = level_mon_key(S.wave) if S.mode == "level" else random_mon_key(S.wave)
        S.monsters.append(spawn_monster(k, x=edge_x, y=random.uniform(0, GRID * CELL)))
    add_effect("boom", edge_x, GRID * CELL / 2, r=CELL * 6, color="#ff6b6b", life=0.8)
    log(f"🌊 百球行！右边界涌出 {count} 只单位（含金球与强化白）!", "warn")

def start_wave(n):
    S.wave = n
    S.spawn["total"] = level_wave_units(n)
    S.spawn["acc"] = 0
    S.spawn["timer"] = 0
    if S.mode == "level":
        # 关卡模式：第 6-10 波每波必出 1 强化白 + 1 金；百球行在关卡指定波次触发
        S.white_pending = (n >= S.level.get("elite_white_gold_from", 99))
        S.gold_pending = (n >= S.level.get("elite_white_gold_from", 99))
        if S.gold_pending:
            S.gold_pending = False
            S.monsters.append(spawn_monster("gold"))
            log("🟡 金·核心 来袭！", "warn")
        if n in S.level.get("hundred_waves", []):
            S.hundred_timer = HUNDRED_WARN_TIME
            log("⚠️ 百球行即将来袭！", "warn")
    else:
        # 无尽模式：白/强化白每波必出，金球每两波必出，百球行第 10 波起每 3 波
        S.white_pending = (n >= WHITE_MIN_WAVE)
        S.gold_pending = (n >= GOLD_MIN_WAVE and (n - GOLD_MIN_WAVE) % 2 == 0)
        # 第 6 波起：白锥/强化白锥每波必出 1 只；生成锥类刷怪点；刷怪上限上升
        S.wcone_pending = (n >= WCONE_MIN_WAVE)
        setup_cone_spawn()
        if n >= CONE_MIN_WAVE:
            S.spawn["total"] += CONE_EXTRA_BUDGET   # 锥类占用共享上限，上限随之上升
        if S.gold_pending:
            S.gold_pending = False
            S.monsters.append(spawn_monster("gold"))
            log("🟡 金·核心 来袭！", "warn")
        if n >= HUNDRED_MIN_WAVE and (n - HUNDRED_MIN_WAVE) % HUNDRED_PERIOD == 0:
            S.hundred_timer = HUNDRED_WARN_TIME
            log("⚠️ 百球行即将来袭！", "warn")
    log(f"⚔ 第 {n} 波来袭！(总权重 {S.spawn['total']})", "info")

# ============ 索敌函数（优先级：嘲讽 > 锁定 > 从近到远） ============
def monster_attack_range(m):
    return m["r"] + CELL * 1.0

def acquire_target(m):
    """返回怪物应攻击的目标（塔或基地），None 表示无目标"""
    # 1. 嘲讽塔优先（5格强制吸引）、防御矩阵弱嘲讽（4格）；被沉默的嘲讽塔/矩阵失去嘲讽
    best = None
    bestd = float("inf")
    for t in S.towers:
        if t.get("removed") or t.get("silence_t", 0) > 0:
            continue
        if t["kind"] == "taunt":
            rr = TAUNT_RANGE
        elif t["kind"] == "matrix":
            rr = MATRIX_TAUNT_RANGE
        else:
            continue
        if dist2(m, t) <= rr ** 2 and dist2(m, t) < bestd:
            bestd = dist2(m, t)
            best = t
    if best:
        return best
    # 2. 已有锁定目标且仍存活 → 不更改
    cur = m.get("target")
    if cur is not None and not cur.get("removed"):
        return cur
    # 3. 重新索敌：从近到远选最近的目标（塔+基地）
    best = None
    bestd = float("inf")
    for t in S.towers:
        if t.get("removed"):
            continue
        d = dist2(m, t)
        if d < bestd:
            bestd = d
            best = t
    return best

def tower_acquire(t, rng):
    """塔选择攻击目标：射程内若有带嘲讽的强化绿则优先锁定它，
    否则攻击最靠左（最接近基地）的敌人。返回目标怪物或 None"""
    # 1. 嘲讽怪优先（强化绿）
    best = None
    bestd = float("inf")
    for m in S.monsters:
        if not m["alive"] or not MON_DEFS[m["type"]].get("taunt"):
            continue
        if dist2(t, m) <= rng * rng and dist2(t, m) < bestd:
            bestd = dist2(t, m); best = m
    if best:
        return best
    # 2. 射程内最左
    best = None
    bestx = float("inf")
    for m in S.monsters:
        if not m["alive"] or dist2(t, m) > rng * rng:
            continue
        if m["x"] < bestx:
            bestx = m["x"]; best = m
    return best

# ============ 怪物逻辑 ============
def _cone_shoot(m, target):
    """红锥/强化红锥发射光束攻击目标塔。
    强化红锥在一个攻击周期内连射 3 束（每次一发，依次飞出），射程极远、伤害较高。"""
    elite = MON_DEFS[m["type"]].get("elite")
    shots = 3 if elite else 1
    dmg = BRCONE_BEAM_DMG if elite else RCONE_BEAM_DMG
    for i in range(shots):
        S.conebeams.append({"x": m["x"], "y": m["y"], "target": target,
                            "dmg": dmg, "delay": i * 0.12, "life": BULLET_LIFE,
                            "elite": elite})
    add_effect("spark", m["x"], m["y"], r=m["r"] * 2, color="#ff6b6b", life=0.3)

def _apply_cone_silence(m, target):
    """黑锥攻击时沉默目标塔；强化黑锥对 3 格范围内所有塔沉默。
    被沉默的塔无法攻击（嘲讽塔同时失去嘲讽）。"""
    if MON_DEFS[m["type"]].get("area_silence"):
        R = BCONEK_SILENCE_R * CELL
        n = 0
        for t in S.towers:
            if t.get("removed") or t["kind"] == "core":
                continue
            if dist2(m, t) <= R * R:
                t["silence_t"] = CONE_SILENCE_TIME
                add_effect("spark", t["x"], t["y"], r=t["size"] * CELL / 2,
                           color="#9b59b6", life=0.5)
                n += 1
        add_effect("range", m["x"], m["y"], r=R, color="#9b59b6", life=0.6)
        if n:
            log(f"🔺 强黑锥范围沉默 {n} 座塔（3格内）!", "warn")
    else:
        if target["kind"] != "core":
            target["silence_t"] = CONE_SILENCE_TIME
            add_effect("spark", target["x"], target["y"],
                       r=target["size"] * CELL / 2, color="#9b59b6", life=0.5)
            log("🔺 黑锥沉默目标塔!", "warn")

def monster_update(m, dt):
    if not m["alive"]:
        return
    m["bob"] += dt * 6
    d = MON_DEFS[m["type"]]
    # 减速/冰冻/强化黑传送冷却 计时递减
    if m["slow"] > 0:
        m["slow"] -= dt
    if m["frozen"] > 0:
        m["frozen"] -= dt
    if m.get("port_cd", 0) > 0:
        m["port_cd"] -= dt

    # 拖尾记录（仅强化球；限长防卡顿）
    if "trail" in m:
        m["trail_t"] += dt
        if m["trail_t"] >= 0.05:
            m["trail_t"] = 0.0
            m["trail"].append((m["x"], m["y"], m["bob"]))
            if len(m["trail"]) > 4:
                del m["trail"][0]

    # 锥类自转（一边自转一边向前移动，自转角度由绘制层体现）
    if d.get("cone"):
        m["spin"] = m.get("spin", 0.0) + dt * 7.0

    # 白锥/强化白锥：不移动、不攻击，仅持续自扣血（召唤逻辑在 update 中处理）
    if d.get("summoner"):
        m["drain_t"] = m.get("drain_t", 0.0) + dt
        if m["drain_t"] >= 1.0:
            m["drain_t"] -= 1.0
            m["hp"] -= WCONE_DRAIN
            if m["hp"] <= 0:
                damage_monster(m, 0)   # 触发死亡逻辑（自扣血致死）
        return

    # 黑色球/黑锥（含强化）：闪现到 10×10 格内最近塔（覆盖当前目标）
    if m["type"] in ("black", "bblack", "kcone", "bconek"):
        m["flash_cd"] -= dt
        if m["flash_cd"] <= 0:
            gc, gr = int(m["x"] // CELL), int(m["y"] // CELL)
            best = None
            bestd = float("inf")
            for t in S.towers:
                if t.get("removed") or t["kind"] == "core":
                    continue
                tc, tr = t["c"] + t["size"] // 2, t["r"] + t["size"] // 2
                if abs(tc - gc) <= 5 and abs(tr - gr) <= 5:
                    dd = (tc - gc) ** 2 + (tr - gr) ** 2
                    if dd < bestd:
                        bestd = dd
                        best = t
            if best:
                ang = math.atan2(m["y"] - best["y"], m["x"] - best["x"])
                dist = best["size"] * CELL / 2 + m["r"] + 2
                m["x"] = best["x"] + math.cos(ang) * dist
                m["y"] = best["y"] + math.sin(ang) * dist
                m["target"] = best
                m["flash_cd"] = 3.0
                log("🔺 黑锥闪现攻击!" if d.get("cone") else "⚫ 黑球闪现攻击!", "warn")
            else:
                m["flash_cd"] = 0.5   # 范围内无塔，稍后再查

    # 红锥/强化红锥：远程光束攻击（在射程内停止移动发射光束，未入射程则靠近）
    if d.get("shoot"):
        target = acquire_target(m)
        m["target"] = target
        if target is None:
            return
        rng = BRCONE_RANGE if d.get("elite") else RCONE_RANGE
        dx, dy = target["x"] - m["x"], target["y"] - m["y"]
        dist = math.hypot(dx, dy)
        if dist <= rng:
            m.setdefault("shoot_cd", 0.0)
            m["shoot_cd"] -= dt
            if m["shoot_cd"] <= 0:
                m["shoot_cd"] = BRCONE_COOLDOWN if d.get("elite") else RCONE_COOLDOWN
                _cone_shoot(m, target)
            return
        # 未进入射程 → 朝目标移动（含强化蓝光环加速）
        if m.get("boosted"):
            eff_speed = m.get("boost_speed", m["speed"])
        else:
            eff_speed = m["speed"]
        step = eff_speed * CELL * dt
        if dist <= step:
            m["x"], m["y"] = target["x"], target["y"]
        else:
            m["x"] += dx / dist * step
            m["y"] += dy / dist * step
        return

    # 索敌
    target = acquire_target(m)
    m["target"] = target
    if target is None:
        return

    dx, dy = target["x"] - m["x"], target["y"] - m["y"]
    dist = math.hypot(dx, dy)
    reach = monster_attack_range(m) + target["size"] * CELL / 2

    if dist <= reach:
        # 黑锥/强化黑锥：接触攻击时对目标塔施加沉默
        if d.get("silence"):
            _apply_cone_silence(m, target)
        # 强化红（撞塔型）：每次冲撞造成一次性大量伤害，带冷却
        if MON_DEFS[m["type"]].get("ram"):
            m.setdefault("ram_cd", 0.0)
            m["ram_cd"] -= dt
            if m["ram_cd"] <= 0:
                m["ram_cd"] = BRED_RAM_COOLDOWN
                dmg = BRED_RAM_DMG
                # 冲撞爆发伤害
                sh = target.get("shield", 0)
                if sh > 0:
                    use = min(sh, dmg)
                    target["shield"] = sh - use
                    dmg -= use
                if target["kind"] == "core":
                    target["hp"] -= dmg
                    if target["hp"] <= 0:
                        game_over()
                        m["target"] = None
                else:
                    target["hp"] -= dmg
                    if target["hp"] <= 0:
                        remove_tower(target)
                        m["target"] = None
                add_effect("boom", m["x"], m["y"], r=m["r"] * 2, color="#ff5555",
                           life=0.3)
            return
        # 攻击目标（先扣护盾，盾破再扣血）
        sh = target.get("shield", 0)
        dmg = m["atk"] * dt
        if sh > 0:
            use = min(sh, dmg)
            target["shield"] = sh - use
            dmg -= use
        if target["kind"] == "core":
            # 基地血量保持 int：累积浮点伤害，满 1 点再扣
            target["hp_frac"] = target.get("hp_frac", 0.0) + dmg
            whole = int(target["hp_frac"])
            target["hp_frac"] -= whole
            target["hp"] -= whole
            if target["hp"] <= 0:
                game_over()
                m["target"] = None
        else:
            target["hp"] -= dmg
            if target["hp"] <= 0:
                remove_tower(target)
                m["target"] = None
    else:
        # 朝目标直线移动（强化蓝光环内友军速度提升至一致；减速/冰冻则放慢）
        if m.get("boosted"):
            eff_speed = m.get("boost_speed", m["speed"])
        else:
            eff_speed = m["speed"]
        if m["frozen"] > 0:
            eff_speed *= 0.0
        elif m["slow"] > 0:
            eff_speed *= LIQUID_SLOW
        step = eff_speed * CELL * dt
        if dist <= step:
            m["x"], m["y"] = target["x"], target["y"]
        else:
            m["x"] += dx / dist * step
            m["y"] += dy / dist * step

# ============ 更新 ============
def update(dt):
    if S.over or S.paused:
        return
    S.time += dt
    budget = S.spawn["total"]

    # 0. 电能包冷却递减
    if S.energy_cd > 0:
        S.energy_cd = max(0.0, S.energy_cd - dt)

    # 0.5 百球行：警告倒计时结束 → 从右边界生成
    if S.hundred_timer > 0:
        S.hundred_timer -= dt
        if S.hundred_timer <= 0:
            S.hundred_timer = 0.0
            spawn_hundred_wave()

    # 1. 出怪
    if budget > 0 and S.spawn["acc"] < budget:
        S.spawn["timer"] += dt
        while S.spawn["timer"] >= S.spawn["interval"] and S.spawn["acc"] < budget:
            S.spawn["timer"] -= S.spawn["interval"]
            # 白/强化白：触发时首次出怪替换为白球或强化白
            if S.white_pending:
                S.white_pending = False
                # 关卡模式只出强化白；无尽模式白/强白各半
                if S.mode == "level":
                    k = "bwhite"
                else:
                    k = "bwhite" if random.random() < WHITE_ELITE_CHANCE else "white"
            # 白锥/强化白锥：每波必出 1 只（第 6 波起，无尽模式）
            elif S.wcone_pending:
                S.wcone_pending = False
                k = "bconew" if random.random() < WCONE_ELITE_CHANCE else "wcone"
            else:
                # 关卡模式用关卡出怪池（红/蓝/黑带强化形态），无尽用普通池
                k = level_mon_key(S.wave) if S.mode == "level" else random_mon_key(S.wave)
            # 无尽模式按权重累加；关卡模式 budget 是单位数，每出 1 只 +1
            if S.mode == "level":
                S.spawn["acc"] += 1
            else:
                S.spawn["acc"] += MON_DEFS[k]["weight"]
            # 锥类（红/黑锥及强化）从锥类专用刷怪点出生；白锥/强白锥与球类从普通出怪点出生
            if MON_DEFS[k].get("cone") and not MON_DEFS[k].get("summoner") and S.conespawn:
                nm = spawn_monster(k, x=S.conespawn["x"], y=S.conespawn["y"])
            else:
                nm = spawn_monster(k)
            S.monsters.append(nm)

    # 2. 下一波
    # 无尽模式：出满权重后等场上怪清到一半再开下一波
    # 关卡模式：独立刷怪点持续出怪会阻塞清场，故出满本波单位即推进
    if S.spawn["acc"] >= budget:
        if S.mode == "level":
            total_waves = len(S.level.get("wave_units", []))
            if S.wave >= total_waves:
                level_cleared()
            else:
                start_wave(S.wave + 1)
        elif remaining_field_weight() <= budget * 0.5:
            start_wave(S.wave + 1)

    # 2.5 关卡独立刷怪点：定时出黑/强化黑
    update_independent_spawn(dt)

    # 3. 太阳能产能量
    n_solar = sum(1 for t in S.towers if t["kind"] == "solar" and not t.get("removed"))
    S.energy = min(MAX_ENERGY, S.energy + n_solar * SOLAR_RATE * dt)

    # 3.5 沉默计时递减（黑锥/强黑锥施加，被沉默的塔无法攻击、嘲讽塔失去嘲讽）
    for t in S.towers:
        if t.get("silence_t", 0) > 0:
            t["silence_t"] = max(0.0, t["silence_t"] - dt)

    # 4. 机枪攻击（优先嘲讽的强化绿，否则射程内最左；无怪时攻击白球裂隙出怪点）
    for t in S.towers:
        if t["kind"] != "gun" or t.get("removed"):
            continue
        if t.get("silence_t", 0) > 0:
            continue   # 被沉默无法攻击
        t["cool"] -= dt
        target = tower_acquire(t, t["range"])
        if target is None:
            # 射程内无怪物 → 攻击最近的白球出怪点（可摧毁）
            best = float("inf")
            for w in S.wspawns:
                if not w["alive"]:
                    continue
                if dist2(t, w) <= t["range"] ** 2 and w["x"] < best:
                    best = w["x"]; target = w
        if target and t["cool"] <= 0:
            # 齿轮数量越多，冷却越短（攻速越快）
            cool = GUN_COOLDOWN * (GEAR_COOLDOWN_FACTOR ** t.get("gears", 0))
            t["cool"] = cool
            S.bullets.append({"x": t["x"], "y": t["y"], "target": target,
                              "life": BULLET_LIFE, "from": t})

    # 4.4 防御矩阵血量叠加：场上矩阵越多，所有矩阵血量上限越高
    n_matrix = sum(1 for t in S.towers if t["kind"] == "matrix" and not t.get("removed"))
    if n_matrix:
        matrix_maxhp = MATRIX_BASE_HP + (n_matrix - 1) * MATRIX_HP_PER_MATRIX
        for t in S.towers:
            if t["kind"] == "matrix" and not t.get("removed"):
                if t["maxhp"] != matrix_maxhp:
                    delta = matrix_maxhp - t["maxhp"]
                    t["maxhp"] = matrix_maxhp
                    t["hp"] = min(matrix_maxhp, t["hp"] + delta)

    # 4.45 液氮塔减速增益：4 格范围内友方攻击塔，其攻击均减速目标
    for t in S.towers:
        t["frost"] = False
    for lt in S.towers:
        if lt.get("removed") or lt["kind"] != "liquid":
            continue
        R = LIQUID_AURA_R * CELL
        for t in S.towers:
            if t.get("removed") or t["kind"] == "core":
                continue
            if t["kind"] in ("gun", "prism", "missile", "flamer", "silode", "liquid") \
                    and dist2(t, lt) <= R * R:
                t["frost"] = True

    # 4.5 新塔逻辑
    for t in S.towers:
        if t.get("removed"):
            continue
        k = t["kind"]
        # 被沉默的攻击塔（光棱/导弹/液氮/喷火器/发射井）无法攻击
        if t.get("silence_t", 0) > 0 and k in ("prism", "missile", "liquid", "flamer", "silode"):
            continue
        # 爆破单元：被怪物触碰即爆炸（一次性），造成 1.5×红血量范围伤害
        if k == "boom_unit":
            touched = False
            for m in S.monsters:
                if m["alive"] and dist2(m, t) <= (m["r"] + CELL * 0.5) ** 2:
                    touched = True
                    break
            if touched:
                # 触碰引爆：爆炸统一由 remove_tower 里的 _boom_explode 触发，避免重复
                remove_tower(t)
            continue
        # 迷你核弹单元：被怪物触碰即核爆（+留辐射），被摧毁也核爆（remove_tower 内处理）
        if k == "mininuke":
            touched = False
            for m in S.monsters:
                if m["alive"] and dist2(m, t) <= (m["r"] + CELL * 0.5) ** 2:
                    touched = True
                    break
            if touched:
                remove_tower(t)   # remove_tower 里触发 _mininuke_explode
            continue
        # 光棱塔：一直锁定 1~3 个目标（聚焦塔增加目标数），3帧一次伤，锁定后不换目标直到死亡/出射程
        if k == "prism":
            t["cool"] -= dt
            n_locks = 1 + t.get("focuses", 0)   # 默认1目标，每个聚焦塔+1
            # 清理已死亡/离开射程/被沉默影响的锁定目标
            locks = []
            for lm in t.get("locks", []):
                if lm.get("alive") and dist2(t, lm) <= t["range"] ** 2:
                    locks.append(lm)
            t["locks"] = locks
            # 补充新的锁定目标直到达到目标数
            if len(t["locks"]) < n_locks:
                existing = set(id(lm) for lm in t["locks"])
                # 选射程内最左（未锁定的）敌人作为新目标
                cand = [m for m in S.monsters if m["alive"] and id(m) not in existing
                        and dist2(t, m) <= t["range"] ** 2]
                cand.sort(key=lambda m: m["x"])
                for m in cand:
                    if len(t["locks"]) >= n_locks:
                        break
                    t["locks"].append(m)
            if t["cool"] <= 0:
                t["cool"] = PRISM_COOLDOWN
                for lm in t["locks"]:
                    damage_monster(lm, PRISM_DMG)
                    # 液氮塔增益：光棱塔攻击减速目标
                    if t.get("frost"):
                        lm["slow"] = max(lm["slow"], LIQUID_SLOW_TIME)
                    S.effects.append({"type": "beam", "x": t["x"], "y": t["y"],
                                      "x2": lm["x"], "y2": lm["y"],
                                      "r": 0, "color": "#d2a8ff",
                                      "life": 0.15, "maxlife": 0.15, "t": 0.0})
            continue
        # 导弹塔：发射追踪导弹（超大射程），命中或超时爆炸
        if k == "missile":
            t["cool"] -= dt
            if t["cool"] <= 0:
                target = tower_acquire(t, t["range"])
                if target:
                    cool = MISSILE_COOLDOWN * (GEAR_COOLDOWN_FACTOR ** t.get("gears", 0))
                    t["cool"] = cool
                    S.missiles.append({"x": t["x"], "y": t["y"], "target": target,
                                       "lock": MISSILE_LOCK, "from": t})
            continue
        # 液氮塔：范围攻击（自身中心4格半径，2.5秒一次，攻击冰冻范围内敌人）
        # 同时给 4 格范围内友方塔提供减速增益（这些塔攻击均减速目标）
        if k == "liquid":
            t["cool"] -= dt
            if t["cool"] <= 0:
                t["cool"] = LIQUID_COOLDOWN
                R = LIQUID_FREEZE_R * CELL
                # 范围攻击：4格半径内所有敌人造成伤害并冰冻
                hit = False
                for m in S.monsters:
                    if m["alive"] and dist2(t, m) <= R * R:
                        damage_monster(m, LIQUID_DMG)
                        m["frozen"] = LIQUID_FREEZE_TIME
                        hit = True
                if hit:
                    add_effect("boom", t["x"], t["y"], r=R, color="#8be9fd", life=0.6)
                    log("❄ 液氮塔范围冰冻!", "info")
            continue
        # 喷火器：锥形扇形火焰，朝射程内最近敌人方向喷射，3帧一次伤；
        # 范围内有液氮塔（受其增益）则喷减速火
        if k == "flamer":
            t["cool"] -= dt
            # 计算喷射方向：朝射程内最近的敌人（无则保持原方向）
            best = None; bestd = float("inf")
            for m in S.monsters:
                if not m["alive"]:
                    continue
                d = dist2(t, m)
                if d <= t["range"] ** 2 and d < bestd:
                    bestd = d; best = m
            if best:
                t["aim"] = math.atan2(best["y"] - t["y"], best["x"] - t["x"])
            if t["cool"] <= 0:
                t["cool"] = FLAMER_COOLDOWN
                # 液氮塔增益：喷火器受液氮塔减速增益（4格内）则喷减速火
                frost = t.get("frost", False)
                for m in S.monsters:
                    if not m["alive"]:
                        continue
                    if not in_sector(t["x"], t["y"], t["aim"], FLAMER_HALF_ARC,
                                     t["range"], m["x"], m["y"]):
                        continue
                    damage_monster(m, FLAMER_DMG)
                    if frost:
                        m["slow"] = max(m["slow"], FLAMER_SLOW_TIME)
                # 火焰喷射特效（锥形火焰从塔口喷出，见 draw_dynamic）
                add_effect("flame", t["x"], t["y"], r=t["range"],
                           color="#ff7b00", life=0.1,
                           aim=t["aim"], half=FLAMER_HALF_ARC, frost=frost)
            continue
        # 发射井：向锁定目标点持续发射导弹（玉米加农炮式；伤害/攻速与导弹塔一致，吃齿轮）
        if k == "silode":
            if t.get("lock_target"):
                t["cool"] -= dt
                if t["cool"] <= 0:
                    cool = MISSILE_COOLDOWN * (GEAR_COOLDOWN_FACTOR ** t.get("gears", 0))
                    t["cool"] = cool
                    lx, ly = t["lock_target"]
                    # 发射一枚飞向锁定点的导弹（到点爆炸）
                    S.missiles.append({"x": t["x"], "y": t["y"],
                                       "target": {"alive": True, "x": lx, "y": ly},
                                       "lock": 999.0, "is_silo": True, "from": t})
            continue
        # 治疗塔：治疗范围内塔 + 套盾
        if k == "healer":
            for tt in S.towers:
                if tt.get("removed") or tt is t:
                    continue
                if dist2(t, tt) <= t["range"] ** 2:
                    if tt["hp"] < tt["maxhp"]:
                        tt["hp"] = min(tt["maxhp"], tt["hp"] + HEAL_RATE * dt)
                    if tt.get("shield", 0) < HEAL_SHIELD:
                        tt["shield"] = HEAL_SHIELD
            continue

    # 4.6 导弹飞行与爆炸
    for mi in S.missiles:
        mi["lock"] -= dt
        if not mi["target"]["alive"] or mi["lock"] <= 0:
            # 超时或目标死亡 → 爆炸
            _missile_explode(mi)
            mi["done"] = True
            continue
        dx, dy = mi["target"]["x"] - mi["x"], mi["target"]["y"] - mi["y"]
        dist = math.hypot(dx, dy)
        step = BULLET_SPEED * 0.8 * dt
        if dist <= step or dist <= 8:
            _missile_explode(mi)
            mi["done"] = True
        else:
            mi["x"] += dx / dist * step
            mi["y"] += dy / dist * step
    S.missiles = [mi for mi in S.missiles if not mi.get("done")]

    # 5. 子弹（目标死亡或超时即清除，防滞留）
    for b in S.bullets:
        b["life"] -= dt
        if b["life"] <= 0:
            b["done"] = True; continue
        if not b["target"]["alive"]:
            b["done"] = True; continue
        dx, dy = b["target"]["x"] - b["x"], b["target"]["y"] - b["y"]
        dist = math.hypot(dx, dy)
        step = BULLET_SPEED * dt
        if dist <= step or dist <= 6:
            if b["target"].get("is_wspawn"):
                w = b["target"]
                w["hp"] -= GUN_DMG
                if w["hp"] <= 0:
                    remove_wspawn(w)
            else:
                damage_monster(b["target"], GUN_DMG)
                # 液氮塔增益：机枪子弹命中减速目标
                if b.get("from") and b["from"].get("frost"):
                    b["target"]["slow"] = max(b["target"]["slow"], LIQUID_SLOW_TIME)
            b["done"] = True
        else:
            b["x"] += dx / dist * step
            b["y"] += dy / dist * step
    S.bullets = [b for b in S.bullets if not b.get("done")]

    # 5.2 红锥/强化红锥光束：朝目标塔飞行，命中造成伤害（强化红锥 3 束依次发出）
    for b in S.conebeams:
        if b["delay"] > 0:
            b["delay"] -= dt
            continue
        b["life"] -= dt
        if b["life"] <= 0:
            b["done"] = True; continue
        target = b["target"]
        if target.get("removed"):
            b["done"] = True; continue
        dx, dy = target["x"] - b["x"], target["y"] - b["y"]
        dist = math.hypot(dx, dy)
        step = CONE_BEAM_SPEED * dt
        if dist <= step or dist <= 6:
            # 命中：对塔造成光束伤害（先扣护盾，盾破再扣血）
            dmg = b["dmg"]
            sh = target.get("shield", 0)
            if sh > 0:
                use = min(sh, dmg); target["shield"] = sh - use; dmg -= use
            if target["kind"] == "core":
                target["hp_frac"] = target.get("hp_frac", 0.0) + dmg
                whole = int(target["hp_frac"]); target["hp_frac"] -= whole
                target["hp"] -= whole
                if target["hp"] <= 0:
                    game_over()
            else:
                target["hp"] -= dmg
                if target["hp"] <= 0:
                    remove_tower(target)
            add_effect("spark", target["x"], target["y"], r=14, color="#ff6b6b",
                       life=0.3)
            b["done"] = True
        else:
            b["x"] += dx / dist * step
            b["y"] += dy / dist * step
    S.conebeams = [b for b in S.conebeams if not b.get("done")]

    # 5.5 强化蓝加速光环：把 6 格圆内友军移速提升至 2 倍（加强）
    for m in S.monsters:
        m["boosted"] = False
    R = BBLUE_AURA_R * CELL
    for m in S.monsters:
        if not m["alive"] or not MON_DEFS[m["type"]].get("aura"):
            continue
        for other in S.monsters:
            if other is m or not other["alive"]:
                continue
            if dist2(other, m) <= R * R:
                other["boosted"] = True
                other["boost_speed"] = m["speed"]   # 提升至与强化蓝自身移速一致
        add_effect("aura", m["x"], m["y"], r=R, color="#79c0ff", life=0.12)

    # 5.6 新怪机制：强化白召唤 / 白锥召唤 / 金球转化
    normal_pool = normal_summon_keys()
    # 白锥召唤池：普通球类 + 普通锥类（不含白/强白/金球/强化类/白锥自身）
    wcone_pool = [k for k in MON_KEYS
                  if k not in ("white", "bwhite", "gold", "wcone", "bconew")
                  and not MON_DEFS[k].get("elite")]
    # 强化白锥召唤池：强化球类（不含强白）+ 强化锥类（不含强白锥）
    bwcone_pool = [k for k in MON_KEYS
                   if MON_DEFS[k].get("elite") and k not in ("bwhite", "bconew")]
    for m in list(S.monsters):
        if not m["alive"]:
            continue
        mt = m["type"]
        # 白锥/强化白锥：每 2 秒在自身范围内召唤敌人（白球/强化白/召唤门不召唤锥类，
        # 但白锥自己会召唤锥类；强化白锥召唤强化类）
        if MON_DEFS[mt].get("summoner"):
            m.setdefault("summon_t", 0.0)
            m["summon_t"] -= dt
            if m["summon_t"] <= 0:
                m["summon_t"] = WCONE_SUMMON_INTERVAL
                RR = WCONE_SUMMON_R * CELL
                elite_summon = bool(MON_DEFS[mt].get("summon_elite"))
                pool = bwcone_pool if elite_summon else wcone_pool
                k = random.choice(pool)
                nm = spawn_monster(k, x=m["x"], y=m["y"])
                nm["x"] += random.uniform(-RR * 0.5, RR * 0.5)
                nm["y"] += random.uniform(-RR * 0.5, RR * 0.5)
                S.monsters.append(nm)
                add_effect("spark", nm["x"], nm["y"], r=CELL * 0.7,
                           color="#f5c542" if elite_summon else "#e6edf3", life=0.4)
            # 持续显示召唤范围特效
            add_effect("range", m["x"], m["y"], r=WCONE_SUMMON_R * CELL,
                       color="#e6edf3", life=0.12)
        # 强化白：每 2 秒在自身范围内召唤 1 只普通怪（白与强化白除外），范围带特效
        if MON_DEFS[mt].get("summon"):
            m.setdefault("summon_t", 0.0)
            m["summon_t"] -= dt
            if m["summon_t"] <= 0:
                m["summon_t"] = BWHITE_SUMMON_INTERVAL
                RR = BWHITE_SUMMON_R * CELL
                k = random.choice(normal_pool)
                nm = spawn_monster(k, x=m["x"], y=m["y"])
                nm["x"] += random.uniform(-RR * 0.5, RR * 0.5)
                nm["y"] += random.uniform(-RR * 0.5, RR * 0.5)
                S.monsters.append(nm)
                add_effect("spark", nm["x"], nm["y"], r=CELL * 0.7,
                           color="#e6edf3", life=0.4)
            # 持续显示召唤范围特效
            add_effect("range", m["x"], m["y"], r=BWHITE_SUMMON_R * CELL,
                       color="#e6edf3", life=0.12)
        # 金球：每 3 秒把范围内普通球变成同色强化球（除白与强化白和自己）
        if MON_DEFS[mt].get("gold"):
            m.setdefault("gold_t", 0.0)
            m["gold_t"] -= dt
            if m["gold_t"] <= 0:
                m["gold_t"] = GOLD_TRANSFORM_INTERVAL
                RR = GOLD_TRANSFORM_R * CELL
                n = 0
                for other in S.monsters:
                    if other is m or not other["alive"]:
                        continue
                    if dist2(other, m) <= RR * RR and _promote_monster(other):
                        n += 1
                        add_effect("spark", other["x"], other["y"],
                                   r=other["r"] * 2, color="#f5c542", life=0.5)
                if n:
                    log(f"🟡 金球转化 {n} 个普通球为强化球!", "warn")
            add_effect("range", m["x"], m["y"], r=GOLD_TRANSFORM_R * CELL,
                       color="#f5c542", life=0.12)

    # 6. 怪物
    for m in S.monsters:
        monster_update(m, dt)

    # 6.2 核辐射区域：持续伤害
    update_radiations(dt)

    # 清理死亡
    S.monsters = [m for m in S.monsters if m["alive"]]

    # 6.5 白球裂隙出怪点：独立定时出怪（不占用刷怪上限）。
    # 白球/强化白及召唤门不召唤锥类，故用排除锥类的普通怪池
    wgate_pool = normal_summon_keys()
    for w in S.wspawns:
        if not w["alive"]:
            continue
        w["timer"] -= dt
        if w["timer"] <= 0:
            w["timer"] = w["interval"]
            nm = spawn_monster(random.choice(wgate_pool), x=w["x"], y=w["y"])
            S.monsters.append(nm)
            add_effect("spark", w["x"], w["y"], r=CELL * 0.7, color="#ffffff", life=0.4)
    S.wspawns = [w for w in S.wspawns if w["alive"]]

    # 7. 特效生命周期
    for ef in S.effects:
        ef["t"] += dt
        ef["life"] -= dt
    S.effects = [ef for ef in S.effects if ef["life"] > 0]

# ============ GUI ============
def reset_state():
    """开始新一局：重置所有游戏状态"""
    global SPAWN_POINTS
    S.energy = START_ENERGY
    S.wave = 1
    S.paused = False
    S.over = False
    S.kills = 0
    S.towers = []
    S.monsters = []
    S.bullets = []
    S.missiles = []
    S.conebeams = []
    S.radiations = []
    S.effects = []
    S.wspawns = []
    S.white_pending = False
    S.gold_pending = False
    S.wcone_pending = False
    S.conespawn = None
    S.silo_locking = None
    S.hundred_timer = 0.0
    S.energy_cd = 0.0
    S.ispawn = None
    S.sel = None
    S.time = 0
    S.spawn = {"total": 0, "acc": 0, "timer": 0, "interval": SPAWN_INTERVAL}
    for r in range(GRID):
        for c in range(GRID):
            grid[r][c] = 0
    # 关卡模式用关卡指定的普通出怪点数量，无尽用默认
    if S.mode == "level" and S.level:
        init_map(S.level.get("spawn_points", NUM_SPAWN))
    else:
        init_map()

class Game:
    def __init__(self, root, tower_list=None, on_back=None, level=None):
        global _game
        _game = self
        self.root = root
        self.on_back = on_back
        if tower_list is None:
            tower_list = list(TOWER_DEFS.keys())
        self.tower_list = [k for k in tower_list if k != "core"]
        # 设定游戏模式与关卡配置（在 reset_state 之前设置）
        S.mode = "level" if level else "endless"
        S.level = level
        # 清空上一界面残留，重置状态并开始新局
        for w in root.winfo_children():
            w.destroy()
        reset_state()
        if S.mode == "level" and S.level:
            S.energy = S.level.get("start_energy", START_ENERGY)
        root.title(f"🎯 {S.level['name']}" if S.mode == "level" else "🏰 无尽塔防")
        root.configure(bg="#0d1117")
        self.canvas = tk.Canvas(root, width=CANVAS_W, height=W, bg="#1b2838",
                                highlightthickness=0)
        self.canvas.pack(side="left", padx=(8, 0), pady=8)

        panel = tk.Frame(root, bg="#161b22", width=PANEL_W)
        panel.pack(side="left", fill="y", padx=8, pady=8)
        panel.pack_propagate(False)

        title_text = f"🎯 {S.level['name']}" if S.mode == "level" else "🏰 无尽塔防"
        tk.Label(panel, text=title_text, bg="#161b22", fg="#58a6ff",
                 font=("Microsoft YaHei", 14, "bold")).pack(pady=(6, 8))

        self.lb = {}
        rows = [("波数", "wave"), ("能量", "energy"), ("场上怪", "mon"),
                ("基地血量", "hp"), ("出怪", "prog")]
        for label, key in rows:
            row = tk.Frame(panel, bg="#161b22")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, bg="#161b22", fg="#8b949e",
                     font=("Microsoft YaHei", 10)).pack(side="left", padx=8)
            tk.Label(row, text="0", bg="#161b22", fg="#e6edf3",
                     font=("Microsoft YaHei", 10, "bold")).pack(side="right", padx=8)
            self.lb[key] = row.winfo_children()[-1]

        self.bar = tk.Canvas(panel, width=PANEL_W - 24, height=10, bg="#21262d",
                             highlightthickness=0)
        self.bar.pack(pady=6)
        self.bar_fill = self.bar.create_rectangle(0, 0, 0, 10, fill="#58a6ff",
                                                  outline="")

        tk.Label(panel, text="── 槽位(按 1-9) ──", bg="#161b22", fg="#8b949e",
                 font=("Microsoft YaHei", 10)).pack(pady=(10, 4))

        self.tool_btns = {}
        for idx, kind in enumerate(self.tower_list):
            d = TOWER_DEFS[kind]
            b = tk.Button(panel, text=f"{idx+1}·{d['name']}  ⚡{d['cost']}",
                          bg="#21262d", fg="#e6edf3", activebackground="#0d2a4a",
                          relief="flat", font=("Microsoft YaHei", 10),
                          command=lambda k=kind: self.toggle_tool(k))
            b.pack(fill="x", pady=2, padx=10)
            self.tool_btns[kind] = b

        tk.Label(panel, text="点格子放置 · 右键取消 · 1-9选塔",
                 bg="#161b22", fg="#8b949e", font=("Microsoft YaHei", 9)).pack(pady=(8, 2))

        self.pause_btn = tk.Button(panel, text="⏸ 暂停", bg="#1f6feb", fg="#fff",
                                   relief="flat", font=("Microsoft YaHei", 10),
                                   command=self.toggle_pause)
        self.pause_btn.pack(fill="x", pady=3, padx=10)

        if self.on_back:
            back_btn = tk.Button(panel, text="← 返回主菜单", bg="#30363d", fg="#e6edf3",
                                 relief="flat", font=("Microsoft YaHei", 10),
                                 command=self.on_back)
            back_btn.pack(fill="x", pady=3, padx=10)

        self.msg_box = tk.Text(panel, height=7, bg="#161b22", fg="#8b949e",
                               font=("Microsoft YaHei", 9), relief="flat",
                               state="disabled", wrap="word")
        self.msg_box.pack(fill="x", pady=6, padx=10)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right)
        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("<Escape>", lambda e: self.set_tool(None))
        # 快捷键 1-9 对应槽位
        for i, kind in enumerate(self.tower_list):
            self.root.bind(str(i + 1),
                           lambda e, k=kind: self.set_tool(None if S.sel == k else k))

        core = {"kind": "core", "c": CORE_C, "r": CORE_R,
                "size": CORE_DEF["size"], "x": (CORE_C + 1) * CELL,
                "y": (CORE_R + 1) * CELL, "hp": CORE_DEF["hp"],
                "maxhp": CORE_DEF["hp"], "hp_frac": 0.0}
        S.towers.append(core)

        # 关卡模式：生成独立强化黑刷怪点（需在 msg_box 创建之后，否则 log 崩溃）
        if S.mode == "level" and S.level:
            setup_independent_spawn()

        self.redraw_static()
        start_wave(1)
        self.update_hud()
        self.last = 0
        self.loop()

    # ---------- 静态层 ----------
    def redraw_static(self):
        self.canvas.delete("static")
        self.canvas.delete("tower")
        for r in range(GRID):
            for c in range(GRID):
                v = grid[r][c]
                if v == 4:
                    fill = "#4a1f2e"          # 出怪点区域
                elif v == 5:
                    fill = "#5c1a1a"          # 白球裂隙出怪点
                elif v == 2:
                    fill = "#4a3b10"
                elif v == 0:
                    fill = "#243447"
                else:
                    fill = "#203047"
                x0, y0 = c * CELL, r * CELL
                self.canvas.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                             fill=fill, outline="#3a4657",
                                             tags="static")
        # 出怪点中心标记
        for i in range(len(SPAWN_POINTS)):
            cx, cy = spawn_center(i)
            self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6,
                                    outline="#ff7b72", width=2, tags="static")
            self.canvas.create_text(cx, cy + 14, text="出怪点", fill="#ff7b72",
                                    font=("Microsoft YaHei", 8), tags="static")
        # 白球裂隙出怪点标记
        for w in S.wspawns:
            if not w["alive"]:
                continue
            wx, wy = w["x"], w["y"]
            self.canvas.create_oval(wx - 7, wy - 7, wx + 7, wy + 7,
                                    outline="#ff7b72", width=2, tags="static")
            self.canvas.create_text(wx, wy, text="❄", fill="#ffdcd7",
                                    font=("Segoe UI Emoji", 12), tags="static")
        # 锥类刷怪点标记（第 6 波起生成，出红/黑锥及强化）
        if S.conespawn:
            sx, sy = S.conespawn["x"], S.conespawn["y"]
            self.canvas.create_polygon(sx, sy - 9, sx - 8, sy + 7, sx + 8, sy + 7,
                                       outline="#ff6b6b", width=2, tags="static")
            self.canvas.create_text(sx, sy + 17, text="锥点", fill="#ff6b6b",
                                    font=("Microsoft YaHei", 8), tags="static")
        # 主基地
        x0 = CORE_C * CELL; y0 = CORE_R * CELL
        self.canvas.create_rectangle(x0 + 2, y0 + 2, x0 + 2 * CELL - 2,
                                     y0 + 2 * CELL - 2, fill=CORE_DEF["color"],
                                     outline="black", width=2, tags="static")
        self.canvas.create_text((CORE_C + 1) * CELL, (CORE_R + 1) * CELL,
                                text="🏰", fill="#111", font=("Segoe UI Emoji", 22),
                                tags="static")
        for t in S.towers:
            if t["kind"] != "core" and not t.get("removed"):
                self.draw_tower(t)

    def draw_tower(self, t):
        size = t["size"]; x, y = t["x"], t["y"]
        x0 = x - size * CELL / 2; y0 = y - size * CELL / 2
        color = TOWER_DEFS.get(t["kind"], {}).get("color", "#aaa")
        self.canvas.create_rectangle(x0 + 2, y0 + 2, x0 + size * CELL - 2,
                                     y0 + size * CELL - 2, fill=color,
                                     outline="black", width=2, tags="tower")
        icon = {"solar": "☀", "gun": "🔫", "taunt": "❗",
                "boom_unit": "💣", "prism": "🔆", "missile": "🚀",
                "liquid": "🧊", "healer": "⛑", "energy": "⚡",
                "mininuke": "☢️", "flamer": "🔥", "silode": "🛰️", "matrix": "🛡"}.get(t["kind"], "?")
        self.canvas.create_text(x, y, text=icon, fill="#111",
                                font=("Segoe UI Emoji", int(size * CELL * 0.5)),
                                tags="tower")
        # 可加装齿轮的塔（机枪/导弹/液氮/发射井）叠加齿轮标记
        if t["kind"] in ("gun", "missile", "liquid", "silode"):
            ng = t.get("gears", 0)
            for k in range(ng):
                gx = x + (k - (ng - 1) / 2.0) * 16
                gy = y + size * CELL * 0.28
                self.canvas.create_oval(gx - 5, gy - 5, gx + 5, gy + 5,
                                        fill=TOWER_DEFS["gear"]["color"],
                                        outline="#7a5a10", width=1, tags="tower")
                self.canvas.create_oval(gx - 2, gy - 2, gx + 2, gy + 2,
                                        fill="#5c3d0e", outline="", tags="tower")
        # 光棱塔：叠加聚焦塔标记（紫色小点），并显示锁定目标数
        if t["kind"] == "prism":
            nf = t.get("focuses", 0)
            for k in range(nf):
                fx = x - 12 + k * 12
                fy = y - size * CELL * 0.28
                self.canvas.create_oval(fx - 4, fy - 4, fx + 4, fy + 4,
                                        fill=TOWER_DEFS["focus"]["color"],
                                        outline="#7a5ad0", width=1, tags="tower")
        # 嘲讽塔显示 5 格嘲讽圈
        if t["kind"] == "taunt":
            self.canvas.create_oval(x - TAUNT_RANGE, y - TAUNT_RANGE,
                                    x + TAUNT_RANGE, y + TAUNT_RANGE,
                                    outline="#5c1a1a", width=1, tags="tower")
        # 防御矩阵：显示 4 格弱嘲讽圈
        if t["kind"] == "matrix":
            self.canvas.create_oval(x - MATRIX_TAUNT_RANGE, y - MATRIX_TAUNT_RANGE,
                                    x + MATRIX_TAUNT_RANGE, y + MATRIX_TAUNT_RANGE,
                                    outline="#2e6b3f", width=1, dash=(3, 3),
                                    tags="tower")
        # 发射井：显示锁定目标点
        if t["kind"] == "silode" and t.get("lock_target"):
            lx, ly = t["lock_target"]
            self.canvas.create_oval(lx - 6, ly - 6, lx + 6, ly + 6,
                                    outline="#ff6b6b", width=2, tags="tower")
            self.canvas.create_text(lx, ly - 10, text="🎯", fill="#ff6b6b",
                                    font=("Segoe UI Emoji", 10), tags="tower")

    def _draw_flame_cone(self, ox, oy, aim, half, rr, color):
        """绘制喷火器的一个锥形火焰层（扇形多边形），顶点在 (ox,oy)，向 aim 方向展开"""
        pts = [ox, oy]
        steps = 8
        for i in range(steps + 1):
            a = aim - half + (2 * half) * (i / steps)
            pts += [ox + math.cos(a) * rr, oy + math.sin(a) * rr]
        self.canvas.create_polygon(*pts, fill=color, outline="", tags="dyn")

    # ---------- 动态层 ----------
    def draw_dynamic(self):
        self.canvas.delete("dyn")
        # 特效层（强化黑传送范围圆、扩散光环、落点闪光、粒子）
        for ef in S.effects:
            prog = 1.0 - ef["life"] / ef["maxlife"]   # 0→1 随时间推进
            fade = max(0.0, ef["life"] / ef["maxlife"])
            if ef["type"] == "range":
                # 被击半径范围圆（脉冲闪烁）
                pr = ef["r"] * (0.9 + 0.1 * math.sin(prog * 12))
                w = 2 + int(fade * 2)
                self.canvas.create_oval(ef["x"] - pr, ef["y"] - pr,
                                        ef["x"] + pr, ef["y"] + pr,
                                        outline=ef["color"], width=w,
                                        dash=(4, 3), tags="dyn")
                # 圆心标记
                self.canvas.create_oval(ef["x"] - 3, ef["y"] - 3,
                                        ef["x"] + 3, ef["y"] + 3,
                                        fill=ef["color"], outline="", tags="dyn")
            elif ef["type"] == "boom":
                # 落点/爆点扩散光环
                er = ef["r"] * (0.3 + 0.7 * prog)
                self.canvas.create_oval(ef["x"] - er, ef["y"] - er,
                                        ef["x"] + er, ef["y"] + er,
                                        outline=ef["color"], width=3,
                                        tags="dyn")
                self.canvas.create_oval(ef["x"] - 4, ef["y"] - 4,
                                        ef["x"] + 4, ef["y"] + 4,
                                        fill=ef["color"], outline="", tags="dyn")
            elif ef["type"] == "spark":
                # 传送起点粒子闪光
                er = ef["r"] * (0.4 + 0.6 * prog)
                for k in range(6):
                    a = k * (3.14159 * 2 / 6) + prog * 2
                    px = ef["x"] + math.cos(a) * er
                    py = ef["y"] + math.sin(a) * er
                    self.canvas.create_oval(px - 2, py - 2, px + 2, py + 2,
                                            fill=ef["color"], outline="",
                                            tags="dyn")
            elif ef["type"] == "aura":
                # 强化蓝加速光环（持续脉动浅蓝圆）
                pr = ef["r"] * (0.96 + 0.04 * math.sin(ef["t"] * 8))
                self.canvas.create_oval(ef["x"] - pr, ef["y"] - pr,
                                        ef["x"] + pr, ef["y"] + pr,
                                        outline=ef["color"], width=2,
                                        dash=(5, 4), tags="dyn")
            elif ef["type"] == "beam":
                # 光棱塔激光线（x,y → x2,y2）
                self.canvas.create_line(ef["x"], ef["y"], ef["x2"], ef["y2"],
                                        fill="#d2a8ff", width=2, tags="dyn")
            elif ef["type"] == "flame":
                # 喷火器锥形火焰：从塔口向喷射方向喷出的多层扇形火焰（真实感）
                aim = ef["extra"]["aim"]; half = ef["extra"]["half"]
                frost = ef["extra"].get("frost")
                ox, oy = ef["x"], ef["y"]
                rr = ef["r"] * (0.75 + 0.25 * prog)   # 火焰随喷发推进
                # 内层（最热，白/亮黄）
                self._draw_flame_cone(ox, oy, aim, half * 0.45, rr, "#fff3b0")
                # 中层（黄）
                self._draw_flame_cone(ox, oy, aim, half * 0.7, rr * 0.8, "#ffd94a")
                # 外层（橙红，减速火偏蓝紫）
                if frost:
                    self._draw_flame_cone(ox, oy, aim, half, rr * 0.6, "#7aa8ff")
                else:
                    self._draw_flame_cone(ox, oy, aim, half, rr * 0.6, "#ff7b00")
                # 喷口根部亮点
                self.canvas.create_oval(ox - 5, oy - 5, ox + 5, oy + 5,
                                        fill="#ffe28a", outline="", tags="dyn")
        # 导弹塔的追踪导弹
        for mi in S.missiles:
            self.canvas.create_oval(mi["x"] - 4, mi["y"] - 4, mi["x"] + 4, mi["y"] + 4,
                                    fill="#ff6b6b", outline="#ffffff", tags="dyn")
            self.canvas.create_oval(mi["x"] - 1.5, mi["y"] - 1.5, mi["x"] + 1.5, mi["y"] + 1.5,
                                    fill="#ffd7a8", outline="", tags="dyn")
        # 核辐射区域：黄绿色脉动圆
        for rad in S.radiations:
            if rad["life"] <= 0:
                continue
            prog = 1.0 - rad["life"] / rad["maxlife"]
            pulse = rad["r"] * (0.85 + 0.15 * math.sin(rad["life"] * 6))
            self.canvas.create_oval(rad["x"] - pulse, rad["y"] - pulse,
                                    rad["x"] + pulse, rad["y"] + pulse,
                                    outline="#d4ff57", width=2,
                                    dash=(6, 4), tags="dyn")
            self.canvas.create_text(rad["x"], rad["y"], text="☢️",
                                    fill="#d4ff57", font=("Segoe UI Emoji", 14),
                                    tags="dyn")
        # 发射井锁定模式提示 / 锁定线
        for t in S.towers:
            if t.get("removed") or t["kind"] != "silode":
                continue
            if t.get("lock_target"):
                lx, ly = t["lock_target"]
                self.canvas.create_line(t["x"], t["y"], lx, ly,
                                        fill="#ff6b6b", width=1, dash=(3, 3),
                                        tags="dyn")
        if S.silo_locking is not None and not S.silo_locking.get("removed"):
            silo = S.silo_locking
            self.canvas.create_oval(silo["x"] - CELL * 1.5, silo["y"] - CELL * 1.5,
                                    silo["x"] + CELL * 1.5, silo["y"] + CELL * 1.5,
                                    outline="#ff6b6b", width=2, dash=(4, 3),
                                    tags="dyn")
            self.canvas.create_text(W // 2, GRID * CELL / 2, text="🚀 选择发射井目标点",
                                    fill="#ff6b6b",
                                    font=("Microsoft YaHei", 20, "bold"),
                                    tags="dyn")
        for t in S.towers:
            if t.get("removed"):
                continue
            if t["hp"] < t["maxhp"]:
                bw = t["size"] * CELL - 8
                by = t["y"] - t["size"] * CELL / 2 - 8
                self.canvas.create_rectangle(t["x"] - bw / 2, by,
                                             t["x"] + bw / 2, by + 4,
                                             fill="#000", tags="dyn")
                ratio = max(0, t["hp"] / t["maxhp"])
                hc = "#f85149" if ratio > 0.35 else "#ff7b72"
                self.canvas.create_rectangle(t["x"] - bw / 2, by,
                                             t["x"] - bw / 2 + bw * ratio, by + 4,
                                             fill=hc, tags="dyn")
            # 护盾显示（治疗塔套的盾，浅蓝色圆环）
            sh = t.get("shield", 0)
            if sh > 0:
                rr = t["size"] * CELL / 2
                self.canvas.create_oval(t["x"] - rr, t["y"] - rr,
                                        t["x"] + rr, t["y"] + rr,
                                        outline="#50fa7b", width=2, tags="dyn")
            # 被黑锥沉默的塔：紫色环 + 头顶图标
            if t.get("silence_t", 0) > 0:
                rr = t["size"] * CELL / 2
                self.canvas.create_oval(t["x"] - rr, t["y"] - rr,
                                        t["x"] + rr, t["y"] + rr,
                                        outline="#9b59b6", width=2, dash=(4, 3),
                                        tags="dyn")
                self.canvas.create_text(t["x"], t["y"] - t["size"] * CELL / 2 - 12,
                                        text="🔇", fill="#9b59b6",
                                        font=("Segoe UI Emoji", 12), tags="dyn")
        for b in S.bullets:
            self.canvas.create_oval(b["x"] - 3, b["y"] - 3, b["x"] + 3, b["y"] + 3,
                                    fill="#ffffff", outline="", tags="dyn")
        # 红锥/强化红锥的光束弹（红色光点，强化红锥更亮更大）
        for cb in S.conebeams:
            if cb["delay"] > 0:
                continue
            rr = 5 if cb["elite"] else 3
            self.canvas.create_oval(cb["x"] - rr, cb["y"] - rr,
                                    cb["x"] + rr, cb["y"] + rr,
                                    fill="#ff6b6b", outline="#ffd7a8", tags="dyn")
        for m in S.monsters:
            if not m["alive"]:
                continue
            bob = abs(math.sin(m["bob"])) * m["r"] * 0.6
            yy = m["y"] - bob
            d = MON_DEFS[m["type"]]
            elite = d.get("elite")
            # 拖尾（仅强化球；残影由近到远淡出）
            if elite and m.get("trail"):
                for k, (tx, ty, tb) in enumerate(m["trail"]):
                    tyy = ty - abs(math.sin(tb)) * m["r"] * 0.6
                    alpha = 0.25 + 0.15 * (k + 1) / len(m["trail"])
                    self.canvas.create_oval(tx - m["r"] * alpha, tyy - m["r"] * alpha,
                                            tx + m["r"] * alpha, tyy + m["r"] * alpha,
                                            outline=d["color"], width=2,
                                            tags="dyn")
            self.canvas.create_oval(m["x"] - m["r"], m["y"] + m["r"] * 0.3,
                                    m["x"] + m["r"], m["y"] + m["r"] * 0.7,
                                    fill="#444444", outline="", tags="dyn")
            eye = "#f85149" if elite else "#d0d0d0"   # 普通白瞳 / 强化红瞳
            if m["type"] in ("black", "bblack"):
                self.canvas.create_oval(m["x"] - m["r"] - 3, yy - m["r"] - 3,
                                        m["x"] + m["r"] + 3, yy + m["r"] + 3,
                                        outline="#9b59b6", width=2, tags="dyn")
            if d.get("cone"):
                # 三棱锥：一边自转一边移动，绘制旋转的等边三角形
                spin = m.get("spin", 0.0)
                cx, cy = m["x"], yy
                r = m["r"]
                pts = []
                for kk in range(3):
                    a = spin + kk * (2 * math.pi / 3)
                    pts += [cx + math.cos(a) * r, cy + math.sin(a) * r]
                self.canvas.create_polygon(*pts, fill=d["color"], outline="black",
                                           width=1, tags="dyn")
                # 锥类眼睛：中心红瞳/白瞳小点
                self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3,
                                        fill=eye, outline="", tags="dyn")
            else:
                self.canvas.create_oval(m["x"] - m["r"], yy - m["r"],
                                        m["x"] + m["r"], yy + m["r"],
                                        fill=d["color"], outline="black", width=1,
                                        tags="dyn")
                # 眼睛：普通球白瞳，强化球红瞳（红眼特效）
                self.canvas.create_oval(m["x"] - m["r"] * 0.6, yy - m["r"] * 0.6,
                                        m["x"] - m["r"] * 0.05, yy - m["r"] * 0.05,
                                        fill=eye, outline="", tags="dyn")
            # 金球：金色眼睛 + 头顶王冠标记
            if d.get("gold"):
                self.canvas.create_oval(m["x"] - m["r"] * 0.6, yy - m["r"] * 0.6,
                                        m["x"] - m["r"] * 0.05, yy - m["r"] * 0.05,
                                        fill="#f5c542", outline="", tags="dyn")
                fy = yy - m["r"] - 8
                self.canvas.create_line(m["x"] - 7, yy - m["r"], m["x"] - 7, fy,
                                        fill="#c9d1d9", width=2, tags="dyn")
                self.canvas.create_line(m["x"] + 7, yy - m["r"], m["x"] + 7, fy,
                                        fill="#c9d1d9", width=2, tags="dyn")
                self.canvas.create_line(m["x"] - 7, fy, m["x"] + 7, fy,
                                        fill="#c9d1d9", width=2, tags="dyn")
                self.canvas.create_polygon(m["x"] - 7, fy, m["x"], fy - 6,
                                           m["x"] + 7, fy, fill="#f5c542",
                                           outline="", tags="dyn")
            # 强化蓝：头顶插旗帜
            if d.get("aura"):
                fx, fy = m["x"], yy - m["r"] - 8
                self.canvas.create_line(m["x"], yy - m["r"], fx, fy,
                                        fill="#c9d1d9", width=2, tags="dyn")
                self.canvas.create_polygon(fx, fy, fx + 10, fy + 4, fx, fy + 8,
                                           fill="#58a6ff", outline="",
                                           tags="dyn")
            # 冰冻/减速状态指示（浅蓝圆环/小冰晶）
            if m["frozen"] > 0:
                self.canvas.create_oval(m["x"] - m["r"] - 3, yy - m["r"] - 3,
                                        m["x"] + m["r"] + 3, yy + m["r"] + 3,
                                        outline="#8be9fd", width=2, tags="dyn")
                self.canvas.create_text(m["x"], yy - m["r"] - 14, text="❄",
                                        fill="#8be9fd", font=("Segoe UI Emoji", 10),
                                        tags="dyn")
            elif m["slow"] > 0:
                self.canvas.create_oval(m["x"] - m["r"] - 3, yy - m["r"] - 3,
                                        m["x"] + m["r"] + 3, yy + m["r"] + 3,
                                        outline="#8be9fd", width=1, dash=(3, 2),
                                        tags="dyn")
            bw = m["r"] * 2.4
            by = yy - m["r"] - 9
            self.canvas.create_rectangle(m["x"] - bw / 2, by, m["x"] + bw / 2,
                                         by + 3.5, fill="#000", tags="dyn")
            ratio = max(0, m["hp"] / m["maxhp"])
            hc = "#3fb950" if ratio > 0.5 else ("#f0d94a" if ratio > 0.25 else "#f85149")
            self.canvas.create_rectangle(m["x"] - bw / 2, by,
                                         m["x"] - bw / 2 + bw * ratio, by + 3.5,
                                         fill=hc, tags="dyn")
            # 强黑锥次数盾：紫色圆环 + 剩余层数（需多次攻击击破）
            if m.get("cshields", 0) > 0:
                self.canvas.create_oval(m["x"] - m["r"] - 4, yy - m["r"] - 4,
                                        m["x"] + m["r"] + 4, yy + m["r"] + 4,
                                        outline="#9b59b6", width=2, tags="dyn")
                self.canvas.create_text(m["x"], by - 8, text=f"🛡{m['cshields']}",
                                        fill="#c9b1e8", font=("Segoe UI Emoji", 9),
                                        tags="dyn")
        # 白球裂隙出怪点：动态血条
        for w in S.wspawns:
            if not w["alive"]:
                continue
            bw = CELL - 4
            by = w["y"] - CELL / 2 - 8
            ratio = max(0, w["hp"] / w["maxhp"])
            self.canvas.create_rectangle(w["x"] - bw / 2, by, w["x"] + bw / 2,
                                         by + 4, fill="#000", tags="dyn")
            self.canvas.create_rectangle(w["x"] - bw / 2, by,
                                         w["x"] - bw / 2 + bw * ratio, by + 4,
                                         fill="#ff7b72", tags="dyn")

        # 百球行警告：触发前在屏幕中间显示粗体红字（类似植物大战僵尸）
        if S.hundred_timer > 0:
            cx = W / 2
            cy = (GRID * CELL) / 2
            pulse = math.sin(S.time * 10)          # 闪烁
            size = int(40 + 4 * pulse)
            alpha_color = "#ff2d2d" if pulse > 0 else "#ff0000"
            self.canvas.create_text(cx, cy - 20, text="🌊 百球行来袭！",
                                    fill=alpha_color, font=("Microsoft YaHei", size, "bold"),
                                    tags="dyn")
            self.canvas.create_text(cx, cy + 30,
                                    text=f"{max(0, S.hundred_timer):.0f}",
                                    fill="#ffffff",
                                    font=("Microsoft YaHei", 26, "bold"),
                                    tags="dyn")

    # ---------- 交互 ----------
    def cell_at(self, e):
        return e.x // CELL, e.y // CELL

    def on_click(self, e):
        # 发射井锁定模式：左键选择目标点
        if S.silo_locking is not None:
            silo = S.silo_locking
            if not silo.get("removed"):
                c, r = self.cell_at(e)
                x = (c + 0.5) * CELL; y = (r + 0.5) * CELL
                silo["lock_target"] = (x, y)
                log(f"🚀 发射井锁定目标点 ({c},{r})，开始持续发射导弹!", "info")
            S.silo_locking = None
            return
        if S.over or not S.sel:
            return
        c, r = self.cell_at(e)
        if 0 <= c < GRID and 0 <= r < GRID:
            if place_tower(S.sel, c, r):
                if S.sel in ("gear", "focus"):
                    self.redraw_static()   # 齿轮/聚焦塔叠放，需重绘塔层
                else:
                    self.draw_tower(S.towers[-1])
                self.refresh_tools()

    def on_right(self, e):
        # 右键点击发射井 → 进入锁定模式（玉米加农炮式：先右键该塔再选目标）
        if not S.over:
            c, r = self.cell_at(e)
            for t in S.towers:
                if t.get("removed") or t["kind"] != "silode":
                    continue
                if t["c"] <= c < t["c"] + t["size"] and t["r"] <= r < t["r"] + t["size"]:
                    S.silo_locking = t
                    log("🚀 发射井进入锁定模式：左键点击地图选择目标点", "warn")
                    return
        S.silo_locking = None
        self.set_tool(None)

    def toggle_tool(self, kind):
        self.set_tool(None if S.sel == kind else kind)

    def set_tool(self, kind):
        S.sel = kind
        self.refresh_tools()

    def toggle_pause(self):
        S.paused = not S.paused
        self.pause_btn.config(text="▶ 继续" if S.paused else "⏸ 暂停")

    def refresh_tools(self):
        for kind, b in self.tool_btns.items():
            d = TOWER_DEFS[kind]
            aff = S.energy < d["cost"]
            sel = S.sel == kind
            # 电能包：冷却中禁用并显示剩余秒数
            if kind == "energy" and S.energy_cd > 0:
                b.config(text=f"{self.tower_list.index(kind)+1}·电能包 ⚡ {S.energy_cd:.0f}s",
                         state="disabled", bg="#21262d")
                continue
            if kind == "energy":
                b.config(text=f"{self.tower_list.index(kind)+1}·电能包  ⚡{d['cost']}")
            b.config(bg="#0d2a4a" if sel else "#21262d",
                     state="disabled" if aff and not sel else "normal")

    # ---------- HUD ----------
    def update_hud(self):
        core = core_tower()
        if S.mode == "level":
            total = len(S.level.get("wave_units", []))
            self.lb["wave"].config(text=f"{S.wave}/{total}")
        else:
            self.lb["wave"].config(text=S.wave)
        self.lb["energy"].config(text=int(S.energy))
        self.lb["mon"].config(text=sum(1 for m in S.monsters if m["alive"]))
        self.lb["hp"].config(text=core["hp"] if core else 0)
        self.lb["prog"].config(text=f"{S.spawn['acc']}/{S.spawn['total']}")
        frac = S.spawn["acc"] / S.spawn["total"] if S.spawn["total"] > 0 else 0
        self.bar.coords(self.bar_fill, 0, 0, (PANEL_W - 24) * frac, 10)

    # ---------- 主循环 ----------
    def loop(self):
        import time
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        update(dt)
        self.draw_dynamic()
        self.update_hud()
        self.refresh_tools()
        self.root.after(16, self.loop)


# ============ 日志 ============
LOG = {"warn": "#f85149", "info": "#3fb950"}
_game = None
def log(text, kind="info"):
    if _game is None:
        return
    _game.msg_box.config(state="normal")
    _game.msg_box.insert("end", f"{text}\n")
    _game.msg_box.config(state="disabled")
    _game.msg_box.see("end")

def game_over():
    if S.over:                 # 弹窗只弹一次
        return
    S.over = True
    import tkinter.messagebox as mb
    mb.showinfo("💀 游戏结束",
                f"基地被摧毁！\n你坚守到了第 {S.wave} 波，击杀 {S.kills} 只怪物。")

def level_cleared():
    """关卡模式：打满所有波次并清场 → 胜利"""
    if S.over:
        return
    S.over = True
    import tkinter.messagebox as mb
    lv_name = S.level["name"] if S.level else ""
    mb.showinfo("🏆 关卡通过",
                f"🎉 恭喜通关《{lv_name}》！\n共 {S.wave} 波，击杀 {S.kills} 只怪物。")
    if _game is not None and _game.on_back:
        _game.on_back()

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


# ============ 多界面应用（主界面 / 选卡 / 图鉴 / 游戏） ============
class App:
    def __init__(self, root):
        self.root = root
        root.title("🏰 无尽塔防")
        root.configure(bg="#0d1117")
        self.show_menu()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ---------- 主界面 ----------
    def show_menu(self):
        self.clear()
        root = self.root
        root.geometry("")   # 恢复默认尺寸
        root.configure(bg="#0d1117")
        fr = tk.Frame(root, bg="#0d1117")
        fr.pack(expand=True)
        tk.Label(fr, text="🏰 几何塔防", bg="#0d1117", fg="#58a6ff",
                 font=("Microsoft YaHei", 30, "bold")).pack(pady=(40, 10))
        tk.Label(fr, text="无尽塔防 · 多炮台作战", bg="#0d1117", fg="#8b949e",
                 font=("Microsoft YaHei", 12)).pack(pady=(0, 40))
        tk.Button(fr, text="▶ 开始无尽游戏", bg="#1f6feb", fg="#fff",
                  activebackground="#0d2a4a", relief="flat",
                  font=("Microsoft YaHei", 16, "bold"), width=18,
                  command=self.show_card).pack(pady=10)
        tk.Button(fr, text="🎯 关卡模式", bg="#8957e5", fg="#fff",
                  activebackground="#0d2a4a", relief="flat",
                  font=("Microsoft YaHei", 16, "bold"), width=18,
                  command=self.show_levels).pack(pady=10)
        tk.Button(fr, text="📖 图鉴", bg="#30363d", fg="#e6edf3",
                  activebackground="#0d2a4a", relief="flat",
                  font=("Microsoft YaHei", 14), width=18,
                  command=self.show_codex).pack(pady=10)

    # ---------- 选卡界面 ----------
    def show_card(self):
        self.clear()
        root = self.root
        root.configure(bg="#0d1117")
        top = tk.Frame(root, bg="#0d1117")
        top.pack(fill="x", padx=20, pady=10)
        tk.Label(top, text="选择 9 种炮台", bg="#0d1117", fg="#58a6ff",
                 font=("Microsoft YaHei", 16, "bold")).pack(side="left")
        self.card_cnt = tk.Label(top, text="已选 0/9", bg="#0d1117", fg="#f0d94a",
                                 font=("Microsoft YaHei", 12, "bold"))
        self.card_cnt.pack(side="right")

        grid = tk.Frame(root, bg="#161b22")
        grid.pack(pady=10)
        self.selected = []
        self.card_btns = {}
        avail = [k for k in TOWER_DEFS.keys() if k != "core"]
        for i, kind in enumerate(avail):
            d = TOWER_DEFS[kind]
            b = tk.Button(grid, text=f"{d['name']}\n⚡{d['cost']}",
                          bg="#21262d", fg="#e6edf3", activebackground="#0d2a4a",
                          relief="flat", font=("Microsoft YaHei", 10),
                          width=10, height=2,
                          command=lambda k=kind: self.toggle_card(k))
            b.grid(row=i // 5, column=i % 5, padx=4, pady=4)
            self.card_btns[kind] = b

        btns = tk.Frame(root, bg="#0d1117")
        btns.pack(pady=10)
        self.start_btn = tk.Button(btns, text="⚔ 开始游戏", bg="#238636", fg="#fff",
                                   relief="flat", font=("Microsoft YaHei", 13, "bold"),
                                   state="disabled", command=self.do_start)
        self.start_btn.pack(side="left", padx=10)
        tk.Button(btns, text="← 返回", bg="#30363d", fg="#e6edf3", relief="flat",
                  font=("Microsoft YaHei", 12), command=self.show_menu).pack(side="left", padx=10)

    def toggle_card(self, kind):
        if kind in self.selected:
            self.selected.remove(kind)
        else:
            if len(self.selected) >= 9:
                return
            self.selected.append(kind)
        # 刷新高亮
        for k, b in self.card_btns.items():
            b.config(bg="#0d2a4a" if k in self.selected else "#21262d")
        self.card_cnt.config(text=f"已选 {len(self.selected)}/9")
        self.start_btn.config(state="normal" if len(self.selected) == 9 else "disabled")

    def do_start(self):
        if len(self.selected) == 9:
            self.show_game(list(self.selected))

    def show_game(self, tower_list):
        self.clear()
        Game(self.root, tower_list, on_back=self.show_menu)

    # ---------- 关卡界面 ----------
    def show_levels(self):
        self.clear()
        root = self.root
        root.configure(bg="#0d1117")
        top = tk.Frame(root, bg="#0d1117")
        top.pack(fill="x", padx=20, pady=10)
        tk.Label(top, text="🎯 关卡模式", bg="#0d1117", fg="#58a6ff",
                 font=("Microsoft YaHei", 16, "bold")).pack(side="left")
        tk.Button(top, text="← 返回", bg="#30363d", fg="#e6edf3", relief="flat",
                  font=("Microsoft YaHei", 11), command=self.show_menu).pack(side="right")

        grid = tk.Frame(root, bg="#161b22")
        grid.pack(pady=10)
        for i, lkey in enumerate(LEVEL_ORDER):
            lv = LEVELS[lkey]
            row = tk.Frame(grid, bg="#161b22")
            row.pack(fill="x", padx=8, pady=6)
            tk.Button(row, text=f"关卡 {i+1} · {lv['name']}", bg="#8957e5", fg="#fff",
                      activebackground="#0d2a4a", relief="flat",
                      font=("Microsoft YaHei", 13, "bold"), width=22,
                      command=lambda k=lkey: self.show_level_game(k)).pack(side="left")
            tk.Label(row, text=lv["desc"], bg="#161b22", fg="#8b949e",
                     font=("Microsoft YaHei", 10), justify="left", anchor="w",
                     wraplength=420).pack(side="left", padx=12)

    def show_level_game(self, level_key):
        self.clear()
        # 关卡模式直接用全部塔，免选卡
        all_towers = [k for k in TOWER_DEFS.keys() if k != "core"]
        Game(self.root, all_towers, on_back=self.show_levels, level=LEVELS[level_key])

    # ---------- 图鉴界面 ----------
    def show_codex(self, tab="tower"):
        self.clear()
        root = self.root
        root.configure(bg="#0d1117")
        top = tk.Frame(root, bg="#0d1117")
        top.pack(fill="x", padx=20, pady=10)
        tk.Label(top, text="📖 图鉴", bg="#0d1117", fg="#58a6ff",
                 font=("Microsoft YaHei", 16, "bold")).pack(side="left")
        tk.Button(top, text="← 返回", bg="#30363d", fg="#e6edf3", relief="flat",
                  font=("Microsoft YaHei", 11), command=self.show_menu).pack(side="right")

        tabs = tk.Frame(root, bg="#0d1117")
        tabs.pack(pady=(0, 8))
        tk.Button(tabs, text="塔", bg="#0d2a4a" if tab == "tower" else "#21262d",
                  fg="#e6edf3", relief="flat", font=("Microsoft YaHei", 12, "bold"),
                  command=lambda: self.show_codex("tower")).pack(side="left", padx=5)
        tk.Button(tabs, text="几何体(敌方)", bg="#0d2a4a" if tab == "mon" else "#21262d",
                  fg="#e6edf3", relief="flat", font=("Microsoft YaHei", 12, "bold"),
                  command=lambda: self.show_codex("mon")).pack(side="left", padx=5)

        canvas = tk.Canvas(root, bg="#161b22", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview,
                                 bg="#30363d", troughcolor="#161b22", width=14,
                                 activebackground="#8b949e")
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        canvas.configure(yscrollcommand=scrollbar.set)
        inner = tk.Frame(canvas, bg="#161b22")
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        inner.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        # 点击滚动条上方/下方空白区域时按页滚动（可选）
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

        if tab == "tower":
            items = [k for k in TOWER_DEFS if k != "core"]
            for kind in items:
                d = TOWER_DEFS[kind]
                self._codex_row(inner, d["color"], d["name"],
                                f"占地 {d['size']}×{d['size']} · 费用 ⚡{d['cost']} · 生命 {d['hp']}",
                                d.get("desc", ""))
        else:
            items = list(MON_DEFS.keys())
            for mtype in items:
                d = MON_DEFS[mtype]
                elite = "强化" if d.get("elite") else ""
                tag = "普通" if not elite else elite
                self._codex_row(inner, d["color"], f"{tag}·{d['name']}",
                                f"血量×{d['hp_mult']} · 攻 {d['atk']} · 速 {d['speed']}",
                                d.get("desc", ""),
                                shape="triangle" if d.get("cone") else "circle")

    def _codex_row(self, parent, color, name, info, desc="", shape="circle"):
        row = tk.Frame(parent, bg="#161b22")
        row.pack(fill="x", padx=10, pady=4)
        cv = tk.Canvas(row, width=36, height=36, bg="#161b22", highlightthickness=0)
        cv.pack(side="left", padx=6)
        if shape == "triangle":
            # 三棱锥：图鉴中显示为三角形
            cv.create_polygon(18, 5, 7, 31, 29, 31, fill=color, outline="black")
        else:
            cv.create_oval(6, 6, 30, 30, fill=color, outline="black")
        col = tk.Frame(row, bg="#161b22")
        col.pack(side="left", fill="x", expand=True)
        tk.Label(col, text=name, bg="#161b22", fg="#e6edf3",
                 font=("Microsoft YaHei", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(col, text=info, bg="#161b22", fg="#8b949e",
                 font=("Microsoft YaHei", 10), anchor="w").pack(fill="x")
        if desc:
            tk.Label(col, text=desc, bg="#161b22", fg="#a8b3c0", justify="left",
                     wraplength=560, font=("Microsoft YaHei", 10),
                     anchor="w").pack(fill="x", pady=(2, 0))


if __name__ == "__main__":
    main()
