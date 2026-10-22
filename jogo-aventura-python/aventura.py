import sys
import os

# --- CORREÇÃO DE CAMINHO PARA EXECUÇÃO E DISTRIBUIÇÃO ---
if getattr(sys, 'frozen', False):
    # Se for o .exe compilado, pega a pasta exata onde o .exe está rodando no disco
    app_path = os.path.dirname(sys.executable)
    os.chdir(app_path)
else:
    # Se for execução direta via Python
    app_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_path)

from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')

from ursina import *
import math

app = Ursina()

# Configurações da Janela
window.title = "Aventura Python - 3 Dungeons"
window.borderless = False
window.fullscreen = False
window.fps_counter.enabled = False

# --- ESTADOS DO JOGO E PROGRESSÃO ---
class GameState:
    def __init__(self):
        self.state = "START"
        self.current_location = "Campo Aberto"
        self.dungeon_progress = 1
        
        self.max_hp = 10
        self.hp = 10
        self.lives = 1
        self.took_damage_in_dungeon = False
        self.dungeon_enemies_left = 0
        self.inactivity_timer = 0.0

        self.has_spin_attack = False
        self.has_shield = False

game_state = GameState()
world_objects = []
wall_objects = []
dungeon_doors = []
current_boss = None

# --- UI / TELAS ---
title_card = Text(text="AVENTURA PYTHON", position=(0, 0.25), origin=(0, 0), scale=3, color=color.gold)
start_instructions = Text(text="Pressione [ ENTER ] para Iniciar", position=(0, -0.1), origin=(0, 0), scale=1.5, color=color.white)
controls_info = Text(text="WASD = Mover | Mouse = Câmera | Clique Esq = Atacar", position=(0, -0.3), origin=(0, 0), scale=1.0, color=color.light_gray)

gameover_card = Text(text="GAME OVER", position=(0, 0.2), origin=(0, 0), scale=3, color=color.red, enabled=False)
gameover_instructions = Text(text="Pressione [ R ] para Tentar Novamente", position=(0, -0.1), origin=(0, 0), scale=1.5, color=color.white, enabled=False)

victory_card = Text(text="PARABÉNS! VOCÊ COMPLETOU A AVENTURA!", position=(0, 0.2), origin=(0, 0), scale=2.5, color=color.green, enabled=False)
restart_instructions = Text(text="Pressione [ R ] para Jogar Novamente", position=(0, -0.1), origin=(0, 0), scale=1.5, color=color.white, enabled=False)

hud_location = Text(text="", position=(-0.85, 0.45), scale=1.5, enabled=False)
hud_stats = Text(text="", position=(-0.85, 0.38), scale=1.4, color=color.light_gray, enabled=False)

hud_boss = Text(text="", position=(0.45, 0.42), origin=(0, 0), scale=1.5, color=color.red, enabled=False)
message_text = Text(text="", position=(0, 0.15), origin=(0, 0), scale=2, color=color.yellow, enabled=False)
door_prompt_text = Text(text="", position=(0, -0.2), origin=(0, 0), scale=1.8, color=color.azure, enabled=False)

def update_hud():
    hud_location.text = f"Local: {game_state.current_location} | Progresso: {game_state.dungeon_progress}/3"
    hud_stats.text = f"Vida: {game_state.hp}/{game_state.max_hp} HP  |  Vidas Extras: {game_state.lives}"
    
    if current_boss and current_boss.enabled and current_boss.is_boss:
        hud_boss.text = f"Chefe: {current_boss.health}/{current_boss.max_health} HP"
        hud_boss.enabled = True
    else:
        hud_boss.enabled = False

def show_message(msg, duration=3):
    message_text.text = msg
    message_text.enabled = True
    invoke(setattr, message_text, 'enabled', False, delay=duration)

# --- PROJÉTIL DE BOLA DE FOGO ---
class Fireball(Entity):
    def __init__(self, position, target_position):
        super().__init__(
            model='sphere',
            color=color.orange,
            scale=(2.0, 2.0, 2.0),
            position=position,
            collider='sphere'
        )
        self.direction = (target_position - position).normalized()
        self.speed = 15.0
        self.damage = 3
        self.lifetime = 4.0

    def update(self):
        if game_state.state != "PLAYING" or not player.enabled:
            return
            
        self.position += self.direction * self.speed * time.dt
        self.lifetime -= time.dt
        
        player_center = player.position + Vec3(0, 0.9, 0)
        if distance(self.position, player_center) < 1.3:
            player.take_damage(self.damage)
            destroy(self)
            return

        if self.lifetime <= 0:
            destroy(self)

# --- ITEM DE CURA ---
class HealthItem(Entity):
    def __init__(self, position=(35, 1, -20)):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1.2, 1.2, 1.2),
            position=position,
            collider=None
        )
        self.heal_amount = 3

    def update(self):
        if game_state.state != "PLAYING" or not player.enabled:
            return
            
        self.rotation_y += 100 * time.dt
        
        if distance_2d(self.position, player.position) < 1.8:
            if game_state.hp < game_state.max_hp:
                game_state.hp = min(game_state.max_hp, game_state.hp + self.heal_amount)
                update_hud()
                show_message(f"VOCÊ RECUPEROU +{self.heal_amount} HP!", 2.5)
                if self in world_objects:
                    world_objects.remove(self)
                destroy(self)

# --- JOGADOR ---
class Player(Entity):
    def __init__(self, position=(0, 1, 0)):
        super().__init__(
            model='cube',
            color=color.white,
            scale=(0.8, 1.8, 0.8),
            position=position,
            collider='box',
            enabled=False
        )
        
        self.facing = Entity(
            parent=self,
            model='cube',
            color=color.yellow,
            scale=(0.3, 0.3, 0.6),
            position=(0, 0.5, 0.5)
        )
        
        self.sword = Entity(
            parent=self,
            model='cube',
            color=color.light_gray,
            scale=(0.12, 0.12, 1.8),
            position=(0.6, 0.2, 0.8)
        )

        self.shield = Entity(
            parent=self,
            model='cube',
            color=color.azure,
            scale=(0.8, 1.0, 0.15),
            position=(-0.6, 0.2, 0.6),
            enabled=False
        )
        
        self.is_attacking = False
        self.is_spin_attacking = False
        self.is_blocking = False
        self.attack_timer = 0
        self.hold_attack_timer = 0
        self.speed = 10.5
        self.invulnerable_timer = 1.5
        self.target_door_num = None

        self.camera_pivot = Entity(position=self.position)
        camera.parent = self.camera_pivot
        camera.position = (0, 3.5, -9.5)
        camera.rotation_x = 18

    def update(self):
        if game_state.state != "PLAYING":
            return

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= time.dt
            self.visible = int(self.invulnerable_timer * 10) % 2 == 0
        else:
            self.visible = True

        self.camera_pivot.position = self.position
        if mouse.locked:
            self.camera_pivot.rotation_y += mouse.velocity[0] * 120
            camera.rotation_x -= mouse.velocity[1] * 120
            camera.rotation_x = clamp(camera.rotation_x, 5, 50)

        cam_world_pos = camera.world_position
        player_world_pos = self.world_position + Vec3(0, 1, 0)
        cam_dir = (player_world_pos - cam_world_pos).normalized()
        cam_dist = distance(cam_world_pos, player_world_pos)
        
        for w in wall_objects:
            w.alpha = 1.0

        cam_ray = raycast(cam_world_pos, cam_dir, distance=cam_dist, ignore=(self,))
        if cam_ray.hit and cam_ray.entity in wall_objects:
            cam_ray.entity.alpha = 0.3

        if game_state.has_shield and (mouse.right or held_keys['shift']):
            self.is_blocking = True
            self.shield.enabled = True
            current_speed = self.speed * 0.5
        else:
            self.is_blocking = False
            self.shield.enabled = False
            current_speed = self.speed

        if game_state.has_spin_attack and (mouse.left or held_keys['space']) and not self.is_blocking:
            self.hold_attack_timer += time.dt
            if self.hold_attack_timer > 0.4:
                self.sword.color = color.gold
        else:
            if game_state.has_spin_attack and self.hold_attack_timer > 0.4:
                self.perform_spin_attack()
            self.hold_attack_timer = 0
            if not self.is_attacking:
                self.sword.color = color.light_gray

        move_dir = Vec3(0, 0, 0)
        is_moving = False
        
        if held_keys['w'] or held_keys['up arrow']:
            move_dir += self.camera_pivot.forward
            is_moving = True
        if held_keys['s'] or held_keys['down arrow']:
            move_dir -= self.camera_pivot.forward
            is_moving = True
        if held_keys['a'] or held_keys['left arrow']:
            move_dir -= self.camera_pivot.right
            is_moving = True
        if held_keys['d'] or held_keys['right arrow']:
            move_dir += self.camera_pivot.right
            is_moving = True

        if game_state.current_location == "Campo Aberto":
            if is_moving or self.is_attacking or self.is_blocking:
                game_state.inactivity_timer = 0.0
            else:
                game_state.inactivity_timer += time.dt
                if game_state.inactivity_timer >= 90.0:
                    game_state.inactivity_timer = 0.0
                    spawn_extra_enemies()

        move_dir.y = 0
        if move_dir.length() > 0:
            move_dir = move_dir.normalized()
            ray = raycast(self.position + Vec3(0, 0.5, 0), move_dir, distance=0.8, ignore=(self,))
            if not ray.hit:
                self.position += move_dir * current_speed * time.dt
            
            target_rot = math.degrees(math.atan2(move_dir.x, move_dir.z))
            self.rotation_y = lerp(self.rotation_y, target_rot, time.dt * 10)

        if self.is_attacking:
            self.attack_timer -= time.dt
            if self.is_spin_attacking:
                self.rotation_y += 1400 * time.dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.is_spin_attacking = False
                self.sword.rotation_y = 0
                self.sword.color = color.light_gray

        if game_state.current_location == "Campo Aberto":
            near_available = False
            for door, door_num in dungeon_doors:
                if door_num == game_state.dungeon_progress:
                    diff_x = abs(self.x - door.x)
                    diff_z = abs(self.z - door.z)
                    
                    if diff_x < 3.5 and diff_z < 2.5:
                        near_available = True
                        self.target_door_num = door_num
                        door_prompt_text.text = f"Pressione [ ENTER ] para entrar na Dungeon {door_num}"
                        door_prompt_text.enabled = True
                        break
            
            if not near_available:
                self.target_door_num = None
                door_prompt_text.enabled = False

    def attack(self):
        if not self.is_attacking and game_state.state == "PLAYING" and not self.is_blocking:
            self.is_attacking = True
            self.attack_timer = 0.25
            self.sword.rotation_y = 90
            
            hit_info = raycast(self.position + Vec3(0, 0.5, 0), self.forward, distance=5.0, ignore=(self,))
            if hit_info.hit and hasattr(hit_info.entity, 'take_damage'):
                hit_info.entity.take_damage(1)

    def perform_spin_attack(self):
        if not self.is_attacking and game_state.state == "PLAYING" and not self.is_blocking:
            self.is_attacking = True
            self.is_spin_attacking = True
            self.attack_timer = 0.35
            self.sword.rotation_y = 90
            self.sword.color = color.yellow
            
            spin_radius = 3.8
            targets_hit = []
            
            for obj in list(world_objects):
                if hasattr(obj, 'take_damage') and obj != self:
                    if distance_2d(self.position, obj.position) < spin_radius:
                        targets_hit.append(obj)
            
            for obj in targets_hit:
                if obj in world_objects:
                    knockback_dir = (obj.position - self.position).normalized()
                    knockback_dir.y = 0
                    obj.position += knockback_dir * 4.5
                    if hasattr(obj, 'stun_timer'):
                        obj.stun_timer = 0.6
                    obj.take_damage(2)

    def take_damage(self, amount, attacker=None):
        if self.invulnerable_timer <= 0 and game_state.state == "PLAYING":
            if self.is_blocking:
                self.invulnerable_timer = 0.5
                if attacker and hasattr(attacker, 'stun_timer'):
                    knockback_dir = (attacker.position - self.position).normalized()
                    knockback_dir.y = 0
                    attacker.position += knockback_dir * 3.5
                    attacker.stun_timer = 0.8
                return

            game_state.hp -= amount
            if game_state.hp <= 0:
                game_state.hp = 0
                update_hud()
                on_player_death()
            else:
                game_state.took_damage_in_dungeon = True
                self.invulnerable_timer = 1.0
                update_hud()

# --- INIMIGO GUERREIRO ---
class Enemy(Entity):
    def __init__(self, position=(0, 1, 0), color_enemy=color.red, hp=2, is_boss=False, damage=1, boss_type=1):
        super().__init__(
            model='cube',
            color=color_enemy,
            scale=(1.4, 2.5, 1.4) if is_boss else (0.8, 1.8, 0.8),
            position=position,
            collider='box'
        )
        self.health = hp
        self.max_health = hp
        self.is_boss = is_boss
        self.original_color = color_enemy
        
        if is_boss and boss_type == 2:
            self.base_speed = 1.8
        elif is_boss:
            self.base_speed = 3.5
        else:
            self.base_speed = 2.5

        self.move_speed = self.base_speed
        self.damage = damage
        self.boss_type = boss_type
        
        self.stun_timer = 0
        self.dash_cooldown = 2.0
        self.fireball_cooldown = 2.0
        self.using_power = False

        self.helmet = Entity(
            parent=self,
            model='cube',
            color=color.yellow,
            scale=(0.4, 0.3, 0.5),
            position=(0, 0.5, 0.4)
        )
        
        self.enemy_sword = Entity(
            parent=self,
            model='cube',
            color=color.dark_gray,
            scale=(0.12, 0.12, 1.4),
            position=(0.6, 0.2, 0.5)
        )

    def reset_speed(self):
        self.move_speed = self.base_speed
        self.using_power = False
        self.color = self.original_color

    def update(self):
        if game_state.state != "PLAYING" or not player.enabled:
            return

        if self.stun_timer > 0:
            self.stun_timer -= time.dt
            self.color = color.light_gray
            return
        elif not self.using_power:
            self.color = self.original_color

        hit_box = self.intersects(player)
        if hit_box.hit:
            player.take_damage(self.damage, attacker=self)
            return

        dist_to_player = distance_2d(self.position, player.position)

        if self.is_boss:
            if self.boss_type == 1:
                self.dash_cooldown -= time.dt
                if self.dash_cooldown <= 0 and dist_to_player < 25:
                    self.dash_cooldown = 1.8
                    self.using_power = True
                    self.move_speed = 8.5
                    self.color = color.yellow
                    invoke(self.reset_speed, delay=0.9)

            elif self.boss_type == 2:
                self.fireball_cooldown -= time.dt
                if self.fireball_cooldown <= 0 and dist_to_player < 35:
                    self.fireball_cooldown = 2.5
                    Fireball(position=self.position + Vec3(0, 1.2, 0), target_position=player.position + Vec3(0, 0.9, 0))

            elif self.boss_type == 3:
                self.fireball_cooldown -= time.dt
                if self.fireball_cooldown <= 0 and dist_to_player < 35:
                    self.fireball_cooldown = 2.8
                    Fireball(position=self.position + Vec3(0, 1.2, 0), target_position=player.position + Vec3(0, 0.9, 0))

                self.dash_cooldown -= time.dt
                if self.dash_cooldown <= 0 and dist_to_player < 30:
                    self.dash_cooldown = 2.0
                    self.using_power = True
                    self.move_speed = 10.0
                    self.rotation_y += 1200 * time.dt
                    self.color = color.cyan
                    invoke(self.reset_speed, delay=0.8)

        if dist_to_player < 45:
            dir_to_player = (player.position - self.position).normalized()
            dir_to_player.y = 0
            
            self.position += dir_to_player * self.move_speed * time.dt
            
            if not (self.is_boss and self.boss_type == 3 and self.using_power):
                target_rot = math.degrees(math.atan2(dir_to_player.x, dir_to_player.z))
                self.rotation_y = lerp(self.rotation_y, target_rot, time.dt * 10)

    def take_damage(self, amount):
        if game_state.state != "PLAYING":
            return
            
        self.health -= amount
        self.color = color.white
        invoke(setattr, self, 'color', self.original_color, delay=0.1)
        update_hud()
        
        if self.health <= 0:
            if self.is_boss:
                invoke(on_boss_defeated, delay=0.01)
            else:
                if "Dungeon" in game_state.current_location:
                    game_state.dungeon_enemies_left -= 1
                    if game_state.dungeon_enemies_left <= 0:
                        spawn_dungeon_boss()

            if self in world_objects:
                world_objects.remove(self)
            destroy(self)

def spawn_extra_enemies():
    show_message("INIMIGOS RENASCERAM NO CAMPO!", 3)
    world_objects.extend([Enemy(position=(20, 1, 20), damage=1), Enemy(position=(-20, 1, 20), damage=1)])

def spawn_dungeon_boss():
    global current_boss
    show_message("O GUERREIRO CHEFE APARECEU!", 3)
    
    boss_props = {
        1: {"color": color.violet, "hp": 5, "damage": 1},
        2: {"color": color.orange, "hp": 7, "damage": 2},
        3: {"color": color.cyan, "hp": 10, "damage": 3}
    }
    prop = boss_props.get(game_state.dungeon_progress, boss_props[1])
    current_boss = Enemy(position=(0, 1.25, 30), color_enemy=prop["color"], hp=prop["hp"], is_boss=True, damage=prop["damage"], boss_type=game_state.dungeon_progress)
    world_objects.append(current_boss)
    update_hud()

# --- GERENCIADOR DE MUNDO ---
def clear_scene():
    global current_boss
    current_boss = None
    door_prompt_text.enabled = False
    for obj in list(world_objects):
        destroy(obj)
    world_objects.clear()
    wall_objects.clear()
    dungeon_doors.clear()

def load_overworld():
    clear_scene()
    game_state.state = "PLAYING"
    game_state.current_location = "Campo Aberto"
    game_state.inactivity_timer = 0.0
    
    player.position = (0, 1, -40)
    player.invulnerable_timer = 1.5
    player.target_door_num = None
    
    # 1. Chão de Grama
    ground = Entity(
        model='plane', 
        scale=(180, 1, 180), 
        texture='grama.png', 
        collider='box'
    )
    ground.texture_scale = (30, 30)

    # 2. Paredes de Floresta
    w1 = Entity(model='cube', scale=(180, 20, 1), position=(0, 10, 90), texture='fundooverworld.png', collider='box')
    w1.texture_scale = (2, 1)
    
    w2 = Entity(model='cube', scale=(180, 20, 1), position=(0, 10, -90), texture='fundooverworld.png', collider='box')
    w2.texture_scale = (2, 1)
    
    w3 = Entity(model='cube', scale=(1, 20, 180), position=(-90, 10, 0), texture='fundooverworld.png', collider='box')
    w3.texture_scale = (2, 1)
    
    w4 = Entity(model='cube', scale=(1, 20, 180), position=(90, 10, 0), texture='fundooverworld.png', collider='box')
    w4.texture_scale = (2, 1)
    
    wall_objects.extend([w1, w2, w3, w4])
    
    # 3. Portas
    d1_door = Entity(model='cube', scale=(6, 8, 1), position=(-30, 4, 88.9), texture='portas.png', collider='box')
    d1_label = Text(text="Dungeon 1", position=(-30, 9, 88.5), scale=1.8, origin=(0, 0), color=color.white)
    
    d2_door = Entity(model='cube', scale=(6, 8, 1), position=(0, 4, 88.9), texture='portas.png', collider='box')
    d2_label = Text(text="Dungeon 2", position=(0, 9, 88.5), scale=1.8, origin=(0, 0), color=color.white)
    
    d3_door = Entity(model='cube', scale=(6, 8, 1), position=(30, 4, 88.9), texture='portas.png', collider='box')
    d3_label = Text(text="Dungeon 3", position=(30, 9, 88.5), scale=1.8, origin=(0, 0), color=color.white)
    
    dungeon_doors.extend([(d1_door, 1), (d2_door, 2), (d3_door, 3)])
    world_objects.extend([ground, w1, w2, w3, w4, d1_door, d1_label, d2_door, d2_label, d3_door, d3_label])

    # 4. Céu
    sky = Sky(texture='ceoverworld.png')
    world_objects.append(sky)

    for door_entity, door_num in dungeon_doors:
        if door_num > game_state.dungeon_progress:
            x1 = Entity(parent=door_entity, model='cube', scale=(0.3, 0.9, 0.2), position=(0, 0, -0.6), rotation_z=45, color=color.red)
            x2 = Entity(parent=door_entity, model='cube', scale=(0.3, 0.9, 0.2), position=(0, 0, -0.6), rotation_z=-45, color=color.red)
            world_objects.extend([x1, x2])
    
    world_objects.extend([Enemy(position=(35, 1, 20), damage=1), HealthItem(position=(35, 1, -20))])
    update_hud()

def load_dungeon(dungeon_num):
    clear_scene()
    game_state.state = "PLAYING"
    game_state.took_damage_in_dungeon = False
    
    player.position = (0, 1, -38)
    player.invulnerable_timer = 1.5
    player.target_door_num = None
    
    # MAPEAMENTO DAS TEXTURAS DAS DUNGEONS
    dungeon_config = {
        1: {
            "name": "Dungeon da Floresta",
            "floor": "dungeon1_chao.png",
            "wall": "dungeon1_parede.png",
            "roof": "dungeon1_teto.png"
        },
        2: {
            "name": "Dungeon do Fogo",
            "floor": "dungeon2_chao.png",
            "wall": "dungeon2_parede.png",
            "roof": "dungeon2_teto.png"
        },
        3: {
            "name": "Dungeon da Água",
            "floor": "dungeon3_chao.png",
            "wall": "dungeon3_parede.png",
            "roof": "dungeon3_teto.png"
        }
    }
    
    cfg = dungeon_config.get(dungeon_num, dungeon_config[1])
    game_state.current_location = cfg["name"]
    
    # 1. Chão
    floor = Entity(model='plane', scale=(90, 1, 90), texture=cfg["floor"], collider='box')
    floor.texture_scale = (15, 15)
    
    # 2. Teto (em y=10 rotacionado para baixo)
    roof = Entity(model='plane', scale=(90, 1, 90), position=(0, 10, 0), rotation_x=180, texture=cfg["roof"], collider='box')
    roof.texture_scale = (15, 15)
    
    # 3. Paredes
    wall_back = Entity(model='cube', scale=(90, 10, 1), position=(0, 5, 45), texture=cfg["wall"], collider='box')
    wall_back.texture_scale = (15, 2)
    
    wall_front = Entity(model='cube', scale=(90, 10, 1), position=(0, 5, -45), texture=cfg["wall"], collider='box')
    wall_front.texture_scale = (15, 2)
    
    wall_left = Entity(model='cube', scale=(1, 10, 90), position=(-45, 5, 0), texture=cfg["wall"], collider='box')
    wall_left.texture_scale = (15, 2)
    
    wall_right = Entity(model='cube', scale=(1, 10, 90), position=(45, 5, 0), texture=cfg["wall"], collider='box')
    wall_right.texture_scale = (15, 2)

    wall_objects.extend([wall_back, wall_front, wall_left, wall_right])
    world_objects.extend([floor, roof, wall_back, wall_front, wall_left, wall_right])
    
    game_state.dungeon_enemies_left = 5
    for pos in [(-20, 1, 10), (20, 1, 10), (-15, 1, 25), (15, 1, 25), (0, 1, 35)]:
        world_objects.append(Enemy(position=pos, hp=2, is_boss=False, damage=1))
    update_hud()

def on_boss_defeated():
    hud_boss.enabled = False
    if game_state.dungeon_progress == 1:
        game_state.has_spin_attack = True
        show_message("VOCÊ GANHOU O ATAQUE GIRATÓRIO!", 4)
    elif game_state.dungeon_progress == 2:
        game_state.has_shield = True
        show_message("VOCÊ GANHOU O ESCUDO DE DEFESA!", 4)
    else:
        show_message("CHEFE FINAL DERROTADO!", 3)

    if not game_state.took_damage_in_dungeon:
        game_state.lives += 1
        invoke(setattr, message_text, 'text', "PERFEITO! +1 VIDA EXTRA!", delay=3.8)

    invoke(next_dungeon_step, delay=4.2)

def next_dungeon_step():
    if game_state.dungeon_progress < 3:
        game_state.dungeon_progress += 1
        load_overworld()
    else:
        game_state.state = "VICTORY"
        mouse.locked = False
        clear_scene()
        player.enabled = False
        hud_location.enabled = False
        hud_stats.enabled = False
        hud_boss.enabled = False
        victory_card.enabled = True
        restart_instructions.enabled = True

def on_player_death():
    game_state.lives -= 1
    if game_state.lives >= 0:
        game_state.state = "RESPAWNING"
        game_state.hp = game_state.max_hp
        show_message(f"VOCÊ MORREU!\nRestam {game_state.lives} Vida(s) Extra(s)!", 3)
        invoke(load_overworld, delay=3)
    else:
        game_state.state = "GAMEOVER"
        mouse.locked = False
        player.enabled = False
        hud_location.enabled = False
        hud_stats.enabled = False
        hud_boss.enabled = False
        gameover_card.enabled = True
        gameover_instructions.enabled = True
        invoke(clear_scene, delay=0.1)

def start_game():
    game_state.state = "PLAYING"
    game_state.dungeon_progress = 1
    game_state.hp = game_state.max_hp
    game_state.lives = 1
    game_state.has_spin_attack = False
    game_state.has_shield = False
    title_card.enabled = False
    start_instructions.enabled = False
    controls_info.enabled = False
    victory_card.enabled = False
    restart_instructions.enabled = False
    gameover_card.enabled = False
    gameover_instructions.enabled = False
    player.enabled = True
    hud_location.enabled = True
    hud_stats.enabled = True
    hud_boss.enabled = False
    mouse.locked = True
    load_overworld()

def input(key):
    if key == 'enter':
        if game_state.state == "START":
            start_game()
        elif game_state.state == "PLAYING" and player.target_door_num is not None:
            if player.target_door_num == game_state.dungeon_progress:
                door_prompt_text.enabled = False
                load_dungeon(game_state.dungeon_progress)
    if key == 'r' and game_state.state in ["VICTORY", "GAMEOVER"]:
        start_game()
    if game_state.state == "PLAYING":
        if key == 'left mouse down':
            player.attack()
        if key == 'escape':
            mouse.locked = not mouse.locked

# --- INICIALIZAÇÃO ---
player = Player(position=(0, 1, -40))

app.run()