#!/usr/bin/env python3
"""
ULTRA PONG 0.1 — FAMICOM EDITION (Files=OFF)
----------------------------------------------
• 60 FPS (NES-accurate)
• Authentic Famicom Pong physics
• Mouse-controlled left paddle
• Classic AI right paddle
• First to 11 points wins
----------------------------------------------
"""

import sys, math, random, numpy as np, pygame
pygame.init(); pygame.mixer.init(frequency=44100, size=-16, channels=2)

# === Screen / Colors ===
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultra Pong 0.1 — Famicom Edition")
clock = pygame.time.Clock()

# === Constants ===
FPS = 60.0
PADDLE_W, PADDLE_H = 12, 60
BALL_SIZE = 8
PADDLE_SPEED = 4
INITIAL_BALL_SPEED = 3.0
MAX_BALL_SPEED = 7.0
WIN_SCORE = 11

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 36)

# === Famicom-style Procedural Beeps ===
def make_tone(freq=440, dur=0.08, vol=0.3, wave="square"):
    try:
        rate = 44100; n = int(rate * dur); t = np.arange(n)/rate
        if wave=="square": w = np.sign(np.sin(2*math.pi*freq*t))
        elif wave=="saw": w = 2*(t*freq - np.floor(0.5+t*freq))
        else: w = np.sin(2*math.pi*freq*t)
        env_len = int(0.01*rate); env = np.linspace(0,1,env_len)
        fade = np.ones_like(w); fade[:env_len]=env; fade[-env_len:]=env[::-1]
        w *= fade
        stereo = np.repeat((w*vol*32767).astype(np.int16)[:,None], 2, 1)
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None

# Initialize sounds
beep_paddle = make_tone(880, 0.06, 0.25)
beep_wall = make_tone(440, 0.06, 0.25)
beep_score = make_tone(220, 0.15, 0.3)
win_sound = make_tone(660, 0.3, 0.35, "saw")

def play_paddle(): 
    if beep_paddle: beep_paddle.play()
def play_wall(): 
    if beep_wall: beep_wall.play()
def play_score(): 
    if beep_score: beep_score.play()
def play_win(): 
    if win_sound: win_sound.play()

# === Classes ===
class Paddle:
    def __init__(self, x, y): 
        self.rect = pygame.Rect(x, y, PADDLE_W, PADDLE_H)
    
    def set_mouse(self, y):
        self.rect.centery = max(PADDLE_H//2, min(HEIGHT-PADDLE_H//2, y))
    
    def move_ai(self, target_y):
        # Classic AI - follows ball with slight delay
        center = self.rect.centery
        if center < target_y - 15: 
            self.rect.y = min(self.rect.y + PADDLE_SPEED, HEIGHT - PADDLE_H)
        elif center > target_y + 15: 
            self.rect.y = max(self.rect.y - PADDLE_SPEED, 0)
    
    def draw(self): 
        pygame.draw.rect(screen, WHITE, self.rect)

class Ball:
    def __init__(self): 
        self.reset()
    
    def reset(self, direction=None):
        self.rect = pygame.Rect(WIDTH//2-BALL_SIZE//2, HEIGHT//2-BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        # Classic Pong: ball serves toward player who was scored on
        if direction is None:
            direction = random.choice([-1, 1])
        self.vx = INITIAL_BALL_SPEED * direction
        self.vy = INITIAL_BALL_SPEED * random.choice([-1, 1]) * 0.7
    
    def move(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # Ball collision with top/bottom walls
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = abs(self.vy)
            play_wall()
        elif self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.vy = -abs(self.vy)
            play_wall()
    
    def speed_up(self):
        # Gradually increase speed like classic Pong
        if abs(self.vx) < MAX_BALL_SPEED:
            self.vx *= 1.05
            self.vy *= 1.05
    
    def draw(self): 
        pygame.draw.rect(screen, WHITE, self.rect)

# === Menu ===
def main_menu():
    blink = 0
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_z, pygame.K_SPACE):
                play_paddle(); return
            if e.type == pygame.MOUSEBUTTONDOWN: 
                play_paddle(); return
        
        screen.fill(BLACK)
        
        title = font.render("ULTRA PONG", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3 - 30))
        
        version = small_font.render("Famicom Edition v0.1", True, WHITE)
        screen.blit(version, (WIDTH//2 - version.get_width()//2, HEIGHT//3 + 40))
        
        blink += 1
        if (blink // 30) % 2 == 0:
            msg = small_font.render("CLICK OR PRESS Z/SPACE", True, WHITE)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 + 60))
        
        pygame.display.flip()

# === Game Over ===
def game_over(winner):
    if winner == "PLAYER": 
        play_win()
    else: 
        play_score()
    
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_y: 
                    play_paddle(); return True
                if e.key == pygame.K_n: 
                    pygame.quit(); sys.exit()
        
        screen.fill(BLACK)
        
        msg = font.render(f"{winner} WINS!", True, WHITE)
        prompt = small_font.render("Y=Restart  N=Quit", True, WHITE)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//3))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 60))
        
        pygame.display.flip()

# === Game Loop ===
def game():
    left = Paddle(30, HEIGHT//2 - PADDLE_H//2)
    right = Paddle(WIDTH - 40, HEIGHT//2 - PADDLE_H//2)
    ball = Ball()
    s1 = s2 = 0
    serve_direction = random.choice([-1, 1])
    
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
        
        # Mouse control
        _, my = pygame.mouse.get_pos()
        left.set_mouse(my)
        
        # AI control
        right.move_ai(ball.rect.centery)
        
        # Ball movement
        ball.move()

        # Paddle collision - classic Pong physics
        if ball.rect.colliderect(left.rect) and ball.vx < 0:
            ball.rect.left = left.rect.right
            ball.vx = abs(ball.vx)
            # Bounce angle based on where ball hits paddle
            hit_pos = (ball.rect.centery - left.rect.centery) / (PADDLE_H / 2)
            ball.vy = hit_pos * 4.5
            ball.speed_up()
            play_paddle()
            
        elif ball.rect.colliderect(right.rect) and ball.vx > 0:
            ball.rect.right = right.rect.left
            ball.vx = -abs(ball.vx)
            # Bounce angle based on where ball hits paddle
            hit_pos = (ball.rect.centery - right.rect.centery) / (PADDLE_H / 2)
            ball.vy = hit_pos * 4.5
            ball.speed_up()
            play_paddle()
        
        # Score handling - classic Pong style
        if ball.rect.right <= 0:
            s2 += 1
            play_score()
            serve_direction = -1  # Serve toward player who was scored on
            ball.reset(serve_direction)
            pygame.time.wait(500)
            
        elif ball.rect.left >= WIDTH:
            s1 += 1
            play_score()
            serve_direction = 1  # Serve toward player who was scored on
            ball.reset(serve_direction)
            pygame.time.wait(500)

        # Win condition
        if s1 >= WIN_SCORE:
            if game_over("PLAYER"): 
                return
            else: 
                break
        elif s2 >= WIN_SCORE:
            if game_over("AI"): 
                return
            else: 
                break

        # Drawing - classic black screen
        screen.fill(BLACK)
        
        # Draw center line (dashed)
        for i in range(0, HEIGHT, 20):
            pygame.draw.rect(screen, WHITE, (WIDTH//2 - 2, i, 4, 10))
        
        left.draw()
        right.draw()
        ball.draw()
        
        # Score display - classic placement
        score_left = font.render(str(s1), True, WHITE)
        score_right = font.render(str(s2), True, WHITE)
        screen.blit(score_left, (WIDTH//4 - score_left.get_width()//2, 30))
        screen.blit(score_right, (WIDTH*3//4 - score_right.get_width()//2, 30))
        
        pygame.display.flip()

# === Run ===
if __name__ == "__main__":
    while True:
        main_menu()
        game()
