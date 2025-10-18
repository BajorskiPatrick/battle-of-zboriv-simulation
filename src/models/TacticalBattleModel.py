import mesa
from src.models.SoldierAgent import SoldierAgent
import numpy as np
from src.models.TerrainPatch import TerrainPatch
from src.models.Warrior import Warrior
from src.models.Rider import Rider
from src.models.Commander import Commander

PLAIN, FOREST, HILL = 0, 1, 2


# --- Agent Morale Definitions ---
MORALE_BREAK_THRESHOLD = 25
MORALE_ALLY_DEATH_PENALTY = 10


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
                "Red Agents": lambda m: sum(
                    1
                    for a in m.schedule.agents
                    if isinstance(a, SoldierAgent) and a.team == "Red"
                ),
                "Blue Agents": lambda m: sum(
                    1
                    for a in m.schedule.agents
                    if isinstance(a, SoldierAgent) and a.team == "Blue"
                ),
                "Red Avg Morale": lambda m: np.mean(
                    [
                        a.morale
                        for a in m.schedule.agents
                        if isinstance(a, SoldierAgent) and a.team == "Red"
                    ]
                    or [0]
                ),
                "Blue Avg Morale": lambda m: np.mean(
                    [
                        a.morale
                        for a in m.schedule.agents
                        if isinstance(a, SoldierAgent) and a.team == "Blue"
                    ]
                    or [0]
                ),
            }
        )

    def _generate_terrain(self):
        for _ in range(20):
            patch_type = self.random.choice( # pyright: ignore[reportAttributeAccessIssue]
                [FOREST, HILL]
            )  # pyright: ignore[reportAttributeAccessIssue]
            w, h = self.random.randint(3, 8), self.random.randint( # pyright: ignore[reportAttributeAccessIssue]
                3, 8
            )  # pyright: ignore[reportAttributeAccessIssue]
            x, y = self.random.randrange( # pyright: ignore[reportAttributeAccessIssue]
                self.width - w
            ), self.random.randrange(  # pyright: ignore[reportAttributeAccessIssue]
                self.height - h
            )
            self.terrain_grid[x : x + w, y : y + h] = patch_type

        for (x, y), terrain_type in np.ndenumerate(self.terrain_grid):
            if terrain_type != PLAIN:
                patch = TerrainPatch(self.next_id(), self, terrain_type)
                self.grid.place_agent(patch, (x, y))

    def _create_teams(self):
        red_commander = Commander(self.next_id(), self, "Red")
        self._place_agent_in_area(red_commander, (0, 0, self.width // 4, self.height))

        for _ in range(self.num_warriors):
            self._place_agent_in_area(
                Warrior(self.next_id(), self, "Red", red_commander),
                (0, 0, self.width // 4, self.height),
            )
        for _ in range(self.num_riders):
            self._place_agent_in_area(
                Rider(self.next_id(), self, "Red", red_commander),
                (0, 0, self.width // 4, self.height),
            )

        blue_commander = Commander(self.next_id(), self, "Blue")
        self._place_agent_in_area(
            blue_commander, (self.width * 3 // 4, 0, self.width, self.height)
        )

        for _ in range(self.num_warriors):
            self._place_agent_in_area(
                Warrior(self.next_id(), self, "Blue", blue_commander),
                (self.width * 3 // 4, 0, self.width, self.height),
            )
        for _ in range(self.num_riders):
            self._place_agent_in_area(
                Rider(self.next_id(), self, "Blue", blue_commander),
                (self.width * 3 // 4, 0, self.width, self.height),
            )

    def _place_agent_in_area(self, agent, area_bounds):
        while True:
            x = self.random.randrange( # pyright: ignore[reportAttributeAccessIssue]
                area_bounds[0], area_bounds[2]
            ) 
            y = self.random.randrange( # pyright: ignore[reportAttributeAccessIssue]
                area_bounds[1], area_bounds[3]
            )  
            if self.grid.is_cell_empty((x, y)):
                self.grid.place_agent(agent, (x, y))
                self.schedule.add(agent)
                break

    def step(self):
        dead_agents_this_step = [
            a for a in self.schedule.agents if isinstance(a, SoldierAgent) and a.hp <= 0
        ]

        for dead_agent in dead_agents_this_step:
            allies_in_range = self.grid.get_neighbors(
                dead_agent.pos,  # pyright: ignore[reportArgumentType]
                moore=True,
                radius=3,
            )
            for agent in allies_in_range:
                if isinstance(agent, SoldierAgent) and agent.team == dead_agent.team:
                    agent.update_morale(penalty=MORALE_ALLY_DEATH_PENALTY)

            self.grid.remove_agent(dead_agent)
            self.schedule.remove(dead_agent)

        self.schedule.step()
        self.datacollector.collect(self)

        red_alive = any(
            isinstance(a, SoldierAgent) and a.team == "Red"
            for a in self.schedule.agents
        )
        blue_alive = any(
            isinstance(a, SoldierAgent) and a.team == "Blue"
            for a in self.schedule.agents
        )

        if not red_alive or not blue_alive:
            self.running = False
