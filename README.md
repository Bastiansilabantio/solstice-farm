# 🌾 Solstice Farm

> A mini Harvest Moon-style farming game set on the longest day of the year.

Built for the [June Solstice Game Jam](https://dev.to/challenges/june-game-jam-2026-06-03) on DEV Community.

---

## 🎮 About the Game

It's the **Summer Solstice** — the longest day of the year. You've inherited an old farm from your grandfather, and you have one extraordinary, sun-drenched day to bring it back to life.

Plant seeds, till the soil, water your crops, and harvest them before the solstice sun sets. Sell your harvest at the shop to buy better seeds. Every second of sunlight counts — crops grow fastest at midday when the sun is at its peak!

---

## ✨ Features

- 🧑‍🌾 **Top-down player character** — Walk around your farm with WASD/Arrow keys
- 🗺️ **Tile-based world** — Explore your farm, the shop, and the water well
- 🌱 **Full farming cycle** — Till → Water → Plant → Grow → Harvest
- 🌻 **5 crop types** — Lettuce, Tomato, Corn, Sunflower, Strawberry
- ☀️ **Solstice sun mechanic** — Crops grow faster during peak sunlight hours
- 💰 **Economy system** — Sell crops and buy seeds at the shop
- 🌤️ **Dynamic sky cycle** — Sunrise → Midday → Golden Hour → Sunset
- ✨ **Particle effects** — Water splash, harvest sparkle, dirt puff
- 🎨 **Retro 16-bit pixel art** — All sprites generated procedurally via code
- 🏆 **Score & rating system** — How much can you earn in one solstice day?

---

## 🛠️ Tech Stack

- **Python 3.x**
- **Pygame**

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install pygame
```

### Run the Game

```bash
python main.py
```

---

## 🕹️ Controls

| Action | Key |
|---|---|
| Move | WASD or Arrow Keys |
| Use Tool | Space |
| Select Hoe | 1 |
| Select Water Can | 2 |
| Select Seeds | 3 |
| Select Harvest | 4 |
| Change Seed Type | Q / E |
| Open Shop | Space (facing shop) or Tab |
| Close Shop | Escape |

---

## 🌱 How to Play

1. **Till the soil** — Select the Hoe (1) and press Space facing a dirt tile
2. **Water the soil** — Select the Water Can (2) and press Space
3. **Plant seeds** — Select Seeds (3), choose type with Q/E, press Space on watered soil
4. **Wait for growth** — Crops grow in real-time, faster during midday!
5. **Water again** — Some crops need multiple waterings during growth
6. **Harvest** — Select Hands (4) and press Space on a fully grown crop
7. **Sell at shop** — Walk to the shop and sell your harvest for gold
8. **Buy more seeds** — Use gold to buy seeds for more valuable crops
9. **Refill water** — Visit the well to refill your watering can

---

## 🌻 Crops

| Crop | Grow Time | Sell Price | Seed Cost | Waters |
|---|---|---|---|---|
| 🥬 Lettuce | 40s | 15g | 5g | 1 |
| 🍅 Tomato | 70s | 35g | 12g | 2 |
| 🌽 Corn | 100s | 60g | 20g | 2 |
| 🍓 Strawberry | 90s | 80g | 25g | 2 |
| 🌻 Sunflower | 120s | 100g | 35g | 3 |

---

## 📁 Project Structure

```
solstice-farm/
├── main.py           # Entry point
├── settings.py       # Global constants & config
├── game.py           # Central game state & scenes
├── world.py          # Tile map & rendering
├── player.py         # Player movement & tools
├── farming.py        # Crop growth system
├── inventory.py      # Inventory & economy
├── shop.py           # Shop UI overlay
├── hud.py            # Heads-up display
├── sky.py            # Day/night sky cycle
├── camera.py         # 2D camera follow
├── sprites.py        # Procedural pixel art
├── particles.py      # Visual effects
├── menu.py           # Title & game over screens
└── README.md
```

---

## 🌍 Theme Connection

The game is directly inspired by the **June Solstice** — the moment when the sun reaches its highest point and the day is at its longest. The core mechanic revolves around this: **crops grow faster when the sun is at its peak**, creating a natural rhythm of urgency and reward tied to the solstice day cycle.

---

## 👤 Author

Made for the DEV June Solstice Game Jam 2026.

---

## 📄 License

MIT License — feel free to fork and build on this!
