import tkinter as tk
import math
import time

# --- Constants ---
WIDTH, HEIGHT = 600, 400
FPS = 60
TARGET_FRAME_TIME_MS = int(1000 / FPS)

# Colors (Converted to Tkinter hex strings)
SKY_BLUE = "#87CEEB"
GRASS_GREEN = "#228B22"
WHITE = "#FFFFFF"
BLACK = "#000000"
RED = "#C80000"
BROWN = "#8B4513"
DARK_BROWN = "#552D0D"
BIRD_BLUE = "#3C3CC8"
SCARF_BLUE = "#00008B"
BIRD_ORANGE = "#FFA500"
WHEEL_GRAY = "#323232"
UI_BAR_BG = "#646464"
UI_BAR_FILL = "#3296FF"

# --- Game State Variables ---
# We use a dictionary to hold state
game_state = {
    "cloud1_x": 100.0,
    "cloud2_x": 450.0,
    "wheel_angle": 0.0,
    "last_time": time.time(),
    "fps": 0
}

# --- Helper Function to draw pixel-style clouds ---
def draw_pixel_cloud(canvas, x, y):
    """Draws a simple, blocky cloud on the canvas."""
    canvas.create_rectangle(x, y, x + 25, y + 10, fill=WHITE, outline=WHITE)
    canvas.create_rectangle(x + 10, y - 10, x + 45, y, fill=WHITE, outline=WHITE)
    canvas.create_rectangle(x + 25, y, x + 55, y + 10, fill=WHITE, outline=WHITE)

# --- Main Animation Loop ---
def animation_loop(root, canvas):
    """The main loop to update and redraw the scene."""
    
    # --- Calculate FPS ---
    current_time = time.time()
    delta_time = current_time - game_state["last_time"]
    game_state["last_time"] = current_time
    if delta_time > 0:
        game_state["fps"] = 1.0 / delta_time

    # --- Game Logic / State Update ---
    
    # Animate clouds
    game_state["cloud1_x"] -= 0.8
    if game_state["cloud1_x"] < -100:
        game_state["cloud1_x"] = WIDTH + 20

    game_state["cloud2_x"] -= 0.5
    if game_state["cloud2_x"] < -100:
        game_state["cloud2_x"] = WIDTH + 20
    
    # Animate wheel spokes
    game_state["wheel_angle"] += 0.05
    if game_state["wheel_angle"] > 2 * math.pi:
        game_state["wheel_angle"] -= 2 * math.pi

    # --- Drawing ---
    
    # Clear the canvas for the new frame
    canvas.delete("all")
    
    # 1. Background
    canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=SKY_BLUE, outline=SKY_BLUE)
    canvas.create_rectangle(0, HEIGHT - 80, WIDTH, HEIGHT, fill=GRASS_GREEN, outline=GRASS_GREEN)

    # 2. Clouds (animated)
    draw_pixel_cloud(canvas, int(game_state["cloud1_x"]), 50)
    draw_pixel_cloud(canvas, int(game_state["cloud2_x"]), 100)

    # 3. Bicycle & Bird
    base_x = WIDTH // 2 - 50
    base_y = HEIGHT - 100
    wheel_radius = 30

    # Wheels
    wheel1_pos = (base_x, base_y)
    wheel2_pos = (base_x + 100, base_y)
    # create_oval takes (x1, y1, x2, y2) as a bounding box
    canvas.create_oval(wheel1_pos[0] - wheel_radius, wheel1_pos[1] - wheel_radius,
                       wheel1_pos[0] + wheel_radius, wheel1_pos[1] + wheel_radius,
                       outline=WHEEL_GRAY, width=4)
    canvas.create_oval(wheel2_pos[0] - wheel_radius, wheel2_pos[1] - wheel_radius,
                       wheel2_pos[0] + wheel_radius, wheel2_pos[1] + wheel_radius,
                       outline=WHEEL_GRAY, width=4)

    # Draw animated spokes
    wheel_angle = game_state["wheel_angle"]
    for i in range(4): # 4 spokes per wheel
        angle = wheel_angle + (i * math.pi / 2)
        # Spoke for wheel 1
        spoke1_end = (wheel1_pos[0] + (wheel_radius - 2) * math.cos(angle), 
                       wheel1_pos[1] + (wheel_radius - 2) * math.sin(angle))
        canvas.create_line(wheel1_pos[0], wheel1_pos[1], spoke1_end[0], spoke1_end[1],
                           fill=WHEEL_GRAY, width=2)
        # Spoke for wheel 2
        spoke2_end = (wheel2_pos[0] + (wheel_radius - 2) * math.cos(angle), 
                       wheel2_pos[1] + (wheel_radius - 2) * math.sin(angle))
        canvas.create_line(wheel2_pos[0], wheel2_pos[1], spoke2_end[0], spoke2_end[1],
                           fill=WHEEL_GRAY, width=2)

    # Bike Frame (Red)
    seat_post_top = (base_x + 35, base_y - 50)
    handle_post_top = (base_x + 85, base_y - 60)
    crank_center = (base_x + 35, base_y - 5)
    canvas.create_line(wheel1_pos[0], wheel1_pos[1], seat_post_top[0], seat_post_top[1], fill=RED, width=4)
    canvas.create_line(crank_center[0], crank_center[1], seat_post_top[0], seat_post_top[1], fill=RED, width=4)
    canvas.create_line(crank_center[0], crank_center[1], handle_post_top[0], handle_post_top[1], fill=RED, width=4)
    canvas.create_line(seat_post_top[0], seat_post_top[1], handle_post_top[0], handle_post_top[1], fill=RED, width=4)
    canvas.create_line(handle_post_top[0], handle_post_top[1], wheel2_pos[0], wheel2_pos[1], fill=RED, width=4)

    # Handlebars & Basket
    handlebar_pos = (base_x + 90, base_y - 70)
    canvas.create_line(handle_post_top[0], handle_post_top[1], handlebar_pos[0], handlebar_pos[1], fill=WHEEL_GRAY, width=4)
    canvas.create_line(handlebar_pos[0], handlebar_pos[1], handlebar_pos[0] + 10, handlebar_pos[1] - 5, fill=WHEEL_GRAY, width=6)
    canvas.create_rectangle(base_x + 95, base_y - 90, base_x + 125, base_y - 70, fill=BROWN, outline="")

    # Seat
    canvas.create_rectangle(base_x + 25, base_y - 60, base_x + 45, base_y - 50, fill=DARK_BROWN, outline="")

    # Bird
    bird_body_pos = (base_x + 45, base_y - 80)
    # Ellipse (x1, y1, x2, y2)
    canvas.create_oval(bird_body_pos[0] - 15, bird_body_pos[1] - 15, 
                       bird_body_pos[0] + 15, bird_body_pos[1] + 30, 
                       fill=BIRD_BLUE, outline="")
    bird_head_pos = (bird_body_pos[0] + 5, bird_body_pos[1] - 25)
    # Circle
    canvas.create_oval(bird_head_pos[0] - 18, bird_head_pos[1] - 18, 
                       bird_head_pos[0] + 18, bird_head_pos[1] + 18, 
                       fill=BIRD_BLUE, outline="")

    # Bird Face (Beak)
    beak_points = [
        bird_head_pos[0] + 15, bird_head_pos[1] - 5,
        bird_head_pos[0] + 35, bird_head_pos[1],
        bird_head_pos[0] + 15, bird_head_pos[1] + 5
    ]
    canvas.create_polygon(beak_points, fill=BIRD_ORANGE, outline="")
    
    # Eye
    canvas.create_oval(bird_head_pos[0] + 5, bird_head_pos[1] - 10, 
                       bird_head_pos[0] + 15, bird_head_pos[1], 
                       fill=WHITE, outline="")
    canvas.create_oval(bird_head_pos[0] + 8, bird_head_pos[1] - 8, 
                       bird_head_pos[0] + 14, bird_head_pos[1] - 2, 
                       fill=BLACK, outline="")

    # Goggles
    canvas.create_rectangle(bird_head_pos[0] - 10, bird_head_pos[1] - 15, 
                            bird_head_pos[0] + 15, bird_head_pos[1] - 5, 
                            outline=BROWN, width=2)
    
    # Scarf
    scarf_points = [
        bird_body_pos[0] - 5, bird_body_pos[1] - 10,
        bird_body_pos[0] - 20, bird_body_pos[1] - 5,
        bird_body_pos[0] - 15, bird_body_pos[1] + 10
    ]
    canvas.create_polygon(scarf_points, fill=SCARF_BLUE, outline="")

    # 4. UI Text ("Falco: 67%")
    falco_text_str = "Falco: 67%"
    # Simple white background rectangle
    canvas.create_rectangle(WIDTH // 2 - 60, 80 - 15, WIDTH // 2 + 60, 80 + 15, fill=WHITE, outline="")
    canvas.create_text(WIDTH // 2, 80, text=falco_text_str, fill=BLACK, font=("Arial", 16, "bold"))

    # 5. Bottom UI Bar
    bar_rect_bg = (10, HEIGHT - 45, WIDTH - 10, HEIGHT - 35)
    fill_width = (WIDTH - 20) * 0.8
    bar_rect_fg = (10, HEIGHT - 45, 10 + fill_width, HEIGHT - 35)
    
    canvas.create_rectangle(bar_rect_bg, fill=UI_BAR_BG, outline="")
    canvas.create_rectangle(bar_rect_fg, fill=UI_BAR_FILL, outline="")

    # 6. Bottom UI Text
    fps_str = f"FPS: {int(game_state['fps'])}"
    canvas.create_text(15, HEIGHT - 22, text=fps_str, fill=BLACK, font=("Arial", 10), anchor="w")
    
    score_str = "Score: 1250 points"
    canvas.create_text(WIDTH - 15, HEIGHT - 22, text=score_str, fill=BLACK, font=("Arial", 10), anchor="e")

    # --- Schedule next frame ---
    root.after(TARGET_FRAME_TIME_MS, lambda: animation_loop(root, canvas))

# --- Main Function ---
def main():
    root = tk.Tk()
    root.title("Tkinter: Melee Bicycle Mayhem")
    
    # Prevent window from being resizable
    root.resizable(False, False)

    # Create the canvas
    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=SKY_BLUE, highlightthickness=0)
    canvas.pack()

    # Start the animation loop
    animation_loop(root, canvas)

    # Start the Tkinter main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
