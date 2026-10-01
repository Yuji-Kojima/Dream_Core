import math
import os
from dataclasses import dataclass


import arcade

# ---------------------------------------------------------------
# 設定
# ---------------------------------------------------------------
SCALE = 4
TILE = 16 * SCALE  # 64px
WINDOW_W, WINDOW_H = 960, 576

SKIN_W, SKIN_H = 48, 64          # プレイヤーの見た目の大きさ
BODY_W, BODY_H = 24, 16          # 足元の判定の大きさ
SKIN_OFFSET_Y = (SKIN_H - BODY_H) / 2

PLAYER_SPEED = 4
DEBUG = True                     # True: 足元判定の赤枠を表示
SWORD_CUTS_BULLETS = False       # True: 剣で敵の弾を消せる

# 0=床, 1=壁, 2=敵の出現位置
test = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]  # 15列 x 9行 x 64px = 960 x 576
mapA = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 0, 0, 2, 1, 0, 0, 0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1],
    [1, 0, 1, 1, 0, 0, 0, 1, 2, 0, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# ---------------------------------------------------------------
# ロジック(描画に依存しない部分)
# ---------------------------------------------------------------
@dataclass
class Stats:
    max_hp: int = 30
    hp: int = 30
    attack: int = 1

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0


# ---------------------------------------------------------------
# 画像の読み込み(ファイルがなければ None を返す)
# ---------------------------------------------------------------
def load_tex(path):
    if os.path.exists(path):
        return arcade.load_texture(path)
    return None


# ---------------------------------------------------------------
# スプライトのクラス
# ---------------------------------------------------------------
class Enemy(arcade.SpriteSolidColor):
    def __init__(self, x, y):
        super().__init__(28, 28, color=arcade.color.GREEN)
        self.center_x, self.center_y = x, y
        self.stats = Stats(max_hp=3, hp=3, attack=10)
        self.shoot_timer = 2.0


class EnemyBullet(arcade.SpriteSolidColor):
    def __init__(self, x, y, dx, dy, speed=3, damage=10):
        super().__init__(10, 10, color=arcade.color.RED)
        self.center_x, self.center_y = x, y
        self.change_x = dx * speed
        self.change_y = dy * speed
        self.damage = damage


# ---------------------------------------------------------------
# 部屋の生成
# ---------------------------------------------------------------
def build_room(layout, walls, wall_visuals, enemy_spawns, wall_tex):
    walls.clear()
    wall_visuals.clear()
    enemy_spawns.clear()
    for r, row in enumerate(layout):
        for c, ch in enumerate(row):
            x = c * TILE + TILE / 2
            y = (len(layout) - 1 - r) * TILE + TILE / 2
            if ch == 1:
                # 判定用(単色・描画しない)
                s = arcade.SpriteSolidColor(TILE, TILE, color=arcade.color.GRAY)
                s.center_x, s.center_y = x, y
                walls.append(s)
                # 見た目用(画像・描画する)
                if wall_tex is not None:
                    v = arcade.Sprite(wall_tex)
                    v.width = TILE
                    v.height = TILE
                else:
                    v = arcade.SpriteSolidColor(TILE, TILE, color=arcade.color.GRAY)
                v.center_x, v.center_y = x, y
                wall_visuals.append(v)
            elif ch == 2:
                enemy_spawns.append((x, y))


# ---------------------------------------------------------------
# ゲーム画面
# ---------------------------------------------------------------
class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.wall_tex = load_tex("assets/wall.jpg")   # load_room が使う
        player_tex = load_tex("assets/images.jpg")

        # --- プレイヤー ---
        self.player = arcade.SpriteSolidColor(BODY_W, BODY_H, color=arcade.color.CYAN)
        self.player.center_x, self.player.center_y = 480, 120

        if player_tex is not None:
            self.player_skin = arcade.Sprite(player_tex)
            self.player_skin.width = SKIN_W
            self.player_skin.height = SKIN_H
        else:
            self.player_skin = arcade.SpriteSolidColor(SKIN_W, SKIN_H, color=arcade.color.CYAN)
        self.player_skins = arcade.SpriteList()
        self.player_skins.append(self.player_skin)

        self.stats = Stats()
        self.invincible = 0.0
        self.facing = (0, -1)

        # --- 剣 ---
        self.sword = arcade.SpriteSolidColor(40, 24, color=arcade.color.WHITE)
        self.sword_list = arcade.SpriteList()
        self.sword_list.append(self.sword)
        self.sword_timer = 0.0
        self.sword_cooldown = 0.0
        self.sword_hit = set()

        # --- 部屋・敵・弾(load_room より前に、全部作っておく) ---
        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.wall_visuals = arcade.SpriteList()
        self.enemy_spawns = []
        self.enemies = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.load_room(test)

        # --- その他 ---
        self.engine = arcade.PhysicsEngineSimple(self.player, self.walls)
        self.keys = set()
        self.game_over = False

        self.hp_text = arcade.Text("", 20, 516, arcade.color.WHITE, 14)
        self.over_text = arcade.Text(
            "GAME OVER  (R: retry)", WINDOW_W / 2, WINDOW_H / 2,
            arcade.color.WHITE, 32, anchor_x="center", anchor_y="center",
        )

        self.sync_skin()

    # ----- 補助 -----
    def sync_skin(self):
        """見た目を、足元の判定の位置に合わせる"""
        self.player_skin.center_x = self.player.center_x
        self.player_skin.center_y = self.player.center_y + SKIN_OFFSET_Y

    def start_swing(self):
        if self.sword_cooldown > 0:
            return
        self.sword_timer = 0.15
        self.sword_cooldown = 0.35
        self.sword_hit.clear()
        if self.facing[0] != 0:
            self.sword.width, self.sword.height = 40, 24
        else:
            self.sword.width, self.sword.height = 24, 40

    # ----- 描画 -----
    def on_draw(self):
        self.clear()
        self.wall_visuals.draw(pixelated=True)
        self.enemies.draw()
        self.bullets.draw()
        self.player_skins.draw(pixelated=True)
        if self.sword_timer > 0:
            self.sword_list.draw()

        # HPバー
        ratio = self.stats.hp / self.stats.max_hp
        arcade.draw_lbwh_rectangle_filled(18, 538, 132, 20, arcade.color.BLACK)
        arcade.draw_lbwh_rectangle_filled(20, 540, 128, 16, arcade.color.DARK_GRAY)
        arcade.draw_lbwh_rectangle_filled(20, 540, 128 * ratio, 16, arcade.color.GREEN)
        self.hp_text.text = f"HP {self.stats.hp}/{self.stats.max_hp}"
        self.hp_text.draw()

        if DEBUG:
            self.player.draw_hit_box(arcade.color.RED, 2)

        if self.game_over:
            self.over_text.draw()

    # ----- 更新 -----
    def on_update(self, delta_time):
        if self.game_over:
            return

        # 移動
        self.player.change_x = (
            (arcade.key.D in self.keys) - (arcade.key.A in self.keys)
        ) * PLAYER_SPEED
        self.player.change_y = (
            (arcade.key.W in self.keys) - (arcade.key.S in self.keys)
        ) * PLAYER_SPEED

        # 向きの更新(斜めのときは前の向きを維持)
        if self.player.change_x != 0 and self.player.change_y == 0:
            self.facing = (1 if self.player.change_x > 0 else -1, 0)
        elif self.player.change_y != 0 and self.player.change_x == 0:
            self.facing = (0, 1 if self.player.change_y > 0 else -1)

        self.engine.update()
        self.sync_skin()

        # 無敵時間
        if self.invincible > 0:
            self.invincible -= delta_time

        # 敵との接触
        if self.invincible <= 0:
            hits = arcade.check_for_collision_with_list(self.player, self.enemies)
            if hits:
                self.stats.take_damage(hits[0].stats.attack)
                self.invincible = 1.0

        # 敵が弾を撃つ
        for e in self.enemies:
            e.shoot_timer -= delta_time
            if e.shoot_timer <= 0:
                e.shoot_timer = 2.0
                dx = self.player.center_x - e.center_x
                dy = self.player.center_y - e.center_y
                dist = math.hypot(dx, dy) or 1
                self.bullets.append(
                    EnemyBullet(e.center_x, e.center_y, dx / dist, dy / dist)
                )

        # 敵の弾を動かす
        for b in list(self.bullets):
            b.center_x += b.change_x
            b.center_y += b.change_y
            if arcade.check_for_collision_with_list(b, self.walls):
                b.remove_from_sprite_lists()
            elif self.invincible <= 0 and arcade.check_for_collision(b, self.player):
                self.stats.take_damage(b.damage)
                self.invincible = 1.0
                b.remove_from_sprite_lists()

        # 剣
        self.sword_cooldown = max(0.0, self.sword_cooldown - delta_time)
        if self.sword_timer > 0:
            self.sword_timer -= delta_time
            self.sword.center_x = self.player.center_x + self.facing[0] * 32
            self.sword.center_y = self.player.center_y + self.facing[1] * 32
            for e in arcade.check_for_collision_with_list(self.sword, self.enemies):
                if e not in self.sword_hit:
                    self.sword_hit.add(e)
                    e.stats.take_damage(self.stats.attack)
                    if e.stats.is_dead:
                        e.remove_from_sprite_lists()
            if SWORD_CUTS_BULLETS:
                for b in arcade.check_for_collision_with_list(self.sword, self.bullets):
                    b.remove_from_sprite_lists()

        # 無敵中は点滅
        blink_off = self.invincible > 0 and int(self.invincible * 10) % 2 == 0
        self.player_skin.visible = not blink_off

        # ゲームオーバー
        if self.stats.is_dead:
            self.game_over = True
            self.player_skin.visible = True

    # ----- 入力 -----
    def on_key_press(self, key, modifiers):
        self.keys.add(key)
        if key == arcade.key.SPACE and not self.game_over:
            self.start_swing()
        if key == arcade.key.R and self.game_over:
            self.window.show_view(GameView())
        if key == arcade.key.L:
            data = open_map_editor()
            if data:
                self.load_room(data, player_pos=(480, 120))
            self.keys.clear()



    def on_key_release(self, key, modifiers):
        self.keys.discard(key)
    def load_room(self, layout, player_pos=None):
        # 壁と出現位置を作り直す
        build_room(layout, self.walls, self.wall_visuals,
                   self.enemy_spawns, self.wall_tex)

        # 敵と弾を作り直す
        self.enemies.clear()
        for x, y in self.enemy_spawns:
            self.enemies.append(Enemy(x, y))
        self.bullets.clear()

        # プレイヤーの位置を移す(指定があれば)
        if player_pos is not None:
            self.player.center_x, self.player.center_y = player_pos
            self.sync_skin()

def open_map_editor():
    from mapeditor import MapEditor
    import tkinter as tk
    root = tk.Tk()
    editor = MapEditor(root, width=15, height=9)
    root.mainloop()                 # エディタを閉じるまで、ここで止まる
    return editor.get_map_data()

window = arcade.Window(WINDOW_W, WINDOW_H, "My Roguelike")
window.show_view(GameView())
arcade.run()  # 必ず最後