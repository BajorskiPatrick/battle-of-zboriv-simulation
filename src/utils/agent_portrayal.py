from src.models.TerrainPatch import TerrainPatch
from src.models.SoldierAgent import SoldierAgent
from src.models.Warrior import Warrior
from src.models.Rider import Rider
from src.models.Commander import Commander

PLAIN, FOREST, HILL = 0, 1, 2


def agent_portrayal(agent):
    if isinstance(agent, TerrainPatch):
        return {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Layer": 0,
            "Color": "darkgreen" if agent.terrain_type == FOREST else "saddlebrown",
            "Filled": "true",
        }
    if isinstance(agent, SoldierAgent):
        portrayal = {
            "Layer": 1,
            "Color": "crimson" if agent.team == "Red" else "royalblue",
            "Filled": "true",
            "opacity": 0.3 + 0.7 * (agent.morale / 100),
        }
        if isinstance(agent, Warrior):
            portrayal.update({"Shape": "rect", "w": 0.8, "h": 0.8})
        elif isinstance(agent, Rider):
            portrayal.update(
                {
                    "Shape": "arrowHead",
                    "scale": 0.8,
                    "heading_x": 1 if agent.team == "Red" else -1,
                    "heading_y": 0,
                }
            )
        elif isinstance(agent, Commander):
            portrayal.update({"Shape": "circle", "r": 0.9})
        return portrayal
    return {}
