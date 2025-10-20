import mesa
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import random

class MilitaryAgent(mesa.Agent):
    """ Agent reprezentujący oddział wojskowy. """
    def __init__(self, unique_id, model, faction, unit_type, hp, morale):
        super().__init__(unique_id, model)
        self.faction = faction
        self.unit_type = unit_type
        self.hp = hp
        self.max_hp = hp
        self.morale = morale
        self.max_morale = morale
        self.state = "IDLE"  # Stany: IDLE, MOVING, ATTACKING, FLEEING
        
        # Atrybuty bojowe na podstawie typu jednostki
        self.attack_range = self.model.unit_params[unit_type]["range"]
        self.damage = self.model.unit_params[unit_type]["damage"]
        self.speed = self.model.unit_params[unit_type]["speed"]
        
        self.target_pos = None
        self.path = []

    def find_enemy(self):
        """ Znajduje najbliższego wroga w zasięgu widzenia. """
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=self.attack_range + 5)
        enemies = [agent for agent in neighbors if isinstance(agent, MilitaryAgent) and agent.faction != self.faction]
        if enemies:
            return min(enemies, key=lambda e: self.distance_to(e))
        return None

    def distance_to(self, other_agent):
        return max(abs(self.pos[0] - other_agent.pos[0]), abs(self.pos[1] - other_agent.pos[1]))

    def move(self):
        if not self.path:
            return

        next_pos = self.path.pop(0)
        if self.model.grid.is_cell_empty(next_pos):
             self.model.grid.move_agent(self, next_pos)

    def calculate_path(self, target_pos):
        finder = AStarFinder()
        start_node = self.model.path_grid.node(self.pos[0], self.pos[1])
        end_node = self.model.path_grid.node(target_pos[0], target_pos[1])
        path, _ = finder.find_path(start_node, end_node, self.model.path_grid)
        self.model.path_grid.cleanup()
        self.path = path[1:] # Pomiń pozycję startową
        
    def step(self):
        """ Logika agenta wykonywana w każdym kroku symulacji (FSM). """
        if self.hp <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # 1. Sprawdź morale i zdecyduj o ucieczce
        if self.morale < 25 and self.state != "FLEEING":
            self.state = "FLEEING"
            # Uciekaj w kierunku przeciwnym do średniej pozycji wrogów lub do bazy
            safe_pos = (self.pos[0], 0) if self.faction == "Kozacy/Tatarzy" else (self.pos[0], self.model.grid.height - 1)
            self.calculate_path(safe_pos)

        if self.state == "FLEEING":
            if self.path:
                self.move()
            else:
                self.state = "IDLE" # Dotarł do bezpiecznego miejsca
            return

        # 2. Znajdź wroga
        enemy = self.find_enemy()

        if enemy:
            distance = self.distance_to(enemy)
            # 3. Jeśli wróg jest w zasięgu - atakuj
            if distance <= self.attack_range:
                self.state = "ATTACKING"
                # Symulacja ataku (prosta - szansa na trafienie)
                if random.random() < 0.5: # Uproszczona szansa na trafienie
                    enemy.hp -= self.damage
                    enemy.morale -= self.damage * 2
            # 4. Jeśli wróg jest poza zasięgiem - ruszaj w jego stronę
            else:
                self.state = "MOVING"
                if not self.path or self.target_pos != enemy.pos:
                    self.target_pos = enemy.pos
                    self.calculate_path(enemy.pos)
                if self.path:
                    self.move()
        else:
            self.state = "IDLE"
            self.path = []