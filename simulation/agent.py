# Plik: simulation/agent.py (WERSJA FINALNA 2.0 - Odporna na typy)

import mesa
from pathfinding.finder.a_star import AStarFinder
import random

class MilitaryAgent(mesa.Agent):
    def __init__(self, unique_id, model, faction, unit_type):
        super().__init__(unique_id, model)
        self.faction = faction
        self.unit_type = unit_type
        
        params = self.model.unit_params[self.unit_type]
        self.hp = params["hp"]
        self.max_hp = params["hp"]
        self.morale = params["morale"]
        self.max_morale = params["morale"]
        self.attack_range = params["range"]
        self.damage = params["damage"]
        self.speed = params["speed"]

        self.state = "IDLE"
        self.path = []
        self.target_pos_tuple = None

        if self.faction == "Armia Koronna":
            self.strategic_target = (self.model.grid.width // 2, 5)
        else:
            self.strategic_target = (self.model.grid.width // 2, self.model.grid.height - 5)

    def get_pos_tuple(self):
        """ NOWA FUNKCJA POMOCNICZA: Zawsze zwraca pozycję jako krotkę (x, y). """
        if isinstance(self.pos, tuple):
            return self.pos
        else:
            # Zakładamy, że to GridNode lub podobny obiekt z atrybutami .x i .y
            return (self.pos.x, self.pos.y)

    def find_enemy(self):
        # Mesa.grid.get_neighbors poprawnie obsługuje różne typy pozycji
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=15)
        enemies = [agent for agent in neighbors if isinstance(agent, MilitaryAgent) and agent.faction != self.faction]
        if enemies:
            return min(enemies, key=lambda e: self.distance_to(e))
        return None

    def distance_to(self, other_agent):
        pos1 = self.get_pos_tuple()
        pos2 = other_agent.get_pos_tuple()
        return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

    def move(self):
        if not self.path:
            return

        next_pos_node = self.path.pop(0)
        next_pos_tuple = (next_pos_node.x, next_pos_node.y)

        if not self.model.grid.out_of_bounds(next_pos_tuple) and self.model.grid.is_cell_empty(next_pos_tuple):
             self.model.grid.move_agent(self, next_pos_tuple)
        else:
             self.path = []

    def calculate_path(self, target_pos_tuple):
        if not isinstance(target_pos_tuple, tuple):
             target_pos_tuple = (target_pos_tuple.x, target_pos_tuple.y)

        current_pos = self.get_pos_tuple()
        finder = AStarFinder()
        start_node = self.model.path_grid.node(current_pos[0], current_pos[1])
        end_node = self.model.path_grid.node(target_pos_tuple[0], target_pos_tuple[1])
        
        if not end_node.walkable:
            self.path = []
            return

        path, _ = finder.find_path(start_node, end_node, self.model.path_grid)
        self.model.path_grid.cleanup()
        self.path = path[1:] if path else []

    def step(self):
        if self.hp <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        current_pos = self.get_pos_tuple()

        if self.morale < 25 and self.state != "FLEEING":
            self.state = "FLEEING"
            safe_pos = (current_pos[0], 0) if self.faction == "Kozacy/Tatarzy" else (current_pos[0], self.model.grid.height - 1)
            self.calculate_path(safe_pos)
        
        if self.state == "FLEEING":
            if self.path: self.move()
            return

        enemy = self.find_enemy()

        if enemy:
            distance = self.distance_to(enemy)
            if distance <= self.attack_range:
                self.state = "ATTACKING"
                self.path = []
                if self.random.random() < 0.6:
                    enemy.hp -= self.damage
                    enemy.morale -= self.damage * 1.5
            else:
                self.state = "MOVING"
                enemy_pos_tuple = enemy.get_pos_tuple()
                if not self.path or self.target_pos_tuple != enemy_pos_tuple:
                    self.target_pos_tuple = enemy_pos_tuple
                    self.calculate_path(enemy_pos_tuple)
                if self.path: self.move()
        else:
            self.state = "MOVING"
            if not self.path or len(self.path) < 5: # Szukaj nowej ścieżki, jeśli stara się kończy
                self.calculate_path(self.strategic_target)
            if self.path: self.move()