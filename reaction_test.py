#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反应力测试软件 (Reaction Time Tester)
=====================================
一个用 tkinter 实现的桌面反应力测试程序。

功能：
  - 基础反应时测试（屏幕随机变红 → 点击 → 记录毫秒）
  - 多次测试统计（平均 / 最快 / 最慢 / 标准差）
  - 历史记录保存（自动保存到本地 JSON 文件）
  - 排行榜 / 评级（根据反应时间给出等级评价）
  - 操作简单，界面友好

运行方式：
  python reaction_test.py
"""

import json
import os
import random
import time
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------------------
# 常量配置
# ---------------------------------------------------------------------------
APP_TITLE = "反应力测试"
VERSION = "1.0.0"

# 随机延迟范围（秒）——变红前的等待时间
DELAY_MIN = 2.0
DELAY_MAX = 5.0

# 测试轮数（默认）
DEFAULT_ROUNDS = 5
MAX_ROUNDS = 30

# 历史记录保存文件（固定在程序所在目录，避免受启动目录影响）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "reaction_history.json")

# 颜色定义
COLOR_IDLE = "#2e3b4e"      # 等待开始（深蓝灰）
COLOR_READY = "#f2f2f2"     # 准备中（浅灰，提示等待变红）
COLOR_STIMULUS = "#e74c3c"  # 变红（刺激出现）
COLOR_RESULT = "#27ae60"    # 结果显示（绿色）

# 评级阈值（毫秒），参考常见反应力测试标准
RATING_TABLE = [
    (180,  "⭐⭐⭐⭐⭐  超神反应", "#e74c3c"),
    (220,  "⭐⭐⭐⭐  非常出色",   "#e67e22"),
    (260,  "⭐⭐⭐  优秀",        "#f1c40f"),
    (300,  "⭐⭐  良好",         "#2ecc71"),
    (400,  "⭐  一般",          "#3498db"),
    (float("inf"), "普通水平，多多练习", "#95a5a6"),
]


def rate_reaction(ms: float):
    """根据反应时间（毫秒）返回 (评级文本, 颜色)。"""
    for threshold, text, color in RATING_TABLE:
        if ms <= threshold:
            return text, color
    return RATING_TABLE[-1][1], RATING_TABLE[-1][2]


def load_history(path: str):
    """加载历史记录；文件不存在或损坏时返回空列表。"""
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
    """把历史记录写入 JSON 文件。"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


class ReactionTestApp:
    """反应力测试主窗口。"""

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(f"{APP_TITLE} v{VERSION}")
        root.geometry("520x680")
        root.minsize(460, 600)
        root.configure(bg=COLOR_IDLE)

        # 历史记录
        self.history = load_history(HISTORY_FILE)

        # 当前会话状态
        self.rounds_total = DEFAULT_ROUNDS
        self.results = []          # 本局每轮反应时间（毫秒）
        self.phase = "idle"        # idle / waiting / stimulus / result
        self.round_index = 0
        self.stimulus_time = None  # 变红时刻（time.monotonic）
        self.delay_job = None      # 变红的定时任务
        self.timer_job = None      # 超时检测
        self.too_soon = False      # 是否过早点击

        self._build_ui()
        self._set_phase("idle")
        self._refresh_stats()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 顶部：标题
        tk.Label(
            self.root, text="⚡ 反应力测试", font=("Microsoft YaHei", 22, "bold"),
            bg=COLOR_IDLE, fg="white"
        ).grid(row=0, column=0, pady=(20, 5))

        # 中部：主测试区域（可点击）
        self.main_frame = tk.Frame(
            self.root, bg=COLOR_READY, cursor="hand2", height=220
        )
        self.main_frame.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")
        self.main_frame.grid_propagate(False)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.main_label = tk.Label(
            self.main_frame, text="", font=("Microsoft YaHei", 16),
            bg=COLOR_READY, fg="#333333", justify="center", wraplength=420
        )
        self.main_label.grid(row=0, column=0, sticky="nsew")

        for widget in (self.main_frame, self.main_label):
            widget.bind("<Button-1>", self._on_click)

        # 下部：控制面板
        control = tk.Frame(self.root, bg=COLOR_IDLE)
        control.grid(row=3, column=0, padx=30, pady=(5, 15), sticky="ew")
        control.grid_columnconfigure(4, weight=1)

        tk.Label(control, text="本轮轮数:", font=("Microsoft YaHei", 11),
                 bg=COLOR_IDLE, fg="white").grid(row=0, column=0, sticky="w")

        self.rounds_var = tk.StringVar(value=str(DEFAULT_ROUNDS))
        tk.Spinbox(control, from_=1, to=MAX_ROUNDS, textvariable=self.rounds_var,
                   width=4, font=("Microsoft YaHei", 11), command=self._on_rounds_change
                   ).grid(row=0, column=1, padx=(4, 15))

        self.start_btn = tk.Button(
            control, text="开始测试", command=self._start_test,
            font=("Microsoft YaHei", 11, "bold"), bg="#3498db", fg="white",
            activebackground="#2980b9", activeforeground="white",
            relief="flat", padx=16, pady=4
        )
        self.start_btn.grid(row=0, column=2, padx=(0, 10))

        self.reset_btn = tk.Button(
            control, text="重置", command=self._reset_session,
            font=("Microsoft YaHei", 11), bg="#7f8c8d", fg="white",
            activebackground="#95a5a6", activeforeground="white",
            relief="flat", padx=16, pady=4
        )
        self.reset_btn.grid(row=0, column=3)

        # 统计信息区
        stats = tk.Frame(self.root, bg=COLOR_IDLE)
        stats.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        stats.grid_columnconfigure(0, weight=1)

        self.stats_label = tk.Label(
            stats, text="", font=("Microsoft YaHei", 12),
            bg=COLOR_IDLE, fg="#cfd8dc", justify="left", anchor="w"
        )
        self.stats_label.grid(row=0, column=0, sticky="nsew")

        # 底部：历史最佳
        self.best_label = tk.Label(
            self.root, text="", font=("Microsoft YaHei", 11),
            bg=COLOR_IDLE, fg="#ffe082", justify="center"
        )
        self.best_label.grid(row=4, column=0, padx=30, pady=(0, 20), sticky="ew")

    # ------------------------------------------------------------------
    # 阶段切换
    # ------------------------------------------------------------------
    def _set_phase(self, phase):
        self.phase = phase
        if phase == "idle":
            self.main_frame.configure(bg=COLOR_IDLE)
            self.main_label.configure(
                bg=COLOR_IDLE, fg="white",
                text="点击下方「开始测试」\n\n屏幕变成红色后，尽快点击屏幕！"
            )
        elif phase == "waiting":
            self.main_frame.configure(bg=COLOR_READY)
            self.main_label.configure(
                bg=COLOR_READY, fg="#555555",
                text="等待变红…\n\n（请勿提前点击，否则本轮作废）"
            )
        elif phase == "stimulus":
            self.main_frame.configure(bg=COLOR_STIMULUS)
            self.main_label.configure(
                bg=COLOR_STIMULUS, fg="white",
                text="点击！💥"
            )
        elif phase == "result":
            self.main_frame.configure(bg=COLOR_RESULT)
            self.main_label.configure(bg=COLOR_RESULT, fg="white", text="")

    # ------------------------------------------------------------------
    # 测试逻辑
    # ------------------------------------------------------------------
    def _on_rounds_change(self):
        try:
            val = int(self.rounds_var.get())
            if 1 <= val <= MAX_ROUNDS:
                self.rounds_total = val
        except ValueError:
            pass

    def _start_test(self):
        self._cancel_jobs()
        try:
            val = int(self.rounds_var.get())
            self.rounds_total = max(1, min(MAX_ROUNDS, val))
        except ValueError:
            self.rounds_total = DEFAULT_ROUNDS
        self.rounds_var.set(str(self.rounds_total))

        self.results = []
        self.round_index = 0
        self.too_soon = False
        self._begin_round()

    def _begin_round(self):
        self.round_index += 1
        self.too_soon = False
        self._set_phase("waiting")
        self._refresh_stats()

        # 随机延迟后变红
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        self.delay_job = self.root.after(int(delay * 1000), self._show_stimulus)

    def _show_stimulus(self):
        self.stimulus_time = time.monotonic()
        self._set_phase("stimulus")
        # 超时检测：3 秒内未点击视为超时
        self.timer_job = self.root.after(3000, self._timeout)

    def _on_click(self, _event=None):
        if self.phase == "stimulus":
            # 记录反应时间
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
                self.timer_job = None
            elapsed = (time.monotonic() - self.stimulus_time) * 1000
            self._record_result(elapsed)
        elif self.phase == "waiting":
            # 过早点击：本轮作废，重新开始本轮
            self.too_soon = True
            if self.delay_job:
                self.root.after_cancel(self.delay_job)
                self.delay_job = None
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
                self.timer_job = None
            self._set_phase("result")
            self.main_label.configure(
                text=f"⚠️ 不要提前点击！\n\n本轮重新开始\n请等待屏幕变红"
            )
            self._refresh_stats()
            # 重新开始本轮
            self.root.after(1000, self._begin_round)
        # idle 状态下点击无操作

    def _timeout(self):
        self.timer_job = None
        self._set_phase("result")
        self.main_label.configure(text="⏱️ 超时未点击！\n\n本轮作废，重新开始")
        self._refresh_stats()
        self.root.after(1000, self._begin_round)

    def _record_result(self, ms):
        ms = round(ms, 1)
        self.results.append(ms)
        text, color = rate_reaction(ms)
        self._set_phase("result")
        self.main_label.configure(
            text=f"{ms:.0f} 毫秒\n\n评级：{text}", fg="white"
        )

        if self.round_index >= self.rounds_total:
            # 本局结束
            self._finish_session()
        else:
            self._refresh_stats()
            self.root.after(1200, self._begin_round)

    def _finish_session(self):
        self._refresh_stats()
        avg = sum(self.results) / len(self.results)
        avg_text, avg_color = rate_reaction(avg)
        self.main_label.configure(
            bg=COLOR_RESULT, fg="white",
            text=(
                f"🎉 本局完成！\n\n"
                f"平均反应：{avg:.0f} 毫秒\n"
                f"整体评级：{avg_text}"
            )
        )
        self._save_session_to_history()
        self._show_best()

    # ------------------------------------------------------------------
    # 统计与历史
    # ------------------------------------------------------------------
    def _refresh_stats(self):
        if not self.results:
            self.stats_label.configure(
                text=f"轮次进度：{max(self.round_index, 0)} / {self.rounds_total}\n"
                     "还没有数据，开始测试吧！"
            )
            return

        avg = sum(self.results) / len(self.results)
        best = min(self.results)
        worst = max(self.results)
        variance = sum((x - avg) ** 2 for x in self.results) / len(self.results)
        std = variance ** 0.5

        self.stats_label.configure(
            text=(
                f"轮次进度：{self.round_index} / {self.rounds_total}\n"
                f"已完成 {len(self.results)} 轮\n"
                f"平均：{avg:.0f} ms   |   最快：{best:.0f} ms   |   最慢：{worst:.0f} ms\n"
                f"标准差：{std:.1f} ms（越小越稳定）"
            )
        )

    def _save_session_to_history(self):
        avg = sum(self.results) / len(self.results)
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "rounds": self.results,
            "average_ms": round(avg, 1),
            "best_ms": round(min(self.results), 1),
        }
        self.history.append(record)
        # 只保留最近 200 条，避免文件无限膨胀
        if len(self.history) > 200:
            self.history = self.history[-200:]
        save_history(HISTORY_FILE, self.history)

    def _show_best(self):
        best = min((r["best_ms"] for r in self.history), default=None)
        if best is not None:
            text, color = rate_reaction(best)
            self.best_label.configure(
                text=f"🏆 历史最佳：{best:.0f} 毫秒（{text}）"
            )

    def _reset_session(self):
        self._cancel_jobs()
        self.results = []
        self.round_index = 0
        self._set_phase("idle")
        self._refresh_stats()

    def _cancel_jobs(self):
        for job in (self.delay_job, self.timer_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        self.delay_job = None
        self.timer_job = None

    def on_close(self):
        self._cancel_jobs()
        self.root.destroy()


def main():
    root = tk.Tk()
    # 尝试使用 Windows 高分辨率感知，避免文字模糊（非致命）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = ReactionTestApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
