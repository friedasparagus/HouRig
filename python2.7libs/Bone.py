import hou

# construct a python Bone object by calling the constructor with an existing bone in the scene
# original hou.ObjNode object can be accessed through Bone.node

# all @properties are pythonic getters/setters and are used like so: some_bone.length -> returns the current length
# some_bone.length = 2.4 -> sets the length to 2.4

# The second class IK_Chain, provides access to all bones that share a common IK solver. An instance can be returned by
# accessing the ik_chain property of a Bone instance if you need persistence: some_chain = some_bone.ik_chain
# otherwise you can perform chain-wide actions like IK->FK matching by calling some_bone.ik_chain.ik_to_fk()
# this could be handy for adding a button to a bone object's interface that calls the method (i.e. every bone in the
# chain can perform the matching from it's own interface)


def io_sort(sel, reverse=True):
    def io_compare(x, y):
        return 1 if x in y.inputAncestors() else -1
    return sorted(sel, io_compare, reverse=reverse)

class Bone(object):
    def __init__(self, bone_obj=None, context=None):
        """
        :param bone_obj:
        :type bone_obj : hou.ObjNode
        """
        if bone_obj is None:
            if context is None:
                context = hou.ui.selectNode()
            bone_obj = hou.node(context).createNode("bone")

        if bone_obj and bone_obj.type().name() != "bone":
            raise ValueError

        self.name = bone_obj.name()
        self.node = bone_obj
        self.prev_child = None
        self.prev_input = None

    @property
    def xform(self):
        return self.node.worldTransform()

    # TODO: This should be moved somewhere else really. Useful function for setting a new world xform whilst moving the
    # delta into the preTransform instead of the parms. The previous xform parm values are kept intact.

    @xform.setter
    def xform(self, world_xform):
        self.node.setPreTransform(
            self.node.parmTransform().inverted() *
            world_xform *
            self.node.parentAndSubnetTransform().inverted())

    @property
    def rotate_order(self):
        return self.node.parm("rOrd").evalAsString()

    @property
    def length(self):
        return self.node.parm("length").eval()

    @length.setter
    def length(self, length):
        self.node.parm("length").set(length)

    @property
    def root(self):
        return self.xform.extractTranslates()

    @property
    def tip(self):
        len = self.length
        v = hou.Vector3((0,0,-len))

        return v * self.xform

    @property
    def parent(self):
        try:
            input_node = self.node.inputs()[0]
            if input_node.type().name() == "bone":
                input_node = Bone(input_node)
                return input_node
            else:
                return self.node.inputs()[0]
        except:
            return None

    @property
    def child(self):
        try:
            output = self.node.outputs()[0]
            if output.type().name() == "bone":
                output = Bone(output)
                return output
            else:
                return None
        except:
            return None

    @property
    def grandchild(self):
        if self.child:
            return self.child.child
        return None

    def disconnect_input(self):
        self.prev_input = self.parent
        self.node.parm("keeppos").set(1)
        self.node.setFirstInput(None)

    def reconnect_input(self):
        self.node.setFirstInput(self.prev_input.node)
        self.node.parm("keeppos").set(0)

    def move_root(self, target, compensate=True):
        with hou.undos.group("Move Bone Root"):
            target = hou.Vector3(target)

            translate_mat = hou.hmath.buildTranslate(target - self.root)

            if compensate:
                if isinstance(self.parent, Bone):
                    self.parent.move_tip(target)
                else:
                    cache_child_xform = self.child.xform
                    cache_tip = self.tip
                    self.parent.setWorldTransform(self.parent.worldTransform() * translate_mat)
                    self.move_tip(cache_tip, False, cache_child_xform)

            else:
                self.parent.setWorldTransform(self.parent.worldTransform() * translate_mat)

    def move_tip(self, target, compensate=True, child_xform=None):
        with hou.undos.group("Move Bone Tip"):
            if self.child:
                grandchild_xform = self.grandchild.xform if self.grandchild else None

                cache_child = self.child
                cache_child_tip = self.child.tip
                cache_child_xform = self.child.xform

            target = hou.Vector3(target)

            vec1 = (self.tip - self.root).normalized()
            vec2 = (target - self.root).normalized()

            diff = (target - self.root) - (self.tip - self.root)

            vec1 *= hou.hmath.buildRotate(self.xform.extractRotates()).inverted()
            vec2 *= hou.hmath.buildRotate(self.xform.extractRotates()).inverted()

            mat = vec1.matrixToRotateTo(vec2)
            self.debug_mat = mat

            self.length = (target - self.root).length()

            new_world_xform = mat * self.xform

            self.xform = new_world_xform

            if child_xform:
                self.child.xform = child_xform
                return

            if compensate and self.child:
                mat_translate = hou.hmath.buildTranslate(diff)
                self.child.xform = cache_child_xform * mat_translate
                self.child.move_tip(cache_child_tip, child_xform=grandchild_xform if grandchild_xform else None)


    @property
    def ik_solver(self):
        for n in self.node.references():
            if n.type().name() == "inversekin":
                return n
        return False

    @property
    def ik_chain(self):
        kin = self.ik_solver

        if not kin:
            return False

        tup = tuple(Bone(n) for n in kin.dependents() if n.type().name() == "bone")

        # this is also bad! at the moment this and downstream methods assume the result of hou.Node.dependents()
        # to be consistently ordered in terms of hierarchy...
        # TODO implement sorting of a node tuple by hierarchy
        tup = tup[::-1]

        return IK_Chain(tup)

    @property
    def fk_rotates(self):
        return self.node.parmTuple("r").eval()

    @fk_rotates.setter
    def fk_rotates(self, vec3):
        for i, p in enumerate(self.node.parmTuple("r")):
            if not p.isLocked():
                p.set(vec3[i])

    # this doesn't really belong in this file, but I need it NOW!
    def ik_tracks(self):
        kin = self.ik_solver

        out_tracks = ()

        for track in kin.tracks():
            strip_front = track.name().split("/")[-1]
            strip_channel = strip_front.split(":")[0]
            if strip_channel == self.node.name():
                out_tracks += (track,)

        return out_tracks

    @property
    def ik_rotates(self):
        kin = self.ik_solver

        in_blend = kin.parm("blend").eval()
        kin.parm("blend").set(1)

        tracks = self.ik_tracks()
        values = ()

        for t in tracks:
            values += (t.eval(),)

        kin.parm("blend").set(in_blend)

        return values


class IK_Chain(object):
    def __init__(self, bones):
        self.bones = io_sort(bones);
        # don't like this... need to do some checking that all bones belong to the same solver in case an instance is created directly (rather than by and instance of the Bone class)
        self.solver = bones[0].ik_solver
        self.length = len(bones)
        self.end_goal = self.solver.node(self.solver.parm("endaffectorpath").eval())
        self.twist_goal = self.solver.node(self.solver.parm("twistaffectorpath").eval())

    def fk_to_ik(self):
        for b in self.bones:
            b.fk_rotates = b.ik_rotates

    def ik_to_fk(self):
        if self.length > 2:
            raise hou.Error("Only two-bone chains are currently supported for IK->FK matching")

        self.solver.parm("blend").set(0)

        self.set_end_pos()
        self.set_twist_pos()

    def set_twist_pos(self, dist=None):
        if not self.twist_goal:
            return False

        bone1 = self.bones[0]
        bone2 = self.bones[1]

        # this is given as a sensible distance to place the twist goal from the end of the bone... may revise
        if not dist:
            dist = hou.Vector3(bone1.tip - bone1.root).length()

        # get vectors for computing cross product
        a = hou.Vector3(bone1.tip - bone1.root).normalized()
        b = hou.Vector3(bone2.tip - bone2.root).normalized()
        c = hou.Vector3(bone1.root - bone2.tip).normalized()

        normal = a.cross(b)

        pole_dir = normal.cross(c)

        new_pos = bone1.tip + (pole_dir * dist)
        mat = hou.hmath.buildTranslate(new_pos)

        self.twist_goal.setWorldTransform(mat)

    def set_end_pos(self, offset=0.001):
        offset_vec = hou.Vector3(self.bones[1].tip - self.bones[1].root).normalized() * offset

        end_pos = hou.hmath.buildTranslate(self.bones[1].tip + offset_vec)
        self.end_goal.setWorldTransform(end_pos)

# best fit from points:
# pts = tuple(pt.position() for pt in geo.points())
    # u, s, v = numpy.linalg.svd(pts)
# v[2] is the normal of our best fit plane
