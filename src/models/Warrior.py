from src.models.SoldierAgent import SoldierAgent


class Warrior(SoldierAgent):
    """A tough, frontline soldier. High HP and defense."""

    def __init__(self, unique_id, model, team, commander):
        super().__init__(unique_id, model, team, commander)
        self.max_hp = 150
        self.hp = self.max_hp
        self.attack_power = 12
        self.defense = 5
        self.movement_points_per_turn = 2
