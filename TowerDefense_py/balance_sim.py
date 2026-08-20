# -*- coding: utf-8 -*-
"""平衡模拟：模拟玩家合理运营(集中建机枪+嘲讽塔+太阳能)能否守住"""
import random
import tower_defense as td

random.seed(5)
core = {"kind": "core", "c": td.CORE_C, "r": td.CORE_R, "size": td.CORE_DEF["size"],
        "x": (td.CORE_C + 1) * td.CELL, "y": (td.CORE_R + 1) * td.CELL,
        "hp": td.BASE_HP, "maxhp": td.BASE_HP}
td.S.towers.append(core)
td.start_wave(1)

# 玩家策略（模拟）：开局建太阳能+嘲讽塔+机枪，集中布防在基地附近
def build_near_core(kind):
    """在基地上方区域找可建格建塔"""
    for r in range(td.CORE_R - 3, td.CORE_R):
        for c in range(td.CORE_C, td.CORE_C + 8):
            if td.place_tower(kind, c, r):
                return True
    return False

import itertools
build_near_core("solar")
build_near_core("solar")
for _ in range(3):
    build_near_core("gun")

# 每帧尝试用能量补建：优先嘲讽塔(1个)和机枪
taunt_built = False
dt = 0.016
max_wave = 1
steps = 0
while steps < 20000 and not td.S.over:
    steps += 1
    # 每 30 帧尝试补塔
    if steps % 30 == 0:
        # 能量富余：建太阳能扩经济，否则补机枪/嘲讽
        if not taunt_built and td.S.energy >= td.TOWER_DEFS["taunt"]["cost"]:
            if build_near_core("taunt"):
                taunt_built = True
        elif td.S.energy >= td.TOWER_DEFS["gun"]["cost"]:
            build_near_core("gun")
        elif td.S.energy >= td.TOWER_DEFS["solar"]["cost"]:
            build_near_core("solar")
    td.update(dt)
    if td.S.wave > max_wave:
        max_wave = td.S.wave
    if td.S.over:
        break

towers_alive = [t["kind"] for t in td.S.towers if not t.get("removed")]
print("结束波次:", td.S.wave, "| 击杀:", td.S.kills, "| game_over:", td.S.over)
print("存活塔:", towers_alive)
print("基地血:", core["hp"] if not core.get("removed") else "已毁")
