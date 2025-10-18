from src.models.SoldierAgent import SoldierAgent

MORALE_AURA_BONUS = 2


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
        nearby_allies = self.model.grid.get_neighbors(  # pyright: ignore[reportAttributeAccessIssue]
            self.pos, moore=True, radius=self.aura_range, include_center=False
        )
        for agent in nearby_allies:
            if isinstance(agent, SoldierAgent) and agent.team == self.team:
                agent.update_morale(bonus=MORALE_AURA_BONUS)

    def step(self):
        self.apply_morale_aura()
        super().step()
