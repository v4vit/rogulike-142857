# -*- coding: utf-8 -*-
"""新增塔（聚焦/迷你核弹/喷火器/发射井/防御矩阵）+ 光棱塔改动 + 强黑锥10层盾 测试"""
import random, math
import tower_defense as td

random.seed(1)

print("=== 1. 强黑锥次数盾 10 层 ===")
b = td.spawn_monster("bconek", x=300, y=300)
td.S.monsters.append(b)
assert b.get("cshields") == 10, f"强黑锥应有10层盾，实际{b.get('cshields')}"
hp0 = b["hp"]
for _ in range(10):
    td.damage_monster(b, 9999)
assert b["hp"] == hp0 and b.get("cshields", 0) == 0, "10层盾期间应免疫"
td.damage_monster(b, 5)
assert b["hp"] < hp0, "破盾后应掉血"
print("  10层盾免疫+破盾后掉血: OK")
td.S.monsters = []

print("\n=== 2. 新塔定义存在 ===")
for k in ("focus", "mininuke", "flamer", "silode", "matrix"):
    assert k in td.TOWER_DEFS, f"缺少塔 {k}"
print("  5 座新塔已定义: OK")

print("\n=== 3. 光棱塔多目标锁定（一直锁定） ===")
td.reset_state()
td.S.mode = 'endless'; td.S.level = None
core = {'kind':'core','c':td.CORE_C,'r':td.CORE_R,'size':2,'x':(td.CORE_C+1)*td.CELL,'y':(td.CORE_R+1)*td.CELL,'hp':99999,'maxhp':99999,'hp_frac':0.0}
td.S.towers.append(core)
prism = {'kind':'prism','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,'hp':160,'maxhp':160,'cool':0,'range':6*td.CELL,'locks':[],'focuses':0}
td.S.towers.append(prism)
# 放 3 只怪在射程内
m1 = td.spawn_monster('red', x=13*td.CELL, y=11*td.CELL)
m2 = td.spawn_monster('red', x=14*td.CELL, y=12*td.CELL)
m3 = td.spawn_monster('red', x=15*td.CELL, y=11*td.CELL)
td.S.monsters += [m1, m2, m3]
# 默认 1 目标
td.update(0.1)
assert len(prism['locks']) == 1, f"默认应锁定1目标，实际{len(prism['locks'])}"
print("  默认锁定1目标:", len(prism['locks']), "OK")
# 加2个聚焦塔 → 3目标
prism['focuses'] = 2
td.update(0.1)
assert len(prism['locks']) == 3, f"2聚焦应锁定3目标，实际{len(prism['locks'])}"
print("  2个聚焦塔后锁定3目标:", len(prism['locks']), "OK")
# 验证一直锁定：让 m1 移出射程，locks 应减少但其他保持
m1['x'] = 30*td.CELL  # 出射程
td.update(0.1)
assert len(prism['locks']) == 2, f"目标出射程后应剩2锁定，实际{len(prism['locks'])}"
print("  目标出射程后释放并保持其余锁定:", len(prism['locks']), "OK")
# 验证3帧攻击造成伤害
m2_hp = m2['hp']
td.update(0.1)  # 约2帧
prism['cool'] = 0
td.update(0.05)
assert m2['hp'] < m2_hp, "光棱塔应造成伤害"
print("  光棱塔攻击造成伤害: OK")

print("\n=== 4. 迷你核弹核爆 + 辐射 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.start_wave(1)
td.S.towers.append(core)
mk = {'kind':'mininuke','c':20,'r':20,'size':1,'x':20.5*td.CELL,'y':20.5*td.CELL,'hp':50,'maxhp':50,'cool':0}
td.S.towers.append(mk)
# 放一只怪触碰它
mm = td.spawn_monster('red', x=20.5*td.CELL, y=20.5*td.CELL)
td.S.monsters.append(mm)
before = mm['hp']
td.update(0.1)
# 触碰触发核爆
assert mk.get('removed'), "迷你核弹触碰应引爆"
assert len(td.S.radiations) == 1, f"应留1个辐射区，实际{len(td.S.radiations)}"
print("  触碰引爆 + 留辐射区: OK, 辐射区数", len(td.S.radiations))
# 辐射区持续伤害
mm2 = td.spawn_monster('red', x=21*td.CELL, y=21*td.CELL)
td.S.monsters.append(mm2)
hp2 = mm2['hp']
for _ in range(20):
    td.update(0.05)
assert mm2['hp'] < hp2, "核辐射区域应造成持续伤害"
print("  核辐射区域持续伤害: OK")

print("\n=== 5. 喷火器 AOE + 液氮减速火 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.S.towers.append(core)
fl = {'kind':'flamer','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,'hp':180,'maxhp':180,'cool':0,'range':td.GUN_RANGE}
td.S.towers.append(fl)
# 2只怪在射程内
a = td.spawn_monster('red', x=13*td.CELL, y=11*td.CELL)
bb = td.spawn_monster('red', x=14*td.CELL, y=12*td.CELL)
td.S.monsters += [a, bb]
ha, hb = a['hp'], bb['hp']
fl['cool'] = 0
td.update(0.1)
assert a['hp'] < ha and bb['hp'] < hb, "喷火器应对射程内所有敌人AOE伤害"
print("  喷火器AOE伤害: OK")
# 旁边放液氮塔 → 减速火（液氮塔需在喷火器4格增益范围内）
liq = {'kind':'liquid','c':10,'r':12,'size':2,'x':11*td.CELL,'y':13*td.CELL,'hp':130,'maxhp':130,'cool':0,'range':4*td.CELL}
td.S.towers.append(liq)
a['slow'] = 0; bb['slow'] = 0
fl['cool'] = 0
td.update(0.1)
assert a.get('slow',0) > 0, "有液氮塔时应喷减速火"
print("  旁有液氮塔喷减速火: OK, 减速时间", round(a.get('slow',0),2))

print("\n=== 6. 发射井锁定 + 唯一限制 + 射导弹 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.S.towers.append(core)
silo = {'kind':'silode','c':5,'r':5,'size':3,'x':6.5*td.CELL,'y':6.5*td.CELL,'hp':220,'maxhp':220,'cool':0,'range':14*td.CELL,'lock_target':None,'gears':0}
td.S.towers.append(silo)
# 锁定目标点
silo['lock_target'] = (30*td.CELL, 20*td.CELL)
# 验证唯一限制
other = {'kind':'silode','c':20,'r':20,'size':3,'x':21.5*td.CELL,'y':21.5*td.CELL,'hp':220,'maxhp':220,'cool':0,'range':14*td.CELL,'lock_target':None,'gears':0}
td.S.towers.append(other)
# 应能放置两个（直接append不受限），但place_tower应拒绝第二个
td.S.towers.remove(other)
# 测试 place_tower 唯一限制
td.S.energy = 1000
ok = td.place_tower('silode', 20, 20)
assert ok is False, "第二个发射井应被拒绝"
print("  发射井全局唯一限制: OK")

print("\n=== 7. 防御矩阵弱嘲讽 + 血量叠加 ===")
td.reset_state(); td.S.mode='endless'; td.S.level=None
td.S.towers.append(core)
m1x = {'kind':'matrix','c':15,'r':15,'size':1,'x':15.5*td.CELL,'y':15.5*td.CELL,'hp':td.MATRIX_BASE_HP,'maxhp':td.MATRIX_BASE_HP,'cool':0}
m2x = {'kind':'matrix','c':16,'r':16,'size':1,'x':16.5*td.CELL,'y':16.5*td.CELL,'hp':td.MATRIX_BASE_HP,'maxhp':td.MATRIX_BASE_HP,'cool':0}
td.S.towers += [m1x, m2x]
# 更新血量叠加：2个矩阵 → 上限 MATRIX_BASE_HP + MATRIX_HP_PER_MATRIX（2026-08-20 矩阵基础血量已翻倍）
td.update(0.1)
expected = td.MATRIX_BASE_HP + td.MATRIX_HP_PER_MATRIX
assert m1x['maxhp'] == expected and m2x['maxhp'] == expected, f"2矩阵上限应{expected}，实际{m1x['maxhp']}"
print(f"  2个矩阵上限叠加到{expected}: OK")
# 弱嘲讽：4格内的怪被矩阵吸引
mm3 = td.spawn_monster('red', x=16*td.CELL, y=16*td.CELL)  # 距m2x约1格
tgt = td.acquire_target(mm3)
assert tgt in (m1x, m2x), "4格内怪应被矩阵吸引"
print("  防御矩阵弱嘲讽吸引4格内怪: OK")

print("\n=== 全部通过 ===")
