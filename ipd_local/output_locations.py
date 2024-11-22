"""This submodule defines the locations of output files for the simulation."""

# json file of the raw output of the simulation (scores and results of every single round)
# this is updated every time the simulation is run, so it only stores results of the latest game
# this is stored as an actual file so that future features may allow user to see round-by-round data easily
RAW_OUT_LOCATION = "./latest_raw_out.json"

# json file of the specifications of the latest simulation
# like the raw output, it only stores the latest run
SPECS_JSON_LOCATION = "./latest_specs.json"

# this is where all issues that arise when the simulation is run are logged
# helps user identify which students need to fix their code, and how
# refreshed every run
PROBLEMS_LOG_LOCATION = "./ipd.log"

# list of functions that have issues
# refreshed when simulation is run with RELOAD_BLACKLIST = True --> list of all the functions that we know are faulty
BLACKLIST_LOCATION = "./blacklist.txt"
