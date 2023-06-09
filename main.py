import pygame
import noise
import numpy as np
import time
import random
import math
from a_star_algorithm import find_path

WINDOW_SIZE = [800, 800]

BLUE = [0, 0, 255]
MEDIUM_BLUE = [0,0,200]
DARK_BLUE = [0,0,150]

SAND = [255, 255, 204]
PLANES_GREEN = [76, 153, 0]
FOREST_GREEN = [0, 102, 0]
DARK_GREEN = [0,51,0]
GREEN = [0, 255, 0]
WHITE = [255, 255, 255]
BROWN = [139, 69, 19]
BLACK = [0,0,0]
RED = [255, 0, 0]
DARKGREEN = [1, 55, 32]
PINK = [255,192,203]
PURPLE = [160, 32, 240]
ORANGE = [255, 165, 0]
LIGHTBLUE = [173, 216, 230]
ARMY_LEADER_RADIUS = 20
GREY = [128, 128, 128]
seed = random.randint(1, 250)

WIDTH = 10
HEIGHT = 10

MOVE_PROBABILITY_MOVING = 0.9
MOVE_PROBABILITY_STILL = 0.1
WATER_DEATH_TIME = 5  
SEX_THRESHOLD = 2
FACTION_COLORS = [RED, DARKGREEN, LIGHTBLUE, PINK, PURPLE, ORANGE]
FACTION_RADIUS = 10
FACTION_JOIN_TIME = 1 
FACTION_MIN_MEMBERS = 4


world_shape = [int(WINDOW_SIZE[0]/WIDTH), int(WINDOW_SIZE[1]/HEIGHT)]
scale = 0.05
octaves = 6
persistence = 0.5
lacunarity = 2.0
shake_duration = 0
shake_monster_duration = 0
shake_intensity = 30

class Monster():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.time_to_jump = 0
        self.elapsed_time = 0
        self.a, self.b, self.c = 0, 0, 0 
        self.direction = 0
        self.jumping = False

    def jump(self):
        self.time_to_jump = random.uniform(5, 10) 
        self.elapsed_time = 0
        self.a = random.uniform(-1.5, 1.5) 
        self.b = random.uniform(-1, 1)
        self.c = self.y 
        self.direction = random.choice([-1, 1])
        self.jumping = True

    def update(self, npcs):
        
        if self.jumping:
            self.elapsed_time += 0.1
            new_y = self.a * (self.elapsed_time ** 2) + self.b * self.elapsed_time + self.c
            new_x = self.x + self.direction * 0.1

            if self.elapsed_time >= self.time_to_jump:
                self.jumping = False
                if (self.time_to_jump > 7):
                    radius = 100  
                    npcs[:] = [npc for npc in npcs if ((npc.x - self.x)**2 + (npc.y - self.y)**2)**0.5 > radius]
                    return True
                else:
                    return False
            if 0 <= self.x < WINDOW_SIZE[0] and 0 <= self.y < WINDOW_SIZE[1]:
                self.x = new_x
                self.y = new_y
                return False
            else:
                self.jumping = False
                return True
        return False
    
    def draw(self, screen):
        pygame.draw.rect(screen, RED, pygame.Rect(int(self.x), int(self.y), 100, 100))

class Army:
    def __init__(self, faction, leader):
        self.faction = faction
        self.members = []
        self.leader = leader
        self.freeze = False
        self.move_toward_battle = False
        self.in_battle = False
        self.battling_army = None
        self.battle_count = 0

    def add_member(self, npc):
        self.members.append(npc)
        npc.join_army(self)

    def remove_member(self, npc):
        self.members.remove(npc)
        npc.in_army = False
    
    def battle(self, army1):
        self.in_battle = True
        army1.in_battle = True

        self.battling_army = army1
        army1.battling_army = self

class NPC:
    def __init__(self, x, y, faction=None):
        self.speed = 1
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 2 * math.pi)
        self.moving = False
        self.water_time = 0
        self.last_update = time.time()
        self.age = 0
        self.life_span = random.randrange(50,100)
        self.reproduction_counter = random.randint(150, 250)
        self.faction = faction  
        self.faction_time = 0
        self.hp = random.randrange(75, 100)
        self.damage = random.randrange(1, 10)
        self.in_army = False
        self.army = None
        self.clicked = False
        self.path = []

    def contains_point(self, x, y):
        return ((x - self.x) ** 2 + (y - self.y) ** 2) <= (WIDTH//2) ** 2
          
    def update(self):
        self.age += time.time()
        if (self.age < self.life_span):
            return False
        
        if world[int(self.y/HEIGHT)][int(self.x/WIDTH)] < 0:  
            self.water_time += time.time() - self.last_update  
            if self.water_time >= WATER_DEATH_TIME:  
                return False  
        else:  
            self.water_time = 0  

        self.reproduction_counter -= 1  

        if self.reproduction_counter <= 0:  
            mate = self.find_mate()  
            if mate:
                self.reproduce(mate)
                self.reproduction_counter = random.randint(50, 100)
        
        if (self.in_army == False or self.army.freeze == False or self.army.leader is not self):
            if self.in_army and len(self.path) == 0:
                if self.distance_to(self.army.leader) > ARMY_LEADER_RADIUS:
                    dx = self.army.leader.x - self.x
                    dy = self.army.leader.y - self.y
                    angle = math.atan2(dy, dx)
                    new_x = self.x + self.speed * math.cos(angle)
                    new_y = self.y + self.speed * math.sin(angle)

                    if 0 <= new_x < WINDOW_SIZE[0] and 0 <= new_y < WINDOW_SIZE[1]: 
                        if world[int(new_y/HEIGHT)][int(new_x/WIDTH)] >= 0:  
                            self.x = new_x
                            self.y = new_y
            
            elif len(self.path) > 0:
                print("moving")
                next_point = self.path[0]  
                dx = next_point[0]*10 - self.x  
                dy = next_point[1]*10 - self.y
                distance = math.hypot(dx, dy)

                if distance < self.speed:  
                    self.path.pop(0) 
                    if self.path: 
                        next_point = self.path[0]
                        dx = next_point[0]*WIDTH - self.x
                        dy = next_point[1]*HEIGHT - self.y
                        distance = math.hypot(dx, dy)

                angle = math.atan2(dy, dx) 
                new_x = self.x + self.speed * math.cos(angle)
                new_y = self.y + self.speed * math.sin(angle)

                if 0 <= new_x < WINDOW_SIZE[0] and 0 <= new_y < WINDOW_SIZE[1]: 
                    if world[int(new_y/HEIGHT)][int(new_x/WIDTH)] >= 0:  
                        self.x = new_x
                        self.y = new_y
            
                if (self.in_army and self.army.leader == self and self.army.move_toward_battle == True):
                    leader_pos = (self.x, self.y)
                    target_pos = (select_army_1.leader.x, select_army_1.leader.y)
                    
                    if (math.sqrt((leader_pos[0] - target_pos[0])**2 + (leader_pos[1] - target_pos[1])**2) < 10):
                        print("army leader frozen")
                        self.army.freeze = True
                    
            else:
                if self.moving:  
                    if random.random() < MOVE_PROBABILITY_MOVING:  
                        dx = self.speed * math.cos(self.angle)
                        dy = self.speed * math.sin(self.angle)
                        new_x = self.x + dx
                        new_y = self.y + dy

                        if 0 <= new_x < WINDOW_SIZE[0] and 0 <= new_y < WINDOW_SIZE[1]:  
                            if world[int(new_y/HEIGHT)][int(new_x/WIDTH)] >= 0:  
                                self.x = new_x
                                self.y = new_y
                        else:  
                            self.angle = random.uniform(0, 2 * math.pi)  
                    else:  
                        if random.random() < MOVE_PROBABILITY_STILL:  
                            self.moving = True
                            self.angle = random.uniform(0, 2 * math.pi)

    
            if self.moving:  
                if random.random() < MOVE_PROBABILITY_MOVING:  
                    dx = self.speed * math.cos(self.angle)
                    dy = self.speed * math.sin(self.angle)
                    new_x = self.x + dx
                    new_y = self.y + dy

                    if 0 <= new_x < WINDOW_SIZE[0] and 0 <= new_y < WINDOW_SIZE[1]:  
                        if world[int(new_y/HEIGHT)][int(new_x/WIDTH)] >= 0:  
                            self.x = new_x
                            self.y = new_y
                    else:  
                        self.angle = random.uniform(0, 2 * math.pi)  
                else:  
                    self.moving = False
            else:
                if random.random() < MOVE_PROBABILITY_STILL:  
                    self.moving = True
                    self.angle = random.uniform(0, 2 * math.pi)

        self.last_update = time.time()
        return True 
    
    def find_mate(self):
        for npc in npcs: 
            if npc != self and npc.reproduction_counter <= 0 and self.distance_to(npc) < SEX_THRESHOLD:
                return npc  
        return None
    
    def reproduce(self, mate):
        if not self.in_army and len(npcs) > 50: 
            child_x = (self.x + mate.x) / 2
            child_y = (self.y + mate.y) / 2
            npcs.append(NPC(child_x, child_y))

    def distance_to(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def update_faction(self):
        if self.faction is not None and len([npc for npc in npcs if npc.faction == self.faction]) < 2:
            self.faction = None 

        if self.faction is None:
            for npc in npcs:
                if npc != self and npc.faction is not None and self.distance_to(npc) <= FACTION_RADIUS:
                    if len(faction_members) < 20: 
                        self.faction = npc.faction 
                        break
                    break
        
        if self.faction is None:
            close_npcs = [npc for npc in npcs if self.distance_to(npc) <= FACTION_RADIUS and npc.faction is None]
            if len(close_npcs) >= FACTION_MIN_MEMBERS:
                new_faction = len(set([npc.faction for npc in npcs if npc.faction is not None]))  
                if new_faction < len(FACTION_COLORS): 
                    self.faction = new_faction
                    for npc in close_npcs:
                        npc.faction = self.faction  

        self.last_update = time.time()

    def join_army(self, army):
        self.in_army = True
        self.army = army

    def draw(self, screen):
        color = FACTION_COLORS[self.faction] if self.faction is not None else BLACK  
        if self.in_army and self.clicked:
            pygame.draw.rect(screen, color, pygame.Rect(int(self.x), int(self.y), WIDTH, HEIGHT))
            pygame.draw.rect(screen, (0,0,0), pygame.Rect(int(self.x) - 2, int(self.y) - 2, WIDTH + 2 * 2, HEIGHT + 2 * 2), 2)
        elif self.in_army:
            pygame.draw.rect(screen, color, pygame.Rect(int(self.x), int(self.y), WIDTH, HEIGHT))
        elif self.clicked:
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), WIDTH//2 + 2)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), WIDTH//2)
        else:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), WIDTH//2)


world = np.zeros(world_shape)
for i in range(world_shape[0]):
    for j in range(world_shape[1]):
        world[i][j] = noise.pnoise2(i*scale, j*scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=seed)
world_a_star = [[True for _ in range(len(world))] for _ in range(len(world[0]))]
for i in range(world_shape[0]):
    for j in range(world_shape[1]):
        world[i][j] = noise.pnoise2(i*scale, j*scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=seed)
        if world[i][j] < 0:
            world_a_star[i][j] = False


pygame.init()

screen = pygame.display.set_mode([800, 900])
pygame.display.set_caption("Procedurally Generated Map")

npcs = [NPC(random.randrange(WINDOW_SIZE[0]), random.randrange(WINDOW_SIZE[1])) for _ in range(10)]

done = False
clock = pygame.time.Clock()

armies = []
monsters = []

npcs = [NPC(random.randrange(WINDOW_SIZE[0]), random.randrange(WINDOW_SIZE[1])) for _ in range(10)]  # increased NPC count
click_spawn_npc = False
spawn_npc_rect = pygame.Rect(10,10,75,75)
screen_shake_rect = pygame.Rect(10,95,75,75)
click_shake_screen = False
explosion_pos = [0,0]
clicked_npc = None

explosion_duration = 0
click_spawn_monster = False
spawn_monster_rect = pygame.Rect(10, 180, 75, 75)
shake_monster_x = 0
shake_monster_y = 0
click_army_attack = False
click_army_attack_rect = pygame.Rect(10, 265, 75, 75)

select_army_1 = None
select_army_2 = None

click_rect_1 = False
click_rect_2 = False
click_rect_3 = False
click_rect_4 = False

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        
        if (click_rect_2 == True and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            shake_duration = 20 
            click_rect_2 = False
            explosion_pos = pygame.mouse.get_pos()
            explosion_duration = 40
        
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            if (click_rect_4):
                for npc in npcs:
                    if (npc.contains_point(*event.pos) and npc.in_army and select_army_1 == None):
                        select_army_1 = npc.army
                        npc.army.freeze = True
                        break
                    elif (npc.contains_point(*event.pos) and npc.in_army and select_army_1 != None and select_army_1.faction != npc.faction):
                        select_army_2 = npc.army
                        start = (int(select_army_2.leader.x / WIDTH), int(select_army_2.leader.y / HEIGHT))
                        end = (int(select_army_1.leader.x / WIDTH), int(select_army_1.leader.y / HEIGHT))
                        select_army_2.leader.path = find_path(world_a_star, start, end)
                        select_army_2.move_toward_battle = True
                        click_rect_4 = False
                        break

        if (select_army_1 != None and select_army_2 != None and select_army_1.freeze == True and select_army_2.freeze == True):
            print("entered battle pos")
            # THIS CODE ALSO WORKS
            # ITS JUST THAT THE BATTLE SEEMS TO NOT BE WORKING
            select_army_1.battle(select_army_2)
            select_army_2.battle(select_army_1)


        if (event.type == pygame.MOUSEBUTTONDOWN):
            if (event.button == 1):
                if (rect_1.collidepoint(event.pos)):
                    click_rect_1 = True
                elif (rect_2.collidepoint(event.pos)):
                    click_rect_2 = True
                elif (rect_3.collidepoint(event.pos)):
                    click_rect_3 = True
                elif (rect_4.collidepoint(event.pos)):
                    click_rect_4 = True
        
        if (event.type == pygame.MOUSEBUTTONDOWN):
            if (event.button == 1):
                if (not spawn_npc_rect.collidepoint(event.pos) and clicked_npc != None):
                    end_point_pos = pygame.mouse.get_pos()
                    end_point = (int(end_point_pos[0]/WIDTH), int(end_point_pos[1]/HEIGHT))
                    clicked_npc.path = find_path(world_a_star, (int(clicked_npc.x / WIDTH), int(clicked_npc.y / HEIGHT)), end_point)
                    clicked_npc.clicked = False
                    if (clicked_npc.in_army):
                        clicked_npc.army.leader = clicked_npc
                        

        if (event.type == pygame.MOUSEBUTTONDOWN):
            if (event.button == 1):
                if (not spawn_npc_rect.collidepoint(event.pos)):
                    for npc in npcs:
                        if (npc.contains_point(*event.pos)):
                            npc.clicked = True
                            clicked_npc = npc
                            break

        if (click_rect_1 == True and event.type == pygame.MOUSEBUTTONDOWN and not rect_1.collidepoint(event.pos) and event.button == 1):
            pos = pygame.mouse.get_pos()
            if (event.button == 1 and pos[0] <= 800 and pos[1] <= 800):
                npcs.append(NPC(pos[0], pos[1]))
                click_rect_1 = False
        elif (click_rect_3 == True and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not rect_3.collidepoint(event.pos)):
            click_rect_3 = False
            pos = pygame.mouse.get_pos()
            monsters.append(Monster(pos[0], pos[1]))
        
    if shake_duration > 0:
        shake_x = random.randint(-shake_intensity, shake_intensity)
        shake_y = random.randint(-shake_intensity, shake_intensity)
        shake_duration -= 1
    else:
        shake_x = 0
        shake_y = 0
    
    if shake_monster_duration > 0:
        shake_monster_x = random.randint(-5, 5)
        shake_monster_y = random.randint(-5,5)
        shake_monster_duration -= 1
    else:
        shake_monster_x = 0
        shake_monster_y = 0
    screen.fill(BLACK)
    screen.fill(BLACK, rect=pygame.Rect(shake_x + shake_monster_x, shake_y + shake_monster_y, *WINDOW_SIZE))

    for row in range(world_shape[0]):
        for column in range(world_shape[1]):
            color = WHITE
            if world[row][column] < -0.25:
                color = DARK_BLUE
            elif world[row][column] < -0.1:
                color = MEDIUM_BLUE
            elif world[row][column] < 0:
                color = BLUE
            elif world[row][column] < 0.05:
                color = SAND
            elif world[row][column] < 0.2:
                color = PLANES_GREEN
            elif world[row][column] < 0.3:
                color = FOREST_GREEN
            else:
                color = WHITE

            pygame.draw.rect(screen, color, [(WIDTH) * column + shake_x + shake_monster_x, (HEIGHT) * row + shake_y + shake_monster_y, WIDTH, HEIGHT])
    font = pygame.font.Font('persansb.ttf', 36)

    npc_text = font.render('NPC', True, BLACK, [255,204,153])
    explosion_text = font.render('Explosion', True, BLACK, [255,255,153])
    monster_text = font.render('Monster', True, BLACK, [204,255,153])
    army_attack_text = font.render('Army Attack', True, BLACK, [153,255,255])

    npc_text_rect = npc_text.get_rect()
    npc_text_rect.center = (50, 850)
    rect_1 = pygame.Rect(4, 821, 95, 54)

    explosion_text_rect = explosion_text.get_rect()
    explosion_text_rect.center = (200, 850)
    rect_2 = pygame.Rect(107, 821, 186, 54)

    monster_text_rect = monster_text.get_rect()
    monster_text_rect.center = (380, 850)
    rect_3 = pygame.Rect(300, 821, 158, 54)

    army_attack_text_rect = army_attack_text.get_rect()
    army_attack_text_rect.center = (588, 850)
    rect_4 = pygame.Rect(467, 821, 242, 54)
    
    if (click_rect_1):
        pygame.draw.rect(screen, [255,153,51], rect_1)
        npc_text = font.render('NPC', True, BLACK, [255,153,51])
        screen.blit(npc_text, npc_text_rect)
    else:
        pygame.draw.rect(screen, [255,204,153], rect_1)
    
    if (click_rect_2):
        pygame.draw.rect(screen, [255,255,51], rect_2)
        explosion_text = font.render('Explosion', True, BLACK, [255,255,51])
    else:
        pygame.draw.rect(screen, [255,255,153], rect_2)

    if (click_rect_3):
        pygame.draw.rect(screen, [128, 255, 0], rect_3)
        monster_text =  font.render('Monster', True, BLACK, [128, 255, 0])
    else:
        pygame.draw.rect(screen, [204,255,153], rect_3)
    
    if (click_rect_4):
        pygame.draw.rect(screen, [51, 255, 255], rect_4)
        army_attack_text = font.render("Army Attack", True, BLACK, [51, 255, 255])
    else:
        pygame.draw.rect(screen, [153,255,255], rect_4)
    
    screen.blit(npc_text, npc_text_rect)
    screen.blit(explosion_text, explosion_text_rect)
    screen.blit(monster_text, monster_text_rect)
    screen.blit(army_attack_text, army_attack_text_rect)

        

    if explosion_duration > 0:
        center = (40 - explosion_duration)*2.5
        num1 = max((explosion_pos[0] - center), 0)
        num2 = max((explosion_pos[1] - center), 0)
        explosion_rect = pygame.Rect(num1, num2, 10 + (40 - explosion_duration)*5, 10 + (40  - explosion_duration)*5)
        pygame.draw.rect(screen, RED, explosion_rect)
        explosion_duration -= 1

        for npc in npcs:
            xycords = (npc.x, npc.y)
            if (explosion_rect.collidepoint(xycords)):
                npcs.remove(npc)

    factions = [npc.faction for npc in npcs if npc.faction is not None]
    factions = set([npc.faction for npc in npcs if npc.faction is not None])
    for faction in factions:
        faction_members = [npc for npc in npcs if npc.faction == faction]
        if len(faction_members) >= FACTION_MIN_MEMBERS:
            if faction not in [army.faction for army in armies]:
                armies.append(Army(faction, faction_members[0]))
            for army in armies:
                if army.faction == faction:
                    faction_army = army
            if len(faction_army.members) < len(faction_members)  * 0.2:
                potential_recruits = [npc for npc in faction_members if not npc.in_army]
                while len(faction_army.members) < len(faction_members) * 0.2 and potential_recruits:
                    recruit = random.choice(potential_recruits)
                    faction_army.add_member(recruit)
                    potential_recruits.remove(recruit)

    npcs = [npc for npc in npcs if npc.update()]  

    for monster in monsters:
        monster.draw(screen)
        if monster.update(npcs):
            shake_monster_duration += 10
        if (random.random() < 0.01 and not monster.jumping):
            print('entered')
            monster.jump()

    


    for npc in npcs: 
        npc.update_faction()

    armies = [army for army in armies if army.leader in npcs and len(army.members) > 0]
    if (select_army_1 != None and select_army_2 != None):
        if (select_army_1.in_battle):
            if (select_army_1.battle_count == 10):
                size_army = len(select_army_1.members)
                damage = max(int(size_army*0.2), 1)
                if (damage > len(select_army_1.battling_army.members)):
                    shake_monster_duration += 10
                    for npc in select_army_2.members:
                        npcs.remove(npc)
                    select_army_2 = None

                    for npc in npcs:
                        if npc.faction == select_army_1.battling_army.faction:
                            npc.faction = select_army_1.faction
                    select_army_1.freeze = False
                    select_army_1.move_toward_battle = False
                    select_army_1.in_battle = False
                    select_army_1.battling_army = None
                    select_army_1.battle_count = 0

                else:
                    for i in range(0, damage):
                        
                        print(f"{select_army_2.members.pop(0)} npc kill")
                    select_army_1.battle_count = 0
            else:
                select_army_1.battle_count += 1

        elif (select_army_2.in_battle):
            if (select_army_2.battle_count == 10):
                size_army = len(select_army_2.members)
                damage = max(int(size_army*0.2), 1)
                if (damage > len(select_army_1.members)):
                    shake_monster_duration += 10
                    print("npc genocide for army 1")
                    for npc in select_army_1.members:
                        npcs.remove(npc)
                    select_army_1 = None
                    for npc in npcs:
                        if npc.faction == select_army_2.battling_army.faction:
                            npc.faction = select_army_2.faction
                    select_army_2.freeze = False
                    select_army_2.move_toward_battle = False
                    select_army_2.in_battle = False
                    select_army_2.battling_army = None
                    select_army_2.battle_count = 0
                else:
                    for i in range(0, damage):
                        print("killin npc kill kill")
                        select_army_1.members.pop(0)
                    select_army_2.battle_count = 0
            else:
                select_army_2.battle_count += 1
    
    for npc in npcs: 
        npc.draw(screen)
    clock.tick(60)
    pygame.display.flip()

pygame.quit()
