import arcade
from visualization.window import SimulationWindow

# --- Stałe konfiguracyjne ---
SCREEN_WIDTH = 2560  # 160 kafelków * 16 pikseli
SCREEN_HEIGHT = 1600  # 100 kafelków * 16 pikseli
SCREEN_TITLE = "Symulacja Bitwy pod Zborowem (1649)"

def main():
    """ Główna funkcja uruchamiająca symulację. """
    window = SimulationWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()