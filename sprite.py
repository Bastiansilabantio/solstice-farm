"""
sprite.py
Modul sprite & animasi karakter 4 arah untuk game 2D dengan pygame.

File gambar yang dipakai: player_spritesheet.png
Susunan grid: 6 kolom x 4 baris (24 frame), background sudah transparan.

  Baris 0 -> jalan menghadap BAWAH (depan)
  Baris 1 -> jalan menghadap KIRI  (samping)
  Baris 2 -> jalan menghadap KIRI  (variasi pose lain, tidak dipakai default)
  Baris 3 -> jalan menghadap ATAS  (belakang)

Catatan: gambar aslinya tidak punya baris menghadap KANAN, jadi arah KANAN
dibuat otomatis dengan membalik (flip horizontal) frame baris KIRI.
Ini teknik umum dipakai di game 2D supaya tidak perlu gambar dobel.

Cara pakai cepat:
    from sprite import Player
    player = Player(x=400, y=300)
    ...
    player.update(dt, keys, bounds=screen.get_rect())
    screen.blit(player.image, player.rect)

Jalankan langsung file ini untuk lihat demo:
    python sprite.py
"""

import os
import pygame

# ---------------------------------------------------------------------------
# KONFIGURASI
# ---------------------------------------------------------------------------
SPRITESHEET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_spritesheet.png")
COLS = 6          # jumlah frame per baris
ROWS = 4          # jumlah baris (arah) di spritesheet
SCALE = 0.5       # ukuran asli tiap frame ~219x392 px (cukup besar), 0.5 -> ~110x196 px
                   # ubah sesuai kebutuhan: 1 = ukuran asli, 2 = 2x lebih besar, dst.

ANIM_SPEED = 0.12     # detik per pergantian frame saat jalan
PLAYER_SPEED = 220    # kecepatan gerak (pixel per detik)


def load_spritesheet(path, cols, rows, scale=1):
    """
    Memotong satu file spritesheet (grid cols x rows) menjadi
    list 2 dimensi: frames[baris][kolom] -> pygame.Surface
    """
    sheet = pygame.image.load(path).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()
    frame_w = sheet_w // cols
    frame_h = sheet_h // rows

    frames = []
    for row in range(rows):
        row_frames = []
        for col in range(cols):
            rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            if scale != 1:
                new_size = (int(frame_w * scale), int(frame_h * scale))
                frame = pygame.transform.scale(frame, new_size)
            row_frames.append(frame)
        frames.append(row_frames)
    return frames


class Player(pygame.sprite.Sprite):
    """Sprite karakter dengan animasi jalan 4 arah (atas/bawah/kiri/kanan)."""

    def __init__(self, x, y, spritesheet_path=SPRITESHEET_PATH):
        super().__init__()

        raw_frames = load_spritesheet(spritesheet_path, COLS, ROWS, scale=SCALE)

        frames_down = raw_frames[0]
        frames_left = raw_frames[1]
        frames_up = raw_frames[3]
        # arah kanan = flip horizontal dari frame kiri
        frames_right = [pygame.transform.flip(f, True, False) for f in frames_left]

        self.frames = {
            "down": frames_down,
            "left": frames_left,
            "right": frames_right,
            "up": frames_up,
        }

        self.direction = "down"     # arah hadap default
        self.frame_index = 0
        self.anim_timer = 0.0
        self.is_moving = False

        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))

        # hitbox lebih kecil dari gambar supaya tabrakan terasa lebih natural
        self.hitbox = self.rect.inflate(-self.rect.width * 0.55, -self.rect.height * 0.1)

    # ------------------------------------------------------------------
    def handle_input(self, keys):
        """Baca tombol arah / WASD, hasilkan vektor arah (dx, dy)."""
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        return dx, dy

    # ------------------------------------------------------------------
    def update(self, dt, keys, bounds=None):
        """
        Panggil tiap frame game loop.
        dt      : delta time dalam detik (mis. clock.tick(60)/1000)
        keys    : hasil pygame.key.get_pressed()
        bounds  : pygame.Rect opsional, batasi gerak player di dalamnya
        """
        dx, dy = self.handle_input(keys)
        self.is_moving = dx != 0 or dy != 0

        if dx != 0 and dy != 0:
            # normalisasi supaya gerak diagonal tidak lebih cepat
            dx *= 0.7071
            dy *= 0.7071

        # tentukan arah hadap berdasarkan input terakhir
        if dx < 0:
            self.direction = "left"
        elif dx > 0:
            self.direction = "right"
        elif dy < 0:
            self.direction = "up"
        elif dy > 0:
            self.direction = "down"

        self.rect.x += dx * PLAYER_SPEED * dt
        self.rect.y += dy * PLAYER_SPEED * dt

        if bounds is not None:
            self.rect.clamp_ip(bounds)

        self.hitbox.center = self.rect.center

        self._animate(dt)

    # ------------------------------------------------------------------
    def _animate(self, dt):
        if self.is_moving:
            self.anim_timer += dt
            if self.anim_timer >= ANIM_SPEED:
                self.anim_timer = 0.0
                frame_count = len(self.frames[self.direction])
                self.frame_index = (self.frame_index + 1) % frame_count
        else:
            # diam -> kembali ke frame pertama (pose berdiri)
            self.frame_index = 0
            self.anim_timer = 0.0

        self.image = self.frames[self.direction][self.frame_index]


# ---------------------------------------------------------------------------
# DEMO - jalankan file ini langsung untuk mencoba karakternya
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    pygame.init()

    SCREEN_W, SCREEN_H = 800, 600
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Demo Sprite Karakter - WASD / Panah untuk gerak, ESC keluar")
    clock = pygame.time.Clock()

    player = Player(SCREEN_W // 2, SCREEN_H // 2)
    all_sprites = pygame.sprite.Group(player)

    bg_color = (34, 139, 34)  # hijau rumput, ganti sesuai selera
    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        all_sprites.update(dt, keys, bounds=screen.get_rect())

        screen.fill(bg_color)
        all_sprites.draw(screen)
        pygame.display.flip()

    pygame.quit()
