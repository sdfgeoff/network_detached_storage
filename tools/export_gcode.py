import sys
import os
import subprocess

from pathlib import Path
tools_folder = Path(__file__).parent.absolute()

SLICER = "prusa-slicer"

SLICER_CONFIG_FILE = tools_folder / "SnapmakerA350PLA.ini"

in_file_path = sys.argv[1]
out_file_path = sys.argv[2]

command = [
    SLICER, 
    "--gcode", 
    "--load", str(SLICER_CONFIG_FILE), 
    "--output", out_file_path, 
    "--config-compatibility", "disable",
    in_file_path,
    
]
print(' '.join(command))
try:
    subprocess.run(command, check=True)
except:
    exit(1)
