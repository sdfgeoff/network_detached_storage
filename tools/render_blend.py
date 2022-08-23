import bpy
import argparse
import sys
import traceback
import os
import logging
sys.dont_write_bytecode = True

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import render

def main(args):
	parser = argparse.ArgumentParser()
	parser.add_argument('--outfile', help="Render to here", required=True)
	parser.add_argument('--resolution_percent', help="Resolution percent as an int", type=int, required=True)
	parser.add_argument('--render_device', help="use the string: 'CPU' or 'GPU'", type=str, required=True)
	config = parser.parse_args(args)
	full_outpath = bpy.path.abspath('//' + config.outfile)

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
