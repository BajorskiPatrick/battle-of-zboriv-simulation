from src.models.SoldierAgent import SoldierAgent


class Rider(SoldierAgent):
    """A fast-moving cavalry unit. High movement, lower defense."""

    def __init__(self, unique_id, model, team, commander):
        super().__init__(unique_id, model, team, commander)
        self.max_hp = 80
        self.hp = self.max_hp
        self.attack_power = 8
        self.defense = 2
        self.movement_points_per_turn = 4
