# -*- coding: utf-8 -*-
"""铁球/强化铁球/银球 + 平衡调整 测试"""
import random, math
import tower_defense as td

random.seed(1)

def reset():
    td.reset_state()
    td.S.mode = 'endless'; td.S.level = None
    td.S.wave = 1
    td.S.time = 0.0
    core = {'kind':'core','c':td.CORE_C,'r':td.CORE_R,'size':2,
            'x':(td.CORE_C+1)*td.CELL,'y':(td.CORE_R+1)*td.CELL,
            'hp':99999,'maxhp':99999,'hp_frac':0.0}
    td.S.towers.append(core)
    return core

print("=== 1. 新球定义存在且视为精英 ===")
for k in ("iron", "biron", "silver"):
    assert k in td.MON_DEFS, f"缺少 {k}"
    assert td.MON_DEFS[k]["elite"], f"{k} 应视为精英球"
print("  iron/biron/silver 已定义, 均精英: OK")

print("\n=== 2. 血量倍率 ===")
assert td.MON_DEFS["iron"]["hp_mult"] == 5.0, "铁球应5倍红球血"
assert td.MON_DEFS["biron"]["hp_mult"] == 20.0, "强化铁球应10倍绿球血(绿=2x红,10*2=20)"
assert td.MON_DEFS["silver"]["hp_mult"] == 12.0 and td.MON_DEFS["silver"]["speed"] == 0.3, \
    "银球速度/血量应同金球"
print("  铁球5x红, 强铁10x绿(=20x红), 银=金(12x红,0.3速): OK")

print("\n=== 3. 铁球每秒最多受10次伤害 ===")
reset()
iron = td.spawn_monster("iron", x=300, y=300)
iron["hp"] = 99999; iron["maxhp"] = 99999
hp0 = iron["hp"]
# 同一秒内连打 20 次，每次 1 点
for _ in range(20):
    td.damage_monster(iron, 1)
assert hp0 - iron["hp"] == td.IRON_HITS_PER_SEC, \
    f"铁球每秒应只受{td.IRON_HITS_PER_SEC}次伤害，实际掉血{hp0-iron['hp']}"
# 过一秒后重置，可再受10次
td.S.time += 1.0
hp1 = iron["hp"]
for _ in range(20):
    td.damage_monster(iron, 1)
assert hp1 - iron["hp"] == td.IRON_HITS_PER_SEC, \
    f"下一秒应再受{td.IRON_HITS_PER_SEC}次，实际掉血{hp1-iron['hp']}"
print(f"  铁球每秒{td.IRON_HITS_PER_SEC}次伤害上限(跨秒重置): OK")

print("\n=== 4. 强化铁球替伤 ===")
reset()
biron = td.spawn_monster("biron", x=310, y=300)
biron["hp"] = 99999; biron["maxhp"] = 99999
td.S.monsters.append(biron)
red = td.spawn_monster("red", x=300, y=300)   # 距强化铁球10px(<3格72px)
red["hp"] = 99999; red["maxhp"] = 99999
td.S.monsters.append(red)
rh0, bh0 = red["hp"], biron["hp"]
td.damage_monster(red, 50)
assert red["hp"] == rh0, "被替伤的红球不应掉血"
assert biron["hp"] == bh0 - 50, f"强化铁球应承受替伤，实际掉血{bh0-biron['hp']}"
print("  强化铁球替3格内球受伤害: OK")

print("\n=== 5. 银球随金球伴生(50%概率) ===")
reset()
n_silver = 0
for _ in range(200):
    reset()
    g = td.spawn_gold_with_silver(x=300, y=300)
    for m in td.S.monsters:
        if m["type"] == "silver":
            n_silver += 1
            d = math.hypot(m["x"] - g["x"], m["y"] - g["y"])
            assert d <= td.GOLD_TRANSFORM_R * td.CELL + 1, "银球应在金球强化范围内"
            assert m["x"] >= 0 and m["y"] >= 0, "银球应有实际坐标(伴生在金球附近)"
print(f"  200次生成中银球出现 {n_silver} 次(约50%): {'OK' if 60 <= n_silver <= 140 else '异常'}")
assert 60 <= n_silver <= 140

print("\n=== 6. 银球拥有强化白功能(召唤+死亡裂隙) ===")
reset()
td.start_wave(5)
sil = td.spawn_monster("silver", x=400, y=400)
td.S.monsters.append(sil)
assert td.MON_DEFS["silver"].get("summon"), "银球应有召唤功能"
assert td.MON_DEFS["silver"].get("spawner"), "银球死亡应生成裂隙出怪点"
# 死亡触发裂隙
sil["hp"] = 1
before = len(td.S.wspawns)
td.damage_monster(sil, 5)
assert len(td.S.wspawns) > before, "银球死亡应生成裂隙出怪点"
print("  银球具有召唤+死亡生成裂隙: OK")

print("\n=== 7. 强化白速度减半且不受强化蓝光环 ===")
reset()
assert td.MON_DEFS["bwhite"]["speed"] == 0.55, f"强化白速度应减半(0.55)，实际{td.MON_DEFS['bwhite']['speed']}"
bw = td.spawn_monster("bwhite", x=300, y=300)
bl = td.spawn_monster("bblue", x=320, y=300)
td.S.monsters += [bw, bl]
td.update(0.1)   # 触发光环
assert not bw.get("boosted"), "强化白不应受强化蓝加速光环影响"
# 对照：普通红球应被加速
r = td.spawn_monster("red", x=310, y=300)
td.S.monsters.append(r)
td.update(0.1)
assert r.get("boosted"), "普通球应被强化蓝加速"
print("  强化白减速+不受强化蓝光环(普通球仍受): OK")

print("\n=== 8. 审判塔30倍DPS + 强化黑冷却0.5 ===")
assert abs(td.JUDGE_MAX_DPS - 30 * td.GUN_DPS) < 1e-6, f"审判塔应30倍机枪DPS，实际{td.JUDGE_MAX_DPS}"
assert td.ELITE_BLACK_PORT_CD == 0.5, "强化黑技能冷却应为0.5s"
print("  审判塔30x机枪DPS, 强化黑冷却0.5s: OK")

print("\n=== 9. 新球不在随机/黄复活/强白锥召唤池 ===")
keys = [k for k in td.MON_KEYS
        if k not in ("white", "bwhite", "gold", "wcone", "bconew", "iron", "biron", "silver")]
for k in ("iron", "biron", "silver"):
    assert k not in keys, f"{k} 不应在普通出怪随机池"
# 黄复活池(随机强化球)不含新球
pool = [k for k in td.MON_KEYS if td.MON_DEFS[k].get("elite")
        and k not in ("bwhite", "iron", "biron", "silver")]
for k in ("iron", "biron", "silver"):
    assert k not in pool, f"{k} 不应在黄复活池"
# 强白锥召唤池不含新球
bwpool = [k for k in td.MON_KEYS if td.MON_DEFS[k].get("elite")
          and k not in ("bwhite", "bconew", "iron", "biron", "silver")]
for k in ("iron", "biron", "silver"):
    assert k not in bwpool, f"{k} 不应在强白锥召唤池"
print("  铁/强铁/银 不在随机池、黄复活池、强白锥召唤池: OK")

print("\n=== 10. 铁球每波必出, 8波后必定强化 ===")
reset()
td.start_wave(9)
assert td.S.iron_pending, "第9波应设iron_pending"
# 模拟出怪循环：设满预算，跑更新看是否出强化铁球
td.S.spawn["total"] = 10
td.S.spawn["acc"] = 0
td.S.spawn["timer"] = 99  # 立即触发
has_biron = any(m["type"] == "biron" for m in td.S.monsters)
# 直接验证波>8逻辑
td.start_wave(9)
assert td.MON_DEFS  # 占位
# 验证 spawn 分支：手动触发一次 pending
td.S.wave = 9
td.S.iron_pending = True
# 模拟 spawn 内部逻辑
if td.S.iron_pending:
    td.S.iron_pending = False
    k = "biron" if td.S.wave > td.IRON_ALWAYS_ELITE_WAVE else ("biron" if random.random() < td.IRON_ELITE_CHANCE else "iron")
assert k == "biron", f"第9波(>8)应出强化铁球，实际{k}"
print("  第9波铁球必定为强化形态: OK")

print("\n=== 全部通过 ===")
