import bpy
import argparse
import sys
import traceback
import os
import logging
sys.dont_write_bytecode = True

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import render

SCALE = 0.1

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--outfile', help="Render to here", required=True)
    parser.add_argument('--infile', help="Use objects from here", required=True)
    parser.add_argument('--resolution_percent', help="Resolution percent as an int", type=int, required=True)
    parser.add_argument('--render_device', help="use the string: 'CPU' or 'GPU'", type=str, required=True)
    parser.add_argument('--project_name', help="The name of the project", type=str, required=True)
    parser.add_argument('--part_name', help="The name of the part", type=str, required=True)
    parser.add_argument('--part_version', help="The version number", type=str, required=True)
    config = parser.parse_args(args)
    full_outpath = os.getcwd() + '../' + config.outfile
    full_inpath = os.getcwd() + '../' + config.infile

    # Link in the collection from the other blend
    with bpy.data.libraries.load(full_inpath) as (data_from, data_to):
        data_to.collections = data_from.collections

    #link object to current scene
    if len(data_to.collections) != 1:
        raise Exception("Expected exactly one collection")

    collection = data_to.collections[0]

    # Replace objects in this blend
    for obj in bpy.data.objects:
        if obj.name.startswith("REPLACE"):
            obj.instance_type = "COLLECTION"
            obj.instance_collection = collection
            obj.scale = [SCALE]*3
    bpy.data.objects["Project"].data.body = config.project_name
    bpy.data.objects["DrawingName"].data.body = config.part_name
    bpy.data.objects["VersionHash"].data.body = config.part_version

    render.render(full_outpath, config.resolution_percent, config.render_device)


def run_function_with_args(function):
    arg_pos = sys.argv.index('--') + 1
    try:
        function(sys.argv[arg_pos:])
    except:
        print("ERROR")
        traceback.print_exc()
        sys.exit(1)

    print("SUCCESS")
    sys.exit(0)


if __name__ == "__main__":
    run_function_with_args(main)
