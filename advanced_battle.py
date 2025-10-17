import mesa
import numpy as np

# --- Terrain Definitions ---
PLAIN, FOREST, HILL = 0, 1, 2
TERRAIN_DEFENSE_BONUS = {PLAIN: 0, FOREST: 3, HILL: 5}
TERRAIN_MOVEMENT_COST = {PLAIN: 1, FOREST: 2, HILL: 2}

# --- Agent Morale Definitions ---
MORALE_BREAK_THRESHOLD = 25
MORALE_ALLY_DEATH_PENALTY = 10
MORALE_AURA_BONUS = 2

class TerrainPatch(mesa.Agent):
    """A simple agent representing a patch of terrain."""
    def __init__(self, unique_id, model, terrain_type):
        super().__init__(unique_id, model)
        self.terrain_type = terrain_type
    
    def step(self):
        pass

class SoldierAgent(mesa.Agent):
    """Base class for all combat units."""
    def __init__(self, unique_id, model, team, commander):
        super().__init__(unique_id, model)
        self.team = team
        self.commander = commander
        self.max_hp = 100
        self.hp = self.max_hp
        self.attack_power = 10
        self.defense = 0
        self.movement_points_per_turn = 2
        self.morale = 100
        self.is_broken = False

    def get_distance(self, pos_1, pos_2):
        return abs(pos_1[0] - pos_2[0]) + abs(pos_1[1] - pos_2[1])

    def take_damage(self, damage):
        terrain_type = self.model.terrain_grid[self.pos]
        defense_bonus = TERRAIN_DEFENSE_BONUS[terrain_type]
        final_damage = max(0, damage - self.defense - defense_bonus)
        self.hp -= final_damage
        self.update_morale(penalty=final_damage * 0.5)

    def update_morale(self, penalty=0, bonus=0):
        if self.is_broken: return
        self.morale = max(0, min(100, self.morale + bonus - penalty))
        if self.morale < MORALE_BREAK_THRESHOLD:
            self.is_broken = True

    def find_nearest_enemy(self):
        enemies = [a for a in self.model.schedule.agents if isinstance(a, SoldierAgent) and a.team != self.team]
        if not enemies:
            return None, float('inf')
        closest_enemy = min(enemies, key=lambda e: self.get_distance(self.pos, e.pos))
        distance = self.get_distance(self.pos, closest_enemy.pos)
        return closest_enemy, distance

    def move_towards(self, target_pos, movement_budget):
        """Move towards a target, respecting movement points, terrain, and avoiding enemies."""
        while movement_budget > 0:
            if self.pos == target_pos:
                break

            dx = target_pos[0] - self.pos[0]
            dy = target_pos[1] - self.pos[1]

            # Determine potential next steps
            possible_steps = []
            if abs(dx) > abs(dy):
                next_x = self.pos[0] + (1 if dx > 0 else -1)
                possible_steps.append((next_x, self.pos[1]))
            else:
                next_y = self.pos[1] + (1 if dy > 0 else -1)
                possible_steps.append((self.pos[0], next_y))
            
            # Add other directions as fallbacks if the primary is blocked
            if abs(dx) <= abs(dy) and dx != 0:
                next_x = self.pos[0] + (1 if dx > 0 else -1)
                possible_steps.append((next_x, self.pos[1]))
            if abs(dy) < abs(dx) and dy != 0:
                next_y = self.pos[1] + (1 if dy > 0 else -1)
                possible_steps.append((self.pos[0], next_y))

            # Filter for valid steps: not outside the grid and not occupied by an enemy soldier.
            valid_steps = []
            for p in possible_steps:
                if not self.model.grid.out_of_bounds(p):
                    is_enemy_occupied = any(
                        isinstance(agent, SoldierAgent) and agent.team != self.team
                        for agent in self.model.grid.get_cell_list_contents([p])
                    )
                    if not is_enemy_occupied:
                        valid_steps.append(p)
            
            if not valid_steps:
                break # Blocked by enemies or map boundary

            # Find the best affordable step
            best_step = None
            min_cost = float('inf')
            
            for step in valid_steps:
                cost = TERRAIN_MOVEMENT_COST[self.model.terrain_grid[step]]
                if movement_budget >= cost:
                    # Prefer cheaper steps, breaking ties by distance to target
                    if cost < min_cost:
                        min_cost = cost
                        best_step = step
                    elif cost == min_cost and self.get_distance(step, target_pos) < self.get_distance(best_step, target_pos):
                        best_step = step

            if best_step:
                self.model.grid.move_agent(self, best_step)
                movement_budget -= min_cost
            else:
                break # No affordable moves left

    def flee(self):
        enemy, _ = self.find_nearest_enemy()
        if not enemy: return
        away_pos = (self.pos[0] * 2 - enemy.pos[0], self.pos[1] * 2 - enemy.pos[1])
        self.move_towards(away_pos, self.movement_points_per_turn)

    def step(self):
        if self.hp <= 0: return
        if self.is_broken:
            self.flee()
            return
        
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True)
        enemies_in_range = [n for n in neighbors if isinstance(n, SoldierAgent) and n.team != self.team]
        
        if enemies_in_range:
            target = self.random.choice(enemies_in_range)
            target.take_damage(self.attack_power)
            return

        enemy, _ = self.find_nearest_enemy()
        if enemy:
            self.move_towards(enemy.pos, self.movement_points_per_turn)

# (The rest of the code for Warrior, Rider, Commander, TacticalBattleModel, and Visualization remains the same)
# ...
class Warrior(SoldierAgent):
    """A tough, frontline soldier. High HP and defense."""
    def __init__(self, unique_id, model, team, commander):
        super().__init__(unique_id, model, team, commander)
        self.max_hp = 150
        self.hp = self.max_hp
        self.attack_power = 12
        self.defense = 5
        self.movement_points_per_turn = 2


class Rider(SoldierAgent):
    """A fast-moving cavalry unit. High movement, lower defense."""
    def __init__(self, unique_id, model, team, commander):
        super().__init__(unique_id, model, team, commander)
        self.max_hp = 80
        self.hp = self.max_hp
        self.attack_power = 8
        self.defense = 2
        self.movement_points_per_turn = 4


class Commander(SoldierAgent):
    """A leader unit. Provides a morale aura to nearby squad members."""
    def __init__(self, unique_id, model, team):
        super().__init__(unique_id, model, team, commander=self)
        self.max_hp = 200
        self.hp = self.max_hp
        self.attack_power = 15
        self.defense = 8
        self.movement_points_per_turn = 2
        self.aura_range = 5

    def apply_morale_aura(self):
        """Boosts morale of nearby friendly units."""
        nearby_allies = self.model.grid.get_neighbors(self.pos, moore=True, radius=self.aura_range, include_center=False)
        for agent in nearby_allies:
            if isinstance(agent, SoldierAgent) and agent.team == self.team:
                agent.update_morale(bonus=MORALE_AURA_BONUS)
    
    def step(self):
        self.apply_morale_aura()
        super().step()


class TacticalBattleModel(mesa.Model):
    def __init__(self, width=40, height=40, num_warriors=10, num_riders=5):
        super().__init__()
        self.width = width
        self.height = height
        self.num_warriors = num_warriors
        self.num_riders = num_riders
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.schedule = mesa.time.RandomActivation(self)
        self.running = True
        self.terrain_grid = np.zeros((width, height), dtype=int)
        self._generate_terrain()
        self._create_teams()
        
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Red Agents": lambda m: sum(1 for a in m.schedule.agents if isinstance(a, SoldierAgent) and a.team == "Red"),
                "Blue Agents": lambda m: sum(1 for a in m.schedule.agents if isinstance(a, SoldierAgent) and a.team == "Blue"),
                "Red Avg Morale": lambda m: np.mean([a.morale for a in m.schedule.agents if isinstance(a, SoldierAgent) and a.team == "Red"] or [0]),
                "Blue Avg Morale": lambda m: np.mean([a.morale for a in m.schedule.agents if isinstance(a, SoldierAgent) and a.team == "Blue"] or [0]),
            }
        )

    def _generate_terrain(self):
        for _ in range(20):
            patch_type = self.random.choice([FOREST, HILL])
            w, h = self.random.randint(3, 8), self.random.randint(3, 8)
            x, y = self.random.randrange(self.width - w), self.random.randrange(self.height - h)
            self.terrain_grid[x:x+w, y:y+h] = patch_type
        
        for (x, y), terrain_type in np.ndenumerate(self.terrain_grid):
            if terrain_type != PLAIN:
                patch = TerrainPatch(self.next_id(), self, terrain_type)
                self.grid.place_agent(patch, (x, y))

    def _create_teams(self):
        red_commander = Commander(self.next_id(), self, "Red")
        self._place_agent_in_area(red_commander, (0, 0, self.width // 4, self.height))
        
        for _ in range(self.num_warriors):
            self._place_agent_in_area(Warrior(self.next_id(), self, "Red", red_commander), (0, 0, self.width // 4, self.height))
        for _ in range(self.num_riders):
            self._place_agent_in_area(Rider(self.next_id(), self, "Red", red_commander), (0, 0, self.width // 4, self.height))

        blue_commander = Commander(self.next_id(), self, "Blue")
        self._place_agent_in_area(blue_commander, (self.width * 3 // 4, 0, self.width, self.height))

        for _ in range(self.num_warriors):
            self._place_agent_in_area(Warrior(self.next_id(), self, "Blue", blue_commander), (self.width * 3 // 4, 0, self.width, self.height))
        for _ in range(self.num_riders):
            self._place_agent_in_area(Rider(self.next_id(), self, "Blue", blue_commander), (self.width * 3 // 4, 0, self.width, self.height))
            
    def _place_agent_in_area(self, agent, area_bounds):
        while True:
            x = self.random.randrange(area_bounds[0], area_bounds[2])
            y = self.random.randrange(area_bounds[1], area_bounds[3])
            if self.grid.is_cell_empty((x, y)):
                self.grid.place_agent(agent, (x, y))
                self.schedule.add(agent)
                break

    def step(self):
        dead_agents_this_step = [a for a in self.schedule.agents if isinstance(a, SoldierAgent) and a.hp <= 0]
        
        for dead_agent in dead_agents_this_step:
            allies_in_range = self.grid.get_neighbors(dead_agent.pos, moore=True, radius=3)
            for agent in allies_in_range:
                if isinstance(agent, SoldierAgent) and agent.team == dead_agent.team:
                    agent.update_morale(penalty=MORALE_ALLY_DEATH_PENALTY)
            
            self.grid.remove_agent(dead_agent)
            self.schedule.remove(dead_agent)
            
        self.schedule.step()
        self.datacollector.collect(self)

        red_alive = any(isinstance(a, SoldierAgent) and a.team == "Red" for a in self.schedule.agents)
        blue_alive = any(isinstance(a, SoldierAgent) and a.team == "Blue" for a in self.schedule.agents)

        if not red_alive or not blue_alive:
            self.running = False

def agent_portrayal(agent):
    if isinstance(agent, TerrainPatch):
        return {"Shape": "rect", "w": 1, "h": 1, "Layer": 0, "Color": "darkgreen" if agent.terrain_type == FOREST else "saddlebrown", "Filled": "true"}
    if isinstance(agent, SoldierAgent):
        portrayal = {"Layer": 1, "Color": "crimson" if agent.team == "Red" else "royalblue", "Filled": "true", "opacity": 0.3 + 0.7 * (agent.morale / 100)}
        if isinstance(agent, Warrior): portrayal.update({"Shape": "rect", "w": 0.8, "h": 0.8})
        elif isinstance(agent, Rider): portrayal.update({"Shape": "arrowHead", "scale": 0.8, "heading_x": 1 if agent.team == "Red" else -1, "heading_y": 0})
        elif isinstance(agent, Commander): portrayal.update({"Shape": "circle", "r": 0.9})
        return portrayal
    return {}

grid = mesa.visualization.CanvasGrid(agent_portrayal, 40, 40, 600, 600)
chart = mesa.visualization.ChartModule([{"Label": "Red Agents", "Color": "Red"}, {"Label": "Blue Agents", "Color": "Blue"}], data_collector_name="datacollector")
morale_chart = mesa.visualization.ChartModule([{"Label": "Red Avg Morale", "Color": "Tomato"}, {"Label": "Blue Avg Morale", "Color": "SkyBlue"}], data_collector_name="datacollector")

server = mesa.visualization.ModularServer(
    TacticalBattleModel,
    [grid, chart, morale_chart],
    "Tactical Battle Model",
    {"num_warriors": mesa.visualization.Slider("Warriors per Team", 10, 5, 20, 1), "num_riders": mesa.visualization.Slider("Riders per Team", 5, 0, 15, 1), "width": 40, "height": 40}
)

if __name__ == "__main__":
    server.launch()
