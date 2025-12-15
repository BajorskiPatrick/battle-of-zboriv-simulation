import mesa
from pathfinding.finder.a_star import AStarFinder
import random

class MilitaryAgent(mesa.Agent):
    """
    Agent reprezentujący historyczny oddział wojskowy.
    Obsługuje pogodę: mgła (wzrok), deszcz (niewypały).
    """

    def __init__(self, unique_id, model, faction, unit_type):
        super().__init__(unique_id, model)
        self.faction = faction
        self.unit_type = unit_type
        
        params = self.model.unit_params[self.unit_type]
        
        self.hp = params["hp"]
        self.max_hp = params["hp"]
        self.morale = params["morale"]
        self.max_morale = params["morale"]
        self.discipline = params.get("discipline", 50)
        self.defense = params.get("defense", 0)
        self.speed = params.get("speed", 1)
        
        self.melee_damage = params.get("melee_damage", 10)
        self.ranged_damage = params.get("ranged_damage", 0)
        self.attack_range = params.get("range", 1)
        self.ammo = params.get("ammo", 0)
        self.max_ammo = self.ammo

        self.state = "IDLE" 
        self.path = []
        self.path_target_pos = None
        self.repath_timer = self.random.randint(0, 10)
        self.target_pos_tuple = None
        
        self._assign_strategic_target()

    def _assign_strategic_target(self):
        safe_margin = min(20, self.model.grid.width // 4)
        center_y = self.model.grid.height // 2
        
        if self.faction == "Armia Koronna":
            target_x = random.randint(safe_margin, self.model.grid.width - safe_margin)
            target_y = max(10, min(center_y, self.model.grid.height - 20))
        else:
            target_x = random.randint(safe_margin, self.model.grid.width - safe_margin)
            target_y = max(20, min(center_y, self.model.grid.height - 10))
        self.strategic_target = (target_x, target_y)

    def get_pos_tuple(self):
        if isinstance(self.pos, tuple): return self.pos
        return self.pos.x, self.pos.y

    def find_enemy(self):
        # Bazowy zasięg
        vision_radius = 20
        
        # Wpływ pogody na widoczność
        if self.model.weather == "fog":
            vision_radius = 6 # Gęsta mgła
        elif self.model.weather == "rain":
            vision_radius = 12 # Ulewa
            
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=vision_radius)
        enemies = [agent for agent in neighbors if isinstance(agent, MilitaryAgent) and agent.faction != self.faction]
        if enemies:
            return min(enemies, key=lambda e: self.distance_to(e))
        return None
    
    def find_any_enemy(self):
        # Znajdowanie wroga na całej mapie (dla ruchu strategicznego)
        all_agents = self.model.schedule.agents
        enemies = [agent for agent in all_agents if isinstance(agent, MilitaryAgent) and agent.faction != self.faction and agent.hp > 0]
        if enemies:
            return min(enemies, key=lambda e: self.distance_to(e))
        return None

    def distance_to_pos(self, pos1, pos2):
        return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

    def distance_to(self, other_agent):
        return self.distance_to_pos(self.get_pos_tuple(), other_agent.get_pos_tuple())

    def move(self):
        if not self.path: return

        next_pos_node = self.path[0]
        next_pos_tuple = (next_pos_node.x, next_pos_node.y)

        # Sprawdź koszt terenu (błoto spowalnia)
        try:
            terrain_cost = self.model.terrain_costs[next_pos_tuple[1]][next_pos_tuple[0]]
            # Im wyższy koszt, tym większa szansa na pominięcie ruchu
            # speed=10 -> szybki, speed=1 -> wolny
            move_chance = self.speed / (terrain_cost * 5.0) 
            if self.random.random() > move_chance:
                return # Jednostka grzęźnie w tym turze
        except: pass

        # --- ZMIANA: Sprawdzenie kolizji z innymi jednostkami ---
        if self.model.grid.out_of_bounds(next_pos_tuple):
            self.path = []
            return

        # Sprawdź, czy na polu docelowym stoi inna żywa jednostka
        cell_contents = self.model.grid.get_cell_list_contents(next_pos_tuple)
        blocking_unit = any(isinstance(obj, MilitaryAgent) and obj.hp > 0 for obj in cell_contents)

        if not blocking_unit:
             self.model.grid.move_agent(self, next_pos_tuple)
             self.path.pop(0)
        else:
             # Jeśli pole jest zajęte (ktoś wszedł tam przed nami w tej turze),
             # czyścimy ścieżkę, co wymusi jej przeliczenie w następnym kroku (ominięcie przeszkody)
             self.path = []

    def calculate_path(self, target_pos_tuple):
        if not isinstance(target_pos_tuple, tuple): target_pos_tuple = (target_pos_tuple[0], target_pos_tuple[1])
        self.path_target_pos = target_pos_tuple
        current_pos = self.get_pos_tuple()
        
        if current_pos == target_pos_tuple:
            self.path = []
            return

        finder = AStarFinder()
        start_node = self.model.path_grid.node(current_pos[0], current_pos[1])
        end_node = self.model.path_grid.node(target_pos_tuple[0], target_pos_tuple[1])
        
        # --- ZMIANA: Traktuj inne jednostki jako przeszkody ---
        # Zbieramy listę węzłów, które tymczasowo zablokujemy
        temp_blocked_nodes = []
        
        # Iterujemy po wszystkich agentach, aby oznaczyć ich pozycje jako zajęte
        for agent in self.model.schedule.agents:
            # Interesują nas tylko żywe jednostki wojskowe, inne niż my sami
            if isinstance(agent, MilitaryAgent) and agent.hp > 0 and agent != self:
                pos = agent.get_pos_tuple()
                # WAŻNE: Nie blokujemy celu podróży (np. jeśli idziemy atakować wroga, musimy móc wyznaczyć ścieżkę do jego sąsiedztwa)
                if pos != target_pos_tuple:
                    node = self.model.path_grid.node(pos[0], pos[1])
                    # Jeśli węzeł był chodliwy, blokujemy go tymczasowo
                    if node.walkable:
                        node.walkable = False
                        temp_blocked_nodes.append(node)
        # -------------------------------------------------------

        if not end_node.walkable:
            # Jeśli cel jest zablokowany (np. ściana), przywracamy stan i kończymy
            for node in temp_blocked_nodes:
                node.walkable = True
            self.path = []
            return

        path, _ = finder.find_path(start_node, end_node, self.model.path_grid)
        
        # --- ZMIANA: Przywracamy stan siatki dla innych agentów ---
        for node in temp_blocked_nodes:
            node.walkable = True
        # -------------------------------------------------------

        self.model.path_grid.cleanup()
        self.path = path[1:] if path else []

    def should_recalculate_path(self, current_target_pos):
        if not self.path: return True
        self.repath_timer += 1
        if self.repath_timer > 15:
            self.repath_timer = 0
            return True
        if self.path_target_pos:
            if self.distance_to_pos(self.path_target_pos, current_target_pos) > 5: return True
        return False

    def receive_damage(self, amount):
        damage_reduction = min(amount - 1, self.random.randint(0, self.defense // 2))
        actual_damage = max(1, amount - damage_reduction)
        self.hp -= actual_damage
        
        morale_loss = actual_damage * 1.5
        if self.discipline > 80: morale_loss *= 0.7
        self.morale -= morale_loss

    def step(self):
        if self.hp <= 0: return
        current_pos = self.get_pos_tuple()

        # 1. Panika
        panic_threshold = 25 - (self.discipline / 5)
        if self.morale < panic_threshold and self.state != "FLEEING":
            if self.random.randint(0, 100) > self.discipline:
                self.state = "FLEEING"
                
                if self.faction == "Armia Koronna":
                    # Polacy uciekają do najbliższego punktu leczenia (obozu)
                    zones = self.model.healing_zones
                    # Znajdź strefę najbliższą aktualnej pozycji
                    closest_zone = min(zones, key=lambda z: self.distance_to_pos(current_pos, z))
                    self.calculate_path(closest_zone)
                else:
                    safe_y = 0 if self.faction == "Kozacy/Tatarzy" else self.model.grid.height - 1
                    self.calculate_path((current_pos[0], safe_y))
        
        if self.state == "FLEEING":
            # Jeśli dotarliśmy do celu ucieczki (punktu leczenia)
            if not self.path and self.faction == "Armia Koronna":
                # Jesteśmy w punkcie leczenia - czekamy na uleczenie przez model (apply_camp_healing)
                pass 
            elif self.path: 
                self.move()
            return

        # 2. Walka
        enemy = self.find_enemy()

        if enemy:
            distance = self.distance_to(enemy)
            
            # Walka dystansowa
            if 1 < distance <= self.attack_range and self.ranged_damage > 0:
                # Wpływ deszczu na broń palną (niewypały)
                misfire_chance = 0.4 if self.model.weather == "rain" else 0.0
                
                if self.ammo > 0:
                    if self.random.random() < (0.7 - misfire_chance):
                        self.state = "ATTACKING"
                        self.ammo -= 1
                        
                        # Bonus za osłonę terenu
                        enemy_pos = enemy.get_pos_tuple()
                        terrain_cover = self.model.terrain_costs[enemy_pos[1]][enemy_pos[0]]
                        dmg = self.ranged_damage
                        if terrain_cover > 1.5: dmg *= 0.6
                        
                        enemy.receive_damage(dmg)
                    else:
                        pass # Niewypał lub celowanie
                else:
                    # Brak amunicji -> szarża
                    self.state = "MOVING"
                    epos = enemy.get_pos_tuple()
                    if self.should_recalculate_path(epos): self.calculate_path(epos)
                    if self.path: self.move()

            # Walka wręcz
            elif distance <= 1.5: # Zasięg 1.5 łapie sąsiednie i ukośne
                self.state = "ATTACKING"
                self.path = []
                if self.random.random() < 0.8:
                    dmg = self.melee_damage
                    # Bonus szarży
                    if "Husaria" in self.unit_type or "Jazda" in self.unit_type:
                        dmg *= 1.5
                    enemy.receive_damage(dmg)

            # Ruch do wroga
            else:
                self.state = "MOVING"
                epos = enemy.get_pos_tuple()
                if self.should_recalculate_path(epos):
                    self.target_pos_tuple = epos
                    self.calculate_path(epos)
                if self.path: self.move()
        
        else:
            # 3. Ruch strategiczny
            self.state = "MOVING_TO_STRATEGIC"
            distant_enemy = self.find_any_enemy()
            target = distant_enemy.get_pos_tuple() if distant_enemy else self.strategic_target
            
            if self.should_recalculate_path(target): self.calculate_path(target)
            
            if self.path: 
                self.move()
            else:
                if self.distance_to_pos(current_pos, self.strategic_target) < 3:
                    self._assign_strategic_target()
                    self.path = []