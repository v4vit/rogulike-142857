#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
假人练枪 (Dummy Trainer)
========================
一个用 tkinter + Canvas 实现的 FPS 练枪软件，模拟 KovaaK 风格的人形假人目标。

场景（掩体线 + 抢时间）：
  画面中有一面横向掩体墙，假人站在墙后的地面线（"站在一条线上"）上。
  每个假人从墙侧随机探出，两种行动模式随机混合：
    - 小身位 peek ：只横向探出一点点，露头即缩回，窗口很短，必须一发爆头
    - 大拉 wide    ：从墙侧横向大角度拉出，完全露出身体，窗口稍长，可爆头或压枪打身体

判定（模型大小与 KovaaK 一致的人形假人）：
  - 头（爆头区）：命中 1 枪死
  - 身体        ：命中需 4 枪（累计血量），血条可见

射击方式：
  准星跟随鼠标移动，按 空格 或 鼠标左键 开枪（FPS 手感）。

出假人逻辑与"点小球"一致：
  随机位置随机模式出一个假人，击杀（或超时缩回）后，在下一个随机位置出下一个。

运行方式：
  python dummy_trainer.py
"""

import json
import math
import os
import random
import sys
import tempfile
import threading
import time
import tkinter as tk
import wave
try:
    import winsound
    _SOUND_OK = True
except ImportError:
    _SOUND_OK = False

# ---------------------------------------------------------------------------
# 常量配置
# ---------------------------------------------------------------------------
APP_TITLE = "假人练枪"
VERSION = "1.0.0"

def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _base_dir()
HISTORY_FILE = os.path.join(BASE_DIR, "dummy_history.json")

# 颜色（深色主题，与 aim_trainer 一致）
COLOR_BG = "#1b2230"
COLOR_PANEL = "#242f42"
COLOR_TEXT = "#e6edf3"
COLOR_DIM = "#8fa3b8"
COLOR_ACCENT = "#3d8bfd"
COLOR_WALL = "#3a475c"          # 掩体墙
COLOR_WALL_TOP = "#55637c"      # 墙顶高光
COLOR_GROUND = "#2a3448"        # 地面
COLOR_BODY = "#ff9f43"          # 假人身体（橙）
COLOR_BODY_HIT = "#e74c3c"      # 身体中弹
COLOR_HEAD = "#ffd23f"          # 假人头（黄，爆头区醒目）
COLOR_HEAD_HIT = "#2ecc71"      # 爆头反馈（绿）
COLOR_MISS = "#e74c3c"          # 失误
COLOR_HP = "#2ecc71"            # 身体血条
COLOR_HP_LOW = "#e74c3c"

# 默认设置
DEFAULT_ROUNDS = 20             # 每轮假人数
DEFAULT_DUMMY_H = 150           # 假人身高（像素，可缩放）
DEFAULT_MIX = "mix"             # 行动模式: wide / peek / mix
DEFAULT_PULL_SPEED = 680        # 拉出速度（px/s，贴近无畏契约横移手感）
DEFAULT_LEFT_PROB = 50          # 假人从左侧出现的概率 %（0=全右,50=随机,100=全左）
DEFAULT_SPEED_VARY = 25         # 拉出速度随机波动幅度 %（0~50）

# 假人比例（参照 KovaaK 人形 bot）
BODY_HP = 4                     # 身体需 4 枪
HEAD_R_F = 0.11                 # 头半径 = 身高 * 0.11
BODY_W_F = 0.28                 # 身体宽 = 身高 * 0.28
WALL_H_F = 1.30                 # 掩体墙高 = 身高 * 1.30（高于假人，能完全遮住）

# 假人几何（相对当前假人身高 H 的动态计算）
#  - 地面线 ground_y（假人脚所在，所有假人同一条线）
#  - 左右两面竖直掩体墙；假人从掩体内侧拉出
#  - peek：小身位拉出（只露头+肩）；大拉：从一边横穿到另一边（露全身）

# 拉出速度（px/s）
#  - 大拉横穿与 peek 探出共用 PULL_SPEED，手感贴近无畏契约（角色横移节奏）
PEEK_BODY_F = 0.7              # peek 半身位：探出距离 = 身体宽 * 系数（露头+上半身）

# 减速机制（被击中后减速，幅度贴近无畏契约）
#  - 无畏契约：武器命中后敌人移速降低约 50%，持续约 0.3~0.5s，连续命中会刷新
SLOW_FACTOR = 0.5              # 减速后速度系数（0.5 = 减速 50%）
SLOW_DUR = 0.4                 # 减速持续时长（秒）

# 动画/时间（毫秒）
PEEK_HOLD_MS = 380             # peek 停留窗口（露头后给你反应+爆头的时间）
WIDE_HOLD_MS = 500             # 大拉停留窗口
RESPAWN_MS = 260               # 击杀/缩回后到下一个的延迟
TICK_MS = 16                   # 帧循环（约 60 FPS）
HIT_TOL = 8                    # 命中判定容差

# 评级阈值（平均反应时间 ms）
RATING_TABLE = [
    (300, "⭐⭐⭐⭐⭐  顶级反应", "#ff5a5a"),
    (380, "⭐⭐⭐⭐  非常出色",   "#ff8c42"),
    (460, "⭐⭐⭐  优秀",        "#ffd23f"),
    (560, "⭐⭐  良好",          "#4cd964"),
    (float("inf"), "继续练习，稳步提升", "#8fa3b8"),
]


def rate_time(ms: float):
    for threshold, text, color in RATING_TABLE:
        if ms <= threshold:
            return text, color
    return RATING_TABLE[-1][1], RATING_TABLE[-1][2]


def load_history(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_history(path, records):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def _shade(hex_color, factor):
    """提亮(正)/压暗(负)一个 #rrggbb 颜色。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    def adj(v):
        if factor >= 0:
            return int(v + (255 - v) * factor)
        return int(v * (1 + factor))
    return f"#{adj(r):02x}{adj(g):02x}{adj(b):02x}"


# ---------------------------------------------------------------------------
# 音效（程序化合成，无需外部音频文件，保持单文件 exe）
# ---------------------------------------------------------------------------
# 与 CS 一致：爆头 = 清脆金属"叮"（高频），身体命中 = 低沉闷响（低频）
_SND_HEAD_WAV = os.path.join(tempfile.gettempdir(), "dummy_headshot.wav")
_SND_BODY_WAV = os.path.join(tempfile.gettempdir(), "dummy_bodyhit.wav")
_SND_LOCK = threading.Lock()


def _synth_wav(path, base_freq, harmonics, dur_s, vol):
    """合成一段单声道 16bit 44.1kHz 的 WAV（谐波叠加 + 指数衰减包络）。"""
    rate = 44100
    n = int(rate * dur_s)
    frames = bytearray()
    decay = 3.0 / dur_s                     # 衰减速度（指数）
    for i in range(n):
        t = i / rate
        env = math.exp(-t * decay)          # 指数衰减包络
        s = 0.0
        for h, a in harmonics:
            s += a * math.sin(2.0 * math.pi * base_freq * h * t)
        v = int(s * env * vol * 32767)
        v = max(-32767, min(32767, v))
        frames += v.to_bytes(2, "little", signed=True)
    try:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(bytes(frames))
    except OSError:
        pass


def _ensure_sounds():
    """确保两段音效已生成（爆头叮 / 身体闷响）。"""
    if not os.path.exists(_SND_HEAD_WAV):
        # 爆头：约 1600Hz 主频 + 谐波，短促清脆的金属"叮"
        _synth_wav(_SND_HEAD_WAV, 1600, [(1, 1.0), (2, 0.55), (3, 0.28), (4, 0.15)],
                   0.16, 0.85)
    if not os.path.exists(_SND_BODY_WAV):
        # 身体：约 240Hz 低频 + 略高次谐波，低沉短促的闷响
        _synth_wav(_SND_BODY_WAV, 240, [(1, 1.0), (2, 0.5), (3, 0.25)], 0.09, 0.95)


def play_sound(kind):
    """异步播放音效，kind: 'head' 爆头 / 'body' 身体命中。不阻塞主循环。"""
    if not _SOUND_OK:
        return
    path = _SND_HEAD_WAV if kind == "head" else _SND_BODY_WAV
    def _play():
        with _SND_LOCK:
            try:
                _ensure_sounds()
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass
    threading.Thread(target=_play, daemon=True).start()


# ---------------------------------------------------------------------------
# 主应用
# ---------------------------------------------------------------------------
class DummyTrainerApp:
    """假人练枪主窗口。"""

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(f"{APP_TITLE} v{VERSION}")
        root.geometry("960x640")
        root.minsize(800, 560)
        root.configure(bg=COLOR_BG)

        self.history = load_history(HISTORY_FILE)

        # 设置
        self.rounds = DEFAULT_ROUNDS
        self.dummy_h = DEFAULT_DUMMY_H
        self.mix = DEFAULT_MIX       # wide / peek / mix
        self.pull_speed = DEFAULT_PULL_SPEED   # 拉出速度 px/s
        self.left_prob = DEFAULT_LEFT_PROB     # 左侧出现概率 %（0=全右,50=随机,100=全左）
        self.speed_vary = DEFAULT_SPEED_VARY   # 拉出速度随机波动 %

        # 会话状态
        self.phase = "menu"
        self.round_index = 0
        self.kills = 0
        self.misses = 0
        self.combo = 0
        self.max_combo = 0
        self.times = []              # 每次击杀的反应时间 ms
        self.score = 0
        self.session_start = 0.0

        # 画布 / 光标
        self.canvas = None
        self.cx = 0.0
        self.cy = 0.0
        self.tick_job = None

        # 假人状态
        self.dummy = None            # dict, 见 _spawn_dummy

        self._build_ui()
        self._show_menu()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.root, bg=COLOR_BG)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 4))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="🎯 假人练枪", font=("Microsoft YaHei", 20, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        self.best_label = tk.Label(header, text="", font=("Microsoft YaHei", 11),
                                   bg=COLOR_BG, fg="#ffd23f")
        self.best_label.grid(row=0, column=2, sticky="e")
        self.menu_btn = tk.Button(header, text="返回菜单", command=self._to_menu,
                                  font=("Microsoft YaHei", 10), bg=COLOR_PANEL,
                                  fg=COLOR_TEXT, activebackground="#32415a",
                                  activeforeground="white", relief="flat", padx=10)
        self.menu_btn.grid(row=0, column=3, padx=(16, 0))

        self.content = tk.Frame(self.root, bg=COLOR_BG)
        self.content.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _to_menu(self):
        self._cancel_jobs()
        self._show_menu()

    def _show_menu(self):
        self.phase = "menu"
        self._clear_content()

        page = tk.Frame(self.content, bg=COLOR_BG)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        tk.Label(page, text="选择行动模式", font=("Microsoft YaHei", 18, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, pady=(10, 20))

        cards = tk.Frame(page, bg=COLOR_BG)
        cards.grid(row=1, column=0)
        modes = [
            ("wide", "大拉 wide", "假人从墙侧横向拉出，完全露出身体\n可爆头(1枪)或压枪打身体(4枪)"),
            ("peek", "小身位 peek", "假人只露头即缩回，窗口极短\n必须一发爆头"),
            ("mix", "随机混合", "每个假人随机大拉或小身位 peek\n锻炼应对两种情况的反应"),
        ]
        for i, (key, title, desc) in enumerate(modes):
            card = tk.Frame(cards, bg=COLOR_PANEL, cursor="hand2",
                            highlightbackground=COLOR_ACCENT,
                            highlightthickness=0, padx=20, pady=16)
            card.grid(row=0, column=i, padx=12)
            tk.Label(card, text=title, font=("Microsoft YaHei", 15, "bold"),
                     bg=COLOR_PANEL, fg=COLOR_TEXT).pack()
            tk.Label(card, text=desc, font=("Microsoft YaHei", 10),
                     bg=COLOR_PANEL, fg=COLOR_DIM, justify="left").pack(pady=(8, 0))
            card.bind("<Button-1>", lambda e, m=key: self._select_mode(m))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, m=key: self._select_mode(m))
                card.bind("<Enter>", lambda e, c=card: c.configure(highlightthickness=2))
                card.bind("<Leave>", lambda e, c=card: c.configure(highlightthickness=0))

        settings = tk.Frame(page, bg=COLOR_PANEL, padx=24, pady=16)
        settings.grid(row=2, column=0, pady=(24, 8))
        tk.Label(settings, text="⚙ 设置", font=("Microsoft YaHei", 13, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT).grid(row=0, column=0, columnspan=4,
                                                     sticky="w", pady=(0, 8))

        tk.Label(settings, text="每轮假人数:", font=("Microsoft YaHei", 11),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=1, column=0, sticky="w",
                                                    padx=(0, 8), pady=4)
        self.rounds_var = tk.IntVar(value=DEFAULT_ROUNDS)
        tk.Spinbox(settings, from_=5, to=100, textvariable=self.rounds_var,
                   width=5, font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=1, column=1, padx=(0, 20))

        tk.Label(settings, text="假人大小:", font=("Microsoft YaHei", 11),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=1, column=2, sticky="w",
                                                    padx=(0, 8), pady=4)
        self.size_var = tk.IntVar(value=DEFAULT_DUMMY_H)
        tk.Spinbox(settings, from_=90, to=220, increment=10, textvariable=self.size_var,
                   width=5, font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=1, column=3, padx=(0, 8))

        tk.Label(settings, text="拉出速度:", font=("Microsoft YaHei", 11),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=2, column=0, sticky="w",
                                                    padx=(0, 8), pady=4)
        self.speed_var = tk.IntVar(value=DEFAULT_PULL_SPEED)
        tk.Spinbox(settings, from_=350, to=1200, increment=20,
                   textvariable=self.speed_var, width=5, font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=2, column=1, padx=(0, 20))
        tk.Label(settings, text="px/s（大拉拉出/横穿速度）", font=("Microsoft YaHei", 9),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=2, column=2, columnspan=2,
                                                    sticky="w", padx=(0, 8), pady=4)

        # 出现侧比例：左 0~100%（0=全右, 50=左右随机, 100=全左）
        tk.Label(settings, text="假人左侧概率:", font=("Microsoft YaHei", 11),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=3, column=0, sticky="w",
                                                    padx=(0, 8), pady=4)
        self.left_var = tk.IntVar(value=DEFAULT_LEFT_PROB)
        self.left_scale = tk.Scale(settings, from_=0, to=100, orient="horizontal",
                                   variable=self.left_var, command=self._read_settings,
                                   showvalue=True, bg=COLOR_PANEL, fg=COLOR_TEXT,
                                   highlightthickness=0, troughcolor=COLOR_BG,
                                   sliderrelief="flat", length=200,
                                   font=("Microsoft YaHei", 9))
        self.left_scale.grid(row=3, column=1, columnspan=2, sticky="w", padx=(0, 8))
        self.left_hint = tk.Label(settings, text="", font=("Microsoft YaHei", 9),
                                  bg=COLOR_PANEL, fg=COLOR_DIM)
        self.left_hint.grid(row=3, column=3, sticky="w", padx=(0, 8))

        # 拉出速度随机波动 %
        tk.Label(settings, text="速度波动:", font=("Microsoft YaHei", 11),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=4, column=0, sticky="w",
                                                    padx=(0, 8), pady=4)
        self.vary_var = tk.IntVar(value=DEFAULT_SPEED_VARY)
        tk.Scale(settings, from_=0, to=50, orient="horizontal",
                 variable=self.vary_var, command=self._read_settings,
                 showvalue=True, bg=COLOR_PANEL, fg=COLOR_TEXT,
                 highlightthickness=0, troughcolor=COLOR_BG,
                 sliderrelief="flat", length=200, font=("Microsoft YaHei", 9)
                 ).grid(row=4, column=1, columnspan=2, sticky="w", padx=(0, 8))
        tk.Label(settings, text="% ±（每个假人速度随机波动）", font=("Microsoft YaHei", 9),
                 bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=4, column=3, sticky="w",
                                                    padx=(0, 8), pady=4)

        self._read_settings()

        self.menu_best = tk.Label(page, text=self._best_summary(),
                                  font=("Microsoft YaHei", 11),
                                  bg=COLOR_BG, fg="#ffd23f")
        self.menu_best.grid(row=3, column=0, pady=(8, 0))

    def _read_settings(self, *_args):
        def clamp(var, lo, hi, default):
            try:
                return max(lo, min(hi, int(var.get())))
            except (ValueError, tk.TclError):
                return default
        self.rounds = clamp(self.rounds_var, 5, 100, DEFAULT_ROUNDS)
        self.dummy_h = clamp(self.size_var, 90, 220, DEFAULT_DUMMY_H)
        self.pull_speed = clamp(self.speed_var, 350, 1200, DEFAULT_PULL_SPEED)
        self.left_prob = clamp(self.left_var, 0, 100, DEFAULT_LEFT_PROB)
        self.speed_vary = clamp(self.vary_var, 0, 50, DEFAULT_SPEED_VARY)
        self.rounds_var.set(self.rounds)
        self.size_var.set(self.dummy_h)
        self.speed_var.set(self.pull_speed)
        self.left_var.set(self.left_prob)
        self.vary_var.set(self.speed_vary)
        # 更新左侧概率的语义提示
        if hasattr(self, "left_hint"):
            if self.left_prob == 0:
                txt = "全右"
            elif self.left_prob == 100:
                txt = "全左"
            elif self.left_prob == 50:
                txt = "左右随机"
            else:
                txt = "左%d%% 右%d%%" % (self.left_prob, 100 - self.left_prob)
            self.left_hint.configure(text=txt)

    # ------------------------------------------------------------------
    # 开始训练
    # ------------------------------------------------------------------
    def _select_mode(self, mix):
        self.mix = mix
        self._read_settings()
        self.round_index = 0
        self.kills = 0
        self.misses = 0
        self.combo = 0
        self.max_combo = 0
        self.times = []
        self.score = 0
        self.phase = "playing"
        self.session_start = time.monotonic()

        self._clear_content()
        canvas = tk.Canvas(self.content, bg=COLOR_BG, highlightthickness=0,
                           cursor="crosshair")
        canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas = canvas

        self.hud_score = canvas.create_text(16, 14, anchor="nw", text="",
                                            fill=COLOR_TEXT,
                                            font=("Microsoft YaHei", 12, "bold"))
        self.hud_combo = canvas.create_text(16, 40, anchor="nw", text="",
                                            fill="#ffd23f",
                                            font=("Microsoft YaHei", 11, "bold"))
        self.hud_hint = canvas.create_text(canvas.winfo_reqwidth() - 16, 14,
                                           anchor="ne", text="", fill=COLOR_DIM,
                                           font=("Microsoft YaHei", 11))

        canvas.bind("<Motion>", self._on_motion)
        canvas.bind("<Button-1>", lambda e: self._on_shoot())
        self.root.bind("<space>", lambda e: self._on_shoot())
        self.canvas.bind("<Configure>", self._on_resize)

        # 光标初始在画布中心
        self.cx, self.cy = self._canvas_size()
        self.cx /= 2
        self.cy /= 2

        self._spawn_dummy()
        self._start_tick()

    def _on_resize(self, _event=None):
        if self.phase == "playing":
            self._spawn_dummy()

    def _canvas_size(self):
        try:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
        except Exception:
            w = h = 400
        if w < 10 or h < 10:
            w, h = self.content.winfo_width(), self.content.winfo_height()
        return max(w, 50), max(h, 50)

    # ------------------------------------------------------------------
    # 场景几何
    # ------------------------------------------------------------------
    def _geometry(self):
        """返回场景几何：
        (ground_y, wall_top, wall_bot, wall_w, mid_x0, mid_x1, H, hr, bw)

        左右各一面长掩体墙；中间开阔地带是假人的活动走廊（一条地面线）。
          - 左掩体：x∈[0, wall_w]，右掩体：x∈[w-wall_w, w]
          - 假人活动区：x∈[mid_x0, mid_x1] = 屏幕中间 2/5
        """
        w, h = self._canvas_size()
        H = self.dummy_h
        hr = H * HEAD_R_F
        bw = H * BODY_W_F
        ground_y = h * 0.80                       # 假人脚所在的地面线（一条线）
        wall_bot = ground_y
        wall_top = ground_y - H * WALL_H_F        # 墙高于假人，能完全遮住躲藏的假人
        wall_w = w * 0.30                         # 每侧长掩体墙宽度（中间留给假人 2/5）
        mid_x0 = wall_w                           # 中间活动区左边界
        mid_x1 = w - wall_w                       # 中间活动区右边界
        return (ground_y, wall_top, wall_bot, wall_w, mid_x0, mid_x1, H, hr, bw)

    def _head_cy(self, ground_y, H, hr):
        return ground_y - H + hr

    # ------------------------------------------------------------------
    # 假人生成 / 状态机
    # ------------------------------------------------------------------
    def _pick_mode(self):
        if self.mix == "wide":
            return "wide"
        if self.mix == "peek":
            return "peek"
        return random.choice(["wide", "peek"])

    def _from_left(self):
        """假人这次是否从左侧掩体出现（依据"左侧概率"设置）。"""
        return random.random() * 100 < self.left_prob

    def _spawn_dummy(self):
        """从掩体内侧生成一个假人。

        - peek ：从一侧长掩体探出半身位（露头+上半身），短暂停留，再缩回掩体
        - 大拉 ：从一边掩体横穿到另一边掩体（左↔右），完全露出身体
        假人只出现在屏幕中间 2/5 的活动区内。
        "左侧概率"设置（self.left_prob）决定假人从左侧掩体出现的比例。
        拉出速度 = PULL_SPEED ± 速度波动（self.speed_vary），每个假人不同。
        """
        self.canvas.delete("dummy")
        self.canvas.delete("fx")
        g, wt, wb, ww, mx0, mx1, H, hr, bw = self._geometry()

        # 每个假人速度在设定值附近随机波动（增加难度变化）
        vary = self.speed_vary / 100.0
        speed_base = self.pull_speed * random.uniform(1 - vary, 1 + vary)

        mode = self._pick_mode()
        from_left = self._from_left()
        if mode == "wide":
            # 从一边掩体横穿到另一边（横穿中间 2/5 区域）
            if from_left:
                start_x, end_x = mx0 + bw * 0.3, mx1 - bw * 0.3   # 左 → 右
            else:
                start_x, end_x = mx1 - bw * 0.3, mx0 + bw * 0.3   # 右 → 左
            hold = WIDE_HOLD_MS
        else:
            # peek 半身位：从一侧掩体探出露头+上半身，再缩回掩体
            expose = bw * PEEK_BODY_F
            if from_left:                                # 左侧掩体
                start_x = mx0 - bw * 0.4                 # 藏在左掩体内
                end_x = mx0 + expose                     # 探出到左掩体外（半身位）
            else:                                        # 右侧掩体
                start_x = mx1 + bw * 0.4
                end_x = mx1 - expose
            hold = PEEK_HOLD_MS

        self.dummy = {
            "mode": mode,
            "start_x": start_x,
            "end_x": end_x,
            "x": start_x,
            "dir": 1.0 if end_x > start_x else -1.0,   # 探出移动方向
            "speed_base": speed_base,            # 基础拉出速度 px/s（含随机波动）
            "slow_factor": 1.0,                        # 减速系数（被击中 -> 0.5）
            "slow_until": 0.0,                         # 减速恢复时刻
            "state": "expose",                    # expose / hold / retreat / gone
            "t0": time.monotonic(),
            "hold": hold / 1000.0,
            "hp": BODY_HP,
            "born": time.monotonic(),
        }
        self.round_index += 1
        self._update_hud()

    def _move_dummy(self, d, move_dir, target, dt):
        """按当前速度（含减速系数）移动假人，返回是否已到达目标。"""
        speed = d["speed_base"] * d["slow_factor"]
        d["x"] += move_dir * speed * dt
        if move_dir > 0:
            return d["x"] >= target
        return d["x"] <= target

    def _dummy_x(self, d):
        return d["x"]

    # ------------------------------------------------------------------
    # 帧循环
    # ------------------------------------------------------------------
    def _start_tick(self):
        self._tick()

    def _tick(self):
        self.tick_job = self.root.after(TICK_MS, self._tick)
        if self.phase != "playing" or not self.canvas:
            return
        d = self.dummy
        if not d:
            return
        now = time.monotonic()
        dt = TICK_MS / 1000.0

        # 减速结束，恢复正常速度
        if d["slow_factor"] < 1.0 and now >= d["slow_until"]:
            d["slow_factor"] = 1.0

        # 阶段推进（expose/retreat 用速度驱动，支持被击中减速）
        if d["state"] == "expose":
            if self._move_dummy(d, d["dir"], d["end_x"], dt):
                d["x"] = d["end_x"]
                d["state"] = "hold"
                d["t0"] = now
        elif d["state"] == "hold" and now - d["t0"] >= d["hold"]:
            d["state"] = "retreat"
            d["t0"] = now
        elif d["state"] == "retreat":
            if self._move_dummy(d, -d["dir"], d["start_x"], dt):
                d["x"] = d["start_x"]
                # 缩回完成：未打死则记 miss，生成下一个
                d["state"] = "gone"
                if self.phase == "playing":
                    self._miss_timeout()
                self.root.after(RESPAWN_MS, self._respawn_after)

        self._render()

    def _respawn_after(self):
        if self.phase == "playing" and self.canvas:
            self._spawn_dummy()

    # ------------------------------------------------------------------
    # 射击
    # ------------------------------------------------------------------
    def _on_shoot(self):
        if self.phase != "playing":
            return
        d = self.dummy
        if not d or d["state"] == "gone":
            return
        g, wt, wb, ww, mx0, mx1, H, hr, bw = self._geometry()
        x = d["x"]
        head_cy = self._head_cy(g, H, hr)

        hit = self._hit_test(d, x, head_cy, hr, bw, g, wt, wb, ww)
        if hit == "head":
            play_sound("head")                  # 爆头：清脆"叮"
            self._on_kill(head=True)
        elif hit == "body":
            play_sound("body")                  # 身体命中：低沉闷响
            d["hp"] -= 1
            # 减速机制：被击中后假人移速降低（幅度贴近无畏契约），连续命中刷新
            d["slow_factor"] = SLOW_FACTOR
            d["slow_until"] = time.monotonic() + SLOW_DUR
            if d["hp"] <= 0:
                self._on_kill(head=False)
            else:
                self._flash_text(x, head_cy - hr - 20, f"身体 -1 ({d['hp']})  减速",
                                 COLOR_HP, 300)
                self._update_hud()
        else:
            self._miss_shot()

    def _hit_test(self, d, x, head_cy, hr, bw, g, wt, wb, ww):
        """返回 'head' / 'body' / None。点在左右掩体墙内视为打中掩体（无效）。"""
        w, _h = self._canvas_size()
        cx, cy = self.cx, self.cy
        # 打在左右掩体墙上 → 无效
        in_left = cx <= ww and wt <= cy <= wb
        in_right = cx >= (w - ww) and wt <= cy <= wb
        if in_left or in_right:
            return None
        # 爆头区（优先）
        if math.hypot(cx - x, cy - head_cy) <= hr + HIT_TOL:
            return "head"
        # 身体矩形
        bx0, bx1 = x - bw / 2, x + bw / 2
        by0, by1 = head_cy + hr, g
        if bx0 <= cx <= bx1 and by0 <= cy <= by1:
            return "body"
        return None

    # ------------------------------------------------------------------
    # 命中 / 失误
    # ------------------------------------------------------------------
    def _on_kill(self, head):
        d = self.dummy
        now = time.monotonic()
        ms = (now - d["born"]) * 1000
        self.times.append(ms)
        self.kills += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)

        base = 100 if head else 80
        combo_bonus = min(self.combo - 1, 10) * 10
        speed_bonus = max(0, 60 - int(ms / 20))
        gained = base + combo_bonus + speed_bonus
        self.score += gained

        label = "爆头" if head else "击杀"
        color = COLOR_HEAD_HIT if head else COLOR_BODY_HIT
        d["state"] = "gone"
        self._flash_kill(d, head, color, f"{label}  +{gained}", ms)
        self._update_hud()

        if self.round_index >= self.rounds:
            self.root.after(350, self._finish)
        else:
            self.root.after(RESPAWN_MS, self._respawn_after)

    def _miss_shot(self):
        self.combo = 0
        self.misses += 1
        self._update_hud()

    def _miss_timeout(self):
        self.combo = 0
        self.misses += 1
        self._update_hud()

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    def _render(self):
        c = self.canvas
        c.delete("dummy")
        c.delete("fx")
        w, h = c.winfo_width(), c.winfo_height()
        g, wt, wb, ww, mx0, mx1, H, hr, bw = self._geometry()
        d = self.dummy

        # 地面线（假人站的那条线）
        c.create_line(0, g, w, g, fill=COLOR_GROUND, width=2, tags=("dummy",))

        # 假人
        if d and d["state"] != "gone":
            x = d["x"]
            head_cy = self._head_cy(g, H, hr)
            # 减速中：身体变蓝，提示被击中减速
            slowed = d["slow_factor"] < 1.0
            body_color = "#5a7fd6" if slowed else COLOR_BODY

            # 身体
            c.create_rectangle(x - bw / 2, head_cy + hr, x + bw / 2, g,
                               fill=body_color, outline=_shade(body_color, -0.35),
                               width=2, tags=("dummy",))
            # 肩部/头颈
            c.create_rectangle(x - bw / 2 - 4, head_cy + hr - 2,
                               x + bw / 2 + 4, head_cy + hr + 14,
                               fill=_shade(body_color, -0.1),
                               outline="", tags=("dummy",))
            # 头
            c.create_oval(x - hr, head_cy - hr, x + hr, head_cy + hr,
                          fill=COLOR_HEAD, outline=_shade(COLOR_HEAD, -0.35),
                          width=2, tags=("dummy",))
            # 头高光
            c.create_oval(x - hr * 0.5, head_cy - hr * 0.75,
                          x - hr * 0.05, head_cy - hr * 0.3,
                          fill="#ffffff", outline="", tags=("dummy",))

            # 身体血条
            if d["state"] in ("expose", "hold"):
                self._draw_hp(x, head_cy - hr - 16, d["hp"])
            # 模式角标
            tag = "大拉" if d["mode"] == "wide" else "peek"
            if slowed:
                tag += "  ⚡减速"
            c.create_text(x, head_cy - hr - 30, text=tag, fill=COLOR_DIM,
                          font=("Microsoft YaHei", 9), tags=("dummy",))

        # 左右掩体墙（竖直，画在假人之后，靠画面左右两侧）
        for wx in (0.0, w - ww):
            c.create_rectangle(wx, wt, wx + ww, wb, fill=COLOR_WALL,
                               outline=_shade(COLOR_WALL, -0.3), tags=("dummy",))
            c.create_line(wx, wt, wx + ww, wt, fill=COLOR_WALL_TOP, width=3,
                          tags=("dummy",))

        # 准星（最顶层）
        self._draw_crosshair()

    def _draw_hp(self, x, y, hp):
        c = self.canvas
        total = BODY_HP
        w = 44
        c.create_rectangle(x - w / 2, y, x + w / 2, y + 5,
                           fill="#333c4e", outline="", tags=("dummy",))
        color = COLOR_HP if hp > 1 else COLOR_HP_LOW
        c.create_rectangle(x - w / 2, y, x - w / 2 + w * hp / total, y + 5,
                           fill=color, outline="", tags=("dummy",))

    def _draw_crosshair(self):
        c = self.canvas
        cx, cy = self.cx, self.cy
        L = 9
        col = "#ffffff"
        c.create_line(cx - L, cy, cx - 3, cy, fill=col, width=2, tags=("dummy",))
        c.create_line(cx + 3, cy, cx + L, cy, fill=col, width=2, tags=("dummy",))
        c.create_line(cx, cy - L, cx, cy - 3, fill=col, width=2, tags=("dummy",))
        c.create_line(cx, cy + 3, cx, cy + L, fill=col, width=2, tags=("dummy",))
        c.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill=col, outline="",
                      tags=("dummy",))

    def _on_motion(self, event):
        self.cx, self.cy = event.x, event.y

    # ------------------------------------------------------------------
    # 反馈
    # ------------------------------------------------------------------
    def _flash_kill(self, d, head, color, text, ms):
        c = self.canvas
        g, wt, wb, ww, mx0, mx1, H, hr, bw = self._geometry()
        x = d["x"]
        head_cy = self._head_cy(g, H, hr)
        c.create_oval(x - hr, head_cy - hr, x + hr, head_cy + hr,
                      outline=color, width=3, tags=("fx",))
        c.create_oval(x - bw / 2 - 6, head_cy + hr - 4, x + bw / 2 + 6, g,
                      outline=color, width=2, tags=("fx",))
        c.create_text(x, head_cy - hr - 40, text=text, fill=color,
                      font=("Microsoft YaHei", 14, "bold"), tags=("fx",))
        if ms is not None:
            c.create_text(x, head_cy - hr - 20, text=f"{ms:.0f} ms",
                          fill=COLOR_DIM, font=("Microsoft YaHei", 10),
                          tags=("fx",))
        self.root.after(500, self._clear_fx)

    def _flash_text(self, x, y, text, color, ms):
        c = self.canvas
        c.create_text(x, y, text=text, fill=color,
                      font=("Microsoft YaHei", 11, "bold"), tags=("fx",))
        if ms:
            self.root.after(ms, self._clear_fx)

    def _clear_fx(self):
        if not self.canvas:
            return
        try:
            if self.canvas.winfo_exists():
                self.canvas.delete("fx")
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def _mode_name(self):
        return {"wide": "大拉", "peek": "小身位", "mix": "随机混合"}[self.mix]

    def _accuracy(self):
        total = self.kills + self.misses
        return 0.0 if total == 0 else self.kills / total * 100

    def _update_hud(self):
        if not hasattr(self, "canvas") or self.phase != "playing":
            return
        self.canvas.itemconfigure(
            self.hud_score,
            text=f"{self._mode_name()}   第 {self.round_index}/{self.rounds} 个   "
                 f"得分 {self.score}")
        combo_text = f"连击 ×{self.combo}" if self.combo >= 2 else ""
        self.canvas.itemconfigure(self.hud_combo, text=combo_text)
        acc = self._accuracy()
        self.canvas.itemconfigure(
            self.hud_hint,
            text=f"命中率 {acc:.0f}%   击杀 {self.kills}   失误 {self.misses}\n"
                 f"空格/左键开枪 · 头1枪 身4枪 · 击中身体减速")

    # ------------------------------------------------------------------
    # 结算
    # ------------------------------------------------------------------
    def _finish(self):
        self._cancel_jobs()
        self.phase = "result"
        avg = (sum(self.times) / len(self.times)) if self.times else 0.0
        acc = self._accuracy()

        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": self.mix,
            "rounds": self.rounds,
            "kills": self.kills,
            "misses": self.misses,
            "accuracy": round(acc, 1),
            "score": self.score,
            "avg_ms": round(avg, 1) if self.times else None,
            "max_combo": self.max_combo,
            "duration_s": round(time.monotonic() - self.session_start, 1),
        }
        self.history.append(record)
        if len(self.history) > 200:
            self.history = self.history[-200:]
        save_history(HISTORY_FILE, self.history)

        self._show_result(record, avg, acc)

    def _show_result(self, record, avg, acc):
        self._clear_content()
        self.phase = "result"
        page = tk.Frame(self.content, bg=COLOR_BG)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        tk.Label(page, text="🏁 训练完成", font=("Microsoft YaHei", 22, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, pady=(20, 4))
        tk.Label(page, text=f"模式：{self._mode_name()}",
                 font=("Microsoft YaHei", 12), bg=COLOR_BG, fg=COLOR_DIM
                 ).grid(row=1, column=0, pady=(0, 16))

        panel = tk.Frame(page, bg=COLOR_PANEL, padx=32, pady=18)
        panel.grid(row=2, column=0)

        stats = [
            ("最终得分", f"{self.score}"),
            ("命中率", f"{acc:.1f}%"),
            ("击杀 / 失误", f"{self.kills} / {self.misses}"),
            ("平均反应时间", f"{avg:.0f} ms" if self.times else "—"),
            ("最大连击", f"×{self.max_combo}"),
            ("用时", f"{record['duration_s']} 秒"),
        ]
        for i, (k, v) in enumerate(stats):
            row = i // 2
            col = i % 2
            tk.Label(panel, text=k, font=("Microsoft YaHei", 11),
                     bg=COLOR_PANEL, fg=COLOR_DIM).grid(
                row=row * 2, column=col, sticky="w", padx=16, pady=(6, 0))
            tk.Label(panel, text=v, font=("Microsoft YaHei", 16, "bold"),
                     bg=COLOR_PANEL, fg=COLOR_TEXT).grid(
                row=row * 2 + 1, column=col, sticky="w", padx=16, pady=(0, 8))

        if self.times:
            text, color = rate_time(avg)
            tk.Label(page, text=text, font=("Microsoft YaHei", 15, "bold"),
                     bg=COLOR_BG, fg=color).grid(row=3, column=0, pady=(16, 4))

        tk.Label(page, text=self._best_summary(), font=("Microsoft YaHei", 11),
                 bg=COLOR_BG, fg="#ffd23f").grid(row=4, column=0, pady=(4, 12))

        btns = tk.Frame(page, bg=COLOR_BG)
        btns.grid(row=5, column=0)
        tk.Button(btns, text="再来一次", command=lambda: self._select_mode(self.mix),
                  font=("Microsoft YaHei", 12, "bold"), bg=COLOR_ACCENT, fg="white",
                  activebackground="#2b6fce", activeforeground="white",
                  relief="flat", padx=20, pady=6).pack(side="left", padx=8)
        tk.Button(btns, text="返回菜单", command=self._to_menu,
                  font=("Microsoft YaHei", 12), bg=COLOR_PANEL, fg=COLOR_TEXT,
                  activebackground="#32415a", activeforeground="white",
                  relief="flat", padx=20, pady=6).pack(side="left", padx=8)

    # ------------------------------------------------------------------
    # 历史最佳
    # ------------------------------------------------------------------
    def _best_summary(self):
        if not self.history:
            return "🏆 尚无历史纪录，快来挑战吧！"
        best_score = max(r["score"] for r in self.history)
        best_acc = max(r["accuracy"] for r in self.history)
        best_time = min((r["avg_ms"] for r in self.history
                         if r.get("avg_ms") is not None), default=None)
        parts = [f"🏆 历史最高分 {best_score}", f"最高命中率 {best_acc:.0f}%"]
        if best_time is not None:
            parts.append(f"最快平均 {best_time:.0f}ms")
        return "    ".join(parts)

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------
    def _cancel_jobs(self):
        if self.tick_job:
            try:
                self.root.after_cancel(self.tick_job)
            except Exception:
                pass
            self.tick_job = None
        try:
            self.root.unbind("<space>")
        except Exception:
            pass

    def on_close(self):
        self._cancel_jobs()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = DummyTrainerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
