import mesa

PLAIN, FOREST, HILL = 0, 1, 2
TERRAIN_DEFENSE_BONUS = {PLAIN: 0, FOREST: 3, HILL: 5}
TERRAIN_MOVEMENT_COST = {PLAIN: 1, FOREST: 2, HILL: 2}

# --- Agent Morale Definitions ---
MORALE_BREAK_THRESHOLD = 25
MORALE_ALLY_DEATH_PENALTY = 10


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
        terrain_type = self.model.terrain_grid[ # type: ignore
            self.pos
        ]  # pyright: ignore[reportAttributeAccessIssue]
        defense_bonus = TERRAIN_DEFENSE_BONUS[terrain_type]
        final_damage = max(0, damage - self.defense - defense_bonus)
        self.hp -= final_damage
        self.update_morale(penalty=final_damage * 0.5)

    def update_morale(self, penalty: float = 0, bonus: float = 0):
        if self.is_broken:
            return
        self.morale = max(0, min(100, self.morale + bonus - penalty))
        if self.morale < MORALE_BREAK_THRESHOLD:
            self.is_broken = True

    def find_nearest_enemy(self):
        enemies = [
            a
            for a in self.model.schedule.agents  # pyright: ignore[reportAttributeAccessIssue]
            if isinstance(a, SoldierAgent) and a.team != self.team
        ]
        if not enemies:
            return None, float("inf")
        closest_enemy = min(enemies, key=lambda e: self.get_distance(self.pos, e.pos))
        distance = self.get_distance(self.pos, closest_enemy.pos)
        return closest_enemy, distance

    def move_towards(self, target_pos, movement_budget):
        """Move towards a target, respecting movement points, terrain, and avoiding enemies."""
        while movement_budget > 0:
            if self.pos == target_pos:
                break

            dx = (
                target_pos[0] - self.pos[0] # type: ignore
            )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
            dy = (
                target_pos[1] - self.pos[1] # type: ignore
            )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]

            # Determine potential next steps
            possible_steps = []
            if abs(dx) > abs(dy):
                next_x = self.pos[0] + ( # type: ignore
                    1 if dx > 0 else -1
                )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                possible_steps.append(
                    (next_x, self.pos[1]) # type: ignore
                )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
            else:
                next_y = self.pos[1] + ( # type: ignore
                    1 if dy > 0 else -1
                )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                possible_steps.append(
                    (self.pos[0], next_y) # type: ignore
                )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]

            # Add other directions as fallbacks if the primary is blocked
            if abs(dx) <= abs(dy) and dx != 0:
                next_x = self.pos[0] + ( # type: ignore
                    1 if dx > 0 else -1
                )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                possible_steps.append(
                    (next_x, self.pos[1]) # type: ignore
                )  # pyright: ignore[reportIndexIssue, reportOptionalSubscript]
            if abs(dy) < abs(dx) and dy != 0:
                next_y = self.pos[1] + ( # type: ignore
                    1 if dy > 0 else -1 
                )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                possible_steps.append(
                    (self.pos[0], next_y) # type: ignore
                )  # pyright: ignore[reportIndexIssue, reportOptionalSubscript]

            # Filter for valid steps: not outside the grid and not occupied by an enemy soldier.
            valid_steps = []
            for p in possible_steps:
                if not self.model.grid.out_of_bounds( # type: ignore
                    p
                ):  # pyright: ignore[reportAttributeAccessIssue]
                    is_enemy_occupied = any(
                        isinstance(agent, SoldierAgent) and agent.team != self.team
                        for agent in self.model.grid.get_cell_list_contents( # type: ignore
                            [p]
                        )  # pyright: ignore[reportAttributeAccessIssue]
                    )
                    if not is_enemy_occupied:
                        valid_steps.append(p)

            if not valid_steps:
                break  # Blocked by enemies or map boundary

            # Find the best affordable step
            best_step = None
            min_cost = float("inf")

            for step in valid_steps:
                cost = TERRAIN_MOVEMENT_COST[
                    self.model.terrain_grid[step] # type: ignore
                ]  # pyright: ignore[reportAttributeAccessIssue]
                if movement_budget >= cost:
                    # Prefer cheaper steps, breaking ties by distance to target
                    if cost < min_cost:
                        min_cost = cost
                        best_step = step
                    elif cost == min_cost and self.get_distance(
                        step, target_pos
                    ) < self.get_distance(best_step, target_pos):
                        best_step = step

            if best_step:
                self.model.grid.move_agent( # type: ignore
                    self, best_step
                )  # pyright: ignore[reportAttributeAccessIssue]
                movement_budget -= min_cost
            else:
                break  # No affordable moves left

    def flee(self):
        enemy, _ = self.find_nearest_enemy()
        if not enemy:
            return
        away_pos = (
            self.pos[0] * 2 - enemy.pos[0], # type: ignore
            self.pos[1] * 2 - enemy.pos[1], # type: ignore
        )  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
        self.move_towards(away_pos, self.movement_points_per_turn)

    def step(self):
        if self.hp <= 0:
            return
        if self.is_broken:
            self.flee()
            return

        neighbors = self.model.grid.get_neighbors( # type: ignore
            self.pos, moore=True
        )  # pyright: ignore[reportAttributeAccessIssue]
        enemies_in_range = [
            n for n in neighbors if isinstance(n, SoldierAgent) and n.team != self.team
        ]

        if enemies_in_range:
            target = self.random.choice(enemies_in_range)
            target.take_damage(self.attack_power)
            return

        enemy, _ = self.find_nearest_enemy()
        if enemy:
            self.move_towards(enemy.pos, self.movement_points_per_turn)
