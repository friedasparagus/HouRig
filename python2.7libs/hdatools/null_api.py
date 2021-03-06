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


# The idea here is simply to provide a more convenient scripting interface for a given node type. Although
# this can be easily extended to provide customized behaviour when we want to consider relationships or parameters
# as being a 'property' of a given type.
#
# An example being that a Bone has length as a property not just a parameter (as with an ObjNode)
# Another example is that an FKControl has something that it controls, implicit to it's definition, whilst a null can
# be any thing!
#
# It also makes writing code that builds atop this to be must more concise and semantic
#
# null1.geoscale = null2.geoscale * 1.5
#
# rather than
#
# null1.parm("geoscale").set(null2.evalParm("geoscale") * 1.5)


# this file was generated by api_gen.generate_properties()

class Null(object):
    def __init__(self, node):
        self.node = node

    @property
    def geoscale(self):
        return self.node.evalParm("geoscale")
    
    @geoscale.setter
    def geoscale(self, value):
        self.node.parm("geoscale").set(value)  

    @property
    def controltype(self):
        return self.node.evalParm("controltype")
    
    @controltype.setter
    def controltype(self, value):
        self.node.parm("controltype").set(value)  

    @property
    def orientation(self):
        return self.node.evalParm("orientation")
    
    @orientation.setter
    def orientation(self, value):
        self.node.parm("orientation").set(value)  

    @property
    def shadedmode(self):
        return self.node.evalParm("shadedmode")
    
    @shadedmode.setter
    def shadedmode(self, value):
        self.node.parm("shadedmode").set(value)  

    @property
    def dcolor(self):
        return self.node.evalParmTuple("dcolor")

    @dcolor.setter
    def dcolor(self, value):
        self.node.parmTuple("dcolor").set(value)  
