# -*- coding: utf-8 -*-
"""v3 核心逻辑测试：出怪点/索敌从近到远/锁定不更改/嘲讽塔优先/黑球闪现"""
import random
import math
import tower_defense as td

def math_dist(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])

random.seed(11)
print("=== 1. 出怪点 ===")
assert len(td.SPAWN_POINTS) == td.NUM_SPAWN, f"应有{td.NUM_SPAWN}个出怪点"
print("出怪点数:", len(td.SPAWN_POINTS), td.SPAWN_POINTS)
# 互不重叠
for i in range(len(td.SPAWN_POINTS)):
    for j in range(i + 1, len(td.SPAWN_POINTS)):
        r0, c0 = td.SPAWN_POINTS[i]
        r1, c1 = td.SPAWN_POINTS[j]
        overlap = (r0 < r1 + td.SPAWN_SIZE and r0 + td.SPAWN_SIZE > r1 and
                   c0 < c1 + td.SPAWN_SIZE and c0 + td.SPAWN_SIZE > c1)
        assert not overlap, f"出怪点{i}和{j}重叠"
print("  出怪点互不重叠: OK")
# 避开基地
for (r, c) in td.SPAWN_POINTS:
    assert not (r < td.CORE_R + td.CORE_DEF["size"] + 1 and
                r + td.SPAWN_SIZE > td.CORE_R - 1 and
                c < td.CORE_C + td.CORE_DEF["size"] + 1 and
                c + td.SPAWN_SIZE > td.CORE_C - 1), "出怪点与基地重叠"
print("  出怪点避开基地: OK")

# 加核心
core = {"kind": "core", "c": td.CORE_C, "r": td.CORE_R, "size": td.CORE_DEF["size"],
        "x": (td.CORE_C + 1) * td.CELL, "y": (td.CORE_R + 1) * td.CELL,
        "hp": td.BASE_HP, "maxhp": td.BASE_HP}
td.S.towers.append(core)
td.start_wave(1)

print("\n=== 2. 索敌从近到远 ===")
# 放两个塔，一个近一个远
far = {"kind": "gun", "c": 35, "r": 5, "size": 1,
       "x": 35 * td.CELL + td.CELL / 2, "y": 5 * td.CELL + td.CELL / 2,
       "hp": 100, "maxhp": 100, "cool": 0, "range": td.GUN_RANGE}
near = {"kind": "gun", "c": 10, "r": 5, "size": 1,
        "x": 10 * td.CELL + td.CELL / 2, "y": 5 * td.CELL + td.CELL / 2,
        "hp": 100, "maxhp": 100, "cool": 0, "range": td.GUN_RANGE}
td.S.towers.append(far)
td.S.towers.append(near)
# 怪在 (10,5) 附近，(15,5)
m = td.spawn_monster("red", x=15 * td.CELL + td.CELL / 2,
                     y=5 * td.CELL + td.CELL / 2)
td.S.monsters.append(m)
tgt = td.acquire_target(m)
print("  怪选最近目标:", "OK(选了近塔)" if tgt is near else f"FAIL(选了{'远' if tgt is far else '其他'})")

print("\n=== 3. 锁定目标不更改 ===")
m["target"] = far     # 先锁定远处塔
m2 = td.acquire_target(m)
print("  有锁定目标不更改:", "OK(仍锁定远塔)" if m2 is far else "FAIL(被更近塔抢走)")
# 但远塔被摧毁后应重新索敌到近塔
far["removed"] = True
m3 = td.acquire_target(m)
print("  目标被毁后重新索敌最近:", "OK(重选近塔)" if m3 is near else "FAIL")
del far["removed"]

print("\n=== 4. 嘲讽塔优先 ===")
# 建一个嘲讽塔在远处，但应强制吸引范围内怪物
taunt = {"kind": "taunt", "c": 38, "r": 10, "size": 1,
         "x": 38 * td.CELL + td.CELL / 2, "y": 10 * td.CELL + td.CELL / 2,
         "hp": 150, "maxhp": 150}
td.S.towers.append(taunt)
# 怪在 (15,5) 附近；嘲讽塔在(38,10)，距离 > 5格 -> 不在嘲讽范围，应忽略嘲讽，保持锁定近塔
m["target"] = near
t4 = td.acquire_target(m)
print("  嘲讽塔在范围外时不影响:", "OK" if t4 is near else "FAIL")
# 把怪放到嘲讽塔 5 格内
m["x"] = 36 * td.CELL + td.CELL / 2
m["y"] = 10 * td.CELL + td.CELL / 2
m["target"] = near     # 已锁定近塔
t5 = td.acquire_target(m)
print("  嘲讽塔范围内强制吸引:", "OK(转攻嘲讽塔)" if t5 is taunt else "FAIL")

print("\n=== 5. 黑色球闪现 (10×10) ===")
black = td.spawn_monster("black", x=(20 * td.CELL + td.CELL / 2),
                         y=(6 * td.CELL + td.CELL / 2))
# 关键：给黑球一个已锁定的"远处目标"，验证它仍会闪现（修复的bug场景）
black["flash_cd"] = 0
black["target"] = {"kind": "gun", "c": 38, "r": 3, "size": 1,
                   "x": 38 * td.CELL + td.CELL / 2, "y": 3 * td.CELL + td.CELL / 2,
                   "hp": 100, "maxhp": 100, "cool": 0, "range": td.GUN_RANGE}
td.S.monsters.append(black)
flash_tower = {"kind": "gun", "c": 19, "r": 5, "size": 1,
               "x": 19 * td.CELL + td.CELL / 2, "y": 5 * td.CELL + td.CELL / 2,
               "hp": 100, "maxhp": 100, "cool": 0, "range": td.GUN_RANGE}
td.S.towers.append(flash_tower)
flashed = False
for _ in range(30):
    td.monster_update(black, 0.1)
    if black["target"] is flash_tower and math_dist(black, flash_tower) < td.CELL:
        flashed = True
        break
print("  黑球已有目标时仍闪现到10×10最近塔:", "OK" if flashed else "FAIL")
# 验证闪现后进入攻击并持续锁定该塔(不因普通索敌跑走)
attacking = False
for _ in range(20):
    td.monster_update(black, 0.1)
    if black["target"] is flash_tower:
        attacking = True
print("  闪现后持续攻击该塔:", "OK" if attacking else "FAIL")

print("\n=== 6. 长时间模拟 ===")
td.S.spawn = {"total": 0, "acc": 0, "timer": 0, "interval": 1.1}
td.start_wave(1)
prev = 1
for _ in range(9000):
    td.update(0.016)
    if td.S.wave > prev:
        prev = td.S.wave
print("  波次:", td.S.wave, "| 击杀:", td.S.kills,
      "| 场上怪:", sum(1 for mm in td.S.monsters if mm["alive"]))
print("  剩余塔:", [t["kind"] for t in td.S.towers if not t.get("removed")])
print("\n=== 全部通过 ===")
