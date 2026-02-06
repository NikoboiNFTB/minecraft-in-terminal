import subprocess
import time
from PIL import Image
from Xlib import display, X
import shutil  # for terminal size

# --- Configuration ---
ascii_chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
char_ratio = 0.5  # Terminal character height/width ratio
max_fps = 30
frame_duration = 1 / max_fps
brightness_boost = 1  # 1.0 = normal, >1 = brighter, for highlight effect

# --- Find Minecraft window ID automatically ---
wmctrl_output = subprocess.check_output(["wmctrl", "-l"]).decode()
window_id = None
for line in wmctrl_output.splitlines():
    if "Minecraft" in line:
        window_id = int(line.split()[0], 16)
        break

if window_id is None:
    raise RuntimeError("Minecraft window not found via wmctrl.")

# --- Get window geometry via xwininfo ---
geom_output = subprocess.check_output(["xwininfo", "-id", hex(window_id)]).decode()

def parse_xwininfo_value(output, key):
    for line in output.splitlines():
        if key in line:
            return int(line.split()[-1])  # Take the last element
    raise RuntimeError(f"{key} not found in xwininfo output")

x = parse_xwininfo_value(geom_output, "Absolute upper-left X:")
y = parse_xwininfo_value(geom_output, "Absolute upper-left Y:")
width = parse_xwininfo_value(geom_output, "Width:")
height = parse_xwininfo_value(geom_output, "Height:")

print(f"Capturing Minecraft window {width}x{height} at ({x},{y})")

# --- Connect to X11 ---
d = display.Display()
win = d.create_resource_object('window', window_id)

# --- Clear terminal once ---
print("\033[2J", end="")

while True:
    start_time = time.time()

    # Grab window contents
    raw = win.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)
    img = Image.frombytes("RGB", (width, height), raw.data, "raw", "BGRX")  # X11 stores BGRX

    # --- Dynamic scaling to terminal size ---
    term_cols, term_rows = shutil.get_terminal_size((80, 24))
    target_height = term_rows
    target_width = int(target_height / (height / width * char_ratio))
    if target_width > term_cols:
        target_width = term_cols
        target_height = int(target_width * (height / width * char_ratio))

    img_resized = img.resize((target_width, target_height))

    # Build colored ASCII frame
    lines = []
    for y_px in range(target_height):
        line = ""
        for x_px in range(target_width):
            r, g, b = img_resized.getpixel((x_px, y_px))
            # Apply brightness boost
            r = min(int(r * brightness_boost), 255)
            g = min(int(g * brightness_boost), 255)
            b = min(int(b * brightness_boost), 255)
            # Determine ASCII character
            brightness = int((r + g + b) / 3)
            char = ascii_chars[brightness // 25]
            # Set both foreground and background color
            line += f"\033[38;2;{r};{g};{b}m\033[48;2;{r};{g};{b}m{char}"
        line += "\033[0m"  # Reset at end of line
        lines.append(line)

    # Move cursor to top and print frame
    print("\033[H", end="")
    print("\n".join(lines))

    # Cap FPS
    elapsed = time.time() - start_time
    time.sleep(max(0, frame_duration - elapsed))
