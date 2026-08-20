# -*- coding: utf-8 -*-
"""喷火器扇形 + 液氮塔重做 测试"""
import random, math
import tower_defense as td

random.seed(1)

def make_core():
    return {'kind':'core','c':td.CORE_C,'r':td.CORE_R,'size':2,'x':(td.CORE_C+1)*td.CELL,'y':(td.CORE_R+1)*td.CELL,'hp':99999,'maxhp':99999,'hp_frac':0.0}

print("=== 1. 扇形判定 in_sector ===")
# 原点(0,0)，朝右(0弧度)，半角0.55，半径100
assert td.in_sector(0,0, 0.0, 0.55, 100, 80, 0) is True, "正前方应在扇形内"
assert td.in_sector(0,0, 0.0, 0.55, 100, 80, 20) is True, "偏上应在扇形内"
assert td.in_sector(0,0, 0.0, 0.55, 100, 80, 80) is False, "侧面90度不应在扇形内"
assert td.in_sector(0,0, 0.0, 0.55, 100, 150, 0) is False, "超射程不应在扇形内"
assert td.in_sector(0,0, math.pi/2, 0.55, 100, 0, 80) is True, "朝下方向应命中"
print("  in_sector 扇形判定: OK")

print("\n=== 2. 喷火器扇形AOE伤害 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.start_wave(1)
core = make_core()
td.S.towers.append(core)
fl = {'kind':'flamer','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,'hp':180,'maxhp':180,'cool':0,'range':td.GUN_RANGE,'aim':0.0}
td.S.towers.append(fl)
# 一只在正前方（扇形内），一只在侧面90度（扇形外）
a = td.spawn_monster('red', x=13*td.CELL, y=11*td.CELL)   # 正右方，扇形内
b = td.spawn_monster('red', x=11*td.CELL, y=15*td.CELL)   # 正下方90度，扇形外
td.S.monsters += [a, b]
ha, hb = a['hp'], b['hp']
fl['cool'] = 0
td.update(0.06)
assert a['hp'] < ha, "扇形内敌人应受伤害"
assert b['hp'] == hb, "扇形外敌人不应受伤害"
print("  扇形内受伤害, 扇形外不受: OK")

print("\n=== 3. 液氮塔范围攻击 + 冰冻 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.start_wave(1)
td.S.towers.append(make_core())
liq = {'kind':'liquid','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,'hp':130,'maxhp':130,'cool':0,'range':4*td.CELL,'frost':False}
td.S.towers.append(liq)
# 3只怪在4格内，1只在4格外
m1 = td.spawn_monster('red', x=12*td.CELL, y=11*td.CELL)  # 1格内
m2 = td.spawn_monster('red', x=14*td.CELL, y=13*td.CELL)  # 约3.6格内
m3 = td.spawn_monster('red', x=20*td.CELL, y=11*td.CELL)  # 9格外
td.S.monsters += [m1, m2, m3]
liq['cool'] = 0
td.update(0.06)
assert m1['frozen'] > 0 and m2['frozen'] > 0, "4格内敌人应被冰冻"
assert m1['hp'] < td.wave_hp(1)*1 and m2['hp'] < td.wave_hp(1)*1, "4格内敌人应受伤害"
assert m3['frozen'] == 0, "4格外敌人不应被冰冻"
print("  4格内敌人伤害+冰冻, 4格外不受: OK, frozen时间", round(m1['frozen'],1))

print("\n=== 4. 液氮塔增益：范围内塔攻击减速 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.start_wave(1)
td.S.towers.append(make_core())
# 液氮塔 + 机枪塔在范围内
liq = {'kind':'liquid','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,'hp':130,'maxhp':130,'cool':99,'range':4*td.CELL}
gun = {'kind':'gun','c':12,'r':10,'size':2,'x':13*td.CELL,'y':11*td.CELL,'hp':220,'maxhp':220,'cool':0,'range':td.GUN_RANGE,'gears':0}
td.S.towers += [liq, gun]
# 机枪塔在液氮塔 2 格内 → 应获 frost
td.update(0.06)
assert gun.get('frost') is True, "范围内机枪塔应获减速增益"
print("  范围内机枪塔 frost =", gun.get('frost'), "OK")
# 子弹命中应减速
mm = td.spawn_monster('red', x=15*td.CELL, y=11*td.CELL)
td.S.monsters.append(mm)
mm['slow'] = 0
gun['cool'] = 0
# 推进到子弹命中
for _ in range(30):
    td.update(0.05)
    if mm.get('slow',0) > 0:
        break
assert mm.get('slow',0) > 0, "受增益机枪子弹应减速目标"
print("  受增益机枪子弹命中减速: OK, slow", round(mm.get('slow',0),1))

print("\n=== 5. 范围外塔不受减速增益 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.start_wave(1)
td.S.towers.append(make_core())
liq = {'kind':'liquid','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,'hp':130,'maxhp':130,'cool':99,'range':4*td.CELL}
gun_far = {'kind':'gun','c':30,'r':10,'size':2,'x':31*td.CELL,'y':11*td.CELL,'hp':220,'maxhp':220,'cool':0,'range':td.GUN_RANGE,'gears':0}
td.S.towers += [liq, gun_far]
td.update(0.06)
assert gun_far.get('frost') is False, "范围外机枪塔不应获减速增益"
print("  范围外机枪塔 frost =", gun_far.get('frost'), "OK")

print("\n=== 6. 喷火器受液氮增益喷减速火 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.start_wave(1)
td.S.towers.append(make_core())
liq = {'kind':'liquid','c':9,'r':9,'size':2,'x':10*td.CELL,'y':10*td.CELL,'hp':130,'maxhp':130,'cool':99,'range':4*td.CELL}
fl = {'kind':'flamer','c':11,'r':11,'size':2,'x':12*td.CELL,'y':12*td.CELL,'hp':180,'maxhp':180,'cool':0,'range':td.GUN_RANGE,'aim':0.0}
td.S.towers += [liq, fl]
td.update(0.06)
mm = td.spawn_monster('red', x=14*td.CELL, y=12*td.CELL)  # 正右方扇形内
td.S.monsters.append(mm)
mm['slow'] = 0
fl['cool'] = 0
td.update(0.06)
assert fl.get('frost') is True, "喷火器在液氮范围内应获frost"
assert mm.get('slow',0) > 0, "受增益喷火器应喷减速火"
print("  喷火器受增益喷减速火: OK, slow", round(mm.get('slow',0),1))

print("\n=== 全部通过 ===")
