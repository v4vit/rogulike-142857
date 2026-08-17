(() => {
  "use strict";

  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");

  // 网格尺寸
  const GRID = 20;          // 行/列数
  const CELL = canvas.width / GRID; // 每格像素

  const scoreEl = document.getElementById("score");
  const bestEl = document.getElementById("best");
  const overlay = document.getElementById("overlay");
  const overlayTitle = document.getElementById("overlay-title");
  const overlaySub = document.getElementById("overlay-sub");
  const startBtn = document.getElementById("start-btn");

  // 状态
  let snake = [];        // 身体数组，[row, col]
  let dir = { r: 0, c: 1 }; // 当前方向
  let nextDir = dir;     // 本帧内暂存的下一个方向（防止一帧内多次转向）
  let food = null;
  let score = 0;
  let running = false;
  let paused = false;
  let gameOver = false;

  const SPEED_MS = 130;  // 每步毫秒
  const BEST_KEY = "snake-best";

  let best = Number(localStorage.getItem(BEST_KEY)) || 0;
  bestEl.textContent = best;

  // 方向映射：WASD + 方向键
  const KEYMAP = {
    w: { r: -1, c: 0 },
    a: { r: 0, c: -1 },
    s: { r: 1, c: 0 },
    d: { r: 0, c: 1 },
    ArrowUp: { r: -1, c: 0 },
    ArrowDown: { r: 1, c: 0 },
    ArrowLeft: { r: 0, c: -1 },
    ArrowRight: { r: 0, c: 1 },
  };

  function randomFood() {
    let pos;
    do {
      pos = {
        r: Math.floor(Math.random() * GRID),
        c: Math.floor(Math.random() * GRID),
      };
    } while (snake.some(s => s.r === pos.r && s.c === pos.c));
    return pos;
  }

  function init() {
    snake = [
      { r: 10, c: 7 },
      { r: 10, c: 6 },
      { r: 10, c: 5 },
      { r: 10, c: 4 },
    ];
    dir = { r: 0, c: 1 };
    nextDir = dir;
    score = 0;
    gameOver = false;
    paused = false;
    food = randomFood();
    scoreEl.textContent = score;
  }

  // ---- 绘制 ----
  function draw() {
    // 背景
    ctx.fillStyle = "#1a2233";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 网格线
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 1;
    for (let i = 1; i < GRID; i++) {
      ctx.beginPath();
      ctx.moveTo(i * CELL, 0);
      ctx.lineTo(i * CELL, canvas.height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * CELL);
      ctx.lineTo(canvas.width, i * CELL);
      ctx.stroke();
    }

    // 食物
    if (food) {
      const pad = CELL * 0.22;
      ctx.fillStyle = "#f87171";
      ctx.beginPath();
      ctx.arc(
        food.c * CELL + CELL / 2,
        food.r * CELL + CELL / 2,
        CELL / 2 - pad,
        0, Math.PI * 2
      );
      ctx.fill();
    }

    // 蛇
    snake.forEach((seg, i) => {
      const pad = 1.5;
      const x = seg.c * CELL + pad;
      const y = seg.r * CELL + pad;
      const size = CELL - pad * 2;
      // 头部高亮
      const t = i === 0 ? 0 : 0.6;
      ctx.fillStyle = i === 0 ? "#4ade80" : `rgba(74, 222, 128, ${0.9 - t * 0.35})`;
      roundRect(ctx, x, y, size, size, 5);
      ctx.fill();

      // 眼睛（头部）：位于头部中心两侧，略偏向运动方向
      if (i === 0) {
        const cx = x + size / 2;
        const cy = y + size / 2;
        // 垂直方向向量（垂直于运动方向的左右）
        const px = -dir.r; // 垂直 x 分量
        const py = dir.c;  // 垂直 y 分量
        const side = 5;    // 眼睛离中心的横向距离
        const fwd = 3;     // 眼睛向前偏移量
        ctx.fillStyle = "#0a1020";
        for (const s of [-1, 1]) {
          ctx.beginPath();
          ctx.arc(
            cx + px * side * s + dir.c * fwd,
            cy + py * side * s + dir.r * fwd,
            2.6, 0, Math.PI * 2
          );
          ctx.fill();
        }
      }
    });
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // ---- 逻辑步进 ----
  function step() {
    if (!running || paused || gameOver) return;

    // 应用方向（禁止 180° 反向）
    if (
      !(nextDir.r === -dir.r && nextDir.c === -dir.c) &&
      !(nextDir.r === dir.r && nextDir.c === dir.c)
    ) {
      dir = nextDir;
    }

    const head = {
      r: snake[0].r + dir.r,
      c: snake[0].c + dir.c,
    };

    // 撞墙
    if (head.r < 0 || head.r >= GRID || head.c < 0 || head.c >= GRID) {
      return endGame();
    }

    // 撞到自己（尾巴即将移走，需排除）
    const eats = food && head.r === food.r && head.c === food.c;
    const body = eats ? snake : snake.slice(0, -1);
    if (body.some(s => s.r === head.r && s.c === head.c)) {
      return endGame();
    }

    snake.unshift(head);

    if (eats) {
      score += 10;
      scoreEl.textContent = score;
      food = randomFood();
    } else {
      snake.pop();
    }

    draw();
  }

  function endGame() {
    gameOver = true;
    running = false;
    if (score > best) {
      best = score;
      localStorage.setItem(BEST_KEY, best);
      bestEl.textContent = best;
    }
    overlayTitle.textContent = "游戏结束";
    overlaySub.innerHTML = `得分 <b>${score}</b> · 最高分 <b>${best}</b><br>再按一次开始`;
    startBtn.textContent = "再来一局";
    overlay.classList.remove("hidden");
  }

  function start() {
    init();
    draw();
    overlay.classList.add("hidden");
    running = true;
  }

  // ---- 输入 ----
  document.addEventListener("keydown", (e) => {
    const key = e.key.toLowerCase();

    // 空格：暂停 / 继续
    if (e.key === " ") {
      e.preventDefault();
      if (running && !gameOver) {
        paused = !paused;
        overlayTitle.textContent = paused ? "已暂停" : "贪吃蛇";
        overlaySub.innerHTML = paused ? "按 空格 继续" : "按 <b>W A S D</b> 移动";
        startBtn.style.display = paused ? "none" : "block";
        overlay.classList.toggle("hidden", !paused);
      }
      return;
    }

    const nd = KEYMAP[key];
    if (nd) {
      e.preventDefault();
      if (!running && !gameOver) return;
      nextDir = nd;
    }
  });

  startBtn.addEventListener("click", start);

  // 防止页面随方向键滚动
  window.addEventListener("keydown", (e) => {
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(e.key)) {
      e.preventDefault();
    }
  });

  // 游戏循环
  setInterval(step, SPEED_MS);

  // 初始渲染
  init();
  draw();
})();
