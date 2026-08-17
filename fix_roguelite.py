import re

path = r"E:\新建文件夹 (3)\roguelite_gui.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# ========== Fix 1: Replace show_card_reward to use tk.Button ==========
old_show_card_reward = '''    def show_card_reward(self, on_done):
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
        self._btn(self.action_inner, "跳过 (0)", self._card_reward_done, color=COLOR_BTN)'''

new_show_card_reward = '''    def show_card_reward(self, on_done):
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
            card_text = f"{L.CARD_RARITY.get(cid,'⭐')} {c['name']}\\n{c['type']} · {'◆'*c['cost']}费\\n{c['desc']}"
            b = tk.Button(row, text=card_text, bg=COLOR_CARD, fg=COLOR_TEXT,
                          activebackground=COLOR_CARD_HL, activeforeground=COLOR_TEXT,
                          relief="ridge", font=("Microsoft YaHei UI", 10),
                          bd=2, cursor="hand2", width=20, height=8,
                          justify="center", wraplength=140,
                          command=lambda ii=i: self.on_card_reward_choose(ii))
            b.pack(side="left", padx=8)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLOR_CARD_HL))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLOR_CARD))
        self._btn(self.action_inner, "跳过 (0)", self._card_reward_done, color=COLOR_BTN)'''

if old_show_card_reward in content:
    content = content.replace(old_show_card_reward, new_show_card_reward)
    print("Fix 1 OK: show_card_reward replaced with Button-based approach")
else:
    print("Fix 1 FAILED: old show_card_reward not found")

# ========== Fix 2: Change card reward probability from 0.35 to 1.0 ==========
old_prob = "if self.rng.random() < 0.35:"
new_prob = "if self.rng.random() < 1.0:"

if old_prob in content:
    content = content.replace(old_prob, new_prob)
    print("Fix 2 OK: card reward probability changed from 0.35 to 1.0")
else:
    print("Fix 2 FAILED: old probability check not found")

# ========== Fix 3: Add card reward after boss fight ==========
old_boss_btn = '        self._btn(self.action_inner, "继续 ▶", self.begin_floor, color=COLOR_OK)'
new_boss_btn = '        self._btn(self.action_inner, "继续 ▶", lambda: self.show_card_reward(self.begin_floor), color=COLOR_OK)'

if old_boss_btn in content:
    content = content.replace(old_boss_btn, new_boss_btn, 1)  # only first occurrence (in after_boss)
    print("Fix 3 OK: card reward added after boss fight")
else:
    print("Fix 3 FAILED: boss continue button not found")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("\nAll fixes applied! File saved.")
