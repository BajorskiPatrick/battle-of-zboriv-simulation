
# Bitwa pod Żbarażem

A simulation project implementing battle scenarios using agent-based modeling.

## Installation

1. Create a virtual environment using Python 3.11:
```bash
uv venv -p python3.11
```

2. Activate the virtual environment:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

## Usage

Run the simulation:
```bash
python main.py
```

The application will start and open a socket connection for communication.

## Project Structure
```
.
├── README.md
├── main.py
├── requirements.txt
├── src
│   ├── models
│   │   ├── Commander.py
│   │   ├── Rider.py
│   │   ├── SoldierAgent.py
│   │   ├── TacticalBattleModel.py
│   │   ├── TerrainPatch.py
│   │   └── Warrior.py
│   └── utils
│       └── agent_portrayal.py
└── structure.txt

```