# -*- coding: utf-8 -*-
"""审判塔 + 起吊机 + 10槽位 测试"""
import random, math
import tower_defense as td

random.seed(1)

def reset():
    td.reset_state()
    td.S.mode = 'endless'; td.S.level = None
    td.S.wave = 1
    core = {'kind':'core','c':td.CORE_C,'r':td.CORE_R,'size':2,
            'x':(td.CORE_C+1)*td.CELL,'y':(td.CORE_R+1)*td.CELL,
            'hp':99999,'maxhp':99999,'hp_frac':0.0}
    td.S.towers.append(core)
    return core

print("=== 1. 审判塔定义存在 ===")
assert 'judge' in td.TOWER_DEFS, "缺少审判塔"
assert td.TOWER_DEFS['judge']['size'] == 2, "审判塔应占地2x2"
assert td.JUDGE_MAX == 2, "审判塔最多2座"
print("  审判塔已定义, 占地2x2, 最多2座: OK")

print("\n=== 2. 审判塔全场最多2座 ===")
reset()
td.S.energy = 10000
assert td.place_tower('judge', 10, 10) is True, "第1座应可建"
assert td.place_tower('judge', 14, 10) is True, "第2座应可建"
assert td.place_tower('judge', 18, 10) is False, "第3座应被拒绝"
print("  3座中前2座可建、第3座被拒: OK")

print("\n=== 3. 审判塔蓄力伤害递增 + 转火重置 ===")
reset()
judge = {'kind':'judge','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,
         'hp':td.JUDGE_HP,'maxhp':td.JUDGE_HP,'cool':0,'range':td.JUDGE_RANGE,
         'locks':[],'focuses':0,'judge_t':0.0}
td.S.towers.append(judge)
m = td.spawn_monster('red', x=14*td.CELL, y=11*td.CELL)
m['hp'] = 99999; m['maxhp'] = 99999
td.S.monsters.append(m)
# 攻击一段时间，测伤害递增：早期单次伤害 < 后期单次伤害
hp0 = m['hp']
judge['cool'] = 0
td.update(0.1)   # 让塔锁定并开打
early_dmg = hp0 - m['hp']
# 持续攻击2秒（伤害应明显高于初始）
for _ in range(40):
    judge['cool'] = 0
    td.update(0.05)
# 对比：蓄力后伤害应显著大于初始0.7倍DPS每帧(0.98)
# 每秒攻击20次，2秒内平均伤害显著上升
dmg_after = hp0 - m['hp']
assert dmg_after > 100, f"蓄力后2秒总伤害应>100，实际{dmg_after}"
# 验证伤害递增：把时间拉长到接近3秒满蓄力，单帧伤害应接近21
m2 = td.spawn_monster('red', x=14*td.CELL, y=11*td.CELL)
m2['hp'] = 99999; m2['maxhp'] = 99999
td.S.monsters.append(m2)
# 切到 m2（转火），重置蓄力
judge['locks'] = [m2]; judge['judge_t'] = 0.0; judge['cool'] = 0
hp2 = m2['hp']
td.update(0.05)   # 攻击一帧
first_frame_dmg = hp2 - m2['hp']
assert first_frame_dmg < 5, f"转火后首帧伤害应接近初始(0.98)，实际{first_frame_dmg}"
# 满蓄力帧伤害
for _ in range(70):
    judge['cool'] = 0
    td.update(0.05)
hp3 = m2['hp']
# 平均每帧伤害（满蓄力区间）应接近21
assert (hp2 - hp3) / 70 > 12, f"满蓄力平均每帧伤害应接近21，实际{(hp2-hp3)/70:.2f}"
print("  蓄力伤害递增 + 转火重置为初始: OK")

print("\n=== 4. 审判塔击杀触发爆炸且不触发亡语 ===")
reset()
td.start_wave(1)
judge = {'kind':'judge','c':10,'r':10,'size':2,'x':11*td.CELL,'y':11*td.CELL,
         'hp':td.JUDGE_HP,'maxhp':td.JUDGE_HP,'cool':0,'range':td.JUDGE_RANGE,
         'locks':[],'focuses':0,'judge_t':0.0}
td.S.towers.append(judge)
# 黄色球(复活)：死亡会复活为红，测试审判击杀不触发复活(亡语)
y = td.spawn_monster('yellow', x=13*td.CELL, y=11*td.CELL)
# 让审判锁定黄球，蓄满力后一击必杀（满蓄力单帧21伤，设hp=20）
y['hp'] = 20; y['maxhp'] = 20
td.S.monsters.append(y)
# 旁边放一个红球(2格爆炸范围内)，验证爆炸波及
side = td.spawn_monster('red', x=12.5*td.CELL, y=11*td.CELL)
side['hp'] = 99999; side['maxhp'] = 99999
td.S.monsters.append(side)
judge['locks'] = [y]; judge['judge_t'] = td.JUDGE_RAMP_TIME  # 直接满蓄力
judge['cool'] = 0
n_before = len(td.S.monsters)
td.update(0.05)
# 黄球应被击杀且不复活(无亡语)：死亡后被清除、场上只剩 side(无复活红出现)
assert not y['alive'], "黄球应被审判击杀"
assert len(td.S.monsters) == n_before - 1, \
    f"审判击杀不应触发复活亡语，怪物数{n_before}->{len(td.S.monsters)}（应少1）"
# 侧红球应被爆炸波及掉血
assert side['hp'] < 99999, "审判击杀爆炸应波及周围敌人"
print("  审判击杀不触发复活亡语 + 爆炸波及: OK")

print("\n=== 5. 聚焦塔缩短蓄力时间 + 可叠在审判塔上 ===")
reset()
td.S.energy = 10000
assert td.place_tower('judge', 10, 10) is True
judge = [t for t in td.S.towers if t['kind']=='judge'][0]
assert td.place_tower('focus', 10, 10) is True, "聚焦塔应可叠在审判塔上"
assert judge['focuses'] == 1, "聚焦塔应计入审判塔focuses"
ramp0 = td.JUDGE_RAMP_TIME
ramp1 = td.JUDGE_RAMP_TIME * td.JUDGE_FOCUS_RAMP_FACTOR
assert abs(ramp1 - ramp0*0.7) < 1e-6
print("  聚焦塔可叠审判塔, 蓄力时间×0.7: OK")

print("\n=== 6. 起吊机移除返还30%能量且不引爆地雷 ===")
reset()
td.S.energy = 500
assert td.place_tower('gun', 10, 10) is True   # 机枪60能量
gun = [t for t in td.S.towers if t['kind']=='gun'][0]
before = td.S.energy
ok = td.crane_remove_tower(gun)
assert ok is True, "起吊机应能移除塔"
assert gun.get('removed'), "被起吊机移除的塔应标记removed"
assert td.S.energy == min(td.MAX_ENERGY, before + int(60*0.3)), \
    f"应返还30%能量(int(60*0.3)=18)，{before}->{td.S.energy}"
# 地雷塔被起吊机移除不应引爆
assert td.place_tower('boom_unit', 12, 12) is True
boom = [t for t in td.S.towers if t['kind']=='boom_unit'][0]
mm = td.spawn_monster('red', x=13*td.CELL, y=13*td.CELL)
td.S.monsters.append(mm)
# 起吊机安全移除地雷，不应引爆伤害怪物
hp = mm['hp']
td.crane_remove_tower(boom)
assert boom.get('removed')
assert mm['hp'] == hp, "起吊机移除地雷不应引爆"
# 基地不可被起吊机移除
core = [t for t in td.S.towers if t['kind']=='core'][0]
assert td.crane_remove_tower(core) is False, "基地不可被起吊机移除"
print("  返还30%能量 + 不引爆地雷 + 基地不可移除: OK")

print("\n=== 7. 第10槽位用0快捷键 ===")
g = td.Game.__new__(td.Game)
g.tower_list = list(range(12))
assert g._hotkey(0) == '1'
assert g._hotkey(8) == '9'
assert g._hotkey(9) == '0'
assert g._hotkey(10) == '11'   # 若有更多塔，超9用数字
print("  第10个槽位(索引9)快捷键为0: OK")

print("\n=== 全部通过 ===")
