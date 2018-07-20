import hou



def keyParmTuple(tup, frame, value=None, onlykeyed=False):

    """Set keys on all parms within a given parm tuple."""

    is_string = isinstance(tup.parmTemplate(), hou.StringParmTemplate)

    # Removing support for string parms temporarily until everything else is locked down
    if is_string:
        return

    with hou.undos.group("Key ParmTuple"):

        if not isinstance(value, tuple):
            value = (value,) * len(tup)

        for idx, p in enumerate(tup):
            if onlykeyed and not p.keyframes():
                continue

            if is_string:
                key = hou.StringKeyframe()
            else:
                key = hou.Keyframe()

            if len(value) > idx and value[idx] is not None:
                if is_string:
                    key.setExpression(value[idx])
                else:
                    key.setValue(value[idx])
            else:
                if is_string:
                    key.setExpression(p.evalAtFrame(frame))
                else:
                    key.setValue(p.evalAtFrame(frame))

            key.setFrame(frame)

            if not is_string:
                key.setInSlopeAuto(True)
                key.setSlopeAuto(True)
            p.setKeyframe(key)

    return key


def moveParmTupleKey(tup, cur_frame, new_frame):

    with hou.undos.group("Move Parm Tuple Keyframe"):
        for p in tup:
            # as we're querying a frame range of length 1, we can safely use the [0] index of the result
            k = p.keyframesInRange(cur_frame, cur_frame)[0]

            k.setFrame(new_frame)

            p.deleteKeyframeAtFrame(cur_frame)
            p.setKeyframe(k)


def tweenParmTuple(tup, valuebias=0.5, timingbias=0.5, ref_frame=None, keyatref=True):

    print(tup)

    if not ref_frame:
        ref_frame = hou.frame()

    with hou.undos.group("Tween ParmTuple"):

        prevframes = ()
        nextframes = ()

        for p in tup:
            if p.keyframesBefore(ref_frame):
                prevframes += (p.keyframesBefore(ref_frame)[-1],)
            if p.keyframesAfter(ref_frame):
                nextframes += (p.keyframesAfter(ref_frame)[0],)

        if not prevframes or not nextframes:
            raise hou.Error("no surrounding keys")

        k1 = max(prevframes)
        k2 = min(nextframes)

        if isCompleteRotate(tup):
            out_v = slerpParmTuple(tup, k1.frame(), k2.frame(), valuebias)
        else:
            out_v = lerpParmTuple(tup, k1.frame(), k2.frame(), valuebias)

        if keyatref:
            out_f = ref_frame
        else:
            out_f = k1.frame() + ((k2.frame() - k1.frame()) * timingbias)

        return keyParmTuple(tup, int(out_f), out_v, onlykeyed=True)

# class rotateKeyframe:
#     def __init__(self):


def lerpKeys(k1, k2, bias):
    """:type k1: hou.Keyframe
    :type k2: hou.Keyframe"""

    diff = k2.value() - k1.value()

    k1.setValue(k1.value() + (diff * bias))

    return k1


def lerpParmTuple(tup, t1, t2, bias):
    """lerp the given parmTuple between the two given frames"""

    out = ()

    v1 = tup.evalAtFrame(t1)
    v2 = tup.evalAtFrame(t2)

    for idx, p in enumerate(tup):
        out_v = v1[idx] + ((v2[idx] - v1[idx]) * bias)
        out += (out_v,)

    return out


def slerpParmTuple(tup, t1, t2, bias):
    if not isCompleteRotate(tup):
        raise hou.Error(str(tup) + " is not a value set of euler rotates")

    r1 = tup.evalAtFrame(t1)
    r2 = tup.evalAtFrame(t2)

    q1 = hou.Quaternion(hou.hmath.buildRotate(r1))
    q2 = hou.Quaternion(hou.hmath.buildRotate(r2))

    outq = q1.slerp(q2, bias)

    return tuple(outq.extractEulerRotates())

# When interpolating a parm that's part of a full set of rotates we want to know if the full set of rotates is available
# if so, perform slerping of their values. The conditions for this are as follows:
# 1) The given parm is part of a tuple of size 3
# 2) The other components of this tuple are unhidden and unlocked
# 3) All 3 components reference the same parmTuple and this tuple is named 'r'

# Situations that need handling are:
# 1) The given parm has a key set but one or more of the other components do not - do we support partial keys?
# 2) Having deduced whether or not the full rotates are available, how do we handle these parms from now on?
# On first sight we want to be passing an object that encapsulates all 3 components as a 'unit' for operations like
# getting/setting keyframes or performing the slerping.

def isCompleteRotate(tup):

    """Returns is the given parm tuple represents a full set of Euler Rotates"""

    bool = True

    if len(tup) < 3:
        bool = False

    for p in tup:
        if p.isHidden() or p.isLocked():
            bool = False

        if tup.node().isLockedHDA():

            # take the first component as sample and get all referenced parms of name 'r'
            # then iterate over remaining components and check for common parm tuple
            refs = (ref.tuple() for ref in tup[0].parmsReferencingThis() if ref.tuple().name() == "r")

            for p in tup:
                _tmprefs = ()

                for p in p.parmsReferencingThis():
                    if p.tuple() in refs:
                        _tmprefs += (p.tuple(),)

                refs = _tmprefs

            if not refs:
                bool = False


    return bool


def keysAtFrame(node, frame=hou.frame()):

    result =()

    for p in node.parms():
        if p.keyframesInRange(frame, frame):
            result += (p,)

    return result

def tupleKeyedIndices(tup):
    indices = ()
    for idx, p in enumerate(tup):
        if p.keyframes():
            indices += (idx,)

    return indices

def setInterpolation(tup, interp):
    for p in tup:
        keys = p.keyframes()

        for k in keys:
            k.setExpression(interp + "()", hou.exprLanguage.Hscript)

        p.setKeyframes(keys)

