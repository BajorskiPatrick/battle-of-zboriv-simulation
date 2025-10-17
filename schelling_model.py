import mesa

# --- 1. Agent Definition ---
class SchellingAgent(mesa.Agent):
    """
    An agent representing a household in the Schelling model.
    
    Attributes:
        unique_id: Agent's unique identifier.
        model: The model instance the agent belongs to.
        agent_type: The group (0 or 1) the agent belongs to.
    """
    def __init__(self, unique_id, model, agent_type):
        super().__init__(unique_id, model)
        self.agent_type = agent_type
        self.is_unhappy = False

    def step(self):
        """
        Defines the agent's behavior in a single simulation step.
        """
        similar_neighbors = 0
        total_neighbors = 0

        # Get all neighbors within a radius of 1, including corners
        for neighbor in self.model.grid.get_neighbors(self.pos, moore=True):
            if neighbor.agent_type == self.agent_type:
                similar_neighbors += 1
            total_neighbors += 1

        # Check if the agent is unhappy
        if total_neighbors > 0:
            percent_similar = similar_neighbors / total_neighbors
            if percent_similar < self.model.homophily:
                self.is_unhappy = True
            else:
                self.is_unhappy = False
        else:
            self.is_unhappy = False

        # If unhappy, move to a new random empty location
        if self.is_unhappy:
            self.model.grid.move_to_empty(self)
            self.model.unhappy_agents_count += 1


# --- 2. Model Definition ---
class SchellingModel(mesa.Model):
    """
    The main model for the Schelling Segregation simulation.
    
    Attributes:
        width, height: Grid dimensions.
        density: The fraction of cells that are occupied by agents.
        homophily: The minimum percentage of similar neighbors an agent needs to be happy.
    """
    def __init__(self, width=20, height=20, density=0.8, homophily=0.4):
        super().__init__()
        self.width = width
        self.height = height
        self.density = density
        self.homophily = homophily
        
        # Scheduler activates agents in a random order each step
        self.schedule = mesa.time.RandomActivation(self)
        
        # The grid where agents live. SingleGrid means max one agent per cell.
        self.grid = mesa.space.SingleGrid(width, height, torus=True)
        
        self.unhappy_agents_count = 0

        # Create agents
        # Iterate through each cell of the grid
        for _, pos in self.grid.coord_iter():
            if self.random.random() < self.density:
                # Assign agent type randomly (50/50 chance for type 0 or 1)
                agent_type = self.random.choice([0, 1])
                agent = SchellingAgent(self.next_id(), self, agent_type)
                self.grid.place_agent(agent, pos)
                self.schedule.add(agent)
                
        # DataCollector to track metrics over time
        self.datacollector = mesa.DataCollector(
            {"unhappy_agents": "unhappy_agents_count"}
        )

    def step(self):
        """
        Execute one step of the model.
        """
        self.unhappy_agents_count = 0  # Reset counter at the start of each step
        self.schedule.step()
        self.datacollector.collect(self)


# --- 3. Visualization and Server Setup ---
def agent_portrayal(agent):
    """
    Defines how agents will be drawn on the grid.
    """
    if agent is None:
        return
    
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.8, "Layer": 0}

    if agent.agent_type == 0:
        portrayal["Color"] = "dodgerblue"
    else:
        portrayal["Color"] = "tomato"
        
    return portrayal


# Grid visualization
canvas_element = mesa.visualization.CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# Chart to display the number of unhappy agents over time
chart_element = mesa.visualization.ChartModule(
    [{"Label": "unhappy_agents", "Color": "Black"}],
    data_collector_name='datacollector'
)

# Model parameters that can be changed via the web interface
model_params = {
    "homophily": mesa.visualization.Slider(
        "Homophily Threshold", 0.4, 0.0, 1.0, 0.05, "The minimum % of same-type neighbors to be happy"
    ),
    "density": mesa.visualization.Slider(
        "Agent Density", 0.8, 0.1, 1.0, 0.05, "Fraction of cells that are occupied"
    ),
    "width": 20,
    "height": 20,
}

# The server that runs the simulation and visualization
server = mesa.visualization.ModularServer(
    SchellingModel,
    [canvas_element, chart_element],
    "Schelling Segregation Model",
    model_params,
)

# Launch the server if this file is run directly
if __name__ == "__main__":
    server.launch()
