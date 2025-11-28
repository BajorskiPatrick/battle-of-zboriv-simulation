import mesa
from pathfinding.finder.a_star import AStarFinder
import random

class MilitaryAgent(mesa.Agent):
    """
    Agent reprezentujący oddział wojskowy z ulepszoną logiką FSM (Finite State Machine).
    """

    def __init__(self, unique_id, model, faction, unit_type):
        super().__init__(unique_id, model)
        self.faction = faction
        self.unit_type = unit_type
        
        # Pobieranie parametrów z centralnej definicji w modelu
        params = self.model.unit_params[self.unit_type]
        self.hp = params["hp"]
        self.max_hp = params["hp"]
        self.morale = params["morale"]
        self.max_morale = params["morale"]
        self.attack_range = params["range"]
        self.damage = params["damage"]
        self.speed = params["speed"]  # Gotowe do przyszłego wykorzystania

        # Stan agenta
        self.state = "IDLE"  # Stany: IDLE, MOVING, ATTACKING, FLEEING
        self.path = []
        
        # --- OPTYMALIZACJA PATHFINDINGU ---
        self.path_target_pos = None  # Gdzie był cel, gdy liczyliśmy trasę ostatnio
        self.repath_timer = self.random.randint(0, 10) # Losowy start, aby rozłożyć obciążenie
        
        self.target_pos_tuple = None
        
        # Losowy cel strategiczny w strefie frontu, aby armie się spotkały
        # Zabezpieczenie przed wychodzeniem poza mapę
        safe_margin = min(20, self.model.grid.width // 4)
        center_y = self.model.grid.height // 2
        
        if self.faction == "Armia Koronna":
            # Koronna idzie do środka lub wyżej (ku Kozakom)
            target_x = random.randint(safe_margin, self.model.grid.width - safe_margin)
            target_y = max(10, min(center_y, self.model.grid.height - 20))
            self.strategic_target = (target_x, target_y)
        else:
            # Kozacy idą do środka lub niżej (ku Koronnym)
            target_x = random.randint(safe_margin, self.model.grid.width - safe_margin)
            target_y = max(20, min(center_y, self.model.grid.height - 10))
            self.strategic_target = (target_x, target_y)

    def get_pos_tuple(self):
        """ Zawsze zwraca pozycję agenta jako krotkę (x, y), niezależnie od typu self.pos. """
        if isinstance(self.pos, tuple):
            return self.pos
        # Zakładamy, że to obiekt GridNode lub podobny z atrybutami .x i .y
        return self.pos.x, self.pos.y

    def find_enemy(self):
        """ Znajduje najbliższego wroga w zasięgu widzenia. """
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=20)
        enemies = [agent for agent in neighbors if isinstance(agent, MilitaryAgent) and agent.faction != self.faction]
        if enemies:
            return min(enemies, key=lambda e: self.distance_to(e))
        return None
    
    def find_any_enemy(self):
        """ Znajduje JAKIEGOKOLWIEK wroga na mapie (wolniejsze, ale pewne). """
        all_agents = self.model.schedule.agents
        enemies = [agent for agent in all_agents if isinstance(agent, MilitaryAgent) and agent.faction != self.faction and agent.hp > 0]
        if enemies:
            return min(enemies, key=lambda e: self.distance_to(e))
        return None

    def distance_to_pos(self, pos1, pos2):
        """ Oblicza dystans szachowy (Chebyshev distance) między dwoma punktami. """
        return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

    def distance_to(self, other_agent):
        """ Oblicza dystans szachowy (Chebyshev distance) do innego agenta. """
        pos1 = self.get_pos_tuple()
        pos2 = other_agent.get_pos_tuple()
        return self.distance_to_pos(pos1, pos2)

    def move(self):
        """ Przesuwa agenta o jeden krok wzdłuż wyznaczonej ścieżki. """
        if not self.path:
            return

        next_pos_node = self.path[0]
        next_pos_tuple = (next_pos_node.x, next_pos_node.y)

        if not self.model.grid.out_of_bounds(next_pos_tuple) and self.model.grid.is_cell_empty(next_pos_tuple):
             self.model.grid.move_agent(self, next_pos_tuple)
             self.path.pop(0) # Usuń wykonany krok
        else:
             # TRIGGER: Kolizja
             # Jeśli ścieżka jest zablokowana, wyczyść ją.
             # To wymusi 'if not self.path' w następnym kroku i ponowne przeliczenie (lub czekanie).
             # Dodajemy element losowości, żeby nie wszyscy przeliczali w tej samej klatce
             if self.random.random() < 0.5:
                self.path = []

    def calculate_path(self, target_pos_tuple):
        """ Oblicza ścieżkę do celu za pomocą algorytmu A*. """
        if not isinstance(target_pos_tuple, tuple):
             target_pos_tuple = (target_pos_tuple[0], target_pos_tuple[1])

        # Zapisz cel tej konkretnej ścieżki (do optymalizacji)
        self.path_target_pos = target_pos_tuple

        current_pos = self.get_pos_tuple()
        
        # Unikaj liczenia ścieżki do samego siebie
        if current_pos == target_pos_tuple:
            self.path = []
            return

        finder = AStarFinder()
        start_node = self.model.path_grid.node(current_pos[0], current_pos[1])
        end_node = self.model.path_grid.node(target_pos_tuple[0], target_pos_tuple[1])
        
        if not end_node.walkable:
            self.path = []
            return

        path, _ = finder.find_path(start_node, end_node, self.model.path_grid)
        
        # WAŻNE: Czyścimy grid po obliczeniach (wymagane przez bibliotekę pathfinding)
        self.model.path_grid.cleanup()
        
        self.path = path[1:] if path else []

    def should_recalculate_path(self, current_target_pos):
        """ 
        Decyduje, czy należy przeliczyć ścieżkę (Optymalizacja). 
        Zwraca True tylko w kluczowych momentach, oszczędzając CPU.
        """
        # 1. Jeśli nie mamy ścieżki, a powinniśmy się ruszać -> licz
        if not self.path:
            return True

        # 2. Timer bezpieczeństwa (co ~15 kroków)
        # Pozwala skorygować trasę jeśli sytuacja na mapie się zmieniła (np. inna jednostka zeszła z drogi)
        self.repath_timer += 1
        if self.repath_timer > 15:
            self.repath_timer = 0
            return True

        # 3. Sprawdź, czy cel uciekł za daleko od miejsca, gdzie zmierzamy
        if self.path_target_pos:
            dist = self.distance_to_pos(self.path_target_pos, current_target_pos)
            # Jeśli cel przesunął się o więcej niż 5 kratek od naszego pierwotnego celu -> przelicz
            if dist > 5:
                return True

        return False

    def step(self):
        """ Główna logika AI agenta, wykonywana w każdym kroku symulacji. """
        if self.hp <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        current_pos = self.get_pos_tuple()

        # 1. Sprawdź morale i zdecyduj o ucieczce
        if self.morale < 25 and self.state != "FLEEING":
            self.state = "FLEEING"
            safe_pos = (current_pos[0], 0) if self.faction == "Kozacy/Tatarzy" else (current_pos[0], self.model.grid.height - 1)
            self.calculate_path(safe_pos)
            print(f"Agent {self.unique_id} ({self.unit_type}) FLEEING!")
        
        if self.state == "FLEEING":
            if self.path: self.move()
            return

        # 2. Znajdź najbliższego wroga
        enemy = self.find_enemy()

        if enemy:
            distance = self.distance_to(enemy)
            
            # 3. Zachowanie w walce
            # a) Wróg w zasięgu strzału, ale nie w zwarciu
            if 1 < distance <= self.attack_range:
                if self.random.random() < 0.7:  # 70% szansy na atak
                    self.state = "ATTACKING"
                    # Nie czyścimy ścieżki agresywnie, może się przydać jak wróg ucieknie
                    
                    # Logika ataku
                    if self.unit_type == "Jazda":
                        charge_bonus = 1.8
                        enemy.hp -= self.damage * charge_bonus
                        enemy.morale -= self.damage * 2.5
                    else:
                        enemy.hp -= self.damage * 1.2
                        enemy.morale -= self.damage * 2
                        
                    if self.random.random() < 0.6: # Szansa na trafienie
                        enemy.hp -= self.damage
                        enemy.morale -= self.damage * 1.5
                else:  # 30% szansy na skrócenie dystansu
                    self.state = "MOVING"
                    enemy_pos = enemy.get_pos_tuple()
                    
                    # OPTYMALIZACJA: Sprawdź czy trzeba liczyć trasę
                    if self.should_recalculate_path(enemy_pos):
                        self.calculate_path(enemy_pos)
                    
                    if self.path: self.move()

            # b) Wróg w zwarciu
            elif distance <= 1:
                self.state = "ATTACKING"
                self.path = [] # W zwarciu nie potrzebujemy ścieżki
                if self.random.random() < 0.8: # Większa szansa na trafienie
                    # Specjalny bonus dla husarii (Jazda) - niszczycielska szarża
                    if self.unit_type == "Jazda":
                        charge_bonus = 1.8  # Husaria ma potężny bonus do szarży
                        enemy.hp -= self.damage * charge_bonus
                        enemy.morale -= self.damage * 2.5  # Większy wpływ na morale
                    else:
                        enemy.hp -= self.damage * 1.2 # Bonus do obrażeń
                        enemy.morale -= self.damage * 2

            # c) Wróg widoczny, ale poza zasięgiem
            else:
                self.state = "MOVING"
                enemy_pos = enemy.get_pos_tuple()
                
                # OPTYMALIZACJA: Sprawdź czy trzeba liczyć trasę
                if self.should_recalculate_path(enemy_pos):
                    self.target_pos_tuple = enemy_pos
                    self.calculate_path(enemy_pos)
                
                if self.path: self.move()
        else:
            # 4. Brak wroga w pobliżu -> szukaj agresywnie na całej mapie
            self.state = "MOVING_TO_STRATEGIC"
            distant_enemy = self.find_any_enemy()
            
            if distant_enemy:
                # Znaleziono wroga daleko - idź w jego kierunku
                enemy_pos = distant_enemy.get_pos_tuple()
                
                # OPTYMALIZACJA: Tutaj też używamy triggerów
                if self.should_recalculate_path(enemy_pos):
                    self.target_pos_tuple = enemy_pos
                    self.calculate_path(enemy_pos)
                    
                    # Jeśli nie można dotrzeć do wroga (np. rzeka), idź do celu strategicznego
                    if not self.path:
                        self.calculate_path(self.strategic_target)
            else:
                # Naprawdę brak wrogów - idź do celu strategicznego
                # Tutaj rzadko zmieniamy cel, więc liczymy tylko jak nie mamy ścieżki
                if not self.path or len(self.path) < 2:
                    self.calculate_path(self.strategic_target)
            
            if self.path: 
                self.move()
            else:
                # Jeśli osiągnięto cel strategiczny, wybierz nowy
                current_pos = self.get_pos_tuple()
                if self.distance_to_pos(current_pos, self.strategic_target) < 3:
                    # Nowy losowy cel w centrum mapy
                    safe_margin = min(20, self.model.grid.width // 4)
                    center_y = self.model.grid.height // 2
                    self.strategic_target = (
                        random.randint(safe_margin, self.model.grid.width - safe_margin),
                        max(10, min(center_y + random.randint(-10, 10), self.model.grid.height - 10))
                    )
                    # Wymuś przeliczenie w następnym kroku
                    self.path = []
                    safe_margin = min(20, self.model.grid.width // 4)
                    center_y = self.model.grid.height // 2
                    self.strategic_target = (
                        random.randint(safe_margin, self.model.grid.width - safe_margin),
                        max(10, min(center_y + random.randint(-10, 10), self.model.grid.height - 10))
                    )
                    self.calculate_path(self.strategic_target)
    
    def distance_to_pos(self, pos1, pos2):
        """ Oblicza dystans między dwiema pozycjami. """
        return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))