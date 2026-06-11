import pyray as rl
import random
import math

# --- RETRO-NEON ULTRA FIRE RENK PALETİ ---
CYAN = rl.Color(0, 255, 255, 255)
MAGENTA = rl.Color(255, 0, 180, 255)
PURPLE = rl.Color(140, 20, 240, 255)
LIME = rl.Color(50, 255, 100, 255)
GOLD = rl.Color(255, 200, 0, 255)
SABER_RED = rl.Color(255, 30, 60, 255)
CABINET_METAL = rl.Color(24, 26, 36, 255)
PANEL_DARK = rl.Color(34, 38, 52, 255)
DARK_BLUE = rl.Color(10, 15, 35, 255)
NEON_PINK = rl.Color(255, 16, 240, 255)
NEON_BLUE = rl.Color(0, 200, 255, 255)

W = 1100
H = 720
TITLE = "NEON ARCADE: ULTRA JUICED"

STATE_HUB = 0
STATE_RACE = 1
STATE_BREAKOUT = 2
STATE_PACMAN = 3
STATE_DANCE = 4

rl.init_window(W, H, TITLE)
rl.set_target_fps(60)

# --- BULLETPROOF SES MOTORU ---
audio_enabled = False
snd_blip = None
snd_explosion = None
snd_coin = None
snd_beat = None
snd_perfect = None

try:
    rl.init_audio_device()
    if rl.is_audio_device_ready():
        w_blip = rl.gen_wave_sine(600, 0.3, 16000)
        snd_blip = rl.load_sound_from_wave(w_blip)
        rl.unload_wave(w_blip)
        
        w_exp = rl.gen_wave_sawtooth(110, 0.5, 22050)
        snd_explosion = rl.load_sound_from_wave(w_exp)
        rl.unload_wave(w_exp)
        
        w_coin = rl.gen_wave_square(950, 0.4, 20000)
        snd_coin = rl.load_sound_from_wave(w_coin)
        rl.unload_wave(w_coin)
        
        w_beat = rl.gen_wave_sine(70, 0.6, 12000)
        snd_beat = rl.load_sound_from_wave(w_beat)
        rl.unload_wave(w_beat)
        
        w_perfect = rl.gen_wave_sine(1200, 0.2, 18000)
        snd_perfect = rl.load_sound_from_wave(w_perfect)
        rl.unload_wave(w_perfect)
        
        audio_enabled = True
except Exception:
    audio_enabled = False

def play_sfx(sound_obj):
    if audio_enabled and sound_obj:
        rl.play_sound(sound_obj)

# --- GLOBAL AKSİYON VE PARÇACIK SİSTEMİ ---
def clamp(v, a, b): return max(a, min(b, v))
def rects_intersect(a, b):
    return not (a["x"] + a["w"] < b["x"] or a["x"] > b["x"] + b["w"] or a["y"] + a["h"] < b["y"] or a["y"] > b["y"] + b["h"])

SCR_X, SCR_Y, SCR_W, SCR_H = 240, 45, 620, 430
screen_shake = 0.0
hit_stop_timer = 0

particles = []
def spawn_particles(x, y, color, count=15, velocity=1.0):
    for _ in range(count):
        particles.append({
            "x": float(x), "y": float(y),
            "vx": random.uniform(-6.0, 6.0) * velocity, "vy": random.uniform(-6.0, 6.0) * velocity,
            "life": 1.0, "decay": random.uniform(0.03, 0.06),
            "color": color, "size": random.uniform(4, 7)
        })

# Atmosferik parçacıklar (arka plan efektleri)
ambient_particles = []
def spawn_ambient_particles(count=5):
    for _ in range(count):
        ambient_particles.append({
            "x": float(random.randint(SCR_X, SCR_X + SCR_W)),
            "y": float(random.randint(SCR_Y, SCR_Y + SCR_H)),
            "vx": random.uniform(-0.5, 0.5),
            "vy": random.uniform(-0.3, 0.1),
            "life": 1.0,
            "decay": random.uniform(0.001, 0.003),
            "color": random.choice([rl.fade(CYAN, 0.3), rl.fade(MAGENTA, 0.2), rl.fade(PURPLE, 0.25)]),
            "size": random.uniform(1, 3)
        })

def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vx"] *= 0.94
        p["vy"] *= 0.94
        p["life"] -= p["decay"]
        if p["life"] <= 0: particles.remove(p)

def update_ambient_particles():
    for p in ambient_particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= p["decay"]
        if p["life"] <= 0: ambient_particles.remove(p)

def draw_particles(ox=0, oy=0):
    for p in particles:
        rl.draw_rectangle(int(p["x"]) + ox, int(p["y"]) + oy, int(p["size"] * p["life"]), int(p["size"] * p["life"]), rl.fade(p["color"], p["life"]))

def draw_ambient_particles(ox=0, oy=0):
    for p in ambient_particles:
        rl.draw_circle(int(p["x"]) + ox, int(p["y"]) + oy, p["size"] * p["life"], rl.fade(p["color"], p["life"] * 0.5))

def get_shake_offsets():
    global screen_shake
    if screen_shake > 0:
        sx = random.uniform(-screen_shake, screen_shake)
        sy = random.uniform(-screen_shake, screen_shake)
        screen_shake *= 0.88
        if screen_shake < 0.3: screen_shake = 0.0
        return int(sx), int(sy)
    return 0, 0

beat_counter = 0
def update_background_music(speed_multiplier=1):
    global beat_counter
    beat_counter += 1
    trigger_frame = max(14, 28 - speed_multiplier)
    if beat_counter >= trigger_frame:
        beat_counter = 0
        play_sfx(snd_beat)

# --- DRAW NEON GLOW EFFECT ---
def draw_neon_glow(x, y, radius, color, intensity=0.3):
    for i in range(1, 5):
        rl.draw_circle_lines(x, y, radius + i * 2, rl.fade(color, intensity * (1.0 - i / 5.0)))

# --- ARCADE CABINET DRAWING ---
def draw_arcade_cabinet(game_title, accent_color, control_type="arcade"):
    t = rl.get_time()
    flicker = 0.95 + 0.05 * math.sin(t * 40)
    title_c = rl.Color(int(accent_color.r * flicker), int(accent_color.g * flicker), int(accent_color.b * flicker), 255)

    # Yan metaller
    rl.draw_rectangle(0, 0, 230, H, rl.Color(12, 14, 20, 255))
    rl.draw_rectangle(W - 230, 0, 230, H, rl.Color(12, 14, 20, 255))
    
    # Neon çizgileri
    rl.draw_line_ex(rl.Vector2(226, 0), rl.Vector2(226, H), 4, rl.fade(accent_color, 0.6))
    rl.draw_line_ex(rl.Vector2(W - 226, 0), rl.Vector2(W - 226, H), 4, rl.fade(accent_color, 0.6))
    
    # Parlayan efekt
    for i in range(1, 3):
        rl.draw_line_ex(rl.Vector2(226 - i, 0), rl.Vector2(226 - i, H), 1, rl.fade(accent_color, 0.2 / i))
        rl.draw_line_ex(rl.Vector2(W - 226 + i, 0), rl.Vector2(W - 226 + i, H), 1, rl.fade(accent_color, 0.2 / i))

    # Üst Tabela
    rl.draw_rectangle(226, 0, 648, 45, rl.BLACK)
    rl.draw_rectangle_lines_ex(rl.Rectangle(226, 0, 648, 45), 2, accent_color)
    rl.draw_text(game_title, 240 + (620 - rl.measure_text(game_title, 22)) // 2, 12, 22, title_c)

    # Ekran çerçevesi
    rl.draw_rectangle_lines_ex(rl.Rectangle(SCR_X - 14, SCR_Y - 14, SCR_W + 28, SCR_H + 28), 14, CABINET_METAL)
    
    # Parlayan ekran bordürü
    for i in range(1, 4):
        rl.draw_rectangle_lines_ex(rl.Rectangle(SCR_X - 14 - i, SCR_Y - 14 - i, SCR_W + 28 + i*2, SCR_H + 28 + i*2), 1, rl.fade(accent_color, (0.4 - i * 0.1)))

    panel_y = 475
    rl.draw_rectangle(226, panel_y, 648, H - panel_y, PANEL_DARK)
    rl.draw_rectangle_gradient_v(226, panel_y, 648, 20, rl.Color(15, 17, 24, 255), PANEL_DARK)
    rl.draw_line_ex(rl.Vector2(226, panel_y), rl.Vector2(W - 226, panel_y), 3, accent_color)

    if control_type == "arcade":
        jx, jy = 420, panel_y + 110
        rl.draw_circle(jx, jy, 30, rl.BLACK)
        rl.draw_circle_lines(jx, jy, 30, rl.GRAY)
        draw_neon_glow(jx, jy, 30, SABER_RED, 0.2)
        
        dx, dy = 0, 0
        if rl.is_key_down(rl.KEY_LEFT) or rl.is_key_down(rl.KEY_A): dx = -16
        if rl.is_key_down(rl.KEY_RIGHT) or rl.is_key_down(rl.KEY_D): dx = 16
        if rl.is_key_down(rl.KEY_UP) or rl.is_key_down(rl.KEY_W): dy = -16
        if rl.is_key_down(rl.KEY_DOWN) or rl.is_key_down(rl.KEY_S): dy = 16
        
        rl.draw_line_ex(rl.Vector2(jx, jy), rl.Vector2(jx + dx, jy + dy), 7, rl.LIGHTGRAY)
        rl.draw_circle(jx + dx, jy + dy, 18, SABER_RED)
        rl.draw_text("JOYSTICK", jx - 32, jy + 42, 13, rl.GRAY)

        btn_keys = [rl.KEY_SPACE, rl.KEY_R, rl.KEY_LEFT, rl.KEY_RIGHT]
        btn_labels = ["ACT", "RST", "L", "R"]
        btn_colors = [CYAN, MAGENTA, GOLD, LIME]
        
        for i in range(4):
            bx = 660 + (i % 2) * 70
            by = (panel_y + 75) + (i // 2) * 65
            is_pressed = rl.is_key_down(btn_keys[i])
            
            rl.draw_circle(bx, by, 22, rl.BLACK)
            if is_pressed:
                rl.draw_circle(bx, by, 15, btn_colors[i])
                rl.draw_circle_lines(bx, by, 22, rl.WHITE)
                draw_neon_glow(bx, by, 22, btn_colors[i], 0.4)
            else:
                rl.draw_circle(bx, by, 19, rl.fade(btn_colors[i], 0.8))
                rl.draw_circle_lines(bx, by, 19, rl.BLACK)
                draw_neon_glow(bx, by, 19, btn_colors[i], 0.2)
            rl.draw_text(btn_labels[i], bx - rl.measure_text(btn_labels[i], 10)//2, by + 23, 10, rl.LIGHTGRAY)

    elif control_type == "dance":
        pad_x = 310
        pad_y = panel_y + 20
        pad_w, pad_h = 85, 85
        pad_spacing = 100
        
        rl.draw_text("NEON FLOOR PAD", 380, panel_y - 20, 16, MAGENTA)
        
        directions = ["<", "v", "^", ">"]
        dir_colors = [CYAN, GOLD, LIME, MAGENTA]
        keys = [rl.KEY_LEFT, rl.KEY_DOWN, rl.KEY_UP, rl.KEY_RIGHT]
        alt_keys = [rl.KEY_A, rl.KEY_S, rl.KEY_W, rl.KEY_D]
        
        for i in range(4):
            x_pos = pad_x + i * pad_spacing
            pressed = rl.is_key_down(keys[i]) or rl.is_key_down(alt_keys[i])
            
            rl.draw_rectangle(x_pos, pad_y, pad_w, pad_h, rl.BLACK)
            
            if pressed:
                rl.draw_rectangle(x_pos + 2, pad_y + 2, pad_w - 4, pad_h - 4, dir_colors[i])
                rl.draw_rectangle_lines_ex(rl.Rectangle(x_pos, pad_y, pad_w, pad_h), 4, rl.WHITE)
                draw_neon_glow(x_pos + pad_w//2, pad_y + pad_h//2, pad_w//2, dir_colors[i], 0.5)
                for _ in range(3):
                    spawn_particles(x_pos + pad_w//2, pad_y + pad_h//2, dir_colors[i], 2)
            else:
                rl.draw_rectangle_lines_ex(rl.Rectangle(x_pos, pad_y, pad_w, pad_h), 3, dir_colors[i])
                draw_neon_glow(x_pos + pad_w//2, pad_y + pad_h//2, pad_w//2, dir_colors[i], 0.2)
            
            rl.draw_text(directions[i], x_pos + pad_w//2 - 8, pad_y + pad_h//2 - 10, 32, dir_colors[i])

    # CRT Scanlines
    for y in range(SCR_Y, SCR_Y + SCR_H, 3):
        rl.draw_line(SCR_X, y, SCR_X + SCR_W, y, rl.fade(rl.BLACK, 0.18))
    rl.draw_rectangle_lines_ex(rl.Rectangle(SCR_X, SCR_Y, SCR_W, SCR_H), 8, rl.fade(rl.BLACK, 0.4))

# --- ULTRA ANIMATED TRASH FIGURE ---
def draw_trash_figure(x, y, color=rl.WHITE, state="idle", frame=0):
    head_r = 10
    body_h = 28
    arm_len = 20
    leg_len = 24
    
    if state == "dancing":
        # ULTRA DANCING ANIMATION
        arm_swing = math.sin(frame * 0.25) * 40
        body_bob = math.cos(frame * 0.15) * 8
        leg_kick = math.sin(frame * 0.18) * 15
        
        # Head with bounce
        rl.draw_circle(int(x), int(y - body_h - head_r + body_bob), head_r, color)
        rl.draw_circle_lines(int(x), int(y - body_h - head_r + body_bob), head_r + 1, rl.fade(color, 0.5))
        
        # Eyes happy
        eye_y = int(y - body_h - head_r + body_bob - 2)
        rl.draw_circle(int(x - 4), eye_y, 2, rl.WHITE)
        rl.draw_circle(int(x + 4), eye_y, 2, rl.WHITE)
        # Smile
        for i in range(-3, 4):
            rl.draw_pixel(int(x + i), eye_y + 3, rl.WHITE)
        
        # Body
        rl.draw_line_ex(rl.Vector2(x, y - body_h + body_bob), rl.Vector2(x, y + body_bob), 4, color)
        
        # Wild arms
        rl.draw_line_ex(rl.Vector2(x, y - body_h + 10 + body_bob), 
                       rl.Vector2(x - arm_len + arm_swing//2, y - body_h - 12 + body_bob), 4, color)
        rl.draw_line_ex(rl.Vector2(x, y - body_h + 10 + body_bob), 
                       rl.Vector2(x + arm_len - arm_swing//2, y - body_h - 12 + body_bob), 4, color)
        
        # Hands
        rl.draw_circle(int(x - arm_len + arm_swing//2), int(y - body_h - 12 + body_bob), 4, MAGENTA)
        rl.draw_circle(int(x + arm_len - arm_swing//2), int(y - body_h - 12 + body_bob), 4, MAGENTA)
        
        # Kicking legs
        rl.draw_line_ex(rl.Vector2(x, y + body_bob), 
                       rl.Vector2(x - 10 + leg_kick, y + leg_len), 4, color)
        rl.draw_line_ex(rl.Vector2(x, y + body_bob), 
                       rl.Vector2(x + 10 - leg_kick, y + leg_len), 4, color)
        
        # Feet
        rl.draw_circle(int(x - 10 + leg_kick), int(y + leg_len), 4, CYAN)
        rl.draw_circle(int(x + 10 - leg_kick), int(y + leg_len), 4, LIME)
    
    elif state == "jumping":
        jump = math.sin(frame * 0.3) * 40
        
        rl.draw_circle(int(x), int(y - body_h - head_r - jump), head_r, color)
        rl.draw_circle_lines(int(x), int(y - body_h - head_r - jump), head_r + 1, rl.fade(color, 0.5))
        
        eye_y = int(y - body_h - head_r - jump)
        rl.draw_circle(int(x - 4), eye_y, 2, rl.WHITE)
        rl.draw_circle(int(x + 4), eye_y, 2, rl.WHITE)
        
        rl.draw_line_ex(rl.Vector2(x, y - body_h - jump), rl.Vector2(x, y - jump), 4, color)
        
        rl.draw_line_ex(rl.Vector2(x, y - body_h + 5 - jump), rl.Vector2(x - arm_len, y - body_h - 10 - jump), 4, color)
        rl.draw_line_ex(rl.Vector2(x, y - body_h + 5 - jump), rl.Vector2(x + arm_len, y - body_h - 10 - jump), 4, color)
        
        rl.draw_line_ex(rl.Vector2(x - 8, y - jump), rl.Vector2(x - 8, y + leg_len - jump), 4, color)
        rl.draw_line_ex(rl.Vector2(x + 8, y - jump), rl.Vector2(x + 8, y + leg_len - jump), 4, color)
    
    else:  # idle
        idle_sway = math.sin(frame * 0.1) * 4
        
        rl.draw_circle(int(x + idle_sway), int(y - body_h - head_r), head_r, color)
        rl.draw_circle_lines(int(x + idle_sway), int(y - body_h - head_r), head_r + 1, rl.fade(color, 0.5))
        
        eye_y = int(y - body_h - head_r - 2)
        rl.draw_circle(int(x + idle_sway - 4), eye_y, 2, rl.WHITE)
        rl.draw_circle(int(x + idle_sway + 4), eye_y, 2, rl.WHITE)
        
        rl.draw_line_ex(rl.Vector2(x + idle_sway, y - body_h), rl.Vector2(x + idle_sway, y), 4, color)
        
        rl.draw_line_ex(rl.Vector2(x + idle_sway, y - body_h + 5), rl.Vector2(x - arm_len + idle_sway, y - body_h - 5), 4, color)
        rl.draw_line_ex(rl.Vector2(x + idle_sway, y - body_h + 5), rl.Vector2(x + arm_len + idle_sway, y - body_h - 5), 4, color)
        
        rl.draw_line_ex(rl.Vector2(x - 6 + idle_sway, y), rl.Vector2(x - 6 + idle_sway, y + leg_len), 4, color)
        rl.draw_line_ex(rl.Vector2(x + 6 + idle_sway, y), rl.Vector2(x + 6 + idle_sway, y + leg_len), 4, color)

# --- HUB AREA ---
player = {"x": W // 2, "y": H - 120, "r": 16, "speed": 6.0, "frame": 0}
cabinets = [
    {"name": "RACE RIOT", "x": 60, "y": 180, "w": 140, "h": 260, "color": SABER_RED, "state": STATE_RACE, "ctrl": "arcade"},
    {"name": "PIXEL SMASH", "x": 270, "y": 180, "w": 140, "h": 260, "color": CYAN, "state": STATE_BREAKOUT, "ctrl": "arcade"},
    {"name": "NEON CHOMP", "x": 480, "y": 180, "w": 140, "h": 260, "color": GOLD, "state": STATE_PACMAN, "ctrl": "arcade"},
    {"name": "DANCE BEAT", "x": 730, "y": 150, "w": 280, "h": 290, "color": MAGENTA, "state": STATE_DANCE, "ctrl": "dance"}
]

# --- GAME 1: RACE RIOT ---
race = {"lane": 1, "px": float(SCR_X + SCR_W//2), "speed": 7.0, "score": 0, "timer": 0, "cars": [], "over": False}
race_lanes = [SCR_X + 90, SCR_X + SCR_W // 2, SCR_X + SCR_W - 90]

def update_race():
    global race, screen_shake
    update_background_music(int(race["speed"]))
    if race["over"]:
        if rl.is_key_pressed(rl.KEY_R): race = {"lane": 1, "px": float(SCR_X + SCR_W//2), "speed": 7.0, "score": 0, "timer": 0, "cars": [], "over": False}
        return STATE_RACE
    if rl.is_key_pressed(rl.KEY_LEFT) or rl.is_key_pressed(rl.KEY_A): race["lane"] = max(0, race["lane"] - 1)
    if rl.is_key_pressed(rl.KEY_RIGHT) or rl.is_key_pressed(rl.KEY_D): race["lane"] = min(2, race["lane"] + 1)

    race["px"] += (race_lanes[race["lane"]] - race["px"]) * 0.25
    race["speed"] += 0.005
    race["score"] += 1

    race["timer"] += 1
    if race["timer"] >= max(12, 40 - int(race["speed"])):
        race["cars"].append({"x": race_lanes[random.choice([0, 1, 2])], "y": SCR_Y - 70, "color": MAGENTA, "speed": race["speed"] * 0.8})
        race["timer"] = 0

    p_rect = {"x": race["px"] - 20, "y": SCR_Y + SCR_H - 90, "w": 40, "h": 70}
    for c in race["cars"][:]:
        c["y"] += c["speed"]
        if rects_intersect(p_rect, {"x": c["x"] - 20, "y": c["y"], "w": 40, "h": 70}):
            race["over"] = True
            screen_shake = 25.0
            play_sfx(snd_explosion)
            spawn_particles(race["px"], c["y"] + 30, SABER_RED, 40)
        if c["y"] > SCR_Y + SCR_H: race["cars"].remove(c)
    return STATE_RACE

def draw_race():
    ox, oy = get_shake_offsets()
    rl.clear_background(rl.BLACK)
    rl.draw_rectangle(SCR_X + ox, SCR_Y + oy, SCR_W, SCR_H, rl.Color(15, 15, 25, 255))
    
    draw_ambient_particles(ox, oy)
    
    for i in range(-1, 6):
        yo = int((i * 100 + rl.get_time() * race["speed"] * 50) % (SCR_H + 100)) + SCR_Y - 100
        rl.draw_rectangle(SCR_X + SCR_W//2 - 60 + ox, yo + oy, 6, 40, rl.DARKGRAY)
        rl.draw_rectangle(SCR_X + SCR_W//2 + 60 + ox, yo + oy, 6, 40, rl.DARKGRAY)

    for c in race["cars"]: 
        rl.draw_rectangle(int(c["x"] - 20) + ox, int(c['y']) + oy, 40, 70, c["color"])
        draw_neon_glow(int(c["x"]) + ox, int(c['y'] + 35) + oy, 25, c["color"], 0.3)
    
    rl.draw_rectangle(int(race["px"]) - 20 + ox, SCR_Y + SCR_H - 90 + oy, 40, 70, CYAN)
    draw_neon_glow(int(race["px"]) + ox, SCR_Y + SCR_H - 55 + oy, 25, CYAN, 0.3)
    
    draw_particles(ox, oy)
    rl.draw_text(f"SCORE: {race['score']}", SCR_X + 25, SCR_Y + 25, 20, GOLD)
    if race["over"]: rl.draw_text("CRASH! R TO RESTART", SCR_X + 140, SCR_Y + 200, 26, SABER_RED)
    draw_arcade_cabinet("RACE RIOT", SABER_RED, "arcade")

# --- GAME 2: PIXEL SMASH (BREAKOUT) ---
def reset_breakout():
    bricks = [{"x": SCR_X + 25 + c * 64, "y": SCR_Y + 60 + r * 22, "w": 58, "h": 16, "color": random.choice([LIME, CYAN, MAGENTA, GOLD])} for r in range(4) for c in range(9)]
    return {"px": float(SCR_X + SCR_W//2 - 50), "bx": float(SCR_X + SCR_W//2), "by": float(SCR_Y + SCR_H - 80), "vx": 5.0, "vy": -5.0, "launch": False, "bricks": bricks, "score": 0, "lives": 3}
breakout = reset_breakout()

def update_breakout():
    global breakout, screen_shake
    update_background_music(10)
    if breakout["lives"] <= 0 or len(breakout["bricks"]) == 0:
        if rl.is_key_pressed(rl.KEY_R): breakout = reset_breakout()
        return STATE_BREAKOUT

    if rl.is_key_down(rl.KEY_LEFT) or rl.is_key_down(rl.KEY_A): breakout["px"] = max(SCR_X + 10, breakout["px"] - 8)
    if rl.is_key_down(rl.KEY_RIGHT) or rl.is_key_down(rl.KEY_D): breakout["px"] = min(SCR_X + SCR_W - 110, breakout["px"] + 8)

    if not breakout["launch"]:
        breakout["bx"], breakout["by"] = breakout["px"] + 50, SCR_Y + SCR_H - 50
        if rl.is_key_pressed(rl.KEY_SPACE): breakout["launch"] = True
    else:
        breakout["bx"] += breakout["vx"]
        breakout["by"] += breakout["vy"]

        if breakout["bx"] <= SCR_X + 10 or breakout["bx"] >= SCR_X + SCR_W - 10: breakout["vx"] *= -1; play_sfx(snd_blip)
        if breakout["by"] <= SCR_Y + 10: breakout["vy"] *= -1; play_sfx(snd_blip)

        if breakout["by"] > SCR_Y + SCR_H:
            breakout["lives"] -= 1; breakout["launch"] = False; play_sfx(snd_explosion); screen_shake = 15.0

        prec = {"x": breakout["px"], "y": SCR_Y + SCR_H - 40, "w": 100, "h": 12}
        if breakout["vy"] > 0 and (breakout["bx"] >= prec["x"] and breakout["bx"] <= prec["x"]+100 and breakout["by"] >= prec["y"] and breakout["by"] <= prec["y"]+12):
            breakout["vy"] *= -1; play_sfx(snd_blip); screen_shake = 4.0
            breakout["vx"] = ((breakout["bx"] - (prec["x"] + 50)) / 50) * 6.0

        for b in breakout["bricks"][:]:
            if breakout["bx"] >= b["x"] and breakout["bx"] <= b["x"]+b["w"] and breakout["by"] >= b["y"] and breakout["by"] <= b["y"]+b["h"]:
                breakout["bricks"].remove(b); breakout["vy"] *= -1; breakout["score"] += 100
                screen_shake = 8.0; play_sfx(snd_coin)
                spawn_particles(b["x"]+29, b["y"]+8, LIME, 12)
                break
    return STATE_BREAKOUT

def draw_breakout():
    ox, oy = get_shake_offsets()
    rl.clear_background(rl.BLACK)
    rl.draw_rectangle(SCR_X + ox, SCR_Y + oy, SCR_W, SCR_H, rl.Color(12, 12, 20, 255))
    
    draw_ambient_particles(ox, oy)
    
    for b in breakout["bricks"]: 
        rl.draw_rectangle(b["x"] + ox, b["y"] + oy, b["w"], b["h"], b["color"])
        draw_neon_glow(b["x"] + b["w"]//2 + ox, b["y"] + b["h"]//2 + oy, 30, b["color"], 0.2)
    
    rl.draw_rectangle(int(breakout["px"]) + ox, SCR_Y + SCR_H - 40 + oy, 100, 12, rl.WHITE)
    rl.draw_circle(int(breakout["bx"]) + ox, int(breakout["by"]) + oy, 7, CYAN)
    draw_neon_glow(int(breakout["bx"]) + ox, int(breakout["by"]) + oy, 10, CYAN, 0.4)
    
    draw_particles(ox, oy)
    rl.draw_text(f"SCORE: {breakout['score']}  LIVES: {breakout['lives']}", SCR_X + 25, SCR_Y + 25, 20, CYAN)
    if breakout["lives"] <= 0: rl.draw_text("GAME OVER! PRESS R", SCR_X + 150, SCR_Y + 200, 26, SABER_RED)
    draw_arcade_cabinet("PIXEL SMASH", CYAN, "arcade")

# --- GAME 3: PAC-MAN JUICED (NEON CHOMPER) ---
def reset_pacman():
    dots = []
    for x in range(11):
        for y in range(7):
            if not (x in [0, 10] and y in [0, 6]) and not (x==5 and y==3):
                dots.append({"x": SCR_X + 60 + x * 50, "y": SCR_Y + 90 + y * 50, "is_power": (x==1 and y==1) or (x==9 and y==5)})
    return {
        "px": float(SCR_X + SCR_W//2), "py": float(SCR_Y + SCR_H//2 + 50),
        "ghosts": [
            {"x": float(SCR_X + 80), "y": float(SCR_Y + 80), "color": SABER_RED, "vx": 3.0, "vy": 0.0},
            {"x": float(SCR_X + SCR_W - 80), "y": float(SCR_Y + 80), "color": MAGENTA, "vx": -3.0, "vy": 0.0}
        ],
        "dots": dots, "score": 0, "lives": 3, "frightened": 0, "over": False, "won": False
    }
pac = reset_pacman()

def update_pacman():
    global pac, screen_shake, hit_stop_timer
    update_background_music(15 if pac["frightened"] > 0 else 8)
    
    if hit_stop_timer > 0:
        hit_stop_timer -= 1
        return STATE_PACMAN

    if pac["over"] or pac["won"] or pac["lives"] <= 0:
        if rl.is_key_pressed(rl.KEY_R): pac = reset_pacman()
        return STATE_PACMAN

    spd = 4.5
    if rl.is_key_down(rl.KEY_LEFT) or rl.is_key_down(rl.KEY_A): pac["px"] -= spd
    if rl.is_key_down(rl.KEY_RIGHT) or rl.is_key_down(rl.KEY_D): pac["px"] += spd
    if rl.is_key_down(rl.KEY_UP) or rl.is_key_down(rl.KEY_W): pac["py"] -= spd
    if rl.is_key_down(rl.KEY_DOWN) or rl.is_key_down(rl.KEY_S): pac["py"] += spd

    pac["px"] = clamp(pac["px"], SCR_X + 25, SCR_X + SCR_W - 25)
    pac["py"] = clamp(pac["py"], SCR_Y + 25, SCR_Y + SCR_H - 25)

    if pac["frightened"] > 0: pac["frightened"] -= 1

    for d in pac["dots"][:]:
        if math.hypot(pac["px"] - d["x"], pac["py"] - d["y"]) < 20:
            pac["dots"].remove(d)
            if d["is_power"]:
                pac["frightened"] = 360
                pac["score"] += 200
                screen_shake = 12.0
                play_sfx(snd_coin)
                spawn_particles(d["x"], d["y"], PURPLE, 20)
            else:
                pac["score"] += 20
                screen_shake = max(screen_shake, 1.8)
                play_sfx(snd_blip)

    if len(pac["dots"]) == 0:
        pac["won"] = True
        screen_shake = 20.0
        play_sfx(snd_coin)
        return STATE_PACMAN

    for g in pac["ghosts"]:
        if random.random() < 0.02:
            if random.choice([True, False]): g["vx"], g["vy"] = random.choice([-3, 3]), 0.0
            else: g["vx"], g["vy"] = 0.0, random.choice([-3, 3])
        
        g["x"] += g["vx"]
        g["y"] += g["vy"]
        g["x"] = clamp(g["x"], SCR_X + 30, SCR_X + SCR_W - 30)
        g["y"] = clamp(g["y"], SCR_Y + 30, SCR_Y + SCR_H - 30)

        if g["x"] <= SCR_X + 32 or g["x"] >= SCR_X + SCR_W - 32: g["vx"] *= -1
        if g["y"] <= SCR_Y + 32 or g["y"] >= SCR_Y + SCR_H - 32: g["vy"] *= -1

        if math.hypot(pac["px"] - g["x"], pac["py"] - g["y"]) < 25:
            if pac["frightened"] > 0:
                pac["score"] += 500
                g["x"], g["y"] = SCR_X + 80, SCR_Y + 80
                screen_shake = 20.0
                hit_stop_timer = 10
                play_sfx(snd_explosion)
                spawn_particles(pac["px"], pac["py"], CYAN, 30)
            else:
                pac["lives"] -= 1
                pac["px"], pac["py"] = SCR_X + SCR_W//2, SCR_Y + SCR_H//2 + 50
                screen_shake = 25.0
                play_sfx(snd_explosion)
                spawn_particles(pac["px"], pac["py"], SABER_RED, 35)
                if pac["lives"] <= 0: pac["over"] = True
    return STATE_PACMAN

def draw_pacman():
    ox, oy = get_shake_offsets()
    rl.clear_background(rl.BLACK)
    rl.draw_rectangle(SCR_X + ox, SCR_Y + oy, SCR_W, SCR_H, rl.Color(10, 10, 14, 255))
    
    draw_ambient_particles(ox, oy)
    
    rl.draw_rectangle_lines_ex(rl.Rectangle(SCR_X + 15 + ox, SCR_Y + 15 + oy, SCR_W - 30, SCR_H - 30), 4, PURPLE)

    for d in pac["dots"]:
        if d["is_power"]: 
            sz = 9 + int(math.sin(rl.get_time()*15)*3)
            rl.draw_circle(d["x"] + ox, d["y"] + oy, sz, GOLD)
            draw_neon_glow(d["x"] + ox, d["y"] + oy, sz + 2, GOLD, 0.3)
        else: 
            rl.draw_circle(d["x"] + ox, d["y"] + oy, 4, CYAN)

    chomp = abs(math.sin(rl.get_time() * 22)) * 0.6
    rl.draw_circle_sector(rl.Vector2(pac["px"] + ox, pac["py"] + oy), 16, chomp * 40, 360 - (chomp * 40), 24, GOLD)

    for g in pac["ghosts"]:
        c = CYAN if pac["frightened"] > 0 else g["color"]
        rl.draw_circle(int(g["x"]) + ox, int(g["y"]) + oy, 15, c)
        rl.draw_rectangle(int(g["x"])-15 + ox, int(g["y"]) + oy, 30, 15, c)
        rl.draw_circle(int(g["x"])-6 + ox, int(g["y"])-3 + oy, 4, rl.WHITE)
        rl.draw_circle(int(g["x"])+6 + ox, int(g["y"])-3 + oy, 4, rl.WHITE)
        draw_neon_glow(int(g["x"]) + ox, int(g["y"]) + oy, 18, c, 0.3)

    draw_particles(ox, oy)
    rl.draw_text(f"SCORE: {pac['score']}  HP: {pac['lives']}", SCR_X + 30, SCR_Y + 30, 20, GOLD)
    if pac["frightened"] > 0: rl.draw_text(f"POWER: {pac['frightened']//60}", SCR_X + SCR_W - 140, SCR_Y + 30, 20, LIME)
    
    if pac["over"]:
        rl.draw_rectangle(SCR_X, SCR_Y, SCR_W, SCR_H, rl.fade(rl.BLACK, 0.8))
        rl.draw_text("GAME OVER! PRESS R", SCR_X + 160, SCR_Y + 200, 26, SABER_RED)
    elif pac["won"]:
        rl.draw_rectangle(SCR_X, SCR_Y, SCR_W, SCR_H, rl.fade(rl.BLACK, 0.85))
        rl.draw_text("VICTORY STAGE CLEAR", SCR_X + 110, SCR_Y + 180, 26, LIME)
        rl.draw_text("PRESS R TO PLAY AGAIN", SCR_X + 150, SCR_Y + 230, 18, GOLD)
        if random.random() < 0.15: spawn_particles(random.randint(SCR_X+50, SCR_X+SCR_W-50), random.randint(SCR_Y+50, SCR_Y+SCR_H-50), random.choice([LIME, GOLD, CYAN]), 20)

    draw_arcade_cabinet("NEON CHOMPER", GOLD, "arcade")

# --- GAME 4: ENHANCED DANCE MACHINE ---
dance = {"arrows": [], "score": 0, "combo": 0, "timer": 0, "rating": "", "rtimer": 0, "speed": 6.0, "over": False, "frame": 0}
dance_lanes_x = [SCR_X + 110, SCR_X + 210, SCR_X + 340, SCR_X + 440]

def update_dance():
    global dance, screen_shake
    update_background_music(22)
    
    dance["frame"] += 1
    
    if dance["over"]:
        if rl.is_key_pressed(rl.KEY_R): dance = {"arrows": [], "score": 0, "combo": 0, "timer": 0, "rating": "", "rtimer": 0, "speed": 6.0, "over": False, "frame": 0}
        return STATE_DANCE

    dance["timer"] += 1
    if dance["timer"] >= 32:
        dance["arrows"].append({"lane": random.randint(0, 3), "y": float(SCR_Y + SCR_H), "hit": False})
        dance["timer"] = 0

    target_y = SCR_Y + 60
    keys = [rl.KEY_LEFT, rl.KEY_DOWN, rl.KEY_UP, rl.KEY_RIGHT]
    alt_keys = [rl.KEY_A, rl.KEY_S, rl.KEY_W, rl.KEY_D]

    for idx in range(4):
        if rl.is_key_pressed(keys[idx]) or rl.is_key_pressed(alt_keys[idx]):
            closest = None
            min_d = 999.0
            for a in dance["arrows"]:
                if a["lane"] == idx and not a["hit"]:
                    d = abs(a["y"] - target_y)
                    if d < min_d: min_d = d; closest = a
            
            if closest and min_d < 50:
                closest["hit"] = True
                dance["combo"] += 1
                if min_d < 18:
                    dance["rating"] = "PERFECT"
                    dance["score"] = dance["score"] + 200 * dance["combo"]
                    screen_shake = 10.0; play_sfx(snd_perfect)
                else:
                    dance["rating"] = "GREAT"
                    dance["score"] = dance["score"] + 100 * dance["combo"]
                    screen_shake = 4.0; play_sfx(snd_blip)
                dance["rtimer"] = 35
                spawn_particles(dance_lanes_x[idx] + 40, target_y + 15, MAGENTA, 20, 1.5)
            else:
                dance["combo"] = 0; dance["rating"] = "MISS"; dance["rtimer"] = 35; play_sfx(snd_explosion)

    for a in dance["arrows"][:]:
        a["y"] -= dance["speed"]
        if a["y"] < target_y - 30 and not a["hit"]:
            dance["arrows"].remove(a); dance["combo"] = 0; dance["rating"] = "MISS"; dance["rtimer"] = 35
        elif a["hit"]: dance["arrows"].remove(a)

    if dance["rtimer"] > 0: dance["rtimer"] -= 1
    return STATE_DANCE

def draw_dance():
    ox, oy = get_shake_offsets()
    rl.clear_background(rl.BLACK)
    rl.draw_rectangle(SCR_X + ox, SCR_Y + oy, SCR_W, SCR_H, rl.Color(16, 12, 26, 255))
    
    draw_ambient_particles(ox, oy)
    
    for i in range(0, SCR_W, 40):
        rl.draw_line(SCR_X + i + ox, SCR_Y + oy, SCR_X + i + ox, SCR_Y + SCR_H + oy, rl.fade(PURPLE, 0.1))
    
    target_y = SCR_Y + 60
    directions = ["<", "v", "^", ">"]
    dir_colors = [CYAN, GOLD, LIME, MAGENTA]
    
    for i, lx in enumerate(dance_lanes_x):
        rl.draw_rectangle_lines_ex(rl.Rectangle(lx + ox, target_y + oy - 20, 80, 40), 3, dir_colors[i])
        rl.draw_rectangle(lx + ox, target_y + oy, 80, 5, rl.fade(dir_colors[i], 0.5))
        draw_neon_glow(lx + 40 + ox, target_y - 10 + oy, 50, dir_colors[i], 0.2)
        rl.draw_text(directions[i], lx + 32 + ox, target_y - 45 + oy, 20, dir_colors[i])

    for a in dance["arrows"]:
        lx = dance_lanes_x[a["lane"]]
        arrow_height = 60
        
        rl.draw_rectangle(lx + ox, int(a["y"]) + oy, 80, arrow_height, rl.fade(dir_colors[a["lane"]], 0.7))
        rl.draw_rectangle_lines_ex(rl.Rectangle(lx + ox, int(a["y"]) + oy, 80, arrow_height), 2, rl.WHITE)
        draw_neon_glow(lx + 40 + ox, int(a["y"]) + arrow_height//2 + oy, 50, dir_colors[a["lane"]], 0.3)
        rl.draw_text(directions[a["lane"]], lx + 28 + ox, int(a["y"]) + 18 + oy, 28, rl.WHITE)

    draw_particles(ox, oy)
    
    # TRASH FIGURE DANCING
    dancer_x = SCR_X + SCR_W - 110
    dancer_y = SCR_Y + 220
    draw_trash_figure(dancer_x + ox, dancer_y + oy, MAGENTA, "dancing", dance["frame"])
    
    rl.draw_text(f"SCORE: {dance['score']}", SCR_X + 30, SCR_Y + SCR_H - 40, 22, GOLD)
    if dance["combo"] > 1: 
        combo_text = f"COMBO x{dance['combo']}"
        rl.draw_text(combo_text, SCR_X + SCR_W - 200, SCR_Y + SCR_H - 40, 22, LIME)
    
    if dance["rtimer"] > 0:
        c = SABER_RED if dance["rating"] == "MISS" else LIME if dance["rating"] == "PERFECT" else GOLD
        rating_text = dance["rating"]
        rl.draw_text(rating_text, SCR_X + SCR_W//2 - rl.measure_text(rating_text, 36)//2, SCR_Y + 200, 36, c)
    
    draw_arcade_cabinet("NEON BEAT", MAGENTA, "dance")

# --- HUB DRAWING ---
def draw_hub():
    rl.clear_background(rl.Color(8, 8, 14, 255))
    t = rl.get_time()
    
    # Atmospheric background
    for i in range(5):
        y = (rl.get_time() * 20 + i * 50) % H
        rl.draw_line_ex(rl.Vector2(0, y), rl.Vector2(W, y), 1, rl.fade(PURPLE, 0.05))
    
    if audio_enabled:
        rl.draw_rectangle(20, 20, 190, 30, rl.Color(20, 50, 30, 255))
        rl.draw_text("AUDIO OK", 30, 28, 14, LIME)
    else:
        rl.draw_rectangle(20, 20, 190, 30, rl.Color(50, 20, 20, 255))
        rl.draw_text("AUDIO MUTED", 30, 28, 14, SABER_RED)

    for y in range(400, H, 16):
        alpha = int(((y - 400) / (H - 400)) * 255)
        rl.draw_line_ex(rl.Vector2(0, y), rl.Vector2(W, y), 2, rl.fade(PURPLE, alpha / 255.0 * 0.25))
    
    rl.draw_text("NEON ARCADE", 320, 35, 40, NEON_PINK)
    rl.draw_text("WASD/ARROWS - MOVE   E - PLAY   ESC - EXIT", 250, 100, 12, rl.LIGHTGRAY)
    
    for i, cab in enumerate(cabinets):
        x, y, w, h = cab["x"], cab["y"], cab["w"], cab["h"]
        nearby = abs(player["x"] - (x + w / 2)) < w and abs(player["y"] - (y + h)) < 110
        
        rl.draw_rectangle(x - 4, y - 4, w + 8, h + 8, rl.BLACK)
        rl.draw_rectangle(x, y, w, h, CABINET_METAL)
        
        rl.draw_rectangle(x + 10, y + 20, w - 20, 80, rl.BLACK)
        glow = 0.2 + 0.2 * math.sin(t * 8 + i)
        rl.draw_rectangle(x + 12, y + 22, w - 24, 76, rl.fade(cab["color"], glow))
        draw_neon_glow(x + w//2, y + 60, 50, cab["color"], glow * 0.3)
        
        rl.draw_rectangle(x - 6, y + 140, w + 12, 20, PANEL_DARK)
        rl.draw_circle(x + 30, y + 150, 4, SABER_RED)
        rl.draw_circle(x + w - 30, y + 150, 2, CYAN)
        rl.draw_circle(x + w - 40, y + 150, 2, GOLD)
        
        rl.draw_text(cab["name"], x + (w - rl.measure_text(cab['name'], 14))//2, y + 185, 14, rl.WHITE)

        if nearby:
            rl.draw_rectangle_lines_ex(rl.Rectangle(x - 4, y - 4, w + 8, h + 8), 3, GOLD)
            rl.draw_text("PRESS E TO PLAY", W // 2 - 100, H - 45, 20, GOLD)

    draw_trash_figure(player["x"], player["y"], rl.WHITE, "idle", player["frame"])
    rl.draw_circle_lines(int(player["x"]), int(player["y"]), player["r"] + 2, rl.fade(CYAN, 0.5))

# --- MAIN LOOP ---
state = STATE_HUB

while not rl.window_should_close():
    update_particles()
    update_ambient_particles()
    
    if random.random() < 0.05:
        spawn_ambient_particles(2)
    
    if rl.is_key_pressed(rl.KEY_ESCAPE) and state != STATE_HUB:
        state = STATE_HUB

    if state == STATE_HUB:
        player["frame"] += 1
        update_background_music(1)
        if rl.is_key_down(rl.KEY_A) or rl.is_key_down(rl.KEY_LEFT): player["x"] -= player["speed"]
        if rl.is_key_down(rl.KEY_D) or rl.is_key_down(rl.KEY_RIGHT): player["x"] += player["speed"]
        if rl.is_key_down(rl.KEY_W) or rl.is_key_down(rl.KEY_UP): player["y"] -= player["speed"]
        if rl.is_key_down(rl.KEY_S) or rl.is_key_down(rl.KEY_DOWN): player["y"] += player["speed"]
        
        player["x"] = clamp(player["x"], 40, W - 40)
        player["y"] = clamp(player["y"], 440, H - 50)

        for i, cab in enumerate(cabinets):
            if abs(player["x"] - (cab["x"] + cab["w"] / 2)) < cab["w"] and abs(player["y"] - (cab["y"] + cab["h"])) < 110:
                if rl.is_key_pressed(rl.KEY_E):
                    state = cab["state"]
                    play_sfx(snd_coin)
                    if state == STATE_BREAKOUT: breakout = reset_breakout()
                    elif state == STATE_PACMAN: pac = reset_pacman()
                    elif state == STATE_DANCE: dance = {"arrows": [], "score": 0, "combo": 0, "timer": 0, "rating": "", "rtimer": 0, "speed": 6.0, "over": False, "frame": 0}
                    particles.clear()
                    break
    else:
        if state == STATE_RACE: state = update_race()
        elif state == STATE_BREAKOUT: state = update_breakout()
        elif state == STATE_PACMAN: state = update_pacman()
        elif state == STATE_DANCE: state = update_dance()

    rl.begin_drawing()
    if state == STATE_HUB: draw_hub()
    elif state == STATE_RACE: draw_race()
    elif state == STATE_BREAKOUT: draw_breakout()
    elif state == STATE_PACMAN: draw_pacman()
    elif state == STATE_DANCE: draw_dance()
    rl.end_drawing()

rl.close_window()
