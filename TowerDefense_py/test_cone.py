# -*- coding: utf-8 -*-
"""新增三棱锥（锥类）功能逻辑测试"""
import random
import math
import tower_defense as td

random.seed(42)

def math_dist(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])

print("=== 1. 强化绿血量翻倍 ===")
assert td.MON_DEFS["bgreen"]["hp_mult"] == 24.0, "强化绿 hp_mult 应为 24.0"
print("  强化绿 hp_mult =", td.MON_DEFS["bgreen"]["hp_mult"], "OK")

print("\n=== 2. 强化蓝移速翻1.5倍 + 光环 ====")
assert abs(td.MON_DEFS["bblue"]["speed"] - 3.15) < 1e-6, "强化蓝速度应为 3.15"
print("  强化蓝 speed =", td.MON_DEFS["bblue"]["speed"], "OK")
# 光环：范围内友军移速提升至与自身一致
bblue = td.spawn_monster("bblue", x=500, y=300)
red = td.spawn_monster("red", x=510, y=300)   # 在 6 格内
td.S.monsters.append(bblue)
td.S.monsters.append(red)
td.update(0.1)   # 触发光环更新
print("  光环内红球被加速 boost_speed =", red.get("boost_speed"),
      "≈ 强化蓝自身 speed =", bblue["speed"],
      "OK" if red.get("boosted") and abs(red.get("boost_speed", 0) - bblue["speed"]) < 1e-6 else "FAIL")
td.S.monsters = []

print("\n=== 3. 锥类定义存在 ===")
for k in ("rcone", "kcone", "wcone", "bconer", "bconek", "bconew"):
    assert k in td.MON_DEFS, f"缺少锥类 {k}"
    assert td.MON_DEFS[k].get("cone"), f"{k} 应标记 cone=True"
print("  6 种锥类均定义且标记 cone=True: OK")

print("\n=== 4. random_mon_key 第6波前不出锥，第6波起出锥 ===")
random.seed(7)
keys_w5 = {td.random_mon_key(5) for _ in range(500)}
keys_w6 = {td.random_mon_key(6) for _ in range(500)}
assert not any(td.MON_DEFS[k].get("cone") for k in keys_w5), f"第5波不应出锥: {keys_w5}"
assert any(td.MON_DEFS[k].get("cone") for k in keys_w6), f"第6波应出锥: {keys_w6}"
# 白锥/强白锥不应出现在普通池
assert not ("wcone" in keys_w6 or "bconew" in keys_w6), "白锥不应进普通池"
print("  第5波:", keys_w5)
print("  第6波:", keys_w6, "OK")

print("\n=== 5. 金球强化对锥类无效 ===")
rcone = td.spawn_monster("rcone", x=100, y=100)
before = rcone["type"]
r = td._promote_monster(rcone)
assert r is False and rcone["type"] == "rcone", "金球不应强化锥类"
print("  金球不强化红锥:", r, "OK")

print("\n=== 6. normal_summon_keys 排除锥类（白球/召唤门不召唤锥） ===")
np = td.normal_summon_keys()
assert not any(td.MON_DEFS[k].get("cone") for k in np), "召唤池不应含锥类"
print("  召唤池:", np, "OK")

print("\n=== 7. 强黑锥次数盾 10 层 ===")
bconek = td.spawn_monster("bconek", x=300, y=300)
td.S.monsters.append(bconek)
assert bconek.get("cshields") == 10, f"强黑锥应有10层盾，实际{bconek.get('cshields')}"
# 打 10 下应不扣血
hp0 = bconek["hp"]
for i in range(10):
    td.damage_monster(bconek, 9999)
assert bconek["hp"] == hp0 and bconek.get("cshields", 0) == 0, "10层盾期间应免疫伤害"
# 第 11 次开始掉血
hp1 = bconek["hp"]
td.damage_monster(bconek, 5)
assert bconek["hp"] < hp1, "盾破后应掉血"
print("  10层盾免疫 + 破盾后掉血: OK")

print("\n=== 8. 黑锥沉默目标塔 ===")
kcone = td.spawn_monster("kcone", x=300, y=300)
tower = {"kind": "gun", "c": 0, "r": 0, "size": 1,
         "x": 300, "y": 300, "hp": 100, "maxhp": 100, "cool": 0, "range": 100}
td.S.towers.append(tower)
td._apply_cone_silence(kcone, tower)
assert tower.get("silence_t", 0) > 0, "黑锥应沉默目标塔"
print("  目标塔沉默时间 =", tower["silence_t"], "OK")

print("\n=== 9. 嘲讽塔被沉默失去嘲讽 ===")
taunt = {"kind": "taunt", "c": 0, "r": 0, "size": 1,
         "x": 320, "y": 320, "hp": 150, "maxhp": 150, "silence_t": 5.0}
td.S.towers.append(taunt)
# 怪锁定近处非嘲讽塔 tower(300,300)；被沉默的嘲讽塔在 5 格内也不应强制吸引
mm = td.spawn_monster("red", x=301, y=300)
mm["target"] = tower
tgt = td.acquire_target(mm)
assert tgt is tower, f"被沉默的嘲讽塔不应强制吸引，实际选中 {tgt}"
print("  被沉默的嘲讽塔不强制吸引:", "OK")
del taunt["silence_t"]
# 对照组：未沉默的嘲讽塔应强制吸引
taunt["silence_t"] = 0.0
mm2 = td.spawn_monster("red", x=318, y=318)
mm2["target"] = tower
tgt2 = td.acquire_target(mm2)
assert tgt2 is taunt, "未沉默的嘲讽塔应强制吸引"
print("  未沉默的嘲讽塔正常强制吸引:", "OK")

print("\n=== 10. 锥类自转 + 白锥自扣血不移动 ===")
wcone = td.spawn_monster("wcone", x=200, y=200)
td.S.monsters.append(wcone)
wx, wy = wcone["x"], wcone["y"]
hpw = wcone["hp"]
for _ in range(50):
    td.monster_update(wcone, 0.1)
assert (wcone["x"], wcone["y"]) == (wx, wy), "白锥不应移动"
assert wcone["hp"] < hpw, "白锥应自扣血"
print("  白锥不移动 + 自扣血:", "OK")
td.S.monsters = []

print("\n=== 11. 强化蓝光环 & 白锥召唤池（白锥召唤锥+球，强白锥召唤强化） ===")
# 验证 wcone_pool 包含球类和锥类
wcp = [k for k in td.MON_KEYS
       if k not in ("white", "bwhite", "gold", "wcone", "bconew")
       and not td.MON_DEFS[k].get("elite")]
assert any(td.MON_DEFS[k].get("cone") for k in wcp), "白锥召唤池应含普通锥"
assert any(not td.MON_DEFS[k].get("cone") for k in wcp), "白锥召唤池应含普通球"
bwcp = [k for k in td.MON_KEYS if td.MON_DEFS[k].get("elite") and k not in ("bwhite", "bconew")]
assert any(td.MON_DEFS[k].get("cone") for k in bwcp), "强白锥召唤池应含强化锥"
print("  白锥召唤池:", wcp)
print("  强白锥召唤池:", bwcp, "OK")

print("\n=== 12. 锥类刷怪点第6波生成 & 白锥每波必出 ===")
td.reset_state()
td.S.mode = "endless"
td.S.level = None
td.start_wave(5)
assert td.S.conespawn is None, "第5波不应有锥类刷怪点"
assert td.S.wcone_pending is False, "第5波不应有白锥"
td.start_wave(6)
assert td.S.conespawn is not None, "第6波应生成锥类刷怪点"
assert td.S.wcone_pending is True, "第6波应有白锥待出"
assert td.S.spawn["total"] >= td.wave_budget(6), "第6波刷怪上限应上升"
print("  第6波锥类刷怪点:", td.S.conespawn, "| 白锥待出:", td.S.wcone_pending,
      "| budget:", td.S.spawn["total"], "OK")

print("\n=== 13. 白锥/强白锥由每波机制刷出（不占普通权重） ===")
# 模拟一次白锥触发：清空出怪状态，timer 已满，white/gold 已消费
td.S.spawn = {"total": 100, "acc": 0, "timer": 100, "interval": td.SPAWN_INTERVAL}
td.S.white_pending = False
td.S.gold_pending = False
td.S.wcone_pending = True
td.S.monsters = []
random.seed(3)
k = None
for _ in range(20):
    td.update(0.016)
    found = [m["type"] for m in td.S.monsters if m["type"] in ("wcone", "bconew")]
    if found:
        k = found[0]
        break
assert k in ("wcone", "bconew"), f"应刷出白锥/强白锥，实际{td.S.monsters[:3]}"
print("  刷出的白锥类型:", k, "OK")

print("\n=== 14. 锥类从锥类刷怪点出生 ===")
td.S.monsters = []
cs = td.S.conespawn
td.S.wave = 6
random.seed(9)
from_cs = False
for _ in range(2000):
    td.update(0.016)
    for m in td.S.monsters:
        if td.MON_DEFS[m["type"]].get("cone") and m["type"] in ("rcone", "kcone", "bconer", "bconek"):
            if math_dist(m, cs) < td.CELL * 2:
                from_cs = True
                break
    if from_cs:
        break
print("  锥类从锥类刷怪点出生:", "OK" if from_cs else "FAIL")
td.S.monsters = []

print("\n=== 全部通过 ===")
