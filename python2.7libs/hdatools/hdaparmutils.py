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


def _prepname(str):
    """custom string formatting function for creating a legible label from a parm name
    takes an incoming label, and sets it to title case unless the 'word' is all caps"""
    parts = ()
    for part in str.split(" "):
        if not part.isupper():
            parts += (part.capitalize(),)
        else:
            parts += (part,)

    return " ".join(parts)


def findFolder(grp, folder_name, _out=()):
    """shorthand function for looking up the containing folders of a given folder label,
    returns the tuple of folder labels that locate the first found instance (depth first) of the given folder_name"""

    _tmp = _out

    for p in (t for t in grp.parmTemplates() if isinstance(t, hou.FolderParmTemplate)):

        _out += (p.label(),)

        if p.label() == folder_name:
            result = _out
        else:
            result = findFolder(p, folder_name, _out)
        if result:
            return result

        _out = _tmp


def folderHierarchy(ptg):
    """return the folders in a nodes interface as a hierarchy stored in a dictionary"""
    d = {}
    folders = (pt for pt in ptg.parmTemplates() if isinstance(pt, hou.FolderParmTemplate))
    for f in folders:
        d[f.label()] = folderHierarchy(f)
    return d


def explodeDictKeys(d, out_tuple=(), _parent_tuple=()):
    """return a tuple of tuples providing 'breadcrumbs' through nested dictionary keys - given:
    d = {
        some: {
            nested:{
                dictionary:
                    {}
                }
            },
            other_branch:{}
    }

    explodeDictKeys(d) #will return

    (('some',), ('some', 'nested'), ('some', 'nested', 'dictionary'), ('some', 'other_branch'))

    see also: folderHierarchy(), getSubFolders()
    """

    for k in d.keys():
        this_tuple = _parent_tuple + (k,)
        out_tuple += (this_tuple,)
        out_tuple = explodeDictKeys(d[k], out_tuple, _parent_tuple=this_tuple)

    return out_tuple


def getSubFolders(ptg, folder=(), include_queried=False):

    """Given a hou.ParmTemplateGroup and a tuple representing the queried folder return a tuple of tuples of all
    all contained 'sub-folders'.

    the include_queried argument specifies is we should include that queried folder in the result"""

    out = ()
    hierarchy = folderHierarchy(ptg)

    for f in explodeDictKeys(hierarchy):
        include = True

        if len(f) < len(folder):
            continue

        if not include_queried and len(f) == len(folder):
            continue

        for idx, s in enumerate(folder):

            if f[idx] == s:
                include = True
            else:
                include = False

        if include:
            out += (f,)

    return out


def createFolder(ptg, address):
    """create a folder in the given parm template group at the address specified
    This function accepts either a tuple of folder labels or a string using '/' to separate the folder names:
    createFolder(ptg, 'Top/Middle/Bottom')
    This function returns both the modified parm template group and the newly created folder parm template"""
    if isinstance(address, str):
        address = address.split("/")

    _address = address

    if ptg.findFolder(_address):
        return ptg, ptg.findFolder(address)

    target = ptg

    i = 1

    while ptg.findFolder(_address[:i]):
        target = ptg.findFolder(_address[:i])
        i += 1

    temp = hou.FolderParmTemplate(_address[-1].lower(), _address[-1])
    _address = _address[i - 1:-1]

    target_clone = None

    if isinstance(target, hou.FolderParmTemplate):
        target_clone = target.clone()

    for f in _address[::-1]:
        n = hou.FolderParmTemplate(f.lower(), f)
        n.addParmTemplate(temp)

        temp = n

    if target_clone:
        target_clone.addParmTemplate(temp)
        ptg.replace(target, target_clone)
    else:
        ptg.addParmTemplate(temp)

    return ptg, ptg.findFolder(address)

def promoteParm(parm, hda=None, folder=None, split_vectors=False, apply_to_definition=True, force=False, suppress_errors=True):
    """function to promote a given Parm or ParmTuple to it's containing HDA.

    parm
        can be either a hou.Parm or hou.ParmTuple. ParmTuples have the option to be split into separate sliders.
    hda (hou.Node)
        the asset to which the parm with be promoted
    folder (str)
        name of the destination folder
    split_vectors (bool)
        if set to True this will promote a given parm tuple into separate sliders of matching type
    apply_to_definition (bool)
        if set to True the parameter will be automatically added to the assets definition, otherwise it will be
        set to the given hda.parmTemplateGroup, the hda definition will have to be updated manually
    force (bool)
        grunt....
    suppress_errors (bool)
        burble..."""

    # check we have a valid hda to promote the parm to
    if not hda:
        hda = parm.node().parent()

    if not hda.isEditable():
        print("Parent node is not an editable hda")
        return

    if parm.node() not in hda.allSubChildren():
        print("Parm does not belong to a node inside the target asset...")
        return

    # promote the parm directly to the type definition
    if apply_to_definition:
        ptg_target = hda.type().definition()
    else:
        # or to the current unlocked instance
        ptg_target = hda

    ptg = ptg_target.parmTemplateGroup()

    # local variable to storer whether of not the incoming parm is a tuple
    # used later in the function when choosing a method to create channel references
    is_tuple = False

    # is it a Parm or ParmTuple?

    # --- CODE FOR PARM INSTANCE ---

    if isinstance(parm, hou.Parm):
        # if the parm is locked or hidden do nothing
        if parm.isLocked() or parm.isHidden():
            return

        tname = parm.node().name() + "_" + parm.name()
        tlabel = _prepname(parm.node().name().replace("_", " ") + " " + parm.name().upper())

        if hda.parm(tname):
            if force:
                ptg.remove(hda.parm(tname).parmTemplate())
            else:
                parm.deleteAllKeyframes()
                parm.set(hda.parm(tname))
                return

        pt = parm.parmTemplate().clone()
        pt.setName(tname)
        pt.setLabel(tlabel)
        pt.setNumComponents(1)

    # --- CODE FOR PARMTUPLE INSTANCE

    elif isinstance(parm, hou.ParmTuple):
        lock_count = 0
        unlocked = None

        # check that more than one Parm in the tuple is unlocked
        for p in parm:
            if p.isLocked():
                lock_count += 1
            else:
                unlocked = p

        if lock_count == len(parm) - 1:
            return promoteParm(unlocked, hda=hda, folder=folder, apply_to_definition=apply_to_definition, suppress_errors=suppress_errors, force=force)
        elif lock_count == len(parm) or unlocked is None:
            return

        is_tuple = True
        if split_vectors:
            for p in parm:
                promoteParm(p, hda=hda, folder=folder, apply_to_definition=apply_to_definition, suppress_errors=suppress_errors, force=force)
            return

        tname = parm.node().name() + "_" + parm.name()
        tlabel = _prepname(parm.node().name().replace("_", " ") + " " + parm.name())

        if ptg.find(tname):
            if force:
                ptg.remove(tname)
            else:
                for idx, p in enumerate(parm):
                    if p.isLocked():
                        hda.parmTuple(tname)[idx].lock(True)
                    else:
                        p.deleteAllKeyframes()
                        p.set(hda.parmTuple(tname)[idx])
                return

        pt = parm.parmTemplate().clone()
        pt.setName(tname)
        pt.setLabel(tlabel)

    else:
        if suppress_errors:
            print("Unrecognized type for " + str(parm) + "... skipping")
            return False
        else:
            raise TypeError("Unrecognized type for input")

    # remove the match transform action button
    tags = {
        'autoscope': pt.tags()['autoscope']
    }
    pt.setTags(tags)

    if folder:
        ptg, f = createFolder(ptg, folder)
        f_clone = f.clone()
        f_clone.addParmTemplate(pt)
        ptg.replace(f, f_clone)

    else:
        ptg.addParmTemplate(pt)

    ptg_target.setParmTemplateGroup(ptg)

    if is_tuple:
        for idx, p in enumerate(parm):
            if p.isLocked():
                hda.parmTuple(tname)[idx].lock(True)
            else:
                p.set(hda.parmTuple(tname)[idx])

    else:
        parm.deleteAllKeyframes()
        parm.set(hda.parm(tname))


def removeParms(parms, node=None, apply_to_definition=False):

    if not node:
        node = parms[0].node()

    if apply_to_definition:
        if not node.isEditable():
            raise hou.Error("Cannot apply to definition, node is not editable")
        target = node.type().definition()
    else:
        target = node

    ptg = target.parmTemplateGroup()
    for p in parms:
        if not ptg.find(p.parmTemplate().name()):
            continue

        ptg.remove(p.parmTemplate().name())
        for rp in p.parmsReferencingThis():
            rp.deleteAllKeyframes()

    target.setParmTemplateGroup(ptg)


def removeFolder(foldername, node, apply_to_definition=False):

    if apply_to_definition:
        if not node.isEditable():
            raise hou.Error("Cannot apply to definition, node is not editable")
        target = node.type().definition()
    else:
        target = node

    ptg = target.parmTemplateGroup()

    ptg.remove(ptg.findFolder(foldername))

    target.setParmTemplateGroup(ptg)


def moveToTop(parm, apply_to_definition=False):
    """move the given parm to the top of it's containing folder"""
    node = parm.node()

    if apply_to_definition:
        if not node.isEditable():
            raise hou.Error("Cannot apply to definition, node is not editable")
        target = node.type().definition()
    else:
        target = node

    ptg = target.parmTemplateGroup()
    pt = parm.parmTemplate()

    ptg.remove(pt.name())

    f = ptg.findFolder(parm.containingFolders())

    templates = f.parmTemplates()
    templates = (pt,) + templates

    f.setParmTemplates(templates)
    ptg.replace(ptg.findFolder(parm.containingFolders()), f)
    target.setParmTemplateGroup(ptg)


def addResetButton(node, folder, apply_to_definition=False, move_to_top=False):
    """add a reset button to a given folder within the target node"""
    if apply_to_definition:
        if not node.isEditable():
            raise hou.Error("Cannot apply to definition, node is not editable")
        target = node.type().definition()
    else:
        target = node

    ptg = target.parmTemplateGroup()

    if isinstance(folder, str):
        split_path = folder.split("/")
        if len(split_path) == 1:
            f_path = findFolder(ptg, folder)
        elif len(split_path) > 1:
            f_path = tuple(split_path)
    elif isinstance(folder, tuple):
        f_path = folder

    print(f_path)

    f = ptg.findFolder(f_path)

    script = """for p in kwargs['node'].parmsInFolder({0}):
    p.revertToDefaults()""".format(f_path)

    button_name = "reset_" + "_".join(f.lower().replace(" ", "_") for f in f_path)

    button = hou.ButtonParmTemplate(button_name, "Reset " + f.label())
    button.setScriptCallback(script)
    button.setScriptCallbackLanguage(hou.scriptLanguage.Python)

    f.addParmTemplate(button)

    ptg.replace(ptg.findFolder(f_path), f)
    target.setParmTemplateGroup(ptg)

    if move_to_top:
        moveToTop(node.parm(button_name), apply_to_definition=apply_to_definition)

    return node.parm(button_name)