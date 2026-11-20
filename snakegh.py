"""
SnakeGH - A Classic Arcade Game
Lab 2 - Python (Level 200)
Name: Darren Yaw Boateg Frempong

Features: player registration, leaderboard, 1 or 2 players, solid or wrap-around
walls, three difficulties, four detailed maps, obstacles that grow with the level,
power-ups, combo scoring, sound effects and a snake customiser (colours, patterns,
hats, tail items and trails).
Controls: Player 1 = W A S D, Player 2 = arrow keys (in 1-player mode both
work). P or Esc = pause, M = mute, Space = continue.
"""
import colorsys
import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave
import tkinter as tk
from datetime import date

try:
    import winsound
except ImportError:  # not on Windows: the game just runs silently
    winsound = None

# ---------------- Settings ----------------
CELL = 24 # size of one square in pixels
COLS = 28 # squares across
ROWS = 20 # squares down
WIDTH = CELL * COLS # 672 pixels
HEIGHT = CELL * ROWS # 480 pixels
PAD = 18
HUD_H = 92
WIN_W = WIDTH + 2 * PAD
WIN_H = HUD_H + HEIGHT + PAD + 6
BX, BY = PAD, HUD_H # top-left corner of the board
FRAME_MS = 40 # animation refresh (effects, tongue, glow)

HIGH_SCORE_FILE = "snake_highscore.txt"
LEADERBOARD_FILE = "snake_leaderboard.json"

BONUS_POINTS = 3 # golden mango value
BONUS_LIFETIME = 5000 # milliseconds the mango stays on the board
BONUS_CHANCE = 0.25 # chance of a mango after eating normal fruit
POWER_CHANCE = 0.20 # chance of a power-up after eating normal fruit
POWER_LIFE = 70 # moves a power-up stays on the board
DOUBLE_TICKS = 60 # length of the double-points power-up
SLOW_TICKS = 45 # length of the slow-motion power-up
COMBO_TICKS = 25 # moves allowed between fruits to keep a combo
MAX_OBSTACLES = 45
WIN_ROUNDS, MAX_ROUNDS = 2, 3 # two-player match: best of 3

# difficulty: (starting move delay in ms, obstacles added per level, obstacles at start)
DIFFICULTY = {"Easy": (170, 1, 0), "Normal": (150, 2, 0), "Hard": (125, 3, 4)}

DIRECTIONS = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
WASD = {"w": "Up", "s": "Down", "a": "Left", "d": "Right"}
ARROWS = {"up": "Up", "down": "Down", "left": "Left", "right": "Right"}

FONT_TITLE = "Impact"
FONT_UI = "Segoe UI"

MAPS = {
    "Baobab Savanna": dict(
        decor="savanna", special="mound", special_col="#8a5a2b",
        bg="#2b2415", panel="#3a301c", panel2="#4a3d24", frame="#8d6e3f", frame2="#5a4326",
        tile_a="#9bb25a", tile_b="#c9ba68", tile_hi="#dcd387", tile_lo="#6f8a3f",
        accent="#ffd54f", text="#fff4d6", dim="#cdbf94", danger="#ff6b4a", good="#9be564",
        btn="#5f7d2a", btn_hi="#7ea037", btn_text="#fff4d6", stone="#9a8f7e"),
    "Emerald Canopy": dict(
        decor="jungle", special="log", special_col="#8d5b2f",
        bg="#08140d", panel="#10281a", panel2="#173824", frame="#6d4c2a", frame2="#3e2a16",
        tile_a="#1c4a2a", tile_b="#2b6b3b", tile_hi="#43934f", tile_lo="#0f2d1a",
        accent="#d4e157", text="#e8f5e9", dim="#8fb99a", danger="#ff5252", good="#69f0ae",
        btn="#2e7d32", btn_hi="#43a047", btn_text="#f1f8e9", stone="#6f8a78"),
    "Gold Coast Dunes": dict(
        decor="dunes", special="cactus", special_col="#2e7d32",
        bg="#3b2a14", panel="#5a4223", panel2="#6e5129", frame="#b9852e", frame2="#7a5415",
        tile_a="#e6c27a", tile_b="#f2d99a", tile_hi="#fbebc0", tile_lo="#c79a4f",
        accent="#ffe082", text="#fff8e1", dim="#e0c38c", danger="#e53935", good="#8bc34a",
        btn="#a1672a", btn_hi="#bd7d36", btn_text="#fff8e1", stone="#a1887f"),
    "Frostbite Lake": dict(
        decor="frost", special="ice", special_col="#8fd3f4",
        bg="#0b1a2b", panel="#13304d", panel2="#1b4366", frame="#b3e5fc", frame2="#4f8fb5",
        tile_a="#a9d6ea", tile_b="#d2ebf8", tile_hi="#ffffff", tile_lo="#7fb4d0",
        accent="#ffe082", text="#e3f2fd", dim="#90b4cc", danger="#ff6b6b", good="#80ffdb",
        btn="#1e6091", btn_hi="#2b83bf", btn_text="#ffffff", stone="#7a8fa3"),
}

# snake customisation options
SKIN_COLORS = { # name: (head colour, tail colour)
    "Emerald": ("#46e08a", "#14753f"), "Gold": ("#ffd54f", "#b8860b"),
    "Crimson": ("#ff6e6e", "#8e0000"), "Sapphire": ("#64b5f6", "#0d47a1"),
    "Violet": ("#ce93d8", "#6a1b9a"), "Midnight": ("#90a4ae", "#263238"),
    "Rainbow": ("#ff5252", "#7e57c2"), "Ghana": ("#fcd116", "#006b3f"),
}
PATTERNS = ["Scales", "Stripes", "Spots", "Plain"]
HATS = ["None", "Crown", "Top Hat", "Party", "Shades", "Halo", "Bow"]
TAILS = ["None", "Rattle", "Flag"]
TRAILS = {"None": None, "Sparkles": ["#ffe082", "#ffffff", "#fff59d"],
          "Fire": ["#ff6d00", "#ffab00", "#ff3d00"], "Bubbles": ["#b3e5fc", "#e1f5fe", "#81d4fa"]}
DEFAULT_SKINS = [
    {"color": "Emerald", "pattern": "Scales", "hat": "None", "tail": "None", "trail": "None"},
    {"color": "Gold", "pattern": "Scales", "hat": "None", "tail": "None", "trail": "None"},
]

SOUNDS = { # (frequency Hz, milliseconds)
    "eat": [(660, 50), (880, 60)],
    "bonus": [(784, 70), (988, 70), (1319, 110)],
    "power": [(523, 60), (659, 60), (784, 60), (1047, 90)],
    "level": [(523, 90), (659, 90), (784, 90), (1047, 160)],
    "crash": [(260, 140), (200, 140), (140, 260)],
    "win": [(659, 100), (784, 100), (988, 100), (1319, 220)],
    "click": [(700, 25)],
}

# ---------------- Logic functions (no GUI code here) ----------------
def next_head(head, direction):
    """Return the square the head moves into."""
    dx, dy = DIRECTIONS[direction]
    return (head[0] + dx, head[1] + dy)

def wrap_cell(cell):
    """Wrap a square around the edges of the board."""
    return (cell[0] % COLS, cell[1] % ROWS)

def hits_wall(cell):
    """True if the square is outside the board."""
    x, y = cell
    return x < 0 or x >= COLS or y < 0 or y >= ROWS

def hits_self(head, snake):
    """True if the head runs into the body (the tail moves away, so skip it)."""
    return head in snake[:-1]

def random_free_cell(taken):
    """Pick a random square that is not in 'taken', or None if the board is full."""
    free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in taken]
    return random.choice(free) if free else None

def level_for(score):
    """Level goes up every 5 points."""
    return score // 5 + 1

def speed_for(level, base=150):
    """Each level is 12 ms faster, but never faster than 55 ms."""
    return max(55, base - (level - 1) * 12)

def neighbours(cell, wrap):
    """The squares next to a cell (wrapping round the edges if wrap is True)."""
    for dx, dy in DIRECTIONS.values():
        nx, ny = cell[0] + dx, cell[1] + dy
        if wrap:
            nx, ny = nx % COLS, ny % ROWS
        elif hits_wall((nx, ny)):
            continue
        yield (nx, ny)

def grid_connected(obstacles, wrap):
    """True if every free square can still be reached (no sealed-off pockets)."""
    start = next(((x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in obstacles), None)
    if start is None:
        return False
    seen, stack = {start}, [start]
    while stack:
        for n in neighbours(stack.pop(), wrap):
            if n not in obstacles and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen) == COLS * ROWS - len(obstacles)

def mix(c1, c2, t):
    """Blend two #rrggbb colours (t = 0 gives c1, t = 1 gives c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def load_high_score():
    """Read the saved high score, or 0 if there is none yet."""
    try:
        with open(HIGH_SCORE_FILE, "r") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_high_score(score):
    """Write the new high score to the file."""
    with open(HIGH_SCORE_FILE, "w") as file:
        file.write(str(score))

def clean_skin(skin, default):
    """Keep only valid snake customisation choices."""
    out = dict(default)
    if isinstance(skin, dict):
        for key, options in (("color", SKIN_COLORS), ("pattern", PATTERNS), ("hat", HATS), ("tail", TAILS), ("trail", TRAILS)):
            if skin.get(key) in options:
                out[key] = skin[key]
    return out

def load_board():
    """Read the leaderboard file (solo scores, versus wins, last names used)."""
    try:
        with open(LEADERBOARD_FILE, "r") as file:
            data = json.load(file)
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("solo", [])
    data.setdefault("versus", {})
    data.setdefault("last", ["", ""])
    saved = data.get("skins", [])
    data["skins"] = [clean_skin(saved[i] if i < len(saved) else None, DEFAULT_SKINS[i]) for i in range(2)]
    best = {}
    for e in data["solo"]:
        key = e["name"].lower()
        if key not in best or e["score"] > best[key]["score"]:
            best[key] = e
    data["solo"] = sorted(best.values(), key=lambda e: e["score"], reverse=True)
    return data

def save_board(data):
    try:
        with open(LEADERBOARD_FILE, "w") as file:
            json.dump(data, file, indent=1)
    except OSError:
        pass

def add_solo_score(data, name, score, level, mode):
    """One row per player: update it if the score is a new personal best.
    Returns (rank, improved). A new name gets a new row."""
    entry = next((e for e in data["solo"] if e["name"].lower() == name.lower()), None)
    improved = entry is None or score > entry["score"]
    if entry is None:
        entry = {"name": name}
        data["solo"].append(entry)
    if improved:
        entry.update({"name": name, "score": score, "level": level, "mode": mode,
                      "date": date.today().isoformat()})
    data["solo"].sort(key=lambda e: e["score"], reverse=True)
    save_board(data)
    return data["solo"].index(entry) + 1, improved

def add_versus_win(data, name):
    data["versus"][name] = data["versus"].get(name, 0) + 1
    save_board(data)

# ---------------- Game state ----------------
map_name = "Baobab Savanna"
T = dict(MAPS[map_name])
state = "name" # name, menu, setup, customize, leaderboard, help, countdown, play, paused, dying, roundover
num_players = 1
walls = "Solid" # "Solid" or "Wrap"
difficulty = "Normal"
players = []
fruits = []
power = None
obstacles = {} # cell -> "stone" or "crate"
level = 1
slow_t = 0
round_no = 1
tally = [0, 0]
particles = []
floaters = []
banner = None
shake_t = 0
shake_origin = (0, 0)
loop_id = cd_id = end_id = None
round_action = None
lb_tab = "solo"
muted = False
best_cache = 0
BUTTONS = {}
ENTRIES = []
board = load_board()
skins = board["skins"]
cust_idx = 0 # which player is being customised
SOUND_FILES = {}

# ---------------- Sound ----------------
def make_sound_files():
    """Build a small .wav file for each sound effect (works on any computer)."""
    folder = tempfile.mkdtemp(prefix="snakegh_")
    rate = 22050
    for name, notes in SOUNDS.items():
        frames = bytearray()
        for freq, ms in notes:
            n = int(rate * ms / 1000)
            for i in range(n):
                fade = max(0.0, min(1.0, i / (rate * 0.005), (n - i) / (rate * 0.012)))
                wave_value = math.sin(2 * math.pi * freq * i / rate) * 0.7 + math.sin(4 * math.pi * freq * i / rate) * 0.15
                frames += struct.pack("<h", int(32767 * 0.55 * fade * wave_value))
        path = os.path.join(folder, name + ".wav")
        with wave.open(path, "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(rate)
            out.writeframes(bytes(frames))
        SOUND_FILES[name] = path

def play(name):
    """Play a sound effect without freezing the game."""
    if muted or name not in SOUND_FILES:
        return
    path = SOUND_FILES[name]
    try:
        if winsound is not None:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            player = shutil.which("paplay") or shutil.which("aplay")
            if player:
                subprocess.Popen([player, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (RuntimeError, OSError):
        pass

def toggle_mute():
    global muted
    muted = not muted

# ---------------- Small helpers ----------------
def wrap_on():
    return walls == "Wrap"

def mode_text():
    return f"{walls}/{difficulty}"

def cell_xy(cell):
    return BX + cell[0] * CELL, BY + cell[1] * CELL

def cell_center(cell):
    x, y = cell_xy(cell)
    return x + CELL / 2, y + CELL / 2

def best_score():
    scores = [e["score"] for e in board["solo"]] + [load_high_score()]
    return max(scores)

def set_map(name):
    global map_name, T
    map_name = name
    T = dict(MAPS[name])
    root.configure(bg=T["bg"])
    canvas.configure(bg=T["bg"])

def skin_head(i):
    """Head colour of a player's snake (used by the HUD and effects)."""
    return SKIN_COLORS[skins[i]["color"]][0]

def rrect(x1, y1, x2, y2, r=10, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)

def draw_star(cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + 36 * i)
        rad = r if i % 2 == 0 else r * 0.4
        pts += [cx + rad * math.cos(ang), cy + rad * math.sin(ang)]
    canvas.create_polygon(pts, fill=fill, outline="")

def button(cx, cy, w, h, text, cmd, tag="ui", selected=False, size=13, key=None):
    """A rounded clickable button drawn on the canvas."""
    name = key or f"btn{len(BUTTONS)}"
    BUTTONS[name] = cmd
    fill = T["accent"] if selected else T["btn"]
    fg = T["bg"] if selected else T["btn_text"]
    shadow = mix(T["bg"], "#000000", 0.5)
    rrect(cx - w / 2 + 2, cy - h / 2 + 4, cx + w / 2 + 2, cy + h / 2 + 4, 10, fill=shadow, outline="", tags=(tag, name))
    rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 10, fill=fill, outline=T["frame"], width=2, tags=(tag, name, name + "bg"))
    canvas.create_text(cx, cy, text=text, fill=fg, font=(FONT_UI, size, "bold"), tags=(tag, name))
    hover = T["accent"] if selected else T["btn_hi"]
    canvas.tag_bind(name, "<Enter>", lambda e: (canvas.itemconfig(name + "bg", fill=hover), canvas.config(cursor="hand2")))
    canvas.tag_bind(name, "<Leave>", lambda e: (canvas.itemconfig(name + "bg", fill=fill), canvas.config(cursor="")))

def mini_button(cx, cy, w, h, text, cmd, key):
    """Small button used in the in-game HUD (redrawn every frame)."""
    BUTTONS[key] = cmd
    rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 6, fill=T["btn"], outline=T["frame"], tags=("dyn", key))
    canvas.create_text(cx, cy, text=text, fill=T["btn_text"], font=(FONT_UI, 8, "bold"), tags=("dyn", key))

def on_click(event):
    items = canvas.find_withtag("current")
    if not items:
        return
    for t in canvas.gettags(items[0]):
        if t in BUTTONS:
            cmd = BUTTONS[t]
            play("click")
            cmd()
            return

def make_entry(x, y, var):
    e = tk.Entry(root, textvariable=var, font=(FONT_UI, 16, "bold"), justify="center", width=16,
                 bg=T["panel2"], fg=T["text"], insertbackground=T["accent"], relief="flat",
                 highlightthickness=2, highlightbackground=T["frame2"], highlightcolor=T["accent"])
    canvas.create_window(x, y, window=e)
    ENTRIES.append(e)
    return e

def stop_loops():
    global loop_id, cd_id, end_id
    for attr in ("loop_id", "cd_id", "end_id"):
        job = globals()[attr]
        if job is not None:
            try:
                root.after_cancel(job)
            except tk.TclError:
                pass
            globals()[attr] = None

def clear_screen():
    stop_loops()
    canvas.delete("all")
    BUTTONS.clear()
    for e in ENTRIES:
        e.destroy()
    ENTRIES.clear()
    canvas.config(cursor="")
    root.focus_set()

def draw_backdrop():
    canvas.configure(bg=T["bg"])
    paint_ground(0, 0, WIN_W // CELL + 1, WIN_H // CELL + 1, "bg", dim=0.72, decor=150)
    for i, col in enumerate(("#ce1126", "#fcd116", "#006b3f")):
        canvas.create_rectangle(0, i * 5, WIN_W, i * 5 + 5, fill=col, outline="")
        canvas.create_rectangle(0, WIN_H - 15 + i * 5, WIN_W, WIN_H - 10 + i * 5, fill=col, outline="")

def draw_title(y, size=46):
    for dx, dy, col in ((3, 4, mix(T["bg"], "#000000", 0.6)), (0, 0, T["accent"])):
        canvas.create_text(WIN_W / 2 + dx, y + dy, text="SnakeGH", fill=col, font=(FONT_TITLE, size))
    draw_star(WIN_W / 2 - 150, y, 14, T["accent"])
    draw_star(WIN_W / 2 + 150, y, 14, T["accent"])

def panel(cx, cy, w, h):
    shadow = mix(T["bg"], "#000000", 0.5)
    rrect(cx - w / 2 + 4, cy - h / 2 + 6, cx + w / 2 + 4, cy + h / 2 + 6, 18, fill=shadow, outline="")
    rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 18, fill=T["panel"], outline=T["frame"], width=3)

def heading(text, y=52):
    canvas.create_text(WIN_W / 2 + 2, y + 3, text=text, fill=mix(T["bg"], "#000000", 0.6), font=(FONT_TITLE, 30))
    canvas.create_text(WIN_W / 2, y, text=text, fill=T["accent"], font=(FONT_TITLE, 30))

# ---------------- Screens: name, menu, setup, leaderboard, help ----------------
def go_name_screen():
    global state
    clear_screen()
    state = "name"
    draw_backdrop()
    draw_title(105)
    panel(WIN_W / 2, 345, 460, 250)
    canvas.create_text(WIN_W / 2, 275, text="REGISTER YOUR PLAYER NAME", fill=T["accent"], font=(FONT_UI, 14, "bold"))
    e = make_entry(WIN_W / 2, 330, name1_var)
    canvas.create_text(WIN_W / 2, 372, text="Your scores are saved to the leaderboard under this name.", fill=T["dim"], font=(FONT_UI, 9))
    button(WIN_W / 2, 425, 200, 44, "CONTINUE", name_continue, key="go")
    e.focus_set()
    e.icursor("end")

def name_continue():
    name = name1_var.get().strip() or "Player"
    name1_var.set(name)
    board["last"][0] = name
    save_board(board)
    go_menu()

def go_menu():
    global state
    clear_screen()
    state = "menu"
    draw_backdrop()
    draw_title(105)
    canvas.create_text(WIN_W / 2, 175, text=f"Welcome, {name1_var.get().strip() or 'Player'}!", fill=T["text"], font=(FONT_UI, 15, "bold"))
    items = [("PLAY", go_setup), ("CUSTOMIZE SNAKE", go_customize), ("LEADERBOARD", go_leaderboard),
             ("HOW TO PLAY", go_help), ("CHANGE PLAYER", go_name_screen), ("QUIT", root.destroy)]
    for i, (label, cmd) in enumerate(items):
        button(WIN_W / 2, 238 + i * 54, 280, 40, label, cmd)

def set_players(n):
    global num_players
    num_players = n
    go_setup()

def set_walls(w):
    global walls
    walls = w
    go_setup()

def set_difficulty(d):
    global difficulty
    difficulty = d
    go_setup()

def set_map_choice(name):
    set_map(name)
    go_setup()

def go_setup():
    global state
    clear_screen()
    state = "setup"
    draw_backdrop()
    heading("GAME SETUP", 48)
    cx = WIN_W / 2
    def row(label, y, options, current, cmd, width, size=11):
        canvas.create_text(cx, y, text=label, fill=T["accent"], font=(FONT_UI, 10, "bold"))
        n = len(options)
        for i, (text, value) in enumerate(options):
            button(cx + (i - (n - 1) / 2) * (width + 10), y + 30, width, 34, text, lambda v=value: cmd(v),
                   selected=(value == current), size=size, key=f"{label}{i}")
    row("PLAYERS", 98, [("1 PLAYER", 1), ("2 PLAYERS", 2)], num_players, set_players, 160)
    row("WALLS", 172, [("SOLID (DIE)", "Solid"), ("WRAP-AROUND", "Wrap")], walls, set_walls, 160)
    row("DIFFICULTY", 246, [("EASY", "Easy"), ("NORMAL", "Normal"), ("HARD", "Hard")], difficulty, set_difficulty, 120)
    row("MAP", 320, [(n.upper(), n) for n in MAPS], map_name, set_map_choice, 160, 9)
    if num_players == 2:
        n1 = name1_var.get().strip() or "Player 1"
        canvas.create_text(cx, 396, text=f"{n1}: W A S D          PLAYER 2 NAME: arrow keys", fill=T["text"], font=(FONT_UI, 10, "bold"))
        make_entry(cx, 426, name2_var)
    else:
        canvas.create_text(cx, 405, text="Control the snake with W A S D or the arrow keys", fill=T["text"], font=(FONT_UI, 10, "bold"))
    button(cx, 486, 240, 44, "START GAME", start_match, key="start")
    button(cx, 540, 140, 32, "BACK", go_menu, size=11, key="back")

def go_leaderboard():
    global state
    clear_screen()
    state = "leaderboard"
    draw_backdrop()
    heading("LEADERBOARD", 48)
    button(WIN_W / 2 - 100, 100, 180, 34, "SOLO TOP 10", lambda: set_tab("solo"), selected=(lb_tab == "solo"), size=11, key="tab1")
    button(WIN_W / 2 + 100, 100, 180, 34, "VERSUS WINS", lambda: set_tab("versus"), selected=(lb_tab == "versus"), size=11, key="tab2")
    panel(WIN_W / 2, 305, 640, 360)
    me = name1_var.get().strip()
    if lb_tab == "solo":
        heads = [("#", 70, "w"), ("NAME", 110, "w"), ("SCORE", 340, "e"), ("LEVEL", 410, "e"), ("MODE", 440, "w"), ("DATE", 600, "w")]
        for text, x, anc in heads:
            canvas.create_text(x, 150, text=text, fill=T["accent"], font=(FONT_UI, 10, "bold"), anchor=anc)
        rows = board["solo"][:10]
        if not rows:
            canvas.create_text(WIN_W / 2, 300, text="No scores yet. Be the first!", fill=T["dim"], font=(FONT_UI, 13, "bold"))
        for i, e in enumerate(rows):
            y = 180 + i * 29
            col = T["accent"] if e["name"] == me else T["text"]
            if i % 2 == 0:
                canvas.create_rectangle(52, y - 13, WIN_W - 52, y + 13, fill=T["panel2"], outline="")
            vals = [(str(i + 1), 70, "w"), (e["name"], 110, "w"), (str(e["score"]), 340, "e"),
                    (str(e["level"]), 410, "e"), (e["mode"], 440, "w"), (e["date"], 600, "w")]
            for text, x, anc in vals:
                canvas.create_text(x, y, text=text, fill=col, font=(FONT_UI, 11, "bold"), anchor=anc)
    else:
        canvas.create_text(WIN_W / 2, 150, text="MATCH WINS (best of 3 rounds)", fill=T["accent"], font=(FONT_UI, 10, "bold"))
        rows = sorted(board["versus"].items(), key=lambda kv: kv[1], reverse=True)[:10]
        if not rows:
            canvas.create_text(WIN_W / 2, 300, text="No two-player matches played yet.", fill=T["dim"], font=(FONT_UI, 13, "bold"))
        for i, (name, wins) in enumerate(rows):
            y = 180 + i * 29
            col = T["accent"] if name == me else T["text"]
            if i % 2 == 0:
                canvas.create_rectangle(52, y - 13, WIN_W - 52, y + 13, fill=T["panel2"], outline="")
            canvas.create_text(100, y, text=f"{i + 1}.  {name}", fill=col, font=(FONT_UI, 12, "bold"), anchor="w")
            canvas.create_text(WIN_W - 100, y, text=f"{wins} win{'s' if wins != 1 else ''}", fill=col, font=(FONT_UI, 12, "bold"), anchor="e")
    button(WIN_W / 2, 535, 160, 36, "BACK", go_menu, size=11, key="back")

def set_tab(tab):
    global lb_tab
    lb_tab = tab
    go_leaderboard()

def go_help():
    global state
    clear_screen()
    state = "help"
    draw_backdrop()
    heading("HOW TO PLAY", 48)
    panel(WIN_W / 2, 310, 640, 380)
    lines = [
        ("Controls", T["accent"]),
        ("Player 1: W A S D        Player 2: arrow keys", T["text"]),
        ("(in 1-player mode both sets work)    P / Esc = pause    M = mute", T["dim"]),
        ("Eat", T["accent"]),
        ("Apples, oranges and cherries = 1 point. Golden mango = 3 points (fades fast).", T["text"]),
        ("Eat fruit quickly one after another to build a COMBO for bonus points.", T["text"]),
        ("Power-ups", T["accent"]),
        ("Shield: survive one crash     2x: double points     Slow: slow motion", T["text"]),
        ("Shrink: lose 3 tail segments", T["text"]),
        ("Levels", T["accent"]),
        ("Every 5 points is a new level: the snake speeds up and obstacles appear.", T["text"]),
        ("Two players", T["accent"]),
        ("Last snake alive wins the round. First to 2 round wins takes the match.", T["text"]),
    ]
    y = 140
    for text, col in lines:
        head = col == T["accent"]
        canvas.create_text(WIN_W / 2, y, text=text, fill=col, font=(FONT_UI, 12 if head else 10, "bold"))
        y += 26 if head else 21
    button(WIN_W / 2, 535, 160, 36, "BACK", go_menu, size=11, key="back")

# ---------------- Snake customiser ----------------
def set_cust(i):
    global cust_idx
    cust_idx = i
    go_customize()

def set_skin(field, value):
    skins[cust_idx][field] = value
    save_board(board)
    go_customize()

def randomise_skin():
    skins[cust_idx].update(color=random.choice(list(SKIN_COLORS)), pattern=random.choice(PATTERNS),
                           hat=random.choice(HATS), tail=random.choice(TAILS), trail=random.choice(list(TRAILS)))
    save_board(board)
    go_customize()

def swatch_colours(name):
    if name == "Rainbow":
        return ["#ef5350", "#ffee58", "#66bb6a", "#42a5f5"]
    if name == "Ghana":
        return ["#ce1126", "#fcd116", "#006b3f"]
    head, tail = SKIN_COLORS[name]
    return [head, mix(head, tail, 0.5), tail]

def go_customize():
    global state
    clear_screen()
    particles.clear()
    state = "customize"
    draw_backdrop()
    heading("CUSTOMIZE SNAKE", 46)
    cx = WIN_W / 2
    sk = skins[cust_idx]
    for i in range(2):
        button(cx + (i - 0.5) * 200, 94, 190, 30, f"PLAYER {i + 1}  ({'WASD' if i == 0 else 'ARROWS'})",
               lambda i=i: set_cust(i), selected=(cust_idx == i), size=10, key=f"tab{i}")
    panel(cx, 172, 420, 100)
    def label(text, x, y):
        canvas.create_text(x, y, text=text, fill=T["accent"], font=(FONT_UI, 9, "bold"))
    def options(text, y, choices, field, width, center):
        label(text, center, y)
        n = len(choices)
        for i, c in enumerate(choices):
            button(center + (i - (n - 1) / 2) * (width + 6), y + 26, width, 28, c.upper(),
                   lambda v=c: set_skin(field, v), selected=(sk[field] == c), size=8, key=f"{field}{i}")
    label("COLOUR", cx, 238)
    names = list(SKIN_COLORS)
    sw, gap = 64, 8
    x0 = cx - (len(names) * sw + (len(names) - 1) * gap) / 2
    for i, name in enumerate(names):
        x = x0 + i * (sw + gap) + sw / 2
        key = f"sw{i}"
        BUTTONS[key] = lambda n=name: set_skin("color", n)
        sel = sk["color"] == name
        cols = swatch_colours(name)
        rrect(x - sw / 2, 252, x + sw / 2, 282, 8, fill=cols[0], outline=T["accent"] if sel else T["frame2"],
              width=3 if sel else 1, tags=("ui", key))
        seg = (sw - 12) / len(cols)
        for j, c in enumerate(cols):
            canvas.create_rectangle(x - sw / 2 + 6 + j * seg, 258, x - sw / 2 + 6 + (j + 1) * seg, 276,
                                    fill=c, outline="", tags=("ui", key))
        canvas.create_text(x, 293, text=name, fill=T["text"] if sel else T["dim"], font=(FONT_UI, 7, "bold"), tags=("ui", key))
    options("PATTERN", 316, PATTERNS, "pattern", 100, cx)
    options("HAT", 372, HATS, "hat", 86, cx)
    options("TAIL ITEM", 430, TAILS, "tail", 84, 175)
    options("TRAIL", 430, list(TRAILS), "trail", 84, 505)
    button(cx - 100, 524, 160, 34, "DONE", go_menu, size=11, key="done")
    button(cx + 100, 524, 160, 34, "RANDOMISE", randomise_skin, size=11, key="rand")

def draw_preview():
    canvas.delete("prev")
    now = time.time()
    cx, cy = WIN_W / 2, 178
    pts = [(cx + 70 - i * 21, cy + math.sin(now * 3 + i * 0.7) * 4) for i in range(10)]
    sk = skins[cust_idx]
    render_snake(pts, "Right", sk, now, tag="prev")
    if int(now * 25) % 2 == 0:
        trail_puff(pts[-1][0], pts[-1][1], sk["trail"], 1)
    for pt in particles:
        r = pt["size"]
        canvas.create_oval(pt["x"] - r, pt["y"] - r, pt["x"] + r, pt["y"] + r, fill=pt["color"], outline="", tags="prev")

# ---------------- Board drawing ----------------
def paint_ground(x0, y0, cols, rows, tag, dim=0.0, decor=170):
    """Textured ground: smooth colour noise, soft patches and scattered scenery (no grid)."""
    rnd = random.Random(sum(map(ord, map_name)))
    lat = {(i, j): rnd.random() for i in range(cols // 4 + 3) for j in range(rows // 4 + 3)}
    def noise(x, y):
        gx, gy = x / 4, y / 4
        ix, iy = int(gx), int(gy)
        fx, fy = gx - ix, gy - iy
        top = lat[(ix, iy)] * (1 - fx) + lat[(ix + 1, iy)] * fx
        bot = lat[(ix, iy + 1)] * (1 - fx) + lat[(ix + 1, iy + 1)] * fx
        return top * (1 - fy) + bot * fy
    def tone(c):
        return mix(c, T["bg"], dim) if dim else c
    for x in range(cols):
        for y in range(rows):
            c = mix(mix(T["tile_a"], T["tile_b"], noise(x, y)), T["tile_hi"], rnd.random() * 0.10)
            px, py = x0 + x * CELL, y0 + y * CELL
            canvas.create_rectangle(px, py, px + CELL + 1, py + CELL + 1, fill=tone(c), outline="", tags=tag)
    w, h = cols * CELL, rows * CELL
    for _ in range(decor // 6 + 4):
        r = rnd.randint(16, 38)
        cx, cy = rnd.uniform(r, w - r), rnd.uniform(r, h - r)
        tint = T["tile_lo"] if rnd.random() < 0.6 else T["tile_hi"]
        canvas.create_oval(x0 + cx - r, y0 + cy - r * 0.7, x0 + cx + r, y0 + cy + r * 0.7,
                           fill=tone(mix(mix(T["tile_a"], T["tile_b"], 0.5), tint, 0.2)), outline="", tags=tag)
    for _ in range(decor):
        draw_decor(T["decor"], x0 + rnd.uniform(8, w - 8), y0 + rnd.uniform(8, h - 8), rnd, tag, tone)

def draw_decor(kind, x, y, rnd, tag, tone):
    """One small piece of scenery (grass, flowers, mushrooms, ripples, cracks...)."""
    def o(x1, y1, x2, y2, fill, outline=""):
        canvas.create_oval(x + x1, y + y1, x + x2, y + y2, fill=tone(fill), outline=tone(outline) if outline else "", tags=tag)
    def ln(x1, y1, x2, y2, col, width=1):
        canvas.create_line(x + x1, y + y1, x + x2, y + y2, fill=tone(col), width=width, tags=tag)
    def leaf(ang, length, col):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        qx, qy = -uy * length * 0.28, ux * length * 0.28
        mx, my = ux * length * 0.5, uy * length * 0.5
        canvas.create_polygon(x, y, x + mx + qx, y + my + qy, x + ux * length, y + uy * length,
                              x + mx - qx, y + my - qy, fill=tone(col), outline="", tags=tag)
    lo, hi, st = T["tile_lo"], T["tile_hi"], T["stone"]
    def pebble():
        o(-3, -1, 3.5, 2.5, mix(lo, "#000000", 0.3))
        o(-3, -2.5, 2.5, 1.5, mix(st, T["tile_b"], 0.35), mix(st, "#000000", 0.4))
    r = rnd.random()
    if kind == "savanna":
        if r < 0.5: # grass tuft
            col = mix(lo, "#000000", 0.15)
            for ang in (-35, 0, 35, -15, 20)[:rnd.randint(3, 5)]:
                a = math.radians(ang - 90)
                length = rnd.uniform(4, 8)
                ln(0, 0, math.cos(a) * length, math.sin(a) * length, col)
        elif r < 0.72: # flower
            petal = rnd.choice(("#fff59d", "#ffffff", "#f8bbd0", "#ffcc80"))
            for dx, dy in ((-2.5, 0), (2.5, 0), (0, -2.5), (0, 2.5)):
                o(dx - 1.8, dy - 1.8, dx + 1.8, dy + 1.8, petal)
            o(-1.5, -1.5, 1.5, 1.5, "#f9a825")
        else:
            pebble()
    elif kind == "jungle":
        if r < 0.35: # fern
            for ang in (-130, -90, -50):
                leaf(ang, rnd.uniform(7, 10), mix("#2e7d32", hi, 0.15))
        elif r < 0.55: # mushroom
            canvas.create_rectangle(x - 1.2, y - 1, x + 1.2, y + 3.5, fill=tone("#efe9d2"), outline="", tags=tag)
            canvas.create_arc(x - 4.5, y - 6, x + 4.5, y + 2, start=0, extent=180, fill=tone("#d32f2f"),
                              outline="", style="chord", tags=tag)
            o(-2.5, -4, -0.8, -2.5, "#ffffff")
            o(1, -3.5, 2.6, -2, "#ffffff")
        elif r < 0.8:
            leaf(rnd.uniform(0, 360), rnd.uniform(5, 8), mix("#43a047", hi, 0.25))
        else: # moss patch
            o(-7, -3, 7, 3, mix(T["tile_a"], "#000000", 0.18))
            o(-4, -2, 3, 1.5, mix(T["tile_b"], hi, 0.3))
    elif kind == "dunes":
        if r < 0.45: # wind ripples
            for k in range(2):
                canvas.create_arc(x - 8 + k * 3, y + k * 3, x + 8 + k * 3, y + 8 + k * 3, start=10, extent=160,
                                  style="arc", outline=tone(lo), width=1, tags=tag)
        elif r < 0.65:
            pebble()
        elif r < 0.85: # shell
            o(-3, -2, 3, 2.5, "#fff1dc", mix(lo, "#000000", 0.2))
            ln(-1.5, 0, 1.5, 0, lo)
        else: # dry shrub
            for ang in (-125, -100, -80, -55):
                a = math.radians(ang)
                ln(0, 0, math.cos(a) * 7, math.sin(a) * 7, "#8d6e3f")
    else: # frost
        if r < 0.4: # ice crack
            px, py = 0.0, 0.0
            for _ in range(4):
                nx, ny = px + rnd.uniform(-3, 6), py + rnd.uniform(-5, 5)
                ln(px, py, nx, ny, lo)
                ln(px + 1, py + 1, nx + 1, ny + 1, "#ffffff")
                px, py = nx, ny
        elif r < 0.7: # snow flecks
            for _ in range(3):
                fx, fy = rnd.uniform(-5, 5), rnd.uniform(-4, 4)
                o(fx - 1.4, fy - 1, fx + 1.4, fy + 1, "#ffffff")
        elif r < 0.85: # glint
            ln(-4, 0, 4, 0, "#ffffff")
            ln(0, -4, 0, 4, "#ffffff")
            ln(-2, -2, 2, 2, "#ffffff")
            ln(-2, 2, 2, -2, "#ffffff")
        else:
            pebble()

def draw_floor():
    """Textured map floor, frame and shadow (drawn once per round)."""
    shadow = mix(T["bg"], "#000000", 0.55)
    rrect(BX - 6 + 4, BY - 6 + 6, BX + WIDTH + 6 + 4, BY + HEIGHT + 6 + 6, 14, fill=shadow, outline="", tags="static")
    rrect(BX - 10, BY - 10, BX + WIDTH + 10, BY + HEIGHT + 10, 14, fill=T["frame"], outline=T["frame2"], width=2, tags="static")
    rrect(BX - 5, BY - 5, BX + WIDTH + 5, BY + HEIGHT + 5, 8, fill=T["frame2"], outline="", tags="static")
    canvas.create_rectangle(BX - 8, BY - 8, BX + WIDTH + 8, BY + HEIGHT + 8, outline=mix(T["frame"], "#ffffff", 0.45),
                            dash=(5, 4), tags="static")
    paint_ground(BX, BY, COLS, ROWS, "static", decor=200)
    for i, t in enumerate((0.45, 0.28, 0.14)): # soft inner shadow along the edges
        canvas.create_rectangle(BX + i, BY + i, BX + WIDTH - i, BY + HEIGHT - i,
                                outline=mix(T["tile_lo"], "#000000", t), tags="static")
    for cx, cy in ((BX - 7, BY - 7), (BX + WIDTH + 7, BY - 7), (BX - 7, BY + HEIGHT + 7), (BX + WIDTH + 7, BY + HEIGHT + 7)):
        canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=T["accent"], outline=T["frame2"], tags="static")

def draw_stone(px, py, seed):
    m = 2
    body = T["stone"]
    rrect(px + m, py + m, px + CELL - m, py + CELL - m, 6, fill=body, outline=mix(body, "#000000", 0.5), width=1, tags="obst")
    canvas.create_line(px + 5, py + 5, px + CELL - 7, py + 5, fill=mix(body, "#ffffff", 0.55), width=2, tags="obst")
    canvas.create_line(px + 5, py + 5, px + 5, py + CELL - 8, fill=mix(body, "#ffffff", 0.35), width=2, tags="obst")
    canvas.create_line(px + CELL - 5, py + 7, px + CELL - 5, py + CELL - 5, px + 7, py + CELL - 5,
                       fill=mix(body, "#000000", 0.35), width=2, tags="obst")
    a = 6 + seed % 6
    canvas.create_line(px + a, py + 9, px + a + 3, py + 13, px + a, py + 15, px + a + 4, py + 19,
                       fill=mix(body, "#000000", 0.5), tags="obst")

def draw_mound(px, py, seed):
    c = T["special_col"]
    d = mix(c, "#000000", 0.45)
    canvas.create_oval(px + 2, py + 5, px + CELL - 2, py + CELL - 2, fill=c, outline=d, tags="obst")
    canvas.create_oval(px + 6, py + 2, px + CELL - 6, py + 14, fill=mix(c, "#ffffff", 0.12), outline=d, tags="obst")
    for k in range(3):
        canvas.create_line(px + 6 + k, py + 9 + k * 4, px + CELL - 6 - k, py + 9 + k * 4, fill=d, tags="obst")
    canvas.create_oval(px + 10, py + 5, px + 13, py + 8, fill=mix(c, "#ffffff", 0.4), outline="", tags="obst")

def draw_log(px, py, seed):
    c = T["special_col"]
    d = mix(c, "#000000", 0.5)
    rrect(px + 2, py + 6, px + CELL - 2, py + CELL - 4, 5, fill=c, outline=d, width=1, tags="obst")
    for yy in (10, 14, 18):
        canvas.create_line(px + 10, py + yy, px + CELL - 5, py + yy, fill=mix(c, "#000000", 0.25), tags="obst")
    canvas.create_oval(px + 2, py + 6, px + 11, py + CELL - 4, fill=mix(c, "#e0b97a", 0.5), outline=d, tags="obst")
    canvas.create_oval(px + 4, py + 9, px + 9, py + CELL - 7, outline=d, tags="obst")

def draw_cactus(px, py, seed):
    c = T["special_col"]
    d = mix(c, "#000000", 0.45)
    hi = mix(c, "#ffffff", 0.3)
    canvas.create_rectangle(px + 9, py + 3, px + CELL - 9, py + CELL - 2, fill=c, outline=d, tags="obst")
    canvas.create_rectangle(px + 3, py + 10, px + 9, py + 13, fill=c, outline=d, tags="obst")
    canvas.create_rectangle(px + 3, py + 6, px + 6, py + 13, fill=c, outline=d, tags="obst")
    canvas.create_rectangle(px + CELL - 9, py + 13, px + CELL - 3, py + 16, fill=c, outline=d, tags="obst")
    canvas.create_rectangle(px + CELL - 6, py + 9, px + CELL - 3, py + 16, fill=c, outline=d, tags="obst")
    canvas.create_line(px + 11, py + 6, px + 11, py + CELL - 5, fill=hi, tags="obst")
    for yy in (8, 12, 16, 20):
        canvas.create_line(px + 9, py + yy, px + 7, py + yy - 1, fill=d, tags="obst")
        canvas.create_line(px + CELL - 9, py + yy, px + CELL - 7, py + yy - 1, fill=d, tags="obst")
    canvas.create_oval(px + 10, py + 1, px + 14, py + 5, fill="#f06292", outline="", tags="obst")

def draw_ice(px, py, seed):
    c = T["special_col"]
    d = mix(c, "#000000", 0.5)
    canvas.create_polygon(px + 12, py + 2, px + CELL - 3, py + 9, px + CELL - 4, py + CELL - 6, px + 12, py + CELL - 2,
                          px + 4, py + CELL - 6, px + 3, py + 9, fill=c, outline=d, tags="obst")
    canvas.create_polygon(px + 12, py + 2, px + CELL - 3, py + 9, px + 12, py + 12, px + 3, py + 9,
                          fill=mix(c, "#ffffff", 0.55), outline="", tags="obst")
    canvas.create_line(px + 12, py + 12, px + 12, py + CELL - 2, fill=mix(c, "#ffffff", 0.7), tags="obst")
    canvas.create_line(px + 12, py + 12, px + CELL - 4, py + CELL - 6, fill=mix(c, "#000000", 0.2), tags="obst")

SPECIALS = {"mound": draw_mound, "log": draw_log, "cactus": draw_cactus, "ice": draw_ice}

def draw_obstacles():
    canvas.delete("obst")
    for cell, kind in obstacles.items():
        px, py = cell_xy(cell)
        seed = cell[0] * 31 + cell[1] * 17
        canvas.create_oval(px + 3, py + CELL - 9, px + CELL - 1, py + CELL, fill=mix(T["tile_a"], "#000000", 0.55),
                           outline="", tags="obst")
        if kind == "stone":
            draw_stone(px, py, seed)
        else:
            SPECIALS[T["special"]](px, py, seed)
    canvas.tag_raise("overlay")

# ---------------- Drawing: fruit, power-ups, snakes ----------------
def draw_fruit(kind, cx, cy, now):
    def oval(x1, y1, x2, y2, **kw):
        canvas.create_oval(cx + x1, cy + y1, cx + x2, cy + y2, tags="dyn", **kw)
    def line(*pts, **kw):
        canvas.create_line(*[cx + v if i % 2 == 0 else cy + v for i, v in enumerate(pts)], tags="dyn", **kw)
    def poly(*pts, **kw):
        canvas.create_polygon(*[cx + v if i % 2 == 0 else cy + v for i, v in enumerate(pts)], tags="dyn", **kw)
    oval(-8, 7, 8, 11, fill=mix(T["tile_a"], "#000000", 0.45), outline="")
    if kind == "apple":
        oval(-9, -8, 9, 10, fill="#c62828", outline="#7f0000")
        oval(-7, -7, 3, 5, fill="#ef5350", outline="")
        oval(-6, -5, -2, -1, fill="#ffcdd2", outline="")
        line(0, -7, 2, -12, fill="#5d4037", width=2)
        poly(2, -9, 8, -13, 7, -7, fill="#43a047", outline="#1b5e20", smooth=True)
    elif kind == "orange":
        oval(-9, -8, 9, 10, fill="#fb8c00", outline="#e65100")
        oval(-7, -7, 3, 4, fill="#ffb74d", outline="")
        oval(-6, -5, -3, -2, fill="#fff3e0", outline="")
        oval(-1, -9, 1, -7, fill="#5d4037", outline="")
        poly(1, -9, 8, -12, 5, -7, fill="#2e7d32", outline="", smooth=True)
    elif kind == "cherry":
        line(-4, 0, 1, -10, fill="#6d4c41", width=2)
        line(5, 1, 1, -10, fill="#6d4c41", width=2)
        oval(-10, -1, 1, 10, fill="#b71c1c", outline="#7f0000")
        oval(0, 0, 11, 11, fill="#c62828", outline="#7f0000")
        oval(-8, 1, -5, 4, fill="#ffcdd2", outline="")
        oval(2, 2, 5, 5, fill="#ffcdd2", outline="")
        poly(1, -10, 9, -13, 7, -8, fill="#43a047", outline="", smooth=True)
    else: # golden mango (bonus)
        pulse = 2 + 2 * math.sin(now * 6)
        oval(-12 - pulse, -12 - pulse, 12 + pulse, 12 + pulse, outline="#ffe082", width=2)
        oval(-8, -10, 9, 10, fill="#ffb300", outline="#ff6f00")
        oval(-6, -8, 2, 3, fill="#ffd54f", outline="")
        oval(-5, -6, -2, -3, fill="#fff8e1", outline="")
        poly(1, -10, 9, -13, 7, -8, fill="#43a047", outline="#1b5e20", smooth=True)

def draw_power_icon(kind, cx, cy, s=1.0):
    r = 10 * s
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=T["panel2"], outline=T["accent"], width=2, tags="dyn")
    if kind == "shield":
        pts = [(0, -6), (6, -3), (5, 3), (0, 7), (-5, 3), (-6, -3)]
        canvas.create_polygon([c for x, y in pts for c in (cx + x * s, cy + y * s)], fill="#4fc3f7", outline="#0277bd", tags="dyn")
    elif kind == "double":
        canvas.create_text(cx, cy, text="2x", fill="#ffb300", font=(FONT_UI, int(9 * s) + 1, "bold"), tags="dyn")
    elif kind == "slow":
        canvas.create_oval(cx - 5 * s, cy - 5 * s, cx + 5 * s, cy + 5 * s, outline="#4dd0e1", width=2, tags="dyn")
        canvas.create_line(cx, cy, cx, cy - 4 * s, fill="#4dd0e1", width=2, tags="dyn")
        canvas.create_line(cx, cy, cx + 3 * s, cy, fill="#4dd0e1", width=2, tags="dyn")
    else:
        canvas.create_text(cx, cy, text="-3", fill="#ba68c8", font=(FONT_UI, int(9 * s) + 1, "bold"), tags="dyn")

def segment_colour(skin, i, n, now):
    """Colour of body segment i (0 = head) for this skin."""
    name = skin["color"]
    if name == "Rainbow":
        r, g, b = colorsys.hsv_to_rgb((now * 0.3 - i * 0.05) % 1.0, 0.6, 1.0)
        return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
    if name == "Ghana":
        return "#fcd116" if i == 0 else ("#ce1126", "#fcd116", "#006b3f")[(i // 2) % 3]
    head, tail = SKIN_COLORS[name]
    return mix(head, tail, i / max(1, n - 1))

def draw_eyes(cx, cy, direction, tag="dyn"):
    dx, dy = DIRECTIONS[direction]
    for sign in (1, -1):
        ex = cx + dx * 4 + (-dy) * 5 * sign
        ey = cy + dy * 4 + dx * 5 * sign
        canvas.create_oval(ex - 3.5, ey - 3.5, ex + 3.5, ey + 3.5, fill="#ffffff", outline="#222222", tags=tag)
        canvas.create_oval(ex - 1.5 + dx, ey - 1.5 + dy, ex + 1.5 + dx, ey + 1.5 + dy, fill="#111111", outline="", tags=tag)

def draw_hat(kind, hx, hy, direction, tag):
    """Head accessory drawn on top of the snake's head."""
    def poly(pts, **kw):
        canvas.create_polygon([c for px, py in pts for c in (hx + px, hy + py)], tags=tag, **kw)
    def rect(x1, y1, x2, y2, **kw):
        canvas.create_rectangle(hx + x1, hy + y1, hx + x2, hy + y2, tags=tag, **kw)
    def oval(x1, y1, x2, y2, **kw):
        canvas.create_oval(hx + x1, hy + y1, hx + x2, hy + y2, tags=tag, **kw)
    if kind == "Crown":
        poly([(-7, -6), (-7, -15), (-3.5, -10), (0, -16), (3.5, -10), (7, -15), (7, -6)], fill="#ffd54f", outline="#b8860b")
        oval(-1.6, -11, 1.6, -7.8, fill="#e53935", outline="")
        oval(-6, -9, -4, -7, fill="#42a5f5", outline="")
        oval(4, -9, 6, -7, fill="#66bb6a", outline="")
    elif kind == "Top Hat":
        rect(-10, -8, 10, -5, fill="#212121", outline="#000000")
        rect(-5.5, -18, 5.5, -8, fill="#2b2b2b", outline="#000000")
        rect(-5.5, -12, 5.5, -9.5, fill="#c62828", outline="")
    elif kind == "Party":
        poly([(-6, -6), (6, -6), (0, -20)], fill="#ab47bc", outline="#6a1b9a")
        poly([(-3.5, -11), (3.5, -11), (2.2, -14), (-2.2, -14)], fill="#ffd54f", outline="")
        oval(-2.5, -22.5, 2.5, -17.5, fill="#ffee58", outline="#f9a825")
    elif kind == "Shades":
        dx, dy = DIRECTIONS[direction]
        centres = []
        for sign in (1, -1):
            ex = hx + dx * 4 + (-dy) * 5 * sign
            ey = hy + dy * 4 + dx * 5 * sign
            centres.append((ex, ey))
        canvas.create_line(*centres[0], *centres[1], fill="#111111", width=2, tags=tag)
        for ex, ey in centres:
            canvas.create_oval(ex - 4.8, ey - 4.8, ex + 4.8, ey + 4.8, fill="#111111", outline="#555555", tags=tag)
            canvas.create_oval(ex - 3, ey - 3.5, ex - 1, ey - 1.5, fill="#90caf9", outline="", tags=tag)
    elif kind == "Halo":
        oval(-9, -19, 9, -13, outline="#ffd54f", width=2)
    elif kind == "Bow":
        poly([(5, -9), (-1, -14), (-1, -4)], fill="#ec407a", outline="#ad1457")
        poly([(5, -9), (11, -14), (11, -4)], fill="#ec407a", outline="#ad1457")
        oval(3, -11, 7, -7, fill="#ad1457", outline="")

def draw_tail_item(kind, pts, tag):
    """Accessory at the tip of the tail."""
    tx, ty = pts[-1]
    if kind == "Rattle":
        ux, uy = 1.0, 0.0
        if len(pts) > 1:
            vx, vy = tx - pts[-2][0], ty - pts[-2][1]
            length = math.hypot(vx, vy)
            if 0 < length < CELL * 1.2:
                ux, uy = vx / length, vy / length
        for k, r in enumerate((4.2, 3.4, 2.6)):
            cx, cy = tx + ux * (7 + k * 6), ty + uy * (7 + k * 6)
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#e8d3ad", outline="#8d6e63", tags=tag)
    elif kind == "Flag":
        canvas.create_line(tx, ty, tx, ty - 22, fill="#5d4037", width=2, tags=tag)
        for k, col in enumerate(("#ce1126", "#fcd116", "#006b3f")):
            canvas.create_rectangle(tx, ty - 22 + k * 3.5, tx + 15, ty - 22 + (k + 1) * 3.5, fill=col, outline="", tags=tag)
        canvas.create_oval(tx + 6.5, ty - 18, tx + 9.5, ty - 15, fill="#111111", outline="", tags=tag)

def render_snake(pts, direction, skin, now, alive=True, shield=False, double=False, tag="dyn"):
    """Draw a snake through the pixel points pts (head first) using a skin."""
    n = len(pts)
    span = max(1, n - 1)
    if alive:
        def colour(i):
            return segment_colour(skin, i, n, now)
    else:
        def colour(i):
            return mix("#9e9e9e", "#5f5f5f", i / span)
    def width(i):
        return CELL - 3 - 6 * i / span
    def joined(i):
        return math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) < CELL * 1.2
    def segment(i, w, c):
        if joined(i):
            canvas.create_line(*pts[i], *pts[i - 1], width=w, capstyle="round", fill=c, tags=tag)
        else:
            x, y = pts[i]
            canvas.create_oval(x - w / 2, y - w / 2, x + w / 2, y + w / 2, fill=c, outline="", tags=tag)
    draw_tail_item(skin["tail"], pts, tag)
    for i in range(n - 1, 0, -1): # dark outline first so the body looks like one piece
        segment(i, width(i) + 3, mix(colour(i), "#000000", 0.6))
    pattern = skin["pattern"]
    for i in range(n - 1, 0, -1):
        c = colour(i)
        segment(i, width(i), c)
        x, y = pts[i]
        if pattern == "Scales" and i % 2 == 1:
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=mix(c, "#ffffff", 0.3), outline="", tags=tag)
        elif pattern == "Spots" and i % 2 == 1:
            canvas.create_oval(x - 3.5, y - 3.5, x + 3.5, y + 3.5, fill=mix(c, "#000000", 0.4), outline="", tags=tag)
        elif pattern == "Stripes" and i % 2 == 0 and joined(i):
            vx, vy = pts[i - 1][0] - x, pts[i - 1][1] - y
            length = math.hypot(vx, vy) or 1
            qx, qy = -vy / length * width(i) * 0.42, vx / length * width(i) * 0.42
            canvas.create_line(x - qx, y - qy, x + qx, y + qy, fill=mix(c, "#000000", 0.45), width=3, tags=tag)
    hx, hy = pts[0]
    hc = colour(0)
    r = CELL / 2 + 0.5
    canvas.create_oval(hx - r - 1, hy - r - 1, hx + r + 1, hy + r + 1, fill=mix(hc, "#000000", 0.6), outline="", tags=tag)
    canvas.create_oval(hx - r, hy - r, hx + r, hy + r, fill=hc, outline="", tags=tag)
    canvas.create_oval(hx - r * 0.6, hy - r * 0.8, hx + r * 0.2, hy - r * 0.2, fill=mix(hc, "#ffffff", 0.3), outline="", tags=tag)
    dx, dy = DIRECTIONS[direction]
    if alive and int(now * 4) % 2 == 0: # tongue flicks in and out
        sx, sy = hx + dx * r, hy + dy * r
        tx, ty = hx + dx * (r + 7), hy + dy * (r + 7)
        canvas.create_line(sx, sy, tx, ty, fill="#e53935", width=2, tags=tag)
        canvas.create_line(tx, ty, tx + dx * 3 - dy * 3, ty + dy * 3 + dx * 3, fill="#e53935", width=2, tags=tag)
        canvas.create_line(tx, ty, tx + dx * 3 + dy * 3, ty + dy * 3 - dx * 3, fill="#e53935", width=2, tags=tag)
    draw_eyes(hx, hy, direction, tag)
    draw_hat(skin["hat"], hx, hy, direction, tag)
    if alive and shield:
        rr = r + 5 + math.sin(now * 8)
        canvas.create_oval(hx - rr, hy - rr, hx + rr, hy + rr, outline="#4fc3f7", width=2, dash=(4, 3), tags=tag)
    if alive and double:
        rr = r + 3
        canvas.create_oval(hx - rr, hy - rr, hx + rr, hy + rr, outline="#ffb300", width=2, tags=tag)

def draw_snake(p, now):
    render_snake([cell_center(c) for c in p["body"]], p["dir"], skins[p["idx"]], now,
                 p["alive"], p["shield"], p["double_t"] > 0)

def trail_puff(x, y, kind, n=2):
    """Little particles left behind the tail (the trail customisation)."""
    cols = TRAILS.get(kind)
    if not cols:
        return
    for _ in range(n):
        particles.append({"x": x + random.uniform(-4, 4), "y": y + random.uniform(-4, 4),
                          "vx": random.uniform(-0.4, 0.4),
                          "vy": random.uniform(-0.5, 0.5) if kind == "Sparkles" else -random.uniform(0.2, 1.0),
                          "life": random.randint(10, 18), "color": random.choice(cols), "size": random.uniform(1.5, 3.2)})

def hud_player(p, x, anchor):
    k = p["idx"] + 1
    sign = 1 if anchor == "w" else -1
    off = 0 if anchor == "w" else -11
    canvas.create_oval(x + off, 16, x + off + 11, 27, fill=skin_head(p["idx"]), outline=T["frame"], tags="dyn")
    name = p["name"] + (f"   ({tally[p['idx']]} W)" if num_players == 2 else "")
    canvas.create_text(x + sign * 17, 22, text=name, fill=T["text"], font=(FONT_UI, 11, "bold"), anchor=anchor, tags="dyn")
    canvas.create_text(x, 38, text="SCORE", fill=T["dim"], font=(FONT_UI, 7, "bold"), anchor=anchor, tags="dyn")
    canvas.create_text(x, 56, text=str(p["score"]), fill=T["accent"], font=(FONT_UI, 20, "bold"), anchor=anchor, tags="dyn")
    if p["combo"] > 1:
        canvas.create_text(x + sign * 52, 38, text=f"COMBO x{p['combo']}", fill=T["good"], font=(FONT_UI, 8, "bold"), anchor=anchor, tags="dyn")
    slot = 0
    if p["shield"]:
        draw_power_icon("shield", x + sign * (112 + slot * 28), 54, 0.9)
        slot += 1
    if p["double_t"] > 0:
        ix = x + sign * (112 + slot * 28)
        draw_power_icon("double", ix, 52, 0.9)
        canvas.create_rectangle(ix - 9, 66, ix - 9 + 18 * p["double_t"] / DOUBLE_TICKS, 69, fill="#ffb300", outline="", tags="dyn")

def draw_hud():
    rrect(PAD, 8, WIN_W - PAD, 78, 12, fill=T["panel"], outline=T["frame"], width=2, tags="dyn")
    cx = WIN_W / 2
    total = sum(p["score"] for p in players)
    head = f"LEVEL {level}" + (f"  -  ROUND {round_no}/{MAX_ROUNDS}" if num_players == 2 else "")
    canvas.create_text(cx, 20, text=head, fill=T["accent"], font=(FONT_UI, 12, "bold"), tags="dyn")
    canvas.create_rectangle(cx - 65, 31, cx + 65, 38, fill=T["tile_lo"], outline="", tags="dyn")
    canvas.create_rectangle(cx - 65, 31, cx - 65 + 130 * (total % 5) / 5, 38, fill=T["accent"], outline="", tags="dyn")
    labels = ["Resume" if state == "paused" else "Pause", "Restart", "Muted" if muted else "Sound"]
    cmds = [toggle_pause, start_match, toggle_mute]
    for i in range(3):
        mini_button(cx + (i - 1) * 66, 60, 60, 20, labels[i], cmds[i], f"hud{i}")
    if slow_t > 0:
        draw_power_icon("slow", cx + 100, 28, 0.9)
    hud_player(players[0], PAD + 16, "w")
    if num_players == 2:
        hud_player(players[1], WIN_W - PAD - 16, "e")
    else:
        x = WIN_W - PAD - 16
        canvas.create_text(x, 38, text="BEST", fill=T["dim"], font=(FONT_UI, 7, "bold"), anchor="e", tags="dyn")
        canvas.create_text(x, 56, text=str(max(best_cache, players[0]["score"])), fill=T["text"], font=(FONT_UI, 20, "bold"), anchor="e", tags="dyn")

GAME_STATES = ("countdown", "play", "paused", "dying", "roundover")

def render():
    canvas.delete("dyn")
    now = time.time()
    draw_hud()
    for f in fruits:
        if f["bonus"] and f["ttl"] < 10 and f["ttl"] % 2:
            continue # blink when about to vanish
        draw_fruit(f["kind"], *cell_center(f["cell"]), now)
    if power and not (power["ttl"] < 15 and power["ttl"] % 2):
        x, y = cell_center(power["cell"])
        draw_power_icon(power["kind"], x, y + math.sin(now * 5) * 2, 1.15)
    for p in players:
        draw_snake(p, now)
    for pt in particles:
        s = pt["size"]
        canvas.create_oval(pt["x"] - s, pt["y"] - s, pt["x"] + s, pt["y"] + s, fill=pt["color"], outline="", tags="dyn")
    for f in floaters:
        canvas.create_text(f["x"] + 1, f["y"] + 1, text=f["text"], fill="#000000", font=(FONT_UI, 11, "bold"), tags="dyn")
        canvas.create_text(f["x"], f["y"], text=f["text"], fill=f["color"], font=(FONT_UI, 11, "bold"), tags="dyn")
    if banner:
        bx, by = BX + WIDTH / 2, BY + 44
        rrect(bx - 130, by - 24, bx + 130, by + 24, 14, fill=T["panel"], outline=T["accent"], width=3, tags="dyn")
        canvas.create_text(bx, by, text=banner["text"], fill=T["accent"], font=(FONT_TITLE, 24), tags="dyn")
    canvas.tag_raise("overlay")

def burst(x, y, color, n=14):
    for _ in range(n):
        ang = random.uniform(0, 6.283)
        spd = random.uniform(1.5, 4.5)
        particles.append({"x": x, "y": y, "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd - 1,
                          "life": random.randint(14, 26), "color": color, "size": random.uniform(2, 4)})

def floater(x, y, text, color):
    floaters.append({"x": x, "y": y, "text": text, "color": color, "life": 32})

def start_shake():
    global shake_t, shake_origin
    if shake_t == 0:
        shake_origin = (root.winfo_x(), root.winfo_y())
    shake_t = 12

def update_effects():
    global banner, shake_t
    if state != "paused":
        for pt in particles:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["vy"] += 0.15
            pt["life"] -= 1
        particles[:] = [pt for pt in particles if pt["life"] > 0]
        for f in floaters:
            f["y"] -= 0.9
            f["life"] -= 1
        floaters[:] = [f for f in floaters if f["life"] > 0]
        if banner:
            banner["ttl"] -= 1
            if banner["ttl"] <= 0:
                banner = None
    if shake_t > 0:
        shake_t -= 1
        ox, oy = shake_origin
        if shake_t == 0:
            root.geometry(f"+{ox}+{oy}")
        else:
            root.geometry(f"+{ox + random.randint(-6, 6)}+{oy + random.randint(-5, 5)}")

def anim_loop():
    if state in GAME_STATES:
        update_effects()
        render()
    elif state == "customize":
        update_effects()
        draw_preview()
    root.after(FRAME_MS, anim_loop)

# ---------------- Round and match flow ----------------
def make_player(i):
    names = (name1_var.get().strip() or "Player 1", name2_var.get().strip() or "Player 2")
    if num_players == 1:
        body, d = [(5, 10), (4, 10), (3, 10)], "Right"
    elif i == 0:
        body, d = [(5, 6), (4, 6), (3, 6)], "Right"
    else:
        body, d = [(COLS - 6, 13), (COLS - 5, 13), (COLS - 4, 13)], "Left"
    return {"idx": i, "name": names[i], "body": body, "dir": d, "next": d, "alive": True, "score": 0,
            "shield": False, "double_t": 0, "combo": 0, "combo_t": 0, "grow": 0}

def occupied():
    taken = set(obstacles)
    for p in players:
        taken.update(p["body"])
    taken.update(f["cell"] for f in fruits)
    if power:
        taken.add(power["cell"])
    return taken

def tick_delay():
    return int(speed_for(level, DIFFICULTY[difficulty][0]) * (1.7 if slow_t > 0 else 1))

def spawn_fruit(bonus=False):
    cell = random_free_cell(occupied())
    if cell is None:
        return
    kind = "mango" if bonus else random.choice(("apple", "orange", "cherry"))
    fruits.append({"cell": cell, "kind": kind, "bonus": bonus, "ttl": BONUS_LIFETIME // tick_delay() if bonus else 0})

def spawn_power():
    global power
    cell = random_free_cell(occupied())
    if cell is not None:
        power = {"cell": cell, "kind": random.choice(("shield", "double", "slow", "shrink")), "ttl": POWER_LIFE}

def valid_obstacle_cell(cell):
    """Obstacles never appear on snakes, items, or in the way of a snake's head."""
    if cell in occupied():
        return False
    for p in players:
        hx, hy = p["body"][0]
        if abs(cell[0] - hx) + abs(cell[1] - hy) <= 5:
            return False
        dx, dy = DIRECTIONS[p["dir"]]
        for k in range(1, 9):
            ahead = (hx + dx * k, hy + dy * k)
            if wrap_on():
                ahead = wrap_cell(ahead)
            if ahead == cell:
                return False
    return True

def add_obstacles():
    """Top up the obstacles to the number the current level asks for."""
    _, per_level, start = DIFFICULTY[difficulty]
    target = min(MAX_OBSTACLES, start + (level - 1) * per_level)
    tries = 0
    while len(obstacles) < target and tries < 250:
        tries += 1
        horizontal = random.random() < 0.5
        x, y = random.randrange(COLS), random.randrange(ROWS)
        cells = [(x + i, y) if horizontal else (x, y + i) for i in range(random.randint(1, 3))]
        cells = cells[:max(1, target - len(obstacles))]
        if not all(not hits_wall(c) and valid_obstacle_cell(c) for c in cells):
            continue
        kind = "special" if level >= 3 and random.random() < 0.5 else "stone"
        trial = dict(obstacles)
        trial.update({c: kind for c in cells})
        if grid_connected(trial, wrap_on()):
            obstacles.update({c: kind for c in cells})

def start_match():
    global round_no, tally
    round_no = 1
    tally = [0, 0]
    begin_round()

def next_round():
    global round_no
    round_no += 1
    begin_round()

def begin_round():
    global players, fruits, power, obstacles, level, slow_t, particles, floaters, banner, state, best_cache
    clear_screen()
    players = [make_player(i) for i in range(num_players)]
    obstacles = {}
    fruits, power, particles, floaters, banner = [], None, [], [], None
    level, slow_t = 1, 0
    best_cache = best_score()
    add_obstacles()
    for _ in players:
        spawn_fruit()
    canvas.configure(bg=T["bg"])
    draw_floor()
    draw_obstacles()
    state = "countdown"
    render()
    countdown(3)

def countdown(n):
    global state, cd_id
    canvas.delete("overlay")
    cx, cy = BX + WIDTH / 2, BY + HEIGHT / 2
    text = str(n) if n > 0 else "GO!"
    canvas.create_text(cx + 3, cy + 4, text=text, fill="#000000", font=(FONT_TITLE, 80), tags="overlay")
    canvas.create_text(cx, cy, text=text, fill=T["accent"], font=(FONT_TITLE, 80), tags="overlay")
    if num_players == 2 and n == 3:
        canvas.create_text(cx, cy + 70, text=f"{players[0]['name']}: W A S D     {players[1]['name']}: arrow keys",
                           fill=T["text"], font=(FONT_UI, 12, "bold"), tags="overlay")
    play("click" if n else "level")
    if n > 0:
        cd_id = root.after(800, lambda: countdown(n - 1))
    else:
        cd_id = root.after(500, begin_play)

def begin_play():
    global state, loop_id
    canvas.delete("overlay")
    state = "play"
    loop_id = root.after(tick_delay(), game_tick)

def eat_fruit(p, f):
    base = BONUS_POINTS if f["bonus"] else 1
    p["combo"] = p["combo"] + 1 if p["combo_t"] > 0 else 1
    p["combo_t"] = COMBO_TICKS
    pts = (base + min(p["combo"] - 1, 3)) * (2 if p["double_t"] > 0 else 1)
    p["score"] += pts
    x, y = cell_center(f["cell"])
    colours = {"apple": "#e53935", "orange": "#fb8c00", "cherry": "#c62828", "mango": "#ffca28"}
    burst(x, y, colours[f["kind"]])
    floater(x, y - 10, f"+{pts}", T["accent"] if f["bonus"] else T["text"])
    play("bonus" if f["bonus"] else "eat")
    if f["bonus"]:
        p["grow"] += 2
        return
    spawn_fruit()
    if not any(g["bonus"] for g in fruits) and random.random() < BONUS_CHANCE:
        spawn_fruit(bonus=True)
    if power is None and random.random() < POWER_CHANCE:
        spawn_power()

def apply_power(p, kind):
    global slow_t
    x, y = cell_center(p["body"][0])
    labels = {"shield": "SHIELD!", "double": "2X POINTS!", "slow": "SLOW-MO!", "shrink": "SHRINK!"}
    if kind == "shield":
        p["shield"] = True
    elif kind == "double":
        p["double_t"] = DOUBLE_TICKS
    elif kind == "slow":
        slow_t = SLOW_TICKS
    else:
        p["body"] = p["body"][:max(3, len(p["body"]) - 3)]
    burst(x, y, "#4fc3f7", 18)
    floater(x, y - 12, labels[kind], "#4fc3f7")
    play("power")

def safe_turn(p, wrap):
    """A direction the snake can turn to right now, or None."""
    others = set()
    for q in players:
        others.update(q["body"])
    for d in DIRECTIONS:
        if d in (p["dir"], OPPOSITE[p["dir"]]):
            continue
        n = next_head(p["body"][0], d)
        if wrap:
            n = wrap_cell(n)
        if (not wrap and hits_wall(n)) or n in obstacles or n in others:
            continue
        return d
    return None

def game_tick():
    global loop_id, level, power, slow_t, banner
    if state != "play":
        return
    wrap = wrap_on()
    live = [p for p in players if p["alive"]]
    fruit_at = {f["cell"]: f for f in fruits}
    info = {}
    for p in live:
        p["dir"] = p["next"]
        h = next_head(p["body"][0], p["dir"])
        if wrap:
            h = wrap_cell(h)
        info[p["idx"]] = {"h": h, "grows": h in fruit_at or p["grow"] > 0, "dead": False, "stay": False}
    for p in live: # work out who crashes
        i = info[p["idx"]]
        h = i["h"]
        cause = None
        if not wrap and hits_wall(h):
            cause = "wall"
        elif h in obstacles:
            cause = "obstacle"
        elif h in (p["body"] if i["grows"] else p["body"][:-1]):
            cause = "self"
        else:
            for q in live:
                if q is p:
                    continue
                qi = info[q["idx"]]
                if h == qi["h"]:
                    cause = "head"
                    break
                if h in (q["body"] if qi["grows"] else q["body"][:-1]):
                    cause = "snake"
                    break
        if cause and cause != "head" and p["shield"]:
            turn = safe_turn(p, wrap)
            if turn:
                p["shield"] = False
                p["dir"] = p["next"] = turn
                i["stay"] = True
                x, y = cell_center(p["body"][0])
                burst(x, y, "#4fc3f7", 20)
                floater(x, y - 12, "SHIELD USED", "#4fc3f7")
                play("power")
                continue
        if cause:
            i["dead"] = True
    global_dead = False
    for p in live: # move, eat, die
        i = info[p["idx"]]
        h = i["h"]
        if i["dead"]:
            p["alive"] = False
            global_dead = True
            x, y = cell_center(p["body"][0])
            burst(x, y, skin_head(p["idx"]), 26)
            continue
        if i["stay"]:
            continue
        p["body"].insert(0, h)
        f = fruit_at.get(h)
        if f:
            fruits.remove(f)
            eat_fruit(p, f)
        elif p["grow"] > 0:
            p["grow"] -= 1
        else:
            p["body"].pop()
        if power and h == power["cell"]:
            apply_power(p, power["kind"])
            power = None
    for p in players: # trail behind the tail
        if p["alive"]:
            trail_puff(*cell_center(p["body"][-1]), skins[p["idx"]]["trail"])
    for p in players: # timers
        if p["combo_t"] > 0:
            p["combo_t"] -= 1
        else:
            p["combo"] = 0
        if p["double_t"] > 0:
            p["double_t"] -= 1
    for f in fruits[:]:
        if f["bonus"]:
            f["ttl"] -= 1
            if f["ttl"] <= 0:
                fruits.remove(f)
    if power:
        power["ttl"] -= 1
        if power["ttl"] <= 0:
            power = None
    if slow_t > 0:
        slow_t -= 1
    if global_dead:
        end_round()
        return
    new_level = level_for(sum(p["score"] for p in players))
    if new_level > level: # harder: faster snake and more obstacles
        level = new_level
        banner = {"text": f"LEVEL {level}!", "ttl": 38}
        play("level")
        add_obstacles()
        draw_obstacles()
    loop_id = root.after(tick_delay(), game_tick)

def end_round():
    global state, end_id
    state = "dying"
    play("crash")
    start_shake()
    end_id = root.after(900, show_round_result)

def overlay_panel(title, lines, buttons, title_color=None):
    canvas.delete("overlay")
    cx, cy = BX + WIDTH / 2, BY + HEIGHT / 2
    w, h = 400, 100 + len(lines) * 26 + len(buttons) * 50
    top = cy - h / 2
    shadow = mix(T["bg"], "#000000", 0.5)
    rrect(cx - w / 2 + 4, top + 6, cx + w / 2 + 4, top + h + 6, 16, fill=shadow, outline="", tags="overlay")
    rrect(cx - w / 2, top, cx + w / 2, top + h, 16, fill=T["panel"], outline=T["accent"], width=3, tags="overlay")
    canvas.create_text(cx, top + 38, text=title, fill=title_color or T["accent"], font=(FONT_TITLE, 26), tags="overlay")
    for i, (text, col) in enumerate(lines):
        canvas.create_text(cx, top + 82 + i * 26, text=text, fill=col, font=(FONT_UI, 12, "bold"), tags="overlay")
    for i, (label, cmd) in enumerate(buttons):
        button(cx, top + 100 + len(lines) * 26 + 20 + i * 50, 240, 38, label, cmd, tag="overlay", key=f"ov{i}")

def show_round_result():
    global state, round_action
    state = "roundover"
    if num_players == 1:
        p = players[0]
        prev_best = best_score()
        rank, improved = add_solo_score(board, p["name"], p["score"], level, mode_text())
        record = p["score"] > prev_best
        if record:
            save_high_score(p["score"])
            play("win")
        lines = [(f"Score: {p['score']}", T["text"]), (f"Level reached: {level}", T["text"]),
                 (f"Best: {max(prev_best, p['score'])}", T["dim"]),
                 (f"Leaderboard rank: #{rank}" + ("" if improved else "  (your best is kept)"), T["accent"])]
        overlay_panel("NEW BEST!" if record else "GAME OVER", lines,
                      [("PLAY AGAIN", start_match), ("LEADERBOARD", go_leaderboard), ("MAIN MENU", go_menu)])
        round_action = start_match
        return
    a, b = players
    if a["alive"] != b["alive"]:
        winner = 0 if a["alive"] else 1
    elif a["score"] != b["score"]:
        winner = 0 if a["score"] > b["score"] else 1
    else:
        winner = None
    if winner is not None:
        tally[winner] += 1
    lines = [(f"{a['name']}  {a['score']}   -   {b['score']}  {b['name']}", T["text"]),
             (f"Rounds won:  {tally[0]}  -  {tally[1]}", T["dim"])]
    decided = max(tally) >= WIN_ROUNDS or round_no >= MAX_ROUNDS
    result = "ROUND DRAWN" if winner is None else f"{players[winner]['name'].upper()} WINS THE ROUND"
    play("win")
    if decided:
        if tally[0] != tally[1]:
            champ = players[0 if tally[0] > tally[1] else 1]["name"]
            add_versus_win(board, champ)
            result = f"{champ.upper()} WINS THE MATCH!"
        else:
            result = "THE MATCH IS A DRAW"
        overlay_panel(result, lines, [("REMATCH", start_match), ("LEADERBOARD", go_leaderboard), ("MAIN MENU", go_menu)])
        round_action = start_match
    else:
        overlay_panel(result, lines, [(f"NEXT ROUND ({round_no + 1}/{MAX_ROUNDS})", next_round), ("MAIN MENU", go_menu)])
        round_action = next_round

def toggle_pause():
    global state, loop_id, round_action
    if state == "play":
        if loop_id is not None:
            root.after_cancel(loop_id)
            loop_id = None
        state = "paused"
        round_action = None
        overlay_panel("PAUSED", [("Press P to continue", T["dim"])],
                      [("RESUME", toggle_pause), ("RESTART", start_match), ("MAIN MENU", go_menu)])
    elif state == "paused":
        canvas.delete("overlay")
        state = "play"
        loop_id = root.after(tick_delay(), game_tick)

# ---------------- Keyboard ----------------
def on_key(event):
    k = event.keysym.lower()
    if state == "name" and k == "return":
        name_continue()
    elif state == "setup":
        if k == "return":
            start_match()
        elif k == "escape":
            go_menu()
    elif state in ("leaderboard", "help", "customize") and k == "escape":
        go_menu()
    elif state == "roundover" and k in ("space", "return") and round_action:
        round_action()
    elif state in ("play", "paused", "countdown", "dying", "roundover") and k == "m":
        toggle_mute()
    elif state in ("play", "paused") and k in ("p", "escape"):
        toggle_pause()
    elif state == "play" and players:
        if k in WASD:
            set_direction(players[0], WASD[k])
        elif k in ARROWS:
            set_direction(players[-1], ARROWS[k])

def set_direction(p, d):
    """Change direction, but never straight back into the body."""
    if p["alive"] and d != OPPOSITE[p["dir"]]:
        p["next"] = d

# ---------------- Build the window ----------------
root = tk.Tk()
root.title("SnakeGH - Classic Arcade Game")
root.resizable(False, False)
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"{WIN_W}x{WIN_H}+{max(0, (sw - WIN_W) // 2)}+{max(0, (sh - WIN_H) // 3)}")
canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg=T["bg"], highlightthickness=0)
canvas.pack()
root.configure(bg=T["bg"])

name1_var = tk.StringVar(value=board["last"][0])
name2_var = tk.StringVar(value=board["last"][1])
for _var in (name1_var, name2_var):
    _var.trace_add("write", lambda *a, v=_var: v.set(v.get()[:12]) if len(v.get()) > 12 else None)

canvas.bind("<Button-1>", on_click)
root.bind("<Key>", on_key)
try:
    make_sound_files()
except OSError:
    pass
go_name_screen()
anim_loop()
root.mainloop()