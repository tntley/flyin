*This project has been created as part of the 42 curriculum by tanrandr*

# Fly-in

## Description

`Fly-in` is a rouing program that aims to **navigate efficiently a fleet of drones from a starting zone to an ending zone** across a network of connected zones. The system aims for all the drones to reach the designated goal in **as few simulation turns as possible**, while complying to **a set of movement constraints**.

### The network

The network, or `Graph`, as refered to across the source files, is made up of Zones and Connections linking said zones to each other, ensuring that there's a viable route for the fleet to reach the goal.

Zones and connections in-betweens are defined based on a set of characteristics :
- **Capacities** : each zone and connection has a maximum number of drones that can occupy said zone or capacity simultaneously. If not specified, the capacity efaults to 1 drone.
- **Type**: some zones are slower to enter, if they are restricted ; other zones might be blocked entirely, while some others are considered priorities in the pathfinding process. The type of the zone also influences its entry cost. A normal zone and a priority zone will cost 1 turn to a drone trying to access it, while a restricted zone requires 2 turns.
- **Colors**: zones can be defined with custom colors that will be displayed throughout the colored terminal output if said color finds a match in a predefined ANSI dictionary. Otherwise, the color will simply default to the terminal's.

### How it works
To put it simply, the program reads and parses a map file fed to it through the shell command line, plans a route for every drone in the fleet, checks the drafted plan against the set of movement constraints with an independent simulation, and then prints the movements turn by turn. An optional colored display shoes the state progression of every zone after each turn throughout the simulation.

### The map file content
The map file, aka the actual base of the network navigation for the fleet of drones, is one of the main foundations of this program's operation. The file is bonded by a set of strict rules regarding the format of its content, that make or break the file :
- The first line of the file must be **nb_drones: number** with a number greater than 0.
- A Zone declaration must look like : **hub: name x y [metadata]**. Metadatas are optional and the brackets should only be included if actual metadatas exist.
- Zone metadatas might include :
  - the Zone type, as **[zone=restricted/normal/priority]**. It defaults to normal if not specified.
  - the color : **[color=blue]**. Any one string word will be admitted.
  - the capacity : **[max_drones=2]**.
- A Connection declaration must be formatted as followed : **connection: name1-name2 [metadata]**.
- Connection metadatas might include :
  - the capacity, as **[max_link_capacity=3]**
- Given the name format of a connection linking two zones, a Zone's name shall not include a dash (-) in it.

Hereby an example of a valid map file :

```txt
# Easy Level 2: Simple fork with two paths
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: junction 1 0 [color=yellow max_drones=2]
hub: path_a 2 1 [color=blue]
hub: path_b 2 -1 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-junction [max_link_capacity=2]
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

## Instructions

**Requirements** :
- Python 3.10 or later;
- `pip` as the package manager. The requirements.txt file locate at the root of the project repository lists a few dependencies to be installed to ensure the `make` targets work properly.

Install dependencies and create a .venv:
```bash
make install
```

Run the program on a map file:
```bash
make run ARGS="maps/easy/01_linear_path.txt"
```

To toggle the colored terminal output option, add `--visual` to the arguments:
```bash
make run ARGS="maps/easy/01_linear_path.txt --visual"
```

Other useful `make` targets include:
- `make debug` : run under `pdb` (`python -m pdb main.py <mapfile_path>`)
- `make lint` / `make lint-strict` : `flake8` + `mypy` (`flake8-docstrings` checks PEP 257 compliance against the numpy model)
- `make clean` : remove `__pycache__`, `.mypy_cache`, and the virtualenv

Alternatively, it is also possible to run the program against a map file without make:

```bash
python3 main.py maps/easy/01_linear_path.txt [--visual]
```

For the sake of organization and separation, the required ouptut (the turn lines) are printed on standard output while the visual display are sent to standard error. This design choice was made so that running the following command :
```bash
python3 main.py maps/easy/01_linear_path.txt --visual > result.txt
```
would only save the turn lines (the required output) to the pointed file while keeping the colored display on the terminal.
