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


def generate_properties(class_name, parms_list, tuples_list, file_path=None):
    out_str = """class {0}(object):
    def __init__(self, node):
        self.node = node
""".format(class_name)

    for p in parms_list:
        template = """
    @property
    def {0}(self):
        return self.node.evalParm("{0}")
    
    @{0}.setter
    def {0}(self, value):
        self.node.parm("{0}").set(value)  
"""
        out_str += template.format(p)

    for t in tuples_list:
        template = """
    @property
    def {0}(self):
        return self.node.evalParmTuple("{0}")

    @{0}.setter
    def {0}(self, value):
        self.node.parmTuple("{0}").set(value)  
"""
        out_str += template.format(t)

    if file_path:
        f = open(file_path, "w")
        f.write(out_str)
        f.close()
    else:
        return out_str