import mesa

from src.models.TacticalBattleModel import TacticalBattleModel
from src.utils.agent_portrayal import agent_portrayal
# --- Terrain Definitions ---
PLAIN, FOREST, HILL = 0, 1, 2
TERRAIN_DEFENSE_BONUS = {PLAIN: 0, FOREST: 3, HILL: 5}
TERRAIN_MOVEMENT_COST = {PLAIN: 1, FOREST: 2, HILL: 2}

# --- Agent Morale Definitions ---
MORALE_BREAK_THRESHOLD = 25
MORALE_ALLY_DEATH_PENALTY = 10


grid = mesa.visualization.CanvasGrid(agent_portrayal, 40, 40, 600, 600)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "Red Agents", "Color": "Red"},
        {"Label": "Blue Agents", "Color": "Blue"},
    ],
    data_collector_name="datacollector",
)
morale_chart = mesa.visualization.ChartModule(
    [
        {"Label": "Red Avg Morale", "Color": "Tomato"},
        {"Label": "Blue Avg Morale", "Color": "SkyBlue"},
    ],
    data_collector_name="datacollector",
)

server = mesa.visualization.ModularServer(
    TacticalBattleModel,
    [grid, chart, morale_chart],
    "Tactical Battle Model",
    {
        "num_warriors": mesa.visualization.Slider("Warriors per Team", 10, 5, 20, 1),
        "num_riders": mesa.visualization.Slider("Riders per Team", 5, 0, 15, 1),
        "width": 40,
        "height": 40,
    },
)

if __name__ == "__main__":
    server.launch()
