# -*- coding: utf-8 -*-
"""护卫球 + 医疗塔改版 + 白棱30秒 + 嘲讽/矩阵血量翻倍 测试"""
import random, math
import tower_defense as td

random.seed(1)

def reset():
    td.reset_state()
    td.S.mode = 'endless'; td.S.level = None
    td.S.wave = 5
    td.S.time = 0.0
    core = {'kind':'core','c':td.CORE_C,'r':td.CORE_R,'size':2,
            'x':(td.CORE_C+1)*td.CELL,'y':(td.CORE_R+1)*td.CELL,
            'hp':99999,'maxhp':99999,'hp_frac':0.0}
    td.S.towers.append(core)
    return core

print("=== 1. 护卫球定义 ===")
assert 'guard' in td.MON_DEFS, "缺少护卫球"
g = td.MON_DEFS['guard']
assert g['atk'] == td.MON_DEFS['black']['atk'] * 3, f"攻击应为黑球3倍(42)，实际{g['atk']}"
assert g['hp_mult'] == td.MON_DEFS['green']['hp_mult'] * 5, f"血量应为绿球5倍(10)，实际{g['hp_mult']}"
assert g['elite'] and g.get('guard'), "护卫球应精英且标记guard"
print(f"  护卫球: 攻击{g['atk']}(=黑球3倍), 血量×{g['hp_mult']}(=绿球5倍): OK")

print("\n=== 2. 护卫球首次冲撞塔 + 生成1-3只强化红球 ===")
reset()
tower = {'kind':'taunt','c':15,'r':15,'size':1,'x':15.5*td.CELL,'y':15.5*td.CELL,
         'hp':100000,'maxhp':100000,'base_maxhp':100000,'cool':0}
td.S.towers.append(tower)
gd = td.spawn_monster('guard', x=15.5*td.CELL+2, y=15.5*td.CELL)  # 紧贴塔
td.S.monsters.append(gd)
hp0 = tower['hp']
td.update(0.1)   # 触发首次攻击（护卫球冲撞 + 生成的强化红球也可能冲撞）
n_bred = sum(1 for m in td.S.monsters if m['type']=='bred')
assert tower['hp'] <= hp0 - td.GUARD_RAM_DMG, \
    f"护卫球冲撞应至少造成{td.GUARD_RAM_DMG}伤害，实际掉血{hp0-tower['hp']}"
assert 1 <= n_bred <= 3, f"应生成1-3只强化红球，实际{n_bred}"
assert gd.get('guard_rammed'), "护卫球应标记已冲撞"
print(f"  冲撞≥{td.GUARD_RAM_DMG}伤害(含强化红球额外冲撞) + 生成{n_bred}只强化红球: OK")

print("\n=== 3. 护卫球近塔加速 ===")
reset()
tower = {'kind':'gun','c':15,'r':15,'size':1,'x':15.5*td.CELL,'y':15.5*td.CELL,
         'hp':100000,'maxhp':100000,'base_maxhp':100000,'cool':0,
         'range':td.GUN_RANGE,'gears':0}
td.S.towers.append(tower)
# 在 GUARD_BOOST_RANGE 内但未到 reach
gd = td.spawn_monster('guard', x=15.5*td.CELL, y=15.5*td.CELL - 5*td.CELL)
td.S.monsters.append(gd)
# 距离5格 < GUARD_BOOST_RANGE(6格)，应加速
y0 = gd['y']
td.update(0.05)
moved = abs(gd['y'] - y0)
# 未加速时的位移 = speed*CELL*dt = 1.1*wave_speed*24*0.05
base_step = gd['speed'] * td.CELL * 0.05
assert moved > base_step * 1.5, f"近塔应大幅加速，位移{moved} vs 基础{base_step}"
print(f"  近塔加速: 位移{moved:.1f} > 基础{base_step:.1f}: OK")

print("\n=== 4. 医疗塔：提升150%生命上限 + 每秒5%回血 ===")
reset()
healer = {'kind':'healer','c':12,'r':12,'size':2,'x':13*td.CELL,'y':13*td.CELL,
          'hp':110,'maxhp':110,'base_maxhp':110,'cool':0,'range':4*td.CELL}
td.S.towers.append(healer)
gun = {'kind':'gun','c':14,'r':12,'size':1,'x':14.5*td.CELL,'y':12.5*td.CELL,
       'hp':220,'maxhp':220,'base_maxhp':220,'cool':0,
       'range':td.GUN_RANGE,'gears':0}
td.S.towers.append(gun)
# 枪塔受损
gun['hp'] = 100
td.update(0.1)
expected_max = 220 + 220*td.HEAL_MAXHP_BONUS   # 220 + 330 = 550
assert abs(gun['maxhp'] - expected_max) < 1e-6, f"医疗塔应提升150%生命上限，实际{gun['maxhp']} vs {expected_max}"
# 每秒5%回血：跑1秒，应回约5%*max
hp_before = gun['hp']
for _ in range(20):
    td.update(0.05)
heal = gun['hp'] - hp_before
expected_heal = gun['maxhp'] * td.HEAL_PCT_RATE * 1.0
assert abs(heal - expected_heal) < expected_heal*0.2, f"每秒应回约5%最大生命({expected_heal:.1f})，实际{heal:.1f}"
print(f"  医疗塔: 上限{gun['maxhp']}(+150%), 1秒回血{heal:.1f}(≈5%/{expected_heal:.1f}): OK")

print("\n=== 5. 医疗塔移除后上限还原 ===")
reset()
healer = {'kind':'healer','c':12,'r':12,'size':2,'x':13*td.CELL,'y':13*td.CELL,
          'hp':110,'maxhp':110,'base_maxhp':110,'cool':0,'range':4*td.CELL}
td.S.towers.append(healer)
gun = {'kind':'gun','c':14,'r':12,'size':1,'x':14.5*td.CELL,'y':12.5*td.CELL,
       'hp':220,'maxhp':220,'base_maxhp':220,'cool':0,
       'range':td.GUN_RANGE,'gears':0}
td.S.towers.append(gun)
td.update(0.1)
assert gun['maxhp'] > 220
healer['removed'] = True
td.update(0.1)
assert abs(gun['maxhp'] - 220) < 1e-6, f"医疗塔移除后上限应还原220，实际{gun['maxhp']}"
print(f"  医疗塔移除后上限还原为{gun['maxhp']}: OK")

print("\n=== 6. 嘲讽塔与矩阵塔血量翻2倍 ===")
assert td.TOWER_DEFS['taunt']['hp'] == 640, f"嘲讽塔应翻2倍为640，实际{td.TOWER_DEFS['taunt']['hp']}"
assert td.MATRIX_BASE_HP == 320, f"矩阵基础血量应翻2倍为320，实际{td.MATRIX_BASE_HP}"
print("  嘲讽塔640, 矩阵320(均翻2倍): OK")

print("\n=== 7. 白棱/强化白棱存活约30秒 ===")
reset()
td.start_wave(5)
w = td.spawn_monster('wcone', x=300, y=300)
w['hp'] = w['maxhp']
h0 = w['hp']
td.monster_update(w, 1.0)   # 过1秒
drained = h0 - w['hp']
expected = w['maxhp'] / td.WCONE_LIFE_TIME
assert abs(drained - expected) < 0.5, f"每秒应掉maxhp/30(={expected:.1f})，实际掉{drained:.1f}"
# 强化白锥同样
bw = td.spawn_monster('bconew', x=320, y=320)
bw['hp'] = bw['maxhp']
hb = bw['hp']
td.monster_update(bw, 1.0)
assert abs(hb - bw['hp'] - bw['maxhp']/td.WCONE_LIFE_TIME) < 0.5, "强化白锥也应30秒存活"
print(f"  白棱每秒掉{expected:.1f}(=maxhp/30), 约30秒消散: OK")

print("\n=== 全部通过 ===")
