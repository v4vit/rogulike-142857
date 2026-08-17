#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肉鸽试炼 —— 图形界面版 (鼠标操作)
基于 roguelite.py 的游戏逻辑, 用 Tkinter 实现纯鼠标交互界面.
运行: python roguelite_gui.py  (打包 exe 时以此为入口)
"""

import random
import sys
import os

import tkinter as tk
from tkinter import font as tkfont

# 复用文字版的游戏逻辑
import roguelite as L

# ============================================================
# 主题配色 (Tkinter 用色值)
# ============================================================
COLOR_BG      = "#1e1e2e"   # 深蓝紫背景
COLOR_PANEL   = "#2a2a3e"   # 面板
COLOR_PANEL2  = "#35354d"
COLOR_BORDER  = "#4a4a6a"
COLOR_TEXT     = "#e6e6f0"
COLOR_SUB      = "#9a9ab0"
COLOR_ACCENT   = "#c792ea"   # 紫色强调
COLOR_HP       = "#f7768e"   # 生命红
COLOR_ENERGY   = "#7dcfff"   # 能量蓝
COLOR_GOLD     = "#e0af68"   # 金币金
COLOR_OK       = "#9ece6a"   # 绿色
COLOR_BAD      = "#f7768e"
COLOR_CARD     = "#31314a"   # 卡牌底色
COLOR_CARD_HL  = "#c792ea"   # 卡牌高亮
COLOR_BTN      = "#3b3b55"
COLOR_BTN_HOV  = "#4a4a6a"
COLOR_SELECT   = "#7aa2f7"

NODE_COLOR = {
    "monster":  COLOR_BAD,
    "elite":    "#ff9e64",
    "treasure": COLOR_GOLD,
    "event":    "#7aa2f7",
}

FONT_MAIN = ("Microsoft YaHei UI", 11)
FONT_TITLE = ("Microsoft YaHei UI", 16, "bold")
FONT_BIG = ("Microsoft YaHei UI", 20, "bold")
FONT_MONO = ("Consolas", 12)


class App:
    def __init__(self, root):
        self.root = root
        root.title("⚔ 肉鸽试炼 · Roguelite Arena")
        root.configure(bg=COLOR_BG)
        root.geometry("900x680")
        root.minsize(820, 620)

        self.rng = random.Random()
        self.game = L.Game(self.rng)

        # 战斗引用
        self.combat = None
        self.selected_target = None
        self.battle_log = []

        self._build_layout()
        self.show_menu()

    # =========================================================
    # 布局
    # =========================================================
    def _build_layout(self):
        # 顶部状态栏
        self.status_bar = tk.Frame(self.root, bg=COLOR_PANEL, height=40)
        self.status_bar.pack(side="top", fill="x")
        self.status_bar.pack_propagate(False)
        self.status_label = tk.Label(self.status_bar, bg=COLOR_PANEL, fg=COLOR_TEXT,
                                     font=FONT_MAIN, anchor="w", padx=12)
        self.status_label.pack(fill="both", expand=True)

        # 中央内容区 (切换不同页面)
        self.content = tk.Frame(self.root, bg=COLOR_BG)
        self.content.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # 底部操作区
        self.action_bar = tk.Frame(self.root, bg=COLOR_PANEL, height=56)
        self.action_bar.pack(side="bottom", fill="x")
        self.action_bar.pack_propagate(False)
        self.action_inner = tk.Frame(self.action_bar, bg=COLOR_PANEL)
        self.action_inner.pack(fill="both", expand=True, padx=8, pady=6)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _clear_actions(self):
        for w in self.action_inner.winfo_children():
            w.destroy()

    def _btn(self, parent, text, cmd, color=COLOR_BTN, fg=COLOR_TEXT, font=FONT_MAIN,
             width=None, padx=12, pady=6):
        b = tk.Button(parent, text=text, command=cmd, bg=color, fg=fg,
                      activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                      relief="flat", font=font, bd=0, cursor="hand2", padx=padx, pady=pady)
        if width:
            b.configure(width=width)
        b.pack(side="left", padx=4, pady=2)
        # hover 效果
        b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
        b.bind("<Leave>", lambda e, w=b, c=color: w.configure(bg=c))
        return b

    def _label(self, text, parent=None, fg=COLOR_TEXT, font=FONT_MAIN, bg=COLOR_BG):
        p = parent or self.content
        return tk.Label(p, text=text, bg=bg, fg=fg, font=font, justify="left", anchor="w")

    def _panel(self, parent=None, bg=COLOR_PANEL):
        p = parent or self.content
        f = tk.Frame(p, bg=bg, highlightbackground=COLOR_BORDER, highlightthickness=1)
        return f

    def _update_status(self):
        g = self.game
        txt = (f"第 {g.floor} 层    "
               f"❤ {g.hp}/{g.max_hp}    "
               f"💰 {g.gold}")
        if g.relics:
            txt += "    ◆ " + "  ".join(L.RELIC_LIB[r]["name"] for r in g.relics)
        self.status_label.configure(text=txt)

    # =========================================================
    # 主菜单
    # =========================================================
    def show_menu(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()

        wrap = tk.Frame(self.content, bg=COLOR_BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="⚔ 肉 鸽 试 炼", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_BIG).pack(pady=(0, 4))
        tk.Label(wrap, text="Roguelite Arena", bg=COLOR_BG, fg=COLOR_SUB,
                 font=FONT_MAIN).pack(pady=(0, 24))

        for text, cmd in [
            ("开始游戏", self.start_new),
            ("卡牌图鉴", self.show_card_codex),
            ("怪物图鉴", self.show_monster_codex),
            ("遗物图鉴", self.show_relic_codex),
        ]:
            b = tk.Button(wrap, text=text, command=cmd, bg=COLOR_BTN, fg=COLOR_TEXT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                          relief="flat", font=("Microsoft YaHei UI", 13), bd=0,
                          cursor="hand2", width=18, pady=8)
            b.pack(pady=5)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    def start_new(self):
        seed = "".join(random.choice("0123456789abcdef") for _ in range(6))
        self.rng = random.Random(seed)
        self.game = L.Game(self.rng)
        self.game.apply_relic_effects()
        self.show_intro()

    def show_intro(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        self._show_node_legend()
        self._btn(self.action_inner, "开始冒险 ▶", self.begin_floor,
                  color=COLOR_OK, font=FONT_TITLE, padx=24, pady=8)

    def _show_node_legend(self):
        wrap = tk.Frame(self.content, bg=COLOR_BG)
        wrap.pack(expand=True)
        tk.Label(wrap, text="每一层有若干行路线, 点击节点向前推进", bg=COLOR_BG,
                 fg=COLOR_TEXT, font=FONT_MAIN).pack(pady=8)
        for key in ["monster", "elite", "treasure", "event"]:
            row = tk.Frame(wrap, bg=COLOR_BG)
            row.pack(pady=3)
            tk.Label(row, text=L.node_icon(key), bg=COLOR_BG,
                     fg=NODE_COLOR[key], font=("Consolas", 16)).pack(side="left", padx=6)
            tk.Label(row, text=f"  {L.NODE_LABEL[key]}", bg=COLOR_BG,
                     fg=COLOR_TEXT, font=FONT_MAIN).pack(side="left")
            desc = {
                "monster": "普通战斗, 温和的成长",
                "elite": "高难战斗, 丰厚奖励",
                "treasure": "丰厚的金币与卡牌",
                "event": "抉择与机缘",
            }[key]
            tk.Label(row, text=desc, bg=COLOR_BG, fg=COLOR_SUB,
                     font=FONT_MAIN).pack(side="left", padx=12)

    # =========================================================
    # 地图
    # =========================================================
    def begin_floor(self):
        self.game.floor_map = L.generate_floor(self.game.rng)
        self.row = 0
        self.show_map()

    def show_map(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()

        grid = self.game.floor_map
        title = tk.Label(self.content, text=f"⛰ 第 {self.game.floor} 层 · 选择路线",
                         bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_TITLE)
        title.pack(pady=(4, 12))

        # 地图面板
        map_panel = self._panel()
        map_panel.pack(padx=30, pady=6, fill="x")
        inner = tk.Frame(map_panel, bg=COLOR_PANEL)
        inner.pack(padx=16, pady=10)

        for r, row in enumerate(grid):
            line = tk.Frame(inner, bg=COLOR_PANEL)
            line.pack(pady=2)
            # 行标记
            tag = "✓" if r < self.row else ("▸" if r == self.row else "·")
            tagcol = COLOR_OK if r < self.row else (COLOR_ACCENT if r == self.row else COLOR_SUB)
            tk.Label(line, text=f" {tag} ", bg=COLOR_PANEL, fg=tagcol,
                     font=FONT_MONO, width=2).pack(side="left")

            is_current = (r == self.row)
            for i, kind in enumerate(row):
                cell = tk.Frame(line, bg=COLOR_PANEL2 if is_current else COLOR_PANEL,
                                highlightbackground=NODE_COLOR[kind] if is_current else COLOR_PANEL,
                                highlightthickness=1, cursor="hand2")
                cell.pack(side="left", padx=4, pady=2)
                innerf = tk.Frame(cell, bg=cell["bg"])
                innerf.pack(padx=8, pady=4)
                tk.Label(innerf, text=L.node_icon(kind), bg=cell["bg"],
                         fg=NODE_COLOR[kind], font=("Consolas", 18)).pack()
                tk.Label(innerf, text=L.NODE_LABEL[kind], bg=cell["bg"],
                         fg=COLOR_TEXT, font=("Microsoft YaHei UI", 9)).pack()
                if is_current:
                    # 整个节点可点击: cell + innerf + 子标签
                    for w in [cell, innerf] + list(innerf.winfo_children()):
                        w.bind("<Button-1>", lambda e, rr=r, ii=i: self.on_node_click(rr, ii))
                else:
                    cell.configure(cursor="arrow")

        tk.Label(self.content, text="点击当前行 (▸) 的一个节点前进", bg=COLOR_BG,
                 fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(10, 0))

    def on_node_click(self, r, i):
        if r != self.row:
            return
        kind = self.game.floor_map[r][i]
        if kind == "monster":
            self.start_battle(monster=True, on_done=self.after_node)
        elif kind == "elite":
            self.start_battle(monster=False, on_done=self.after_node)
        elif kind == "treasure":
            self.show_treasure()
        elif kind == "event":
            self.show_event()

    def after_node(self):
        self.row += 1
        if self.row < len(self.game.floor_map):
            if self.ask_rest():
                return
            self.show_map()
        else:
            self.show_boss()

    def ask_rest(self):
        """休息询问. 返回 True 表示已处理(需要等待)."""
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="💤 是否就地休息?",
                 bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_TITLE).pack(pady=20)
        tk.Label(self.content, text="回复 10 点生命, 但跳过下一路线",
                 bg=COLOR_BG, fg=COLOR_SUB, font=FONT_MAIN).pack(pady=4)
        panel = self._panel()
        panel.pack(pady=10)
        tk.Label(panel, text=f"❤ {self.game.hp} / {self.game.max_hp}",
                 bg=COLOR_PANEL, fg=COLOR_HP, font=FONT_TITLE).pack(padx=20, pady=10)

        def rest():
            self.game.hp = min(self.game.max_hp, self.game.hp + 10)
            self.show_map()

        def cont():
            self.show_map()

        self._btn(self.action_inner, "休息 (+10❤)", rest, color=COLOR_OK)
        self._btn(self.action_inner, "继续前进 ▶", cont, color=COLOR_BTN)
        return True

    # =========================================================
    # 战斗
    # =========================================================
    def start_battle(self, monster, on_done):
        lib = L.monster_lib()
        keys = L.MONSTER_POOL["normal"] if monster else L.MONSTER_POOL["elite"]
        key = self.rng.choice(keys)
        data = lib[key]
        scale = 1.0 + (self.game.floor - 1) * 0.25
        enemies = [L.Combatant(data["name"], int(data["hp"] * scale),
                               int(data["hp"] * scale), strength=0, block=data["block"],
                               act=data["act"], dmg=data["dmg"], art=data["art"])]
        if monster and self.game.floor > 1 and self.rng.random() < 0.3:
            key2 = self.rng.choice(keys)
            d2 = lib[key2]
            enemies.append(L.Combatant(d2["name"], int(d2["hp"] * scale * 0.7),
                                       int(d2["hp"] * scale * 0.7), block=0,
                                       act=d2["act"], dmg=d2["dmg"], art=d2["art"]))
        self._battle_on_done = on_done
        self._battle_data = data
        self._start_combat(enemies)

    def show_boss(self):
        lib = L.monster_lib()
        pool = L.boss_pool_for_floor(self.game.floor)
        key = self.rng.choice(pool)
        data = lib[key]
        scale = 1.0 + max(0, (self.game.floor - 1)) * 0.15
        boss = L.Combatant(data["name"], int(data["hp"] * scale), int(data["hp"] * scale),
                           act=data["act"], dmg=int(data["dmg"] * scale), art=data["art"])
        self._battle_on_done = self.after_boss
        self._battle_data = data
        self._start_combat([boss], boss=True)

    def _start_combat(self, enemies, boss=False):
        g = self.game
        # 同步玩家状态
        g.player.hp = g.hp
        g.player.max_hp = g.max_hp
        g.player.block = 0
        g.player.strength = 0
        g.player.regen = 0
        g.player.poison = 0
        self.combat = L.Combat(g.player, enemies, self.rng, g.relics)
        self.selected_target = None
        self.battle_log = []
        self.boss_fight = boss
        # 战斗开始遗物
        if "burning" in g.relics:
            g.player.strength += 2
        if "shield" in g.relics:
            g.player.block += 4
        if "vial" in g.relics:
            g.player.hp = min(g.player.max_hp, g.player.hp + 5)
        self.combat.start_player_turn()
        self.render_battle()

    def render_battle(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()

        if self.boss_fight:
            tk.Label(self.content, text="👑 首领战", bg=COLOR_BG, fg=COLOR_ACCENT,
                     font=FONT_TITLE).pack(pady=(2, 6))

        # ---- 敌人区 ----
        enemy_frame = tk.Frame(self.content, bg=COLOR_BG)
        enemy_frame.pack(fill="x", padx=10)
        for i, e in enumerate(self.combat.enemies):
            self._render_enemy(enemy_frame, e, i)

        self.battle_log_label = self._label("")
        self.battle_log_label.pack(pady=(6, 2), padx=16)

        # ---- 玩家状态 ----
        self._render_player_status()

        # ---- 手牌 ----
        self._render_hand()

        # ---- 操作按钮 ----
        self._btn(self.action_inner, "结束回合 ▶", self.end_turn, color=COLOR_BTN)
        self._btn(self.action_inner, "逃跑 🏳", self.flee, color=COLOR_BAD)

    def _render_enemy(self, parent, e, idx):
        panel = tk.Frame(parent, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER,
                         highlightthickness=1, cursor="hand2")
        panel.pack(fill="x", pady=3)
        # 像素画
        art = (e.art or "").strip("\n")
        artbox = tk.Frame(panel, bg=COLOR_PANEL)
        artbox.pack(side="left", padx=(8, 12))
        tk.Label(artbox, text=art, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MONO, justify="left").pack()
        # 信息
        info = tk.Frame(panel, bg=COLOR_PANEL)
        info.pack(side="left", padx=6, pady=6)
        name = f"{e.name}"
        if e.block:
            name += f"   ⛨{e.block}"
        if e.strength:
            name += f"   ⚡{e.strength}"
        tk.Label(info, text=name, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
        self._render_hpbar(info, e)

        # 高亮选中目标
        if self.selected_target is e:
            panel.configure(highlightbackground=COLOR_SELECT, highlightthickness=2)
        # 若需选目标, 点击敌人 (整个敌人块都可点)
        if len(self.combat.enemies) > 1:
            all_widgets = [panel, artbox] + list(artbox.winfo_children()) + \
                          [info] + list(info.winfo_children())
            for w in all_widgets:
                w.bind("<Button-1>", lambda ev, en=e: self.on_enemy_click(en))
        else:
            panel.configure(cursor="arrow")

    def _render_hpbar(self, parent, e):
        bar = tk.Canvas(parent, width=260, height=18, bg=COLOR_PANEL,
                        highlightthickness=0)
        bar.pack(anchor="w", pady=(4, 2))
        ratio = max(0, min(1, e.hp / e.max_hp))
        fw = int(260 * ratio)
        color = COLOR_OK if ratio > 0.5 else (COLOR_GOLD if ratio > 0.25 else COLOR_HP)
        bar.create_rectangle(2, 2, 2 + fw, 16, fill=color, outline="")
        bar.create_text(130, 10, text=f"{e.hp} / {e.max_hp}", fill=COLOR_TEXT,
                        font=("Microsoft YaHei UI", 8))

    def _render_player_status(self):
        p = self.combat.player
        panel = self._panel()
        panel.pack(fill="x", padx=10, pady=6)
        row = tk.Frame(panel, bg=COLOR_PANEL)
        row.pack(padx=12, pady=6)
        tk.Label(row, text="你", bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(side="left", padx=(0, 14))
        tk.Label(row, text=f"❤ {p.hp}/{p.max_hp}", bg=COLOR_PANEL, fg=COLOR_HP,
                 font=FONT_MAIN).pack(side="left", padx=10)
        if p.block:
            tk.Label(row, text=f"⛨ {p.block}", bg=COLOR_PANEL, fg=COLOR_SELECT,
                     font=FONT_MAIN).pack(side="left", padx=10)
        if p.strength:
            tk.Label(row, text=f"⚡ {p.strength}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=FONT_MAIN).pack(side="left", padx=10)
        if p.regen:
            tk.Label(row, text=f"✚ {p.regen}", bg=COLOR_PANEL, fg=COLOR_OK,
                     font=FONT_MAIN).pack(side="left", padx=10)
        if p.poison:
            tk.Label(row, text=f"☣ {p.poison}", bg=COLOR_PANEL, fg="#bb9af7",
                     font=FONT_MAIN).pack(side="left", padx=10)
        # 能量
        energy = "◆" * self.combat.energy + "◇" * max(0, self.combat.base_energy - self.combat.energy)
        tk.Label(row, text=energy, bg=COLOR_PANEL, fg=COLOR_ENERGY,
                 font=FONT_MONO).pack(side="right", padx=10)

    def _render_hand(self):
        panel = self._panel()
        panel.pack(fill="x", padx=10, pady=4)
        hand = tk.Frame(panel, bg=COLOR_PANEL)
        hand.pack(pady=8)
        if not self.combat.hand:
            tk.Label(hand, text="( 无手牌 )", bg=COLOR_PANEL, fg=COLOR_SUB,
                     font=FONT_MAIN).pack()
        for i, cid in enumerate(self.combat.hand):
            self._render_card_button(hand, i, cid)

    def _render_card_button(self, parent, idx, cid):
        c = L.CARD_LIB[cid]
        can_play = c["cost"] <= self.combat.energy
        frame = tk.Frame(parent, bg=COLOR_CARD, highlightbackground=COLOR_BORDER,
                         highlightthickness=1, cursor="hand2", padx=0, pady=0)
        frame.pack(side="left", padx=4)
        # 卡牌内容
        inner = tk.Frame(frame, bg=COLOR_CARD, width=76, height=88)
        inner.pack_propagate(False)
        inner.pack()
        tk.Label(inner, text=c["name"], bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Microsoft YaHei UI", 10, "bold")).pack(pady=(6, 0))
        tk.Label(inner, text="◆" * c["cost"], bg=COLOR_CARD, fg=COLOR_ENERGY,
                 font=FONT_MONO).pack(pady=(2, 0))
        tk.Label(inner, text=c["type"], bg=COLOR_CARD,
                 fg=COLOR_ACCENT if c["type"] == "技能" else COLOR_BAD,
                 font=("Microsoft YaHei UI", 8)).pack(pady=(2, 0))
        tk.Label(inner, text=c["desc"], bg=COLOR_CARD, fg=COLOR_SUB,
                 font=("Microsoft YaHei UI", 7), wraplength=72,
                 justify="center").pack(pady=(3, 0))

        if can_play:
            # 整卡可点击: frame + inner + 所有子标签都绑定
            for w in [frame, inner] + list(inner.winfo_children()):
                w.bind("<Button-1>", lambda e, i=idx: self.on_card_click(i))
                w.bind("<Enter>", lambda e, ww=w, ff=frame: ff.configure(
                    highlightbackground=COLOR_CARD_HL, highlightthickness=2))
                w.bind("<Leave>", lambda e, ww=w, ff=frame: ff.configure(
                    highlightbackground=COLOR_BORDER, highlightthickness=1))
        else:
            frame.configure(cursor="arrow")
            for lbl in inner.winfo_children():
                lbl.configure(fg=COLOR_SUB)

    def on_card_click(self, idx):
        cid = self.combat.hand[idx]
        card = L.CARD_LIB[cid]
        # 攻击牌需要目标
        if card["type"] == "攻击":
            alive = [e for e in self.combat.enemies if e.alive]
            if len(alive) > 1:
                self.selected_target = None
                self._set_log("选择攻击目标: 点击一个敌人")
                # 等待点击敌人
                self.combat.pending_play = idx
                self.render_battle()
                return
            else:
                # 单敌: 直接指定
                self.combat.pick_target = lambda: alive[0]
        else:
            self.combat.pick_target = lambda: None

        self._play_selected_card(idx)

    def on_enemy_click(self, enemy):
        if enemy not in self.combat.enemies or not enemy.alive:
            return
        pending = getattr(self.combat, "pending_play", None)
        if pending is not None:
            self.selected_target = enemy
            self.combat.pick_target = lambda: self.selected_target
            del self.combat.pending_play
            self._play_selected_card(pending)
        else:
            self.selected_target = enemy
            self.render_battle()

    def _play_selected_card(self, idx):
        result = self.combat.play_card(idx)
        if result == "not_enough":
            self._set_log("能量不足!")
            self.render_battle()
            return
        # 清理死亡敌人
        self.combat.enemies = [e for e in self.combat.enemies if e.alive]
        if not self.combat.enemies:
            self.battle_victory()
            return
        if not self.combat.player.alive:
            self.battle_defeat()
            return
        self.selected_target = None
        self.render_battle()

    def end_turn(self):
        # 敌人回合
        logs = []
        for e in list(self.combat.enemies):
            if e.alive:
                logs += self.combat.enemy_turn(e)
        self.battle_log = logs
        if not self.combat.player.alive:
            self.battle_defeat()
            return
        self.combat.start_player_turn()
        self.selected_target = None
        self.render_battle()

    def _set_log(self, text):
        if hasattr(self, "battle_log_label"):
            self.battle_log_label.configure(text="  " + text, fg=COLOR_SUB)

    def _show_battle_log(self):
        if self.battle_log and hasattr(self, "battle_log_label"):
            txt = "\n".join("  " + l for l in self.battle_log)
            self.battle_log_label.configure(text=txt, fg=COLOR_TEXT)
            self.battle_log = []

    def battle_victory(self):
        self.game.hp = self.combat.player.hp
        data = self._battle_data
        g = self.reward_gold(data["reward"])
        self._clear_content()
        self._clear_actions()
        self._update_status()
        lines = [f"🏆 胜利!  获得 {g} 金币"]
        if data.get("drop"):
            lines.append(f"掉落: {data['drop']}")
        panel = self._panel()
        panel.pack(expand=True)
        for ln in lines:
            tk.Label(panel, text=ln, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_TITLE).pack(pady=4)
        self._btn(self.action_inner, "继续 ▶", self._continue_after_victory, color=COLOR_OK)

    def _continue_after_victory(self):
        if self.rng.random() < 0.35:
            self.show_card_reward(lambda: self._battle_on_done())
        else:
            self._battle_on_done()

    def battle_defeat(self):
        self.game.hp = 0
        self.game_over()

    def flee(self):
        self.game_over(quit=True)

    def reward_gold(self, base):
        m = 1.5 if "coin" in self.game.relics else 1.0
        g = int(base * m)
        self.game.gold += g
        return g

    # =========================================================
    # 首领战结束
    # =========================================================
    def after_boss(self):
        self.game.hp = self.combat.player.hp
        data = self._battle_data
        g = self.reward_gold(data["reward"])
        self.game.floor += 1
        # 进入新层回血
        heal = 10
        self.game.hp = min(self.game.max_hp, self.game.hp + heal)
        self._clear_content()
        self._clear_actions()
        self._update_status()
        lines = [f"🏆 击败首领!  获得 {g} 金币"]
        if data.get("drop"):
            lines.append(f"掉落: {data['drop']}")
        lines.append(f"✦ 进入第 {self.game.floor} 层, 回复 {heal} 生命")
        panel = self._panel()
        panel.pack(expand=True)
        for ln in lines:
            tk.Label(panel, text=ln, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_TITLE).pack(pady=4)
        self._btn(self.action_inner, "继续 ▶", self.begin_floor, color=COLOR_OK)

    # =========================================================
    # 宝藏
    # =========================================================
    def show_treasure(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="💰 宝 藏", bg=COLOR_BG, fg=COLOR_GOLD,
                 font=FONT_TITLE).pack(pady=10)
        gained = []
        gold = self.rng.randint(40, 70)
        g = self.reward_gold(gold)
        gained.append(f"{g} 金币")

        self._btn(self.action_inner, "继续 ▶", self.after_node, color=COLOR_OK)
        panel = self._panel()
        panel.pack(expand=True)
        tk.Label(panel, text=f"你打开沉重的宝箱... 获得 {g} 金币!",
                 bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(pady=10)
        if self.rng.random() < 0.6:
            self._pending_after = self.after_node
            self.show_card_reward_auto(self.after_node)

    # =========================================================
    # 事件
    # =========================================================
    def show_event(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        ev = L.event_factory(self.rng)
        self._current_event = ev
        tk.Label(self.content, text="❔ 事 件", bg=COLOR_BG, fg=COLOR_SELECT,
                 font=FONT_TITLE).pack(pady=(8, 6))
        tk.Label(self.content, text=ev["title"], bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(0, 10))
        text_panel = self._panel()
        text_panel.pack(fill="x", padx=20, pady=4)
        tk.Label(text_panel, text=ev["text"], bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MAIN, wraplength=640, justify="left").pack(padx=14, pady=10)
        # 选项
        cho_panel = tk.Frame(self.content, bg=COLOR_BG)
        cho_panel.pack(pady=12)
        for i, (label, kind, param) in enumerate(ev["choices"]):
            b = tk.Button(cho_panel, text=f"{i+1}. {label}", bg=COLOR_BTN, fg=COLOR_TEXT,
                          activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXT,
                          relief="flat", font=FONT_MAIN, bd=0, cursor="hand2",
                          command=lambda k=kind, p=param: self.resolve_event(k, p),
                          width=44, pady=7, anchor="w")
            b.pack(pady=4)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    def resolve_event(self, kind, param):
        g = self.game
        result_text = ""
        if kind == "buy_card":
            if g.gold >= param["cost"]:
                g.gold -= param["cost"]
                self.show_card_reward_auto(self.after_event)
                return
            else:
                result_text = "金币不足, 你悻悻离开。"
        elif kind == "risky_card":
            if self.rng.random() < 0.6:
                self.show_card_reward_auto(self.after_event)
                return
            else:
                dmg = self.rng.randint(6, 10)
                g.hp = max(1, g.hp - dmg)
                result_text = f"短剑弹出, 划伤了你! 损失 {dmg} 生命。"
        elif kind == "heal":
            g.hp = min(g.max_hp, g.hp + param["value"])
            result_text = f"回复 {param['value']} 点生命。"
        elif kind == "gamble":
            r = self.rng.random()
            if r < 0.5:
                g.player.strength += 2
                result_text = "药剂灼烧着你的血脉, 获得 2 点力量。"
            elif r < 0.8:
                g.hp = min(g.max_hp, g.hp + 10)
                result_text = "暖流涌动, 回复 10 点生命。"
            else:
                g.hp = max(1, g.hp - 8)
                result_text = "药剂剧烈反噬, 损失 8 点生命!"
        elif kind == "treasure_trap":
            gg = self.reward_gold(param["gold"])
            result_text = f"搜刮到 {gg} 金币!"
            if self.rng.random() < 0.35:
                dmg = self.rng.randint(5, 12)
                g.hp = max(1, g.hp - dmg)
                result_text += f" 但触发了机关! 损失 {dmg} 生命。"
        elif kind == "upgrade":
            self.show_upgrade(self.after_event)
            return
        elif kind == "relic":
            rid = self.rng.choice(list(L.RELIC_LIB.keys()))
            rel = self.game.add_relic(rid)
            result_text = f"你郑重接过遗物「{rel['name']}」: {rel['desc']}"
        elif kind == "gold":
            gg = self.reward_gold(param["value"])
            result_text = f"获得 {gg} 金币。"
        elif kind == "pool_gamble":
            r = self.rng.random()
            if r < 0.5:
                g.hp = min(g.max_hp, g.hp + 8)
                result_text = "清冽泉水治愈了你, 回复 8 生命。"
            else:
                g.hp = max(1, g.hp - 10)
                result_text = "池水剧毒! 损失 10 生命。"
        self._show_event_result(result_text, self.after_event)

    def after_event(self):
        self.after_node()

    def _show_event_result(self, text, on_done):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="❔ 事件结果", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=16)
        panel = self._panel()
        panel.pack(expand=True)
        tk.Label(panel, text=text, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=FONT_MAIN, wraplength=600, justify="center").pack(padx=20, pady=14)
        self._btn(self.action_inner, "继续 ▶", on_done, color=COLOR_OK)

    # =========================================================
    # 卡牌奖励
    # =========================================================
    def show_card_reward_auto(self, on_done):
        self.show_card_reward(on_done)

    def show_card_reward(self, on_done):
        self._card_reward_done = on_done
        options = self.rng.sample(L.SHOP_POOL, 3)
        self._card_reward_opts = options
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🃏 卡牌奖励 · 选择一张加入卡组",
                 bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_TITLE).pack(pady=10)

        row = tk.Frame(self.content, bg=COLOR_BG)
        row.pack(pady=8)
        for i, cid in enumerate(options):
            c = L.CARD_LIB[cid]
            frame = tk.Frame(row, bg=COLOR_CARD, highlightbackground=COLOR_BORDER,
                             highlightthickness=1, cursor="hand2")
            frame.pack(side="left", padx=8)
            inner = tk.Frame(frame, bg=COLOR_CARD, width=150, height=150)
            inner.pack_propagate(False)
            inner.pack()
            tk.Label(inner, text=f"{L.CARD_RARITY.get(cid,'⭐')} {c['name']}", bg=COLOR_CARD,
                     fg=COLOR_TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(pady=(10, 2))
            tk.Label(inner, text=f"{c['type']} · {'◆'*c['cost']}费", bg=COLOR_CARD,
                     fg=COLOR_ENERGY, font=FONT_MAIN).pack(pady=(2, 4))
            tk.Label(inner, text=c["desc"], bg=COLOR_CARD, fg=COLOR_SUB,
                     font=("Microsoft YaHei UI", 9), wraplength=130,
                     justify="center").pack(pady=(4, 0))
            # 整卡可点击: frame + inner + 所有子标签都绑定点击
            for w in [frame, inner] + list(inner.winfo_children()):
                w.bind("<Button-1>", lambda e, ii=i: self.on_card_reward_choose(ii))
                w.bind("<Enter>", lambda e, ww=w, ff=frame: ff.configure(
                    highlightbackground=COLOR_CARD_HL, highlightthickness=2))
                w.bind("<Leave>", lambda e, ww=w, ff=frame: ff.configure(
                    highlightbackground=COLOR_BORDER, highlightthickness=1))
        self._btn(self.action_inner, "跳过 (0)", self._card_reward_done, color=COLOR_BTN)

    def on_card_reward_choose(self, idx):
        cid = self._card_reward_opts[idx]
        self.game.deck.append(cid)
        self._card_reward_done()

    def show_upgrade(self, on_done):
        self._upgrade_done = on_done
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🔨 强化一张牌 (+3)",
                 bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_TITLE).pack(pady=10)
        # 卡组列表
        wrap = tk.Frame(self.content, bg=COLOR_BG)
        wrap.pack()
        for i, cid in enumerate(self.game.deck):
            c = L.CARD_LIB[cid]
            b = tk.Button(wrap, text=f"{i+1}. {c['name']}  ({c['type']})",
                          bg=COLOR_BTN, fg=COLOR_TEXT, activebackground=COLOR_BTN_HOV,
                          activeforeground=COLOR_TEXT, relief="flat", font=FONT_MAIN,
                          bd=0, cursor="hand2", width=30, pady=4,
                          command=lambda ii=i: self.do_upgrade(ii))
            b.pack(pady=2)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_BTN_HOV))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_BTN))

    def do_upgrade(self, idx):
        cid = self.game.deck[idx]
        card = L.CARD_LIB[cid]
        if "value" in card:
            card["value"] += 3
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text=f"✦「{card['name']}」已强化! (+3)",
                 bg=COLOR_BG, fg=COLOR_OK, font=FONT_TITLE).pack(pady=16)
        self._btn(self.action_inner, "继续 ▶", self._upgrade_done, color=COLOR_OK)

    # =========================================================
    # 游戏结束
    # =========================================================
    def game_over(self, quit=False):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="☠ 游戏结束" if not quit else "🏳 弃塔而逃",
                 bg=COLOR_BG, fg=COLOR_BAD, font=FONT_BIG).pack(pady=16)
        panel = self._panel()
        panel.pack(expand=True)
        stats = [f"攀爬层数: {self.game.floor}",
                 f"剩余金币: {self.game.gold}",
                 f"卡组数量: {len(self.game.deck)}"]
        if self.game.relics:
            stats.append("遗物: " + ", ".join(L.RELIC_LIB[r]["name"] for r in self.game.relics))
        for s in stats:
            tk.Label(panel, text=s, bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(pady=3)
        self._btn(self.action_inner, "返回主菜单", self.show_menu, color=COLOR_BTN)

    # =========================================================
    # 图鉴
    # =========================================================
    def show_card_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="🃏 卡牌图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 4))
        tk.Label(self.content, text="⭐普通  ⭐⭐稀有  ⭐⭐⭐史诗", bg=COLOR_BG,
                 fg=COLOR_SUB, font=FONT_MAIN).pack(pady=(0, 8))
        groups = {"攻击": [], "技能": [], "能力": []}
        for cid, c in L.CARD_LIB.items():
            groups.setdefault(c["type"], []).append((cid, c))
        canvas = tk.Canvas(self.content, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLOR_BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for gname, cards in groups.items():
            tk.Label(inner, text=f"— {gname}牌 —", bg=COLOR_BG, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(8, 2))
            for cid, c in cards:
                p = self._panel(inner)
                p.pack(fill="x", padx=10, pady=2)
                tk.Label(p, text=f"{L.CARD_RARITY.get(cid,'⭐')} {c['name']}  ({c['cost']}费)  {c['type']}",
                         bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w", padx=10, pady=(4, 0))
                tk.Label(p, text="   " + c["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                         font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def show_monster_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="👹 怪物图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 4))
        lib = L.monster_lib()
        canvas = tk.Canvas(self.content, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLOR_BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        groups = [("小怪", L.MONSTER_POOL["normal"]), ("精英", L.MONSTER_POOL["elite"])]
        for title, keys in groups:
            tk.Label(inner, text=f"— {title} —", bg=COLOR_BG, fg=COLOR_ACCENT,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(8, 2))
            for k in keys:
                self._monster_card(inner, lib[k])
        tk.Label(inner, text="— 首领 —", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(8, 2))
        for k, m in lib.items():
            if "tier" in m:
                self._monster_card(inner, m)
        self._btn(self.action_inner, "← 返回", self.show_menu)

    def _monster_card(self, parent, m):
        p = self._panel(parent)
        p.pack(fill="x", padx=10, pady=3)
        left = tk.Frame(p, bg=COLOR_PANEL)
        left.pack(side="left", padx=8, pady=4)
        tk.Label(left, text=(m.get("art") or "").strip("\n"), bg=COLOR_PANEL,
                 fg=COLOR_TEXT, font=FONT_MONO, justify="left").pack()
        right = tk.Frame(p, bg=COLOR_PANEL)
        right.pack(side="left", padx=6, pady=4)
        stats = f"{m['name']}  生命{m['hp']}  伤害{m['dmg']}"
        if m.get("block"):
            stats += f"  格挡{m['block']}"
        tk.Label(right, text=stats, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        tk.Label(right, text=m["desc"], bg=COLOR_PANEL, fg=COLOR_SUB,
                 font=FONT_MAIN, wraplength=500, justify="left").pack(anchor="w", pady=(2, 0))
        if m.get("drop"):
            tk.Label(right, text=f"掉落: {m['drop']}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=FONT_MAIN).pack(anchor="w")

    def show_relic_codex(self):
        self._clear_content()
        self._clear_actions()
        self._update_status()
        tk.Label(self.content, text="◆ 遗物图鉴", bg=COLOR_BG, fg=COLOR_ACCENT,
                 font=FONT_TITLE).pack(pady=(6, 8))
        canvas = tk.Canvas(self.content, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLOR_BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for rid, r in L.RELIC_LIB.items():
            p = self._panel(inner)
            p.pack(fill="x", padx=10, pady=3)
            tk.Label(p, text=f"◆ {r['name']}", bg=COLOR_PANEL, fg=COLOR_GOLD,
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=10, pady=(4, 0))
            tk.Label(p, text="   " + r["desc"], bg=COLOR_PANEL, fg=COLOR_TEXT,
                     font=FONT_MAIN).pack(anchor="w", padx=10, pady=(0, 4))
        self._btn(self.action_inner, "← 返回", self.show_menu)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
