-- tup.creategitignore()

gen_stls = tup.foreach_rule('*.stl.blend', blender .. '%f -b --python $(TOP)/tools/export_stl.py -- --outfile %o', '$(STL_FOLDER)/%B')
gen_blends = tup.foreach_rule(gen_stls, '^o^ ' .. blender .. ' -b --python $(TOP)/tools/import_stl.py -- --infile %f --outfile %o', '$(GEN_BLEND_FOLDER)/%B.blend')
gen_gcode = tup.foreach_rule(gen_stls, 'python3 $(TOP)/tools/export_gcode.py %f %o', '$(STL_FOLDER)/%B.gcode')
part_details = tup.foreach_rule(gen_blends, blender .. '%f -b --python $(TOP)/tools/generate_part_details.py -- --outfile %o', '$(STL_FOLDER)/%B-details.txt')
part_images = tup.foreach_rule(gen_blends, blender .. ' $(TOP)/tools/part_template.blend -b --python $(TOP)/tools/render_part.py -- --infile %f --outfile %o --resolution_percent @(RENDER_RESOLUTION_PERCENT) --render_device @(RENDER_DEVICE) --project_name="$(PROJECT_NAME)" --part_name %B --part_version $(VERSION)', '$(GEN_IMAGE_FOLDER)/%B.jpg')

gen_images = tup.foreach_rule('*.png.blend', blender .. '-b %f --python $(TOP)/tools/render_blend.py -- --outfile %o --resolution_percent @(RENDER_RESOLUTION_PERCENT) --render_device @(RENDER_DEVICE)', '$(GEN_IMAGE_FOLDER)/%B')
gen_images = tup.foreach_rule('*.jpg.blend', blender .. '-b %f --python $(TOP)/tools/render_blend.py -- --outfile %o --resolution_percent @(RENDER_RESOLUTION_PERCENT) --render_device @(RENDER_DEVICE)', '$(GEN_IMAGE_FOLDER)/%B')

