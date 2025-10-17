import mesa

class BattleAgent(mesa.Agent):
    """An agent with health and attack power."""
    
    def __init__(self, unique_id, model, team, hp=100, attack_power=10):
        super().__init__(unique_id, model)
        self.team = team
        self.hp = hp
        self.attack_power = attack_power

    def get_distance(self, pos_1, pos_2):
        """Calculate the Manhattan distance between two points."""
        x1, y1 = pos_1
        x2, y2 = pos_2
        return abs(x1 - x2) + abs(y1 - y2)

    def step(self):
        """
        The agent's action in a single step.
        1. If it has enemies in attack range, attack one.
        2. Otherwise, move towards the nearest enemy.
        """
        # Do nothing if the agent is dead
        if self.hp <= 0:
            return

        # 1. Attack if possible
        # Get neighbors in a Moore neighborhood (including diagonals)
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True)
        enemies_in_range = [n for n in neighbors if isinstance(n, BattleAgent) and n.team != self.team]

        if enemies_in_range:
            # Attack a random enemy in range
            target = self.random.choice(enemies_in_range)
            target.hp -= self.attack_power
            # If target dies, remove it from grid and schedule
            if target.hp <= 0:
                self.model.grid.remove_agent(target)
                self.model.schedule.remove(target)
            return # End turn after attacking

        # 2. If no enemies in range, move
        # Find all opponents on the grid
        all_opponents = [a for a in self.model.schedule.agents if a.team != self.team]
        if not all_opponents:
            return # No enemies left to move towards

        # Find the closest opponent
        closest_enemy = min(
            all_opponents, 
            key=lambda enemy: self.get_distance(self.pos, enemy.pos)
        )
        
        # Move one step towards the closest enemy
        self.move_towards(closest_enemy.pos)

    def move_towards(self, target_pos):
        """Move one step towards a target position."""
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]

        # Move horizontally or vertically towards the target
        # This is a simple but effective pathfinding for this model
        possible_steps = []
        if dx > 0: possible_steps.append((self.pos[0] + 1, self.pos[1]))
        if dx < 0: possible_steps.append((self.pos[0] - 1, self.pos[1]))
        if dy > 0: possible_steps.append((self.pos[0], self.pos[1] + 1))
        if dy < 0: possible_steps.append((self.pos[0], self.pos[1] - 1))
        
        # Filter for empty cells
        valid_steps = [p for p in possible_steps if self.model.grid.is_cell_empty(p)]
        
        if valid_steps:
            # Move to the best valid step (closest to target)
            best_step = min(valid_steps, key=lambda p: self.get_distance(p, target_pos))
            self.model.grid.move_agent(self, best_step)


class BattleModel(mesa.Model):
    """A model for a simple battle simulation."""

    def __init__(self, width=25, height=25, num_agents_per_team=20):
        super().__init__()
        self.width = width
        self.height = height
        self.num_agents_per_team = num_agents_per_team
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.schedule = mesa.time.RandomActivation(self)
        self.running = True  # The model is running until a team is eliminated

        # Create agents
        # Red Team on the left
        for i in range(self.num_agents_per_team):
            x = self.random.randrange(0, width // 2)
            y = self.random.randrange(height)
            agent = BattleAgent(self.next_id(), self, "Red")
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

        # Blue Team on the right
        for i in range(self.num_agents_per_team):
            x = self.random.randrange(width // 2, width)
            y = self.random.randrange(height)
            agent = BattleAgent(self.next_id(), self, "Blue")
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
            
        # Data collector to track the number of agents per team
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Red Agents": lambda m: sum(1 for a in m.schedule.agents if a.team == "Red"),
                "Blue Agents": lambda m: sum(1 for a in m.schedule.agents if a.team == "Blue"),
            }
        )

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()
        self.datacollector.collect(self)
        
        # Check for win condition
        red_agents_alive = any(a.team == "Red" for a in self.schedule.agents)
        blue_agents_alive = any(a.team == "Blue" for a in self.schedule.agents)

        if not red_agents_alive or not blue_agents_alive:
            self.running = False


# --- Visualization ---
def agent_portrayal(agent):
    if agent.hp <= 0:
        return  # Don't draw dead agents
        
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "Color": "red" if agent.team == "Red" else "blue",
        "r": 0.5 * (agent.hp / 100) + 0.2, # Radius reflects health
    }
    return portrayal


# Grid and chart setup
grid = mesa.visualization.CanvasGrid(agent_portrayal, 25, 25, 600, 600)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "Red Agents", "Color": "Red"},
        {"Label": "Blue Agents", "Color": "Blue"},
    ],
    data_collector_name="datacollector",
)

# Server setup
server = mesa.visualization.ModularServer(
    BattleModel,
    [grid, chart],
    "Simple Battle Model",
    {
        "num_agents_per_team": mesa.visualization.Slider(
            "Number of Agents Per Team", 20, 5, 50, 5
        ),
        "width": 25,
        "height": 25,
    },
)

if __name__ == "__main__":
    server.launch()
