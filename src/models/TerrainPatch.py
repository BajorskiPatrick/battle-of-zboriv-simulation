import mesa


class TerrainPatch(mesa.Agent):
    """A simple agent representing a patch of terrain."""

    def __init__(self, unique_id, model, terrain_type):
        super().__init__(unique_id, model)
        self.terrain_type = terrain_type

    def step(self):
        pass
