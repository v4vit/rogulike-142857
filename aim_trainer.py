#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瞄准训练器 (Aim Trainer)
========================
一个用 tkinter + Canvas 实现的瞄准训练软件，功能类似 Aim Lab。

训练模式：
  - 网格/静态靶  ：小球随机出现在屏幕，逐个快速点击
  - 移动靶       ：小球持续移动，需预判并点击移动目标
  - 出现即消失   ：小球短暂出现后消失，需快速反应定位点击 (flick)

核心指标：
  - 命中率 accuracy
  - 平均反应时间 / 平均命中时间
  - 连击 combo
  - 每轮得分与历史最佳纪录（自动保存 JSON）

运行方式：
  python aim_trainer.py
"""

import json
import math
import os
import random
import sys
import time
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------------------
# 常量配置
# ---------------------------------------------------------------------------
APP_TITLE = "瞄准训练器"
VERSION = "1.0.0"

def _base_dir():
    """定位程序所在目录。

    - 打包成 exe 时：用 exe 所在目录（sys.executable），这样历史纪录会存到
      exe 旁边，不会因 PyInstaller 临时解压目录而丢失。
    - 源码运行时：用脚本所在目录。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _base_dir()
HISTORY_FILE = os.path.join(BASE_DIR, "aim_history.json")

# 颜色定义（深色主题，模拟 Aim Lab 风格）
COLOR_BG = "#1b2230"          # 主背景（深蓝灰）
COLOR_PANEL = "#242f42"       # 面板
COLOR_TEXT = "#e6edf3"        # 主文字
COLOR_DIM = "#8fa3b8"         # 次要文字
COLOR_ACCENT = "#3d8bfd"      # 强调蓝
COLOR_BALL = "#ff5a5a"        # 目标球（红）
COLOR_BALL_HIT = "#2ecc71"    # 命中反馈（绿）
COLOR_MISS = "#e74c3c"        # 失误反馈

# 默认设置
DEFAULT_ROUNDS = 20           # 每轮目标数
DEFAULT_BALL_R = 24           # 球半径
DEFAULT_SPEED = 5             # 移动靶速度（像素/帧）
DEFAULT_SHOW_MS = 600         # flick 模式球的显示时长（毫秒）
DEFAULT_3D = True             # 是否启用近大远小的 3D 景深效果

# 3D 景深参数
Z_NEAR = 0.0                  # 最近深度
Z_FAR = 1.0                   # 最远深度
Z_DEPTH_AMP = 0.78            # 深度引起的尺寸变化幅度（越大近大远小越明显）
Z_SPEED_FAR = 0.35            # 最远目标的移动速度缩放（相对近景）
# 深度视觉颜色：近球亮红，远球偏暗偏蓝（模拟空气透视）
Z_COLOR_NEAR = "#ff4545"      # 近处球颜色（亮）
Z_COLOR_FAR = "#a04060"       # 远处球颜色（暗/淡）

# 中央聚焦区：目标只出现在屏幕中央约占 1/4 面积的区域内
# 两个方向各取屏幕边长的 FOCUS 比例，面积 = FOCUS * FOCUS = 0.25
FOCUS_W = 0.5                 # 聚焦区宽占画布宽的比例
FOCUS_H = 0.5                 # 聚焦区高占画布高的比例
FOCUS_COLOR = "#3d8bfd"       # 聚焦区边框颜色

# 透视网格：聚焦区内的 3D 透视格子（近大远小）
GRID_COLS = 8                 # 纵向格子数（列）
GRID_ROWS = 8                 # 横向格子数（行）

# 移动靶的移动步进（毫秒/帧），约 60 FPS
MOVE_TICK_MS = 16
# flick 模式球消失后的冷却/重新出现延迟
FLICK_RESPAWN_MS = 250

# 评级阈值（平均命中时间/反应，毫秒），参考常见 fps 瞄准标准
RATING_TABLE = [
    (500, "⭐⭐⭐⭐⭐  顶级枪法", "#ff5a5a"),
    (650, "⭐⭐⭐⭐  非常出色",   "#ff8c42"),
    (800, "⭐⭐⭐  优秀",        "#ffd23f"),
    (1000, "⭐⭐  良好",         "#4cd964"),
    (float("inf"), "继续练习，稳步提升", "#8fa3b8"),
]


def rate_time(ms: float):
    """根据平均命中/反应时间（毫秒）返回 (评级文本, 颜色)。"""
    for threshold, text, color in RATING_TABLE:
        if ms <= threshold:
            return text, color
    return RATING_TABLE[-1][1], RATING_TABLE[-1][2]


def load_history(path: str):
    """加载历史纪录；文件不存在或损坏时返回空列表。"""
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


def save_history(path: str, records: list):
    """把历史纪录写入 JSON 文件。"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# 主应用
# ---------------------------------------------------------------------------
class AimTrainerApp:
    """瞄准训练器主窗口。"""

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(f"{APP_TITLE} v{VERSION}")
        root.geometry("900x640")
        root.minsize(760, 560)
        root.configure(bg=COLOR_BG)

        # 历史纪录
        self.history = load_history(HISTORY_FILE)

        # 当前设置
        self.rounds = DEFAULT_ROUNDS
        self.ball_r = DEFAULT_BALL_R
        self.speed = DEFAULT_SPEED
        self.show_ms = DEFAULT_SHOW_MS
        self.use_3d = DEFAULT_3D
        self.mode = None          # "grid" / "move" / "flick"

        # 训练会话状态
        self.phase = "menu"       # menu / playing / result
        self.round_index = 0
        self.hits = 0             # 命中数
        self.misses = 0           # 未命中（点击空白 + flick 超时）
        self.combo = 0
        self.max_combo = 0
        self.times = []           # 每次命中的反应/命中时间（毫秒）
        self.score = 0
        self.ball_id = None
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.ball_z = Z_NEAR      # 球的深度（0 近 ~ 1 远）
        self.ball_display_r = float(DEFAULT_BALL_R)  # 当前实际显示/判定半径
        self.ball_born = None     # 球出现时刻（time.monotonic）
        self.tick_job = None      # 动画定时器
        self.phase_job = None     # 阶段切换定时器
        self.session_start = 0.0

        self._build_ui()
        self._show_menu()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 顶部标题栏
        header = tk.Frame(self.root, bg=COLOR_BG)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 4))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="🎯 瞄准训练器", font=("Microsoft YaHei", 20, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        self.best_label = tk.Label(header, text="", font=("Microsoft YaHei", 11),
                                   bg=COLOR_BG, fg="#ffd23f")
        self.best_label.grid(row=0, column=2, sticky="e")
        self.menu_btn = tk.Button(header, text="返回菜单", command=self._to_menu,
                                  font=("Microsoft YaHei", 10), bg=COLOR_PANEL,
                                  fg=COLOR_TEXT, activebackground="#32415a",
                                  activeforeground="white", relief="flat", padx=10)
        self.menu_btn.grid(row=0, column=3, padx=(16, 0))

        # 内容区（菜单 / 画布 / 结算都放在这里）
        self.content = tk.Frame(self.root, bg=COLOR_BG)
        self.content.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # 页面切换
    # ------------------------------------------------------------------
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
        page.grid_rowconfigure(3, weight=1)
        page.grid_columnconfigure(0, weight=1)

        tk.Label(page, text="选择训练模式", font=("Microsoft YaHei", 18, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, pady=(10, 20))

        # 模式卡片
        cards = tk.Frame(page, bg=COLOR_BG)
        cards.grid(row=1, column=0)
        modes = [
            ("grid", "静态靶", "小球随机出现，逐个快速点击\n训练基础瞄准与反应"),
            ("move", "移动靶", "小球持续移动\n训练预判与动态瞄准"),
            ("flick", "出现即消失", "小球短暂出现后消失\n训练快速定位(flick)"),
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
                card.bind("<Enter>", lambda e, c=card: c.configure(
                    highlightthickness=2))
                card.bind("<Leave>", lambda e, c=card: c.configure(
                    highlightthickness=0))

        # 设置面板
        settings = tk.Frame(page, bg=COLOR_PANEL, padx=24, pady=16)
        settings.grid(row=2, column=0, pady=(24, 8))
        tk.Label(settings, text="⚙ 设置", font=("Microsoft YaHei", 13, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT).grid(row=0, column=0, columnspan=6,
                                                     sticky="w", pady=(0, 8))

        def row_label(r, text):
            tk.Label(settings, text=text, font=("Microsoft YaHei", 11),
                     bg=COLOR_PANEL, fg=COLOR_DIM).grid(row=r, column=0, sticky="w",
                                                        padx=(0, 8), pady=4)

        # 目标数
        row_label(1, "每轮目标数:")
        self.rounds_var = tk.IntVar(value=DEFAULT_ROUNDS)
        tk.Spinbox(settings, from_=5, to=100, textvariable=self.rounds_var,
                   width=5, font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=1, column=1, padx=(0, 20))

        # 球大小
        row_label(1, "球大小:")
        self.size_var = tk.IntVar(value=DEFAULT_BALL_R)
        tk.Spinbox(settings, from_=10, to=50, textvariable=self.size_var,
                   width=5, font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=1, column=3, padx=(0, 20))

        # 移动靶速度
        row_label(2, "移动速度:")
        self.speed_var = tk.IntVar(value=DEFAULT_SPEED)
        tk.Spinbox(settings, from_=2, to=20, textvariable=self.speed_var,
                   width=5, font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=2, column=1, padx=(0, 20))

        # flick 显示时长
        row_label(2, "显示时长(ms):")
        self.show_var = tk.IntVar(value=DEFAULT_SHOW_MS)
        tk.Spinbox(settings, from_=200, to=2000, increment=50,
                   textvariable=self.show_var, width=5,
                   font=("Microsoft YaHei", 11),
                   command=self._read_settings).grid(row=2, column=3, padx=(0, 20))

        # 3D 景深开关
        self.d3_var = tk.BooleanVar(value=DEFAULT_3D)
        tk.Checkbutton(settings, text="3D 景深（近大远小 + 透视网格）", variable=self.d3_var,
                       command=self._read_settings, bg=COLOR_PANEL, fg=COLOR_TEXT,
                       activebackground=COLOR_PANEL, activeforeground=COLOR_TEXT,
                       selectcolor=COLOR_BG, font=("Microsoft YaHei", 11)
                       ).grid(row=3, column=0, columnspan=6, sticky="w", pady=(4, 0))

        self._read_settings()

        # 底部历史最佳
        self.menu_best = tk.Label(page, text=self._best_summary(),
                                  font=("Microsoft YaHei", 11),
                                  bg=COLOR_BG, fg="#ffd23f")
        self.menu_best.grid(row=4, column=0, pady=(8, 0))

    def _read_settings(self):
        def clamp(var, lo, hi, default):
            try:
                v = int(var.get())
                return max(lo, min(hi, v))
            except (ValueError, tk.TclError):
                return default
        self.rounds = clamp(self.rounds_var, 5, 100, DEFAULT_ROUNDS)
        self.ball_r = clamp(self.size_var, 10, 50, DEFAULT_BALL_R)
        self.speed = clamp(self.speed_var, 2, 20, DEFAULT_SPEED)
        self.show_ms = clamp(self.show_var, 200, 2000, DEFAULT_SHOW_MS)
        try:
            self.use_3d = bool(self.d3_var.get())
        except tk.TclError:
            self.use_3d = DEFAULT_3D
        self.rounds_var.set(self.rounds)
        self.size_var.set(self.ball_r)
        self.speed_var.set(self.speed)
        self.show_var.set(self.show_ms)

    # ------------------------------------------------------------------
    # 开始训练
    # ------------------------------------------------------------------
    def _select_mode(self, mode):
        self.mode = mode
        self._read_settings()
        self.round_index = 0
        self.hits = 0
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
        canvas.bind("<Button-1>", self._on_click)

        # HUD（顶部叠加信息用 canvas 文本实现）
        self.hud_score = canvas.create_text(16, 14, anchor="nw",
                                            text="", fill=COLOR_TEXT,
                                            font=("Microsoft YaHei", 12, "bold"))
        self.hud_combo = canvas.create_text(self.canvas.winfo_reqwidth() - 16, 14,
                                            anchor="ne", text="", fill="#ffd23f",
                                            font=("Microsoft YaHei", 12, "bold"))
        self.hud_info = canvas.create_text(16, 44, anchor="nw", text="",
                                           fill=COLOR_DIM,
                                           font=("Microsoft YaHei", 11))

        self.canvas.bind("<Configure>", self._on_resize)
        self._draw_focus_frame()
        self._begin_round()
        self._start_clock()

    def _on_resize(self, _event=None):
        # 窗口尺寸变化时，重画透视网格
        if self.phase == "playing":
            self._draw_focus_frame()

    def _draw_focus_frame(self):
        """在画布中央绘制透视聚焦框（近大远小的梯形地面）+ 透视网格线。

        聚焦框不再是一个平面矩形，而是一个略带上抬、近宽远窄的透视平面，
        配合收拢的网格线，营造 3D 空间纵深感。
        """
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("focus")
        if not self.use_3d:
            # 平面模式：画普通矩形框即可
            cx, cy, half_w, half_h = self._focus_rect()
            self.canvas.create_rectangle(
                cx - half_w, cy - half_h, cx + half_w, cy + half_h,
                outline=FOCUS_COLOR, width=2, dash=(6, 4), tags=("focus",))
            self._raise_ball_above_focus()
            return

        w, h = self._canvas_size()
        cx, cy, near_w, far_w, top_y, bot_y = self._grid_geometry()

        # 地面（用稀疏点阵填充，弱化遮挡，让球能透出）
        self.canvas.create_polygon(
            cx - far_w / 2, top_y,
            cx + far_w / 2, top_y,
            cx + near_w / 2, bot_y,
            cx - near_w / 2, bot_y,
            fill="#1b2230", outline=FOCUS_COLOR, width=2, stipple="gray25",
            tags=("focus",))

        # 纵向网格线：GRID_COLS 列（近边到远边收拢），共 GRID_COLS+1 条
        for c in range(GRID_COLS + 1):
            f = c / GRID_COLS
            x_near = cx - near_w / 2 + near_w * f
            x_far = cx - far_w / 2 + far_w * f
            self.canvas.create_line(
                x_near, bot_y, x_far, top_y,
                fill=FOCUS_COLOR, width=1, tags=("focus",))

        # 横向网格线：GRID_ROWS 行（透视投影，近疏远密），共 GRID_ROWS+1 条
        for r in range(GRID_ROWS + 1):
            v = r / GRID_ROWS
            t = v * v                       # 平方投影：远处密、近处疏
            yy = top_y + (bot_y - top_y) * t
            w_at = far_w + (near_w - far_w) * t
            self.canvas.create_line(
                cx - w_at / 2, yy, cx + w_at / 2, yy,
                fill=FOCUS_COLOR, width=1, tags=("focus",))

        # 焦点框重画后，始终把球提升到顶层，避免被网格遮住
        self._raise_ball_above_focus()

    def _raise_ball_above_focus(self):
        """把球提升到焦点框之上（球应显示在透视网格最上层）。"""
        if hasattr(self, "canvas"):
            try:
                # 把球的所有图形提升到所有焦点框图形之上
                self.canvas.tag_raise("ball", "focus")
                # 再整体提到最顶层，确保不被其它元素遮挡
                self.canvas.tag_raise("ball")
            except tk.TclError:
                pass

    def _on_click(self, event):
        if self.phase != "playing" or self.ball_id is None:
            return
        # 命中判定：点到球中心距离 <= 当前显示半径 + 容差
        # （3D 模式下球越大越容易命中，越小越难，符合近大远小手感）
        tol = 6
        dx = event.x - self.ball_x
        dy = event.y - self.ball_y
        dist = math.hypot(dx, dy)
        if dist <= self.ball_display_r + tol:
            self._hit()
        else:
            self._miss_click()

    # ------------------------------------------------------------------
    # 回合逻辑
    # ------------------------------------------------------------------
    def _begin_round(self):
        self.round_index += 1
        self._spawn_ball()
        if self.mode == "flick":
            # flick：球出现一段时间后消失
            self.phase_job = self.root.after(self.show_ms, self._flick_disappear)
        self._update_hud()

    def _canvas_size(self):
        try:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
        except Exception:
            w = h = 400
        if w < 10 or h < 10:
            w, h = self.content.winfo_width(), self.content.winfo_height()
        return max(w, 50), max(h, 50)

    def _focus_rect(self):
        """返回中央聚焦区 (cx, cy, half_w, half_h)。

        目标只出现在这个约占屏幕 1/4 面积的中央区域内。
        """
        w, h = self._canvas_size()
        half_w = w * FOCUS_W / 2
        half_h = h * FOCUS_H / 2
        return w / 2, h / 2, half_w, half_h

    def _grid_geometry(self):
        """返回透视网格梯形几何参数 (cx, cy, near_w, far_w, top_y, bot_y)。

        聚焦区被画成一个近大远小的透视梯形：
          - near_w / far_w：近边（底）/ 远边（顶）的宽度
          - top_y / bot_y  ：顶 / 底的纵向坐标（顶部略微上抬）
        """
        cx, cy, half_w, half_h = self._focus_rect()
        near_w = half_w * 2 * 1.15
        far_w = half_w * 2 * 0.55
        top_y = cy - half_h - half_h * 0.12
        bot_y = cy + half_h
        return cx, cy, near_w, far_w, top_y, bot_y

    def _grid_cell_center(self, col: int, row: int):
        """返回第 (col, row) 个格子的中心在画布上的坐标 (x, y)。

        格子编号：col = 0..GRID_COLS-1（左到右），row = 0..GRID_ROWS-1（远到近）。
        采用透视映射：远处行窄、近处行宽，纵向按平方曲线分布（近疏远密）。
        """
        cx, cy, near_w, far_w, top_y, bot_y = self._grid_geometry()
        # 该格子在参数空间中的中心（v：0=远/上，1=近/下）
        u = (col + 0.5) / GRID_COLS
        v = (row + 0.5) / GRID_ROWS
        # 纵向：透视投影（平方曲线，近疏远密）
        y = top_y + (bot_y - top_y) * (v * v)
        # 该深度处网格宽度
        w_at = far_w + (near_w - far_w) * v
        x = cx - w_at / 2 + w_at * u
        return x, y

    def _depth_radius(self, z: float) -> float:
        """根据深度 z 返回球在当前深度下的显示半径。

        3D 景深开启时：越近（z 小）球越大，越远（z 大）球越小。
        关闭时：统一为设置的基础半径。
        """
        if not self.use_3d:
            return float(self.ball_r)
        # 近大远小：z=0 -> 基础半径*(1+AMP)，z=1 -> 基础半径*(1-AMP)
        return self.ball_r * (1.0 + Z_DEPTH_AMP * (Z_FAR - z) / (Z_FAR - Z_NEAR) * 2.0
                              - Z_DEPTH_AMP)

    def _depth_color(self, z: float) -> str:
        """根据深度 z 返回球的颜色（近亮远暗，模拟空气透视）。

        3D 关闭时返回统一球色。
        """
        if not self.use_3d:
            return COLOR_BALL
        t = (z - Z_NEAR) / (Z_FAR - Z_NEAR)   # 0 近 ~ 1 远
        # 在近色与远色之间线性插值 RGB
        near = (0xFF, 0x45, 0x45)
        far = (0xA0, 0x40, 0x60)
        r = int(near[0] + (far[0] - near[0]) * t)
        g = int(near[1] + (far[1] - near[1]) * t)
        b = int(near[2] + (far[2] - near[2]) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _spawn_ball(self):
        if self.ball_id is not None:
            self.canvas.delete("ball")
            self.ball_id = None
        w, h = self._canvas_size()

        # 目标落在透视网格某个格子的中心
        # 随机选一个格子 (col, row)：col 左到右，row 远到近
        col = random.randrange(GRID_COLS)
        row = random.randrange(GRID_ROWS)

        if self.use_3d:
            # 深度由格子行决定：越靠上（row 小）越远（z 大），越靠下越近（z 小）
            span = max(GRID_ROWS - 1, 1)
            self.ball_z = Z_NEAR + (Z_FAR - Z_NEAR) * (GRID_ROWS - 1 - row) / span
        else:
            self.ball_z = Z_NEAR

        r = self._depth_radius(self.ball_z)
        self.ball_display_r = r

        # 球中心对齐到该格子的中心（透视映射）
        self.ball_x, self.ball_y = self._grid_cell_center(col, row)

        if self.mode == "move":
            # 移动靶：随机方向，速度随深度缩放（远快近慢/远慢近快取决于设定）
            ang = random.uniform(0, math.tau)
            depth_speed = 1.0 - (1.0 - Z_SPEED_FAR) * (self.ball_z - Z_NEAR) / (Z_FAR - Z_NEAR)
            speed = self.speed * depth_speed
            self.ball_vx = math.cos(ang) * speed
            self.ball_vy = math.sin(ang) * speed

        self.ball_born = time.monotonic()
        self._draw_ball(COLOR_BALL)
        # 球要显示在透视网格之上，避免被聚焦框遮住
        if self.ball_id is not None:
            self.canvas.tag_raise("ball")

    def _draw_ball(self, _color=None):
        r = self.ball_display_r
        # 用 tag "ball" 统一管理球体及其装饰，方便整体增删
        self.canvas.delete("ball")

        # 3D：底部投影（近球阴影大而明显，远球阴影小且淡）
        if self.use_3d:
            t = (self.ball_z - Z_NEAR) / (Z_FAR - Z_NEAR) if Z_FAR > Z_NEAR else 0.0
            shadow_r = r * (1.05 - 0.3 * t)
            shadow_alpha = 1.0 - 0.5 * t   # 远处阴影更淡
            shadow_hex = int(0x00 * (1 - shadow_alpha) + 0x1b * shadow_alpha)
            sh = f"#{shadow_hex:02x}{shadow_hex:02x}{shadow_hex:02x}"
            self.canvas.create_oval(
                self.ball_x - shadow_r, self.ball_y - shadow_r * 0.7 + r * 0.9,
                self.ball_x + shadow_r, self.ball_y + shadow_r * 0.7 + r * 0.9,
                fill=sh, outline="", tags=("ball",))

        color = self._depth_color(self.ball_z) if self.use_3d else COLOR_BALL

        # 球体渲染：主圆 + 暗部（下） + 高光（上偏左），模拟球体光照立体感
        # 主圆
        self.ball_id = self.canvas.create_oval(
            self.ball_x - r, self.ball_y - r, self.ball_x + r, self.ball_y + r,
            fill=color, outline="", tags=("ball",))

        if self.use_3d:
            # 偏右下暗部（做深色弧形，营造下半球暗面）
            dark = self._shade_color(color, -0.45)
            self.canvas.create_oval(
                self.ball_x - r * 0.92, self.ball_y - r * 0.15,
                self.ball_x + r * 0.92, self.ball_y + r * 1.0,
                fill=dark, outline="", tags=("ball",))
            # 偏左上主高光（亮色椭圆，模拟顶部受光）
            light = self._shade_color(color, 0.55)
            self.canvas.create_oval(
                self.ball_x - r * 0.6, self.ball_y - r * 1.0,
                self.ball_x + r * 0.6, self.ball_y - r * 0.15,
                fill=light, outline="", tags=("ball",))
            # 小镜面高光（近顶偏左的小亮斑，让球体感更强）
            self.canvas.create_oval(
                self.ball_x - r * 0.30, self.ball_y - r * 0.72,
                self.ball_x + r * 0.05, self.ball_y - r * 0.38,
                fill="#ffffff", outline="", tags=("ball",))
        else:
            # 平面模式：保留内圈准星高光
            self.canvas.create_oval(
                self.ball_x - r / 2.6, self.ball_y - r / 2.6,
                self.ball_x + r / 2.6, self.ball_y + r / 2.6,
                outline="#ffffff", width=2, tags=("ball",))

    @staticmethod
    def _shade_color(hex_color: str, factor: float) -> str:
        """把 #rrggbb 颜色按 factor 提亮（正）或压暗（负）后返回新颜色。"""
        h = hex_color.lstrip("#")
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        def adj(v):
            if factor >= 0:
                return int(v + (255 - v) * factor)
            return int(v * (1 + factor))
        return f"#{adj(r):02x}{adj(g):02x}{adj(b):02x}"

    def _flick_disappear(self):
        self.phase_job = None
        if self.phase != "playing":
            return
        if self.ball_id is not None:
            # 超时未点击 → 记一次失误，球消失
            self.canvas.delete("ball")
            self.ball_id = None
            self._miss_timeout()
        # 等待后生成下一个球
        self.phase_job = self.root.after(FLICK_RESPAWN_MS, self._next_after_miss)

    def _next_after_miss(self):
        self.phase_job = None
        if self.phase == "playing":
            self._begin_round()

    def _hit(self):
        now = time.monotonic()
        ms = (now - self.ball_born) * 1000
        self.times.append(ms)
        self.hits += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        # 得分：基础分 + 连击加成 + 速度加成 + 深度加成
        base = 100
        combo_bonus = min(self.combo - 1, 10) * 10
        speed_bonus = max(0, 50 - int(ms / 20))
        depth_bonus = 0
        if self.use_3d:
            # 球越远（越小、越难打中）得分越高，鼓励挑战远处小目标
            depth_bonus = int((self.ball_z - Z_NEAR) / (Z_FAR - Z_NEAR) * 40)
        gained = base + combo_bonus + speed_bonus + depth_bonus
        self.score += gained

        # 命中反馈（3D 模式下标注目标远近）
        if self.ball_id is not None:
            self.canvas.delete("ball")
            self.ball_id = None
        hit_text = f"+{gained}"
        if self.use_3d:
            depth_ratio = (self.ball_z - Z_NEAR) / (Z_FAR - Z_NEAR)
            label = "远" if depth_ratio >= 0.5 else "近"
            hit_text = f"+{gained}  {label}"
        self._flash_feedback(self.ball_x, self.ball_y, COLOR_BALL_HIT,
                             hit_text, ms)
        self._update_hud()

        if self.round_index >= self.rounds:
            self.root.after(300, self._finish)
        else:
            if self.mode == "flick" and self.phase_job:
                self.root.after_cancel(self.phase_job)
                self.phase_job = None
            self.root.after(150, self._begin_round)

    def _miss_click(self):
        self.combo = 0
        self.misses += 1
        self._flash_feedback(self.ball_x, self.ball_y, COLOR_MISS, "MISS", None)
        self._update_hud()

    def _miss_timeout(self):
        self.combo = 0
        self.misses += 1
        self._update_hud()

    def _flash_feedback(self, x, y, color, text, ms):
        r = self.ball_display_r
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                outline=color, width=3)
        self.canvas.create_text(x, y, text=text, fill=color,
                                font=("Microsoft YaHei", 13, "bold"))
        if ms is not None:
            self.canvas.create_text(x, y + r + 16, text=f"{ms:.0f} ms",
                                    fill=COLOR_DIM,
                                    font=("Microsoft YaHei", 10))
        self.root.after(400, self._clear_feedback)

    def _clear_feedback(self):
        if self.phase == "playing" and self.canvas:
            # 删除非球、非 HUD、非聚焦边框的图形（反馈层）
            items = self.canvas.find_all()
            for i in items:
                if i in (self.hud_score, self.hud_combo, self.hud_info):
                    continue
                tags = self.canvas.gettags(i)
                if "ball" in tags or "focus" in tags:
                    continue
                self.canvas.delete(i)

    # ------------------------------------------------------------------
    # 移动靶动画
    # ------------------------------------------------------------------
    def _start_clock(self):
        if self.mode == "move":
            self._move_tick()

    def _move_tick(self):
        self.tick_job = self.root.after(MOVE_TICK_MS, self._move_tick)
        if self.phase != "playing":
            return
        if self.ball_id is None:
            return
        w, h = self._canvas_size()
        r = self.ball_display_r
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # 边界反弹：限定在中央聚焦区内（用当前显示半径）
        cx, cy, half_w, half_h = self._focus_rect()
        r = self.ball_display_r
        if self.ball_x < cx - half_w + r:
            self.ball_x = cx - half_w + r
            self.ball_vx = abs(self.ball_vx)
        elif self.ball_x > cx + half_w - r:
            self.ball_x = cx + half_w - r
            self.ball_vx = -abs(self.ball_vx)
        if self.ball_y < cy - half_h + r:
            self.ball_y = cy - half_h + r
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y > cy + half_h - r:
            self.ball_y = cy + half_h - r
            self.ball_vy = -abs(self.ball_vy)
        # _draw_ball 内部会用 tag 先删旧球再画新球，避免残留
        self._draw_ball(COLOR_BALL)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def _update_hud(self):
        if not hasattr(self, "canvas") or self.phase != "playing":
            return
        mode_name = {"grid": "静态靶", "move": "移动靶", "flick": "出现即消失"}[self.mode]
        self.canvas.itemconfigure(
            self.hud_score,
            text=f"{mode_name}   第 {self.round_index}/{self.rounds} 个   得分 {self.score}")
        combo_text = f"连击 ×{self.combo}" if self.combo >= 2 else ""
        self.canvas.itemconfigure(self.hud_combo, text=combo_text)
        acc = self._accuracy()
        self.canvas.itemconfigure(
            self.hud_info,
            text=f"命中率 {acc:.0f}%   命中 {self.hits}   未中 {self.misses}")

    def _accuracy(self):
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total * 100

    # ------------------------------------------------------------------
    # 结算
    # ------------------------------------------------------------------
    def _finish(self):
        self._cancel_jobs()
        self.phase = "result"
        avg = (sum(self.times) / len(self.times)) if self.times else 0.0
        acc = self._accuracy()

        # 保存到历史
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": self.mode,
            "rounds": self.rounds,
            "hits": self.hits,
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

        mode_name = {"grid": "静态靶", "move": "移动靶", "flick": "出现即消失"}[self.mode]
        tk.Label(page, text="🎉 训练完成", font=("Microsoft YaHei", 22, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, pady=(20, 4))
        tk.Label(page, text=f"模式：{mode_name}",
                 font=("Microsoft YaHei", 12), bg=COLOR_BG, fg=COLOR_DIM
                 ).grid(row=1, column=0, pady=(0, 16))

        panel = tk.Frame(page, bg=COLOR_PANEL, padx=32, pady=18)
        panel.grid(row=2, column=0)

        stats = [
            ("最终得分", f"{self.score}"),
            ("命中率", f"{acc:.1f}%"),
            ("命中 / 未中", f"{self.hits} / {self.misses}"),
            ("平均命中时间", f"{avg:.0f} ms" if self.times else "—"),
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

        # 评级
        if self.times:
            text, color = rate_time(avg)
            tk.Label(page, text=text, font=("Microsoft YaHei", 15, "bold"),
                     bg=COLOR_BG, fg=color).grid(row=3, column=0, pady=(16, 4))

        # 历史最佳提示
        tk.Label(page, text=self._best_summary(), font=("Microsoft YaHei", 11),
                 bg=COLOR_BG, fg="#ffd23f").grid(row=4, column=0, pady=(4, 12))

        btns = tk.Frame(page, bg=COLOR_BG)
        btns.grid(row=5, column=0)
        tk.Button(btns, text="再来一次", command=lambda: self._select_mode(self.mode),
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

    def _update_best_label(self):
        if hasattr(self, "best_label"):
            self.best_label.configure(text=self._best_summary())

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------
    def _cancel_jobs(self):
        for job in (self.tick_job, self.phase_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        self.tick_job = None
        self.phase_job = None

    def on_close(self):
        self._cancel_jobs()
        self.root.destroy()


def main():
    root = tk.Tk()
    # 高 DPI 感知，避免文字模糊（非致命）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = AimTrainerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
