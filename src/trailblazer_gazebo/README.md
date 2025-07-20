# Trailblazer Gazebo
Paczka ROS 2 trailblazer_gazebo służy do uruchamiania symulacji łazika marsjańskiego [Legendary LRT 2.2 “Wolverine”](https://legendary.prz.edu.pl/?page_id=469). w środowisku Gazebo Classic.

Paczka pozwala na uruchomienie świata symulacyjnego, załadowanie opisu robota i przygotowanie interfejsów do integracji z systemami ROS 2 (np. slam_toolbox, nav2).

TODO:
- [ ] Migracja z Gazebo Classic na Gazebo Ingnition
- [ ] Dodanie domyślnych startowych światów

## 📚 Spis treści

- [📁 Struktura katalogów](#-struktura-katalogów)
- [🌍 Środowisko symulacyjne](#-środowisko-symulacujne)
- [🛠️ Jak używać](#️-jak-używać)

## 📁 Struktura katalogów
    src/trailblazer_gazebo
    ├── config/                 # Parametry do symulacji
    ├── launch/                 # Główny plik uruchamiający symulację w Gazebo
    ├── worlds/                 # Plik środowiska Gazebo
    ├── test/                   # Testy
    ├── setup.py                # Pliki budowania paczki
    ├── package.xml             # Opis paczki i zależności

## 🌍 Środowisko symulacyjne
### Czym jest Gazebo?
Gazebo to jedno z najpopularniejszych środowisk do symulacji robotów w 3D. Umożliwia realistyczne odwzorowanie fizyki (grawitacja, tarcie, masy, siły), sensorów (LIDAR, kamera, GPS, IMU), środowiska oraz interakcji z otoczeniem. Dzięki integracji z ROS 2 możliwa jest komunikacja między światem symulowanym a rzeczywistymi nodami ROS – tak, jakby robot fizycznie istniał.

## 🛠️ Jak używać
### ✅ Zbudowanie paczki
```bash
cd ~/TrailblazerML
colcon build --packages-select trailblazer_gazebo
source install/setup.bash
```
### 🚀 Uruchomienie symulacji samodzielnie
```bash
ros2 launch trailblazer_gazebo simulation.launch.py
```

### 🧩 Integracja z innymi paczkami
```python

```