// Mathbuddy design layer (spec 777): small moments on top of design.css.
// It only adds data-mb-* attributes and its own elements (confetti canvas,
// "+1"); it never changes what Streamlit shows, so the app works without it.
(() => {
  const VERSION = "777-1";
  if (window.__mathbuddyDesign === VERSION) return;
  window.__mathbuddyDesign = VERSION;

  const doc = document;
  const root = doc.documentElement;
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Streamlit reuses page elements for new content, so every mark is checked
  // again on every change and removed where it no longer fits.
  function flag(element, name, on) {
    if (on === name in element.dataset) return;
    if (on) element.dataset[name] = "";
    else delete element.dataset[name];
  }
  function unflag(selector, name, fits) {
    doc.querySelectorAll(selector).forEach((element) => {
      if (!element.matches(fits)) flag(element, name, false);
    });
  }

  // --- Light or dark: follow the colours Streamlit actually uses ---
  function brightness(color) {
    const parts = (color || "").match(/[\d.]+/g);
    if (!parts || parts.length < 3) return 0;
    const [r, g, b] = parts.map(Number);
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  }
  function syncTheme() {
    const app = doc.querySelector(".stApp");
    if (!app) return;
    const theme = brightness(getComputedStyle(app).color) > 0.6 ? "dark" : "light";
    if (root.dataset.mbTheme !== theme) root.dataset.mbTheme = theme;
  }

  // --- A maths symbol for every operation, number type and topic ---
  const GLYPHS = {
    Addition: "+",
    Subtraction: "−",
    Multiplication: "×",
    Division: "÷",
    Random: "?",
    Percentage: "%",
    Square: "x²",
    "Square root": "√",
    "Square numbers": "x²",
    "Natural numbers": "ℕ",
    Decimals: ".5",
    "Large numbers": "10⁶",
    Money: "€",
    Fractions: "½",
    "Word problems": "Aa",
    "Mixed tasks": "±",
    "Digit sums": "Σ",
    "Rule of three": "∝",
    Equations: "x=",
    "Chain calculations": "→",
    "Fun with fractions": "⅔",
    Basics: "1+1",
    "Case interview": "€%",
    "Estimating & rounding": "≈",
  };
  function glyphFor(text) {
    const name = (text || "").replace(/\s*\(\d+\)\s*$/, "").trim();
    return GLYPHS[name];
  }
  const GLYPH_BUTTONS =
    '[data-testid="stButtonGroup"] button[data-variant="pills"],' +
    '[class*="st-key-kn_category_"] button, [class*="st-key-tb_category_"] button';
  function tagGlyphs() {
    unflag("[data-mb-glyph]", "mbGlyph", GLYPH_BUTTONS);
    doc.querySelectorAll(GLYPH_BUTTONS).forEach((button) => {
      const glyph = glyphFor(button.textContent);
      if (!glyph) flag(button, "mbGlyph", false);
      else if (button.dataset.mbGlyph !== glyph) button.dataset.mbGlyph = glyph;
    });
  }

  // --- Cards: st.container(border=True) has a border, other containers do not ---
  const CARD_PLACES = '[data-testid="stMain"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"]';
  function tagCards() {
    unflag("[data-mb-card]", "mbCard", CARD_PLACES);
    unflag("[data-mb-example]", "mbExample", CARD_PLACES);
    doc.querySelectorAll(CARD_PLACES).forEach((block) => {
      const card = parseFloat(getComputedStyle(block).borderTopWidth) > 0;
      flag(block, "mbCard", card);
      const caption = card && block.querySelector('[data-testid="stCaptionContainer"]');
      flag(block, "mbExample", !!caption && caption.textContent.trim().startsWith("Example task"));
    });
  }

  function tagEmptyCells() {
    unflag("[data-mb-empty]", "mbEmpty", '[data-testid="stTable"] tbody td');
    doc.querySelectorAll('[data-testid="stTable"] tbody td').forEach((cell) => {
      flag(cell, "mbEmpty", cell.textContent.trim() === "–");
    });
  }

  // --- Tests: the seconds left as a ring that empties ---
  const timers = new WeakMap();
  function seconds(text) {
    const value = (text || "").trim();
    if (/^\d+$/.test(value)) return Number(value);
    const clock = value.match(/^(\d+):(\d{2})$/);
    return clock ? Number(clock[1]) * 60 + Number(clock[2]) : null;
  }
  function tagTimer() {
    const top = doc.querySelector("[data-mb-topbar]");
    const full = Number(top && top.dataset.mbTestSeconds) || 60;
    unflag("[data-mb-timer]", "mbTimer", '[data-testid="stMetric"]');
    unflag("[data-mb-urgent]", "mbUrgent", '[data-testid="stMetric"]');
    doc.querySelectorAll('[data-testid="stMain"] [data-testid="stMetric"]').forEach((metric) => {
      const label = metric.querySelector('[data-testid="stMetricLabel"]');
      const isTimer =
        !!label && label.textContent.trim() === "Time left" && !metric.closest('[data-testid="stHorizontalBlock"]');
      flag(metric, "mbTimer", isTimer);
      if (!isTimer) {
        flag(metric, "mbUrgent", false);
        return;
      }
      const value = seconds(metric.querySelector('[data-testid="stMetricValue"]')?.textContent);
      if (value === null) return;
      const state = timers.get(metric) || { max: Math.max(full, value), last: value };
      if (value > state.last) state.max = Math.max(full, value); // a new run started
      state.last = value;
      timers.set(metric, state);
      metric.style.setProperty("--mb-p", Math.max(0, Math.min(1, value / state.max)).toFixed(4));
      flag(metric, "mbUrgent", value <= 10);
    });
  }

  // --- A new task pops in ---
  const HERO =
    '[data-testid="stElementContainer"]:has(> [data-testid="stHeading"]):has(+ [data-testid="stLayoutWrapper"] > [data-testid="stForm"]) > [data-testid="stHeading"],' +
    '[data-testid="stElementContainer"]:has(> [data-testid="stHeading"]):has(+ [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] [class*="choice_"]) > [data-testid="stHeading"]';
  const COUNTDOWN = '.stApp:has(.st-key-cancel, .st-key-tr_cancel) [data-testid="stMain"] [data-testid="stHeading"] h2';
  const POPPING = [HERO, COUNTDOWN, ".chain-big", '[data-mb-timer] [data-testid="stMetricValue"]'].join(",");
  const texts = new WeakMap();
  function replay(element, attribute) {
    element.removeAttribute(attribute);
    void element.offsetWidth; // restart the animation
    element.setAttribute(attribute, "");
    clearTimeout(element.__mbTimeout);
    element.__mbTimeout = setTimeout(() => element.removeAttribute(attribute), 650);
  }
  function popChanged() {
    let elements;
    try {
      elements = doc.querySelectorAll(POPPING);
    } catch (error) {
      return; // a browser without :has()
    }
    elements.forEach((element) => {
      const text = element.textContent;
      const before = texts.get(element);
      texts.set(element, text);
      if (before !== undefined && before !== text && !element.matches('[data-mb-timer] [data-testid="stMetricValue"]')) {
        replay(element, "data-mb-pop");
      }
    });
  }
  function hero() {
    try {
      return doc.querySelector(HERO);
    } catch (error) {
      return null;
    }
  }

  // --- Confetti ---
  const COLORS = ["#6c47ff", "#a04bff", "#ff7a59", "#ffc53d", "#12b886", "#2f80ed", "#ff6b8b"];
  let canvas = null;
  let context = null;
  let pieces = [];
  let frame = 0;
  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(innerWidth * ratio);
    canvas.height = Math.round(innerHeight * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  function launch({ x, y, angle = -90, spread = 60, count = 80, power = 1 }) {
    if (calm.matches || doc.hidden) return;
    if (!canvas) {
      canvas = doc.createElement("canvas");
      canvas.className = "mb-confetti";
      canvas.setAttribute("aria-hidden", "true");
      doc.body.appendChild(canvas);
      context = canvas.getContext("2d");
      addEventListener("resize", resize);
    }
    if (!canvas.isConnected) doc.body.appendChild(canvas);
    resize();
    for (let i = 0; i < count; i += 1) {
      const direction = ((angle + (Math.random() - 0.5) * spread * 2) * Math.PI) / 180;
      const speed = (7 + Math.random() * 9) * power;
      pieces.push({
        x,
        y,
        vx: Math.cos(direction) * speed,
        vy: Math.sin(direction) * speed,
        gravity: 0.28 + Math.random() * 0.12,
        size: 6 + Math.random() * 7,
        spin: Math.random() * Math.PI,
        turn: (Math.random() - 0.5) * 0.35,
        wobble: Math.random() * 10,
        color: COLORS[i % COLORS.length],
        round: Math.random() < 0.3,
        age: 0,
        life: 80 + Math.random() * 60,
      });
    }
    if (!frame) frame = requestAnimationFrame(draw);
  }
  // Time based, so confetti looks the same on 60 Hz and 120 Hz screens.
  let last = 0;
  function draw(now) {
    const step = last ? Math.min(3, (now - last) / 16.7) : 1;
    last = now;
    context.clearRect(0, 0, innerWidth, innerHeight);
    pieces = pieces.filter((piece) => piece.age < piece.life && piece.y < innerHeight + 40);
    for (const piece of pieces) {
      piece.age += step;
      const drag = Math.pow(0.984, step);
      piece.vx *= drag;
      piece.vy = piece.vy * drag + piece.gravity * step;
      piece.x += (piece.vx + Math.sin((piece.age + piece.wobble) / 7) * 0.6) * step;
      piece.y += piece.vy * step;
      piece.spin += piece.turn * step;
      context.save();
      context.globalAlpha = Math.max(0, Math.min(1, (piece.life - piece.age) / 25));
      context.translate(piece.x, piece.y);
      context.rotate(piece.spin);
      context.fillStyle = piece.color;
      if (piece.round) {
        context.beginPath();
        context.arc(0, 0, piece.size / 2.6, 0, Math.PI * 2);
        context.fill();
      } else {
        const height = (piece.size / 2) * Math.abs(Math.cos(piece.spin * 2)) + 1.5;
        context.fillRect(-piece.size / 2, -piece.size / 4, piece.size, height);
      }
      context.restore();
    }
    if (pieces.length) {
      frame = requestAnimationFrame(draw);
    } else {
      frame = 0;
      last = 0;
      context.clearRect(0, 0, innerWidth, innerHeight);
    }
  }
  function celebrate() {
    launch({ x: innerWidth * 0.12, y: innerHeight + 10, angle: -62, spread: 22, count: 90, power: 1.25 });
    launch({ x: innerWidth * 0.88, y: innerHeight + 10, angle: -118, spread: 22, count: 90, power: 1.25 });
    setTimeout(() => launch({ x: innerWidth / 2, y: innerHeight * 0.3, angle: -90, spread: 100, count: 70, power: 0.8 }), 260);
  }
  function cheer() {
    launch({ x: innerWidth / 2, y: innerHeight * 0.32, angle: -90, spread: 70, count: 70, power: 0.85 });
  }

  // Celebrate once when a win or a result appears, not on every rerun.
  const BIG = /^(New highscore!|You solved it!|You found it!)/;
  const SMALL = /^(Right!|Time's up|Training finished|Practice finished)/;
  let shown = new Set();
  let ready = false;
  function celebrations() {
    const now = new Set();
    unflag("[data-mb-win]", "mbWin", '[data-testid="stAlert"]');
    doc.querySelectorAll('[data-testid="stMain"] :is([data-testid="stAlert"], [data-testid="stHeading"])').forEach((element) => {
      const text = element.textContent.trim();
      if (element.matches('[data-testid="stAlert"]')) flag(element, "mbWin", BIG.test(text));
      if (BIG.test(text) || SMALL.test(text)) now.add(text.slice(0, 80));
    });
    if (ready) {
      const fresh = [...now].filter((text) => !shown.has(text));
      if (fresh.some((text) => BIG.test(text))) celebrate();
      else if (fresh.length) cheer();
    }
    shown = now;
    ready = true;
  }

  // --- Right or wrong: react to the green / red flash of the answer field ---
  const seenStyles = new WeakSet();
  function plusOne() {
    if (calm.matches) return;
    const field = doc.querySelector('[data-testid="stForm"] [data-testid="stTextInputRootElement"]');
    const box = (field || hero() || doc.body).getBoundingClientRect();
    const plus = doc.createElement("div");
    plus.className = "mb-plus";
    plus.textContent = "+1";
    plus.setAttribute("aria-hidden", "true");
    plus.style.left = `${box.left + box.width / 2}px`;
    plus.style.top = `${box.top - 6}px`;
    doc.body.appendChild(plus);
    setTimeout(() => plus.remove(), 950);
    launch({ x: box.left + box.width / 2, y: box.top + 8, angle: -90, spread: 55, count: 16, power: 0.55 });
  }
  function onStyle(style) {
    if (seenStyles.has(style)) return;
    seenStyles.add(style);
    const css = style.textContent || "";
    if (!/flash-\d+/.test(css)) return;
    const answer = css.includes('answer [data-testid="stTextInputRootElement"]');
    if (css.includes("22, 163, 74")) {
      if (answer) plusOne();
    } else if (css.includes("220, 38, 38")) {
      const card = answer ? hero() : null;
      if (card && !calm.matches) replay(card, "data-mb-shake");
      if (navigator.vibrate) {
        try {
          navigator.vibrate(35);
        } catch (error) {
          /* not allowed here */
        }
      }
    }
  }
  doc.querySelectorAll("style").forEach((style) => seenStyles.add(style)); // older than this script

  // --- Top bar: greeting by the time of day, avatar opens the account panel ---
  function greet() {
    const hour = new Date().getHours();
    const text = hour < 5 ? "Up late?" : hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
    doc.querySelectorAll("[data-mb-greet]").forEach((element) => {
      if (element.textContent !== text) element.textContent = text;
    });
    const top = doc.querySelector("[data-mb-topbar]");
    const sidebar = doc.querySelector('[data-testid="stSidebarUserContent"]');
    if (top && sidebar && sidebar.dataset.mbInitial !== top.dataset.mbInitial) {
      sidebar.dataset.mbInitial = top.dataset.mbInitial;
    }
  }
  doc.addEventListener("click", (event) => {
    const account = event.target.closest && event.target.closest("[data-mb-account]");
    if (!account) return;
    const open = doc.querySelector('[data-testid="stExpandSidebarButton"]');
    if (open) open.click();
    else doc.querySelector('[data-testid="stSidebarCollapseButton"] button')?.click();
  });

  // --- Run everything after Streamlit changes the page ---
  function scan() {
    syncTheme();
    tagGlyphs();
    tagCards();
    tagEmptyCells();
    tagTimer();
    popChanged();
    celebrations();
    greet();
  }
  let queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      try {
        scan();
      } catch (error) {
        console.warn("Mathbuddy design:", error);
      }
    });
  }
  new MutationObserver((records) => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (node.nodeType !== 1) continue;
        if (node.tagName === "STYLE") onStyle(node);
        else if (node.querySelectorAll) node.querySelectorAll("style").forEach(onStyle);
      }
    }
    schedule();
  }).observe(doc.body, { childList: true, subtree: true, characterData: true });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", schedule);
  setInterval(syncTheme, 1500);
  schedule();
})();
