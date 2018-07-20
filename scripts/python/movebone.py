def moveBoneTip(bone, pos, compensate=True):

	xform = bone.worldTransform()
	children = bone.outputs()
	child_xforms = []
	grandchild_xforms = []

	for c in children:
		child_xforms.append(c.worldTransform())
		grandchild_xforms.append(tuple(gc.worldTransform() for gc in c.outputs()))


	start_tip = hou.Vector3((0,0,-bone.evalParm("length"))) * xform
	root = xform.extractTranslates()

	diff_m = hou.hmath.buildTranslate(pos - start_tip)

	goal_dir = (pos - root).normalized()

	rot = hou.Vector3((0,0,-1)).matrixToRotateTo(goal_dir.multiplyAsDir(xform.inverted()))

	bone.setWorldTransform(rot * xform)

	bone.parm("length").set((pos - root).length())

	for idx, c in enumerate(children):
		if c.type().name() != "bone":
			continue

		start_tip = hou.Vector3((0,0,-c.evalParm("length"))) * xform
		goal_dir = (start_tip - pos).normalized()
		rot = hou.Vector3((0,0,-1)).matrixToRotateTo(goal_dir.multiplyAsDir(child_xforms[idx].inverted()))

		bone2.setWorldTransform(rot * child_xforms[idx] * diff_m)
