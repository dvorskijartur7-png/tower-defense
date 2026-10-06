import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense")

# Шрифти
font = pygame.font.SysFont('Arial', 14, bold=True)
title_font = pygame.font.SysFont('Arial', 30, bold=True)
btn_font = pygame.font.SysFont('Arial', 16, bold=True)

# Кольори
GREEN = (34, 139, 34)
GRAY = (128, 128, 128)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
BROWN = (139, 69, 19)
DARK_GRAY = (50, 50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
CAGE_COLOR = (200, 200, 200)

clock = pygame.time.Clock()

game_state = 'MENU'
is_paused = False
show_tutorial = False
current_level = 1

level_stars = {1: 0, 2: 0, 3: 0, 4: 0}
level_unlocked = {1: True, 2: False, 3: False, 4: False}

# Траси для 4 рівнів
LEVEL_WAYPOINTS = {
    1: [(0, 80), (220, 80), (220, 340), (520, 340), (520, 200), (720, 200)],
    2: [(0, 60), (700, 60), (700, 180), (100, 180), (100, 300), (700, 300), (700, 410), (720, 410)],
    3: [(0, 50), (380, 50), (380, 220), (120, 220), (120, 390), (620, 390), (620, 150), (500, 150), (500, 280), (720, 280)],
    4: [(0, 40), (740, 40), (740, 140), (60, 140), (60, 240), (740, 240), (740, 340), (60, 340), (60, 410), (720, 410)]
}

def point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

class Coin:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.radius = 8
        self.timer = 420  # Зникає через 7 секунд
        self.offset_y = random.randint(-12, -4)
        self.vy = -3

    def update(self):
        self.timer -= 1
        if self.vy < 0:
            self.offset_y += self.vy
            self.vy += 0.5

    def is_clicked(self, mx, my):
        return math.hypot(mx - self.x, my - (self.y + self.offset_y)) <= self.radius + 6

    def draw(self, surface):
        if self.timer < 60 and (self.timer // 6) % 2 == 0:
            return

        draw_y = int(self.y + self.offset_y)
        pygame.draw.circle(surface, YELLOW, (int(self.x), draw_y), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), draw_y), self.radius, 1)
        c_txt = font.render("$", True, BLACK)
        surface.blit(c_txt, (self.x - c_txt.get_width() // 2, draw_y - c_txt.get_height() // 2))

class Enemy:
    def __init__(self, waypoints, enemy_type='normal', level=1):
        self.waypoints = waypoints
        self.target_wp = 1
        self.x, self.y = waypoints[0]
        self.type = enemy_type
        self.is_caught = False
        self.cage_timer = 120  # 2 секунди при 60 FPS

        if level == 4:
            if enemy_type == 'fast':
                self.speed = 4.5
                self.hp = 600
                self.max_hp = self.hp
                self.color = YELLOW
                self.radius = 11
                self.reward = 15
                self.drop_chance = 0.65
            elif enemy_type == 'tank':
                self.speed = 1.8
                self.hp = 3500
                self.max_hp = self.hp
                self.color = DARK_GRAY
                self.radius = 20
                self.reward = 35
                self.drop_chance = 1.0
            else:
                self.speed = 2.8
                self.hp = 1200
                self.max_hp = self.hp
                self.color = RED
                self.radius = 14
                self.reward = 20
                self.drop_chance = 0.80
        else:
            if enemy_type == 'fast':
                self.speed = 2.2 + (0.3 * level)
                self.hp = 80 + (30 * level)
                self.max_hp = self.hp
                self.color = YELLOW
                self.radius = 11
                self.reward = 15
                self.drop_chance = 0.65
            elif enemy_type == 'tank':
                self.speed = 0.8 + (0.1 * level)
                self.hp = 350 * level
                self.max_hp = self.hp
                self.color = DARK_GRAY
                self.radius = 18
                self.reward = 40
                self.drop_chance = 1.0
            else:
                self.speed = 1.4 + (0.2 * level)
                self.hp = 110 + (40 * level)
                self.max_hp = self.hp
                self.color = RED
                self.radius = 14
                self.reward = 20
                self.drop_chance = 0.80

    def move(self):
        if self.is_caught:
            self.cage_timer -= 1
            return

        if self.target_wp < len(self.waypoints):
            tx, ty = self.waypoints[self.target_wp]
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed:
                self.x, self.y = tx, ty
                self.target_wp += 1
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
        if not self.is_caught:
            pygame.draw.rect(surface, RED, (self.x - 12, self.y - self.radius - 6, 24, 4))
            pygame.draw.rect(surface, (0, 255, 0), (self.x - 12, self.y - self.radius - 6, max(0, int(24 * (self.hp / self.max_hp))), 4))
        else:
            box_size = self.radius * 2 + 6
            rx = int(self.x - box_size // 2)
            ry = int(self.y - box_size // 2)
            pygame.draw.rect(surface, BLACK, (rx, ry, box_size, box_size), 2)
            for i in range(1, 4):
                line_x = rx + (box_size // 4) * i
                pygame.draw.line(surface, CAGE_COLOR, (line_x, ry), (line_x, ry + box_size), 2)
            for i in range(1, 4):
                line_y = ry + (box_size // 4) * i
                pygame.draw.line(surface, CAGE_COLOR, (rx, line_y), (rx + box_size, line_y), 2)

class Tower:
    def __init__(self, x, y, tower_type):
        self.x = x
        self.y = y
        self.type = tower_type
        self.cooldown = 0
        self.size = 28
        if tower_type == 'basic':
            self.color = BLUE
            self.range = 130
            self.damage = 35
            self.max_cooldown = 25
        else:
            self.color = RED
            self.range = 210
            self.damage = 100
            self.max_cooldown = 50

    def draw(self, surface):
        rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        pygame.draw.rect(surface, self.color, rect, border_radius=4)
        pygame.draw.rect(surface, BLACK, rect, 2, border_radius=4)
        
        inner_rect = pygame.Rect(self.x - 5, self.y - 5, 10, 10)
        pygame.draw.rect(surface, WHITE, inner_rect, border_radius=2)

class Game:
    def __init__(self):
        self.reset(1)

    def reset(self, level):
        global current_level, show_tutorial, is_paused
        current_level = level
        self.level = level
        self.waypoints = LEVEL_WAYPOINTS[level]
        
        show_tutorial = (level == 1)
        is_paused = False

        if level == 1:
            self.money = 180
            self.max_waves = 3
        elif level == 2:
            self.money = 150
            self.max_waves = 3
        elif level == 3:
            self.money = 140
            self.max_waves = 5
        elif level == 4:
            self.money = 600
            self.max_waves = 10

        self.health = 10
        self.max_health = 10
        self.wave = 1
        self.enemies_to_spawn = 6 if level < 4 else 15
        self.spawn_timer = 0
        self.selected_type = 'basic'
        
        self.tower_limits = {1: 4, 2: 2, 3: 3, 4: 3}
        self.max_limit = self.tower_limits[level]

        self.towers = []
        self.bullets = []
        self.enemies = []
        self.dropped_coins = []
        self.caught_count = 0
        self.game_over = False
        self.game_win = False

    def count_towers(self, t_type):
        return sum(1 for t in self.towers if t.type == t_type)

    def get_cost(self, t_type):
        base = 50 if t_type == 'basic' else 100
        return base + self.count_towers(t_type) * 20

    def can_build(self, x, y):
        if self.count_towers(self.selected_type) >= self.max_limit:
            return False
        if y > 420 or y < 20 or x < 20 or x > WIDTH - 20:
            return False
        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]
            if point_to_segment_dist(x, y, x1, y1, x2, y2) < 28:
                return False
        for t in self.towers:
            if math.hypot(t.x - x, t.y - y) < 35:
                return False
        return True

    def update(self):
        if self.game_over or self.game_win or is_paused or show_tutorial:
            return

        # Поява ворогів
        if self.enemies_to_spawn > 0:
            self.spawn_timer += 1
            delay = 20 if self.level == 4 else 55
            if self.spawn_timer >= delay:
                if self.level == 1:
                    types = ['normal', 'fast']
                elif self.level == 4:
                    types = ['fast', 'tank', 'tank']
                else:
                    types = ['normal', 'fast', 'tank']

                e_type = random.choice(types)
                self.enemies.append(Enemy(self.waypoints, e_type, self.level))
                self.enemies_to_spawn -= 1
                self.spawn_timer = 0

        # Оновлення ворогів
        for e in self.enemies[:]:
            e.move()
            if not e.is_caught and e.target_wp >= len(self.waypoints):
                self.health -= 1
                self.enemies.remove(e)
                if self.health <= 0:
                    self.game_over = True
            elif e.is_caught and e.cage_timer <= 0:
                self.enemies.remove(e)

        # Оновлення монет
        for c in self.dropped_coins[:]:
            c.update()
            if c.timer <= 0:
                self.dropped_coins.remove(c)

        # Зміна хвиль та перемога
        if self.enemies_to_spawn == 0 and len(self.enemies) == 0 and len(self.dropped_coins) == 0:
            if self.wave < self.max_waves:
                self.wave += 1
                self.enemies_to_spawn = (5 + self.wave * 3) if self.level < 4 else (15 + self.wave * 5)
            else:
                self.game_win = True
                level_stars[self.level] = max(level_stars[self.level], 3 if self.health > 7 else 2)
                if self.level + 1 in level_unlocked:
                    level_unlocked[self.level + 1] = True

        # Стрільба веж
        for t in self.towers:
            if t.cooldown > 0:
                t.cooldown -= 1
            else:
                for e in self.enemies:
                    if not e.is_caught and math.hypot(e.x - t.x, e.y - t.y) <= t.range:
                        self.bullets.append({'x': t.x, 'y': t.y, 'target': e, 'damage': t.damage})
                        t.cooldown = t.max_cooldown
                        break

        # Рух снарядів
        for b in self.bullets[:]:
            e = b['target']
            if e in self.enemies and not e.is_caught:
                dx, dy = e.x - b['x'], e.y - b['y']
                dist = math.hypot(dx, dy)
                if dist < 12:
                    e.hp -= b['damage']
                    if e.hp <= 0:
                        e.is_caught = True
                        self.caught_count += 1
                        if random.random() <= e.drop_chance:
                            self.dropped_coins.append(Coin(e.x, e.y, e.reward))
                    self.bullets.remove(b)
                else:
                    b['x'] += (dx / dist) * 12
                    b['y'] += (dy / dist) * 12
            else:
                self.bullets.remove(b)

game = Game()

# Головний цикл гри для ПК
running = True
while running:
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == 'MENU':
                if 300 <= mx <= 500 and 220 <= my <= 270:
                    game.reset(1)
                    game_state = 'GAME'
                elif 300 <= mx <= 500 and 290 <= my <= 340:
                    game_state = 'LEVEL_SELECT'

            elif game_state == 'LEVEL_SELECT':
                btns = [(60, 220), (230, 220), (400, 220), (570, 220)]
                for i, (bx, by) in enumerate(btns, 1):
                    if bx <= mx <= bx + 130 and by <= my <= by + 70 and level_unlocked[i]:
                        game.reset(i)
                        game_state = 'GAME'
                if 300 <= mx <= 500 and 340 <= my <= 390:
                    game_state = 'MENU'

            elif game_state == 'GAME':
                if show_tutorial:
                    if 330 <= mx <= 470 and 300 <= my <= 345:
                        show_tutorial = False

                elif is_paused:
                    if 180 <= mx <= 280 and 270 <= my <= 320:
                        is_paused = False  # Продовжити гру
                    elif 300 <= mx <= 400 and 270 <= my <= 320:
                        game.reset(current_level)  # Перезапуск
                    elif 420 <= mx <= 520 and 270 <= my <= 320:
                        game_state = 'MENU'  # Вихід у меню
                        is_paused = False

                elif game.game_win or game.game_over:
                    if game.game_win and current_level < 4:
                        if 180 <= mx <= 280 and 270 <= my <= 320:
                            game.reset(current_level)
                        elif 300 <= mx <= 400 and 270 <= my <= 320:
                            game.reset(current_level + 1)
                        elif 420 <= mx <= 520 and 270 <= my <= 320:
                            game_state = 'MENU'
                    else:
                        if 260 <= mx <= 380 and 270 <= my <= 320:
                            game.reset(current_level)
                        elif 400 <= mx <= 520 and 270 <= my <= 320:
                            game_state = 'MENU'

                else:
                    coin_collected = False
                    for c in game.dropped_coins[:]:
                        if c.is_clicked(mx, my):
                            game.money += c.value
                            game.dropped_coins.remove(c)
                            coin_collected = True
                            break

                    if not coin_collected:
                        if 740 <= mx <= 780 and 15 <= my <= 55:
                            is_paused = True
                        elif my > 430:
                            if 20 <= mx <= 160:
                                game.selected_type = 'basic'
                            elif 180 <= mx <= 320:
                                game.selected_type = 'sniper'
                        elif game.can_build(mx, my):
                            cost = game.get_cost(game.selected_type)
                            if game.money >= cost:
                                game.towers.append(Tower(mx, my, game.selected_type))
                                game.money -= cost

    if game_state == 'GAME':
        game.update()

    screen.fill(DARK_GRAY)

    if game_state == 'MENU':
        txt = title_font.render("ЗАХИСТ ВЕЖІ", True, YELLOW)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 120))

        pygame.draw.rect(screen, GREEN, (300, 220, 200, 50), border_radius=8)
        t1 = btn_font.render("Грати", True, WHITE)
        screen.blit(t1, (400 - t1.get_width() // 2, 245 - t1.get_height() // 2))

        pygame.draw.rect(screen, BLUE, (300, 290, 200, 50), border_radius=8)
        t2 = btn_font.render("Вибір рівня", True, WHITE)
        screen.blit(t2, (400 - t2.get_width() // 2, 315 - t2.get_height() // 2))

    elif game_state == 'LEVEL_SELECT':
        txt = title_font.render("ВИБІР РІВНЯ", True, WHITE)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 80))

        btns = [(60, 220), (230, 220), (400, 220), (570, 220)]
        for idx, (lx, ly) in enumerate(btns, 1):
            unlocked = level_unlocked[idx]
            color = PURPLE if idx == 4 and unlocked else (BLUE if unlocked else GRAY)
            pygame.draw.rect(screen, color, (lx, ly, 130, 70), border_radius=8)

            l_name = f"Рівень {idx}" if idx < 4 else "Рівень 4 💀"
            t_lbl = font.render(l_name, True, WHITE if unlocked else BLACK)
            screen.blit(t_lbl, (lx + 65 - t_lbl.get_width() // 2, ly + 20))

            st_txt = ("★" * level_stars[idx]) if unlocked else "🔒"
            t_st = font.render(st_txt, True, YELLOW if unlocked else BLACK)
            screen.blit(t_st, (lx + 65 - t_st.get_width() // 2, ly + 42))

        pygame.draw.rect(screen, RED, (300, 340, 200, 50), border_radius=8)
        tb = btn_font.render("Назад", True, WHITE)
        screen.blit(tb, (400 - tb.get_width() // 2, 365 - tb.get_height() // 2))

    elif game_state == 'GAME':
        screen.fill(GREEN)
        pygame.draw.lines(screen, GRAY, False, game.waypoints, 36)

        # Кінець доріжки (Скарб)
        ex, ey = game.waypoints[-1]
        pygame.draw.rect(screen, BROWN, (ex - 15, ey - 15, 30, 30))
        pygame.draw.rect(screen, YELLOW, (ex - 15, ey - 15, 30, 30), 2)

        tr_label = font.render(f"Скарб: {game.health}/10", True, WHITE)
        screen.blit(tr_label, (ex - tr_label.get_width() // 2, ey - 32))

        # Індикатор спійманих ворогів
        pygame.draw.rect(screen, DARK_GRAY, (10, 10, 150, 30), border_radius=6)
        pygame.draw.rect(screen, WHITE, (10, 10, 150, 30), 2, border_radius=6)
        cnt_txt = font.render(f"Спіймано: {game.caught_count}", True, YELLOW)
        screen.blit(cnt_txt, (20, 17))

        # Приціл / макет вежі
        if not game.game_over and not game.game_win and not is_paused and not show_tutorial and my < 420:
            r = 130 if game.selected_type == 'basic' else 210
            can = game.can_build(mx, my)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 0, 40) if can else (255, 0, 0, 40), (r, r), r)
            screen.blit(s, (mx - r, my - r))

        for t in game.towers:
            t.draw(screen)

        for e in game.enemies:
            e.draw(screen)

        for c in game.dropped_coins:
            c.draw(screen)

        for b in game.bullets:
            pygame.draw.circle(screen, YELLOW, (int(b['x']), int(b['y'])), 4)

        # Нижнє меню
        pygame.draw.rect(screen, DARK_GRAY, (0, 430, WIDTH, 70))

        # Базова вежа
        b_cost = game.get_cost('basic')
        b_cnt = game.count_towers('basic')
        b_border = WHITE if game.selected_type == 'basic' else DARK_GRAY
        pygame.draw.rect(screen, b_border, (20, 440, 140, 50), 2, border_radius=5)
        pygame.draw.rect(screen, BLUE, (28, 454, 22, 22), border_radius=3)
        pygame.draw.rect(screen, BLACK, (28, 454, 22, 22), 1, border_radius=3)
        screen.blit(font.render(f"Базова {b_cost}$", True, WHITE), (56, 448))
        screen.blit(font.render(f"({b_cnt}/{game.max_limit})", True, YELLOW if b_cnt < game.max_limit else RED), (56, 466))

        # Снайперська вежа
        s_cost = game.get_cost('sniper')
        s_cnt = game.count_towers('sniper')
        s_border = WHITE if game.selected_type == 'sniper' else DARK_GRAY
        pygame.draw.rect(screen, s_border, (180, 440, 140, 50), 2, border_radius=5)
        pygame.draw.rect(screen, RED, (188, 454, 22, 22), border_radius=3)
        pygame.draw.rect(screen, BLACK, (188, 454, 22, 22), 1, border_radius=3)
        screen.blit(font.render(f"Снайпер {s_cost}$", True, WHITE), (216, 448))
        screen.blit(font.render(f"({s_cnt}/{game.max_limit})", True, YELLOW if s_cnt < game.max_limit else RED), (216, 466))

        # Кнопка паузи
        pygame.draw.rect(screen, WHITE, (740, 15, 40, 40), 2, border_radius=5)
        screen.blit(btn_font.render("||", True, WHITE), (753, 23))

        # Вступне віконце 1-го рівня
        if show_tutorial:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            panel = pygame.Rect(180, 110, 440, 250)
            pygame.draw.rect(screen, DARK_GRAY, panel, border_radius=12)
            pygame.draw.rect(screen, YELLOW, panel, 2, border_radius=12)

            t_head = title_font.render("ГОЛОВНА МЕТА", True, YELLOW)
            screen.blit(t_head, (WIDTH // 2 - t_head.get_width() // 2, 125))

            t_desc1 = font.render("Пройдіть усі 4 рівні та захистіть Скарб!", True, WHITE)
            t_desc2 = font.render("• Ловіть ворогів у решітки за допомогою веж.", True, WHITE)
            t_desc3 = font.render("• Клікайте на монети, що випадають з ворогів.", True, WHITE)
            
            screen.blit(t_desc1, (WIDTH // 2 - t_desc1.get_width() // 2, 175))
            screen.blit(t_desc2, (WIDTH // 2 - t_desc2.get_width() // 2, 210))
            screen.blit(t_desc3, (WIDTH // 2 - t_desc3.get_width() // 2, 235))

            pygame.draw.rect(screen, GREEN, (330, 295, 140, 45), border_radius=8)
            t_btn = btn_font.render("Розпочати", True, WHITE)
            screen.blit(t_btn, (400 - t_btn.get_width() // 2, 317 - t_btn.get_height() // 2))

        # Вікна (Пауза, Перемога, Поразка)
        elif game.game_win or game.game_over or is_paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            is_three_btn = (game.game_win and current_level < 4) or is_paused
            panel = pygame.Rect(160, 120, 480, 230) if is_three_btn else pygame.Rect(220, 120, 360, 230)
            pygame.draw.rect(screen, DARK_GRAY, panel, border_radius=12)
            pygame.draw.rect(screen, WHITE, panel, 2, border_radius=12)

            title_str = "ПЕРЕМОГА!" if game.game_win else ("ПАУЗА" if is_paused else "ГРУ ЗАКІНЧЕНО")
            title_col = YELLOW if game.game_win else (WHITE if is_paused else RED)
            t_win = title_font.render(title_str, True, title_col)
            screen.blit(t_win, (WIDTH // 2 - t_win.get_width() // 2, 150))

            # 3 кнопки для ПАУЗИ
            if is_paused:
                pygame.draw.rect(screen, GREEN, (180, 270, 100, 50), border_radius=8)
                tc = btn_font.render("Назад", True, WHITE)
                screen.blit(tc, (230 - tc.get_width() // 2, 295 - tc.get_height() // 2))

                pygame.draw.rect(screen, BLUE, (300, 270, 100, 50), border_radius=8)
                tr = btn_font.render("Заново", True, WHITE)
                screen.blit(tr, (350 - tr.get_width() // 2, 295 - tr.get_height() // 2))

                pygame.draw.rect(screen, RED, (420, 270, 100, 50), border_radius=8)
                tm = btn_font.render("Меню", True, WHITE)
                screen.blit(tm, (470 - tm.get_width() // 2, 295 - tm.get_height() // 2))

            # 3 кнопки при ПЕРЕМОЗІ
            elif game.game_win and current_level < 4:
                pygame.draw.rect(screen, BLUE, (180, 270, 100, 50), border_radius=8)
                tr = btn_font.render("Заново", True, WHITE)
                screen.blit(tr, (230 - tr.get_width() // 2, 295 - tr.get_height() // 2))

                pygame.draw.rect(screen, GREEN, (300, 270, 100, 50), border_radius=8)
                tn = btn_font.render("Далі ➔", True, WHITE)
                screen.blit(tn, (350 - tn.get_width() // 2, 295 - tn.get_height() // 2))

                pygame.draw.rect(screen, RED, (420, 270, 100, 50), border_radius=8)
                tm = btn_font.render("Меню", True, WHITE)
                screen.blit(tm, (470 - tm.get_width() // 2, 295 - tm.get_height() // 2))

            # 2 кнопки при ПОРАЗЦІ або після 4-го рівня
            else:
                pygame.draw.rect(screen, GREEN, (260, 270, 120, 50), border_radius=8)
                tr = btn_font.render("Заново", True, WHITE)
                screen.blit(tr, (320 - tr.get_width() // 2, 295 - tr.get_height() // 2))

                pygame.draw.rect(screen, BLUE, (400, 270, 120, 50), border_radius=8)
                tm = btn_font.render("Меню", True, WHITE)
                screen.blit(tm, (460 - tm.get_width() // 2, 295 - tm.get_height() // 2))

    pygame.display.set_caption(f"TD | Рівень: {game.level} | Монети: {game.money}$ | Скарб: {game.health}/10 | Хвиля: {game.wave}/{game.max_waves}")
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()