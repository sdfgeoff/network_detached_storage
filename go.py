import os
from tools.upload_to_octoprint import upload_file


PROJECT_NAME = "Network Detached Storage"


# Build all the files
res = os.system('tup')
if res != 0:
    print("Building Failed")
    exit(1)

# Upload to octoprint
GCODE_FOLDER = 'generated/stl'
gcode_files =[f for f in os.listdir(GCODE_FOLDER) if f.endswith('.gcode')]

for filename in gcode_files:
    upload_file(f'{PROJECT_NAME}/{filename}', os.path.join(GCODE_FOLDER, filename))



