# MIT License
#
# Copyright (c) 2018 Henry Sebastian Dean
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import hou
import null_api
import hdaparmutils


class FKControl(null_api.Null):
    target_node = None  # type: hou.ObjNode
    active_parms = ()

    def __init__(self, target_node, mask=511, folder=None):
        with hou.undos.group("Create FK control"):
            self.target_node = target_node

            name = self.target_node.name() + "_FK"

            node = target_node.parent().createNode("null", name)
            null_api.Null.__init__(self, node)

            self.node.setFirstInput(self.target_node.inputs()[0])
            self.node.setWorldTransform(self.target_node.worldTransform())
            self.node.moveParmTransformIntoPreTransform()
            self.node.parm("rOrd").set(self.target_node.evalParm("rOrd"))

            if isinstance(mask, str):
                mask = int(mask, 2)

            self.connectparms(mask)
            self.promoteTRS(folder=folder)

    def connectparms(self, mask=511):

        parm_mask = format(mask, "b").zfill(9)
        parms = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")

        for i, p in enumerate(parms):
            target_parm = self.target_node.parm(p)
            if parm_mask[i] is "1" and not target_parm.isLocked() or target_parm.isHidden():
                target_parm.set(self.node.parm(p))
                self.active_parms += (self.node.parm(p),)
            else:
                target_parm.lock(True)
                self.node.parm(p).lock(True)

    def promoteTRS(self, mask=511, lock_unused=True, split_vectors=(), folder=None):
        parms = (
            self.node.parmTuple("t"),
            self.node.parmTuple("r"),
            self.node.parmTuple("s")
        )

        for p in parms:
            hdaparmutils.promoteParm(p, folder=folder, apply_to_definition=False)

