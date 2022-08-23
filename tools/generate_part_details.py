""" Checks the mesh in a blend file for watertightness. Generates a summary
including the mass of the part """


import bpy
import argparse
import sys
import traceback
import os
import logging
import json


sys.dont_write_bytecode = True

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import render

SCALE = 0.1

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--outfile', help="Generate summary here", required=True)
    config = parser.parse_args(args)
    full_outpath = os.path.join(os.getcwd(), config.outfile)

    from addon_utils import enable
    import object_print3d_utils.report
    enable("object_print3d_utils")

    output_data = {}

    # Tolerances
    bpy.context.scene.print_3d.thickness_min = 0.01

    # Check solidity
    bpy.ops.mesh.print3d_check_solid()
    for text, data in object_print3d_utils.report._data:
        field, val = text.split(": ")
        val = int(val)
        if val != 0:
            print("Solidity check failed with {}".format(text))
            exit(1)

    # Check self-intersections
    # This generates a lot of false-positives on thin faces
    # ~ bpy.ops.mesh.print3d_check_intersect()
    # ~ for text, data in object_print3d_utils.report._data:
        # ~ field, val = text.split(": ")
        # ~ val = int(val)
        # ~ if val != 0:
            # ~ print("Intersection check failed with {}".format(text))
            # ~ exit(1)

    # Generate some stats
    bpy.ops.mesh.print3d_info_volume()
    for text, data in object_print3d_utils.report._data:
        field, val = text.split(": ")
        assert field == "Volume"
        val, unit = val.split(" ")
        assert unit == "mm³", f"Unit was {unit}"
        output_data["volume_cm3"] = float(val) * 0.001

    bpy.ops.mesh.print3d_info_area()
    for text, data in object_print3d_utils.report._data:
        field, val = text.split(": ")
        assert field == "Area"
        val, unit = val.split(" ")
        assert unit == "mm²"
        output_data["surface_area_cm2"] = float(val) * 0.01

    part_volume = output_data["volume_cm3"]
    perimeters_volume = output_data["surface_area_cm2"] * 0.1 # aproxximately 0.1cm perimeter thickness
    if part_volume < perimeters_volume:
        approx_material_volume = part_volume
    else:
        remaining_volume = part_volume - perimeters_volume
        approx_material_volume = perimeters_volume + remaining_volume * 0.15 # 15% infill

    approx_material_volume = min(approx_material_volume, output_data["volume_cm3"]) # If this is a thin part, there

    approx_weight = approx_material_volume * 1.24  # PLA is 1.24g/cm3
    approx_cost = approx_weight /1000 * 46  # Cost of 1kg of filament is about $46 from my local store

    output_data["approx_material_volume_cm3"] = approx_material_volume
    output_data["approx_weight_grams"] = approx_weight
    output_data["approx_cost"] = approx_cost






    with open(full_outpath, 'w') as out_file:
        json.dump(output_data, out_file, indent=2)


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
