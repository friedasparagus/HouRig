# Copyright 2018 Henry Sebastian Dean

import hou, toolutils
from PySide2 import QtWidgets, QtGui, QtCore

# change the threshold to set how much of an influence on a given primitive the
# cregion will need to be displayed in the list
THRESHOLD = 0.01

class ChoiceButton(QtWidgets.QPushButton):
    def __init__(self, label):
        super(ChoiceButton, self).__init__(label.replace("/cregion 0", ""))
        self.target = label
        
        self.defstyle = "background: #454545; color: #dddddd; border-radius: 5px"
        self.hoverstyle = "background: #888888; color: #dddddd; border-radius: 5px"
        
        self.setStyleSheet(self.defstyle)
        self.setMouseTracking(True)
    
    def mousePressEvent(self, e):
        self.parentWidget().sop.parm("cregion").set(self.target)
        self.parentWidget().close()
        
    def mouseMoveEvent(self, e):
        self.setStyleSheet(self.hoverstyle)
        
    def leaveEvent(self, e):
        self.setStyleSheet(self.defstyle)
        
class weightDisplay(QtWidgets.QLabel):
    def __init__(self, weight):
        super(weightDisplay, self).__init__("{0:.4f}".format(weight))
        
        self.weight = weight
        
        self.setStyleSheet("color: black; background: transparent")
        self.setFixedWidth(100)
        
    def paintEvent(self, paintEvent):
        painter = QtGui.QPainter(self)
        
        pen = QtGui.QPen(QtGui.QColor.fromRgb(0,0,0))
        brush = QtGui.QBrush(QtGui.QColor.fromRgb(200, 120,0))
        
        bar_width = 100 * self.weight
        
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(brush)
        painter.drawRect(0, 0, bar_width, self.rect().height())
        
        painter.setPen(pen)
        
        painter.drawText(self.rect(), QtCore.Qt.AlignVCenter, "{0:.4f}".format(self.weight))
        
        
class cregionDialog(QtWidgets.QDialog):
    def __init__(self, parent, kwargs):
        super(cregionDialog, self).__init__(parent)
        
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(125,125,125, 50%)")
        
        self.sop = kwargs["node"]
        
        layout = QtWidgets.QVBoxLayout()
        
        for idx, c in enumerate(kwargs["choices"]):
            line = QtWidgets.QHBoxLayout()
            button = ChoiceButton(c)
            button.setFixedWidth(200)
            weight = weightDisplay(kwargs["weights"][idx])
    
            line.addWidget(button)
            line.addWidget(weight)
            layout.addLayout(line)
        
        self.setLayout(layout)
        self.adjustSize()
        
    def close(self):
        with hou.undos.disabler():
            toolutils.sceneViewer().enterCurrentNodeState()
        self.setParent(None)
        
    def reject(self):
        self.close()
        
    def paintEvent(self, paintEvent):
        painter = QtGui.QPainter(self)
        
        c = QtGui.QColor.fromRgbF(1,1,1,0.5)
        brush = QtGui.QBrush(c)
        
        painter.setBrush(brush)
        
        painter.drawRoundedRect(self.rect(), 10, 10)
        
    def mousePressEvent(self, e):
        self.close()
        

def cregionFromSurface():
    sv = toolutils.sceneViewer()
    gv = sv.curViewport()
    
    #sv.enterCurrentNodeState()

    if hou.selectedNodes() and hou.selectedNodes()[0].type().name() == "capturelayerpaint":
        with hou.undos.disabler():
            pos = sv.selectPositions()[0]
    
            pixel = gv.mapToScreen(pos)
    
            node = hou.selectedNodes()[0]
            geo = node.geometry()

    else:
        hou.ui.displayMessage("Please select a Capture Layer Paint SOP")
        return
    
    screenPos = gv.mapToScreen(pos)
    dir, origin = gv.mapToWorld(screenPos[0], screenPos[1])
    
    p = hou.Vector3()
    n = hou.Vector3()
    uvw = hou.Vector3()
    
    intersect_prim = geo.intersect(origin, dir, p, n, uvw)
    
    if intersect_prim == -1:
        return
    
    prim = geo.iterPrims()[intersect_prim]
    boneCapture = geo.findPointAttrib("boneCapture")
    
    indices = []
    weights = []
    
    pts = [v.point() for v in prim.vertices()]
    p_indices = []
    p_weights = []
    
    for pt in pts:
        bc = pt.attribValue("boneCapture")
        pt_indices = bc[::2]
        pt_weights = bc[1::2]
        p_indices.append(pt_indices)
        p_weights.append(pt_weights)
        
        for i in pt_indices:
            if i not in indices:
                indices.append(i)
     
    for i, cur_idx in enumerate(indices):
        total_weight = 0
        
        for pti, idx_tuple in enumerate(p_indices):
            if cur_idx in idx_tuple:
                weight_idx =  idx_tuple.index(cur_idx)
                total_weight += p_weights[pti][weight_idx]
            
        total_weight /= len(pts)
        weights.append(total_weight)

    idx_by_weight = sorted(range(len(weights)), key=weights.__getitem__, reverse=True)

    indices = [int(indices[i]) for i in idx_by_weight]
    weights = tuple(weights[i] for i in idx_by_weight)
    
    choices = []

    for i, index in enumerate(indices):
        if weights[i] < THRESHOLD:
            break

        propTable = boneCapture.indexPairPropertyTables()[0]

        path = propTable.stringPropertyValueAtIndex("pCaptPath", int(index))
        choices.append(path)


    if len(choices) == 1:
        node.parm("cregion").set(choices[0])
        sv.enterCurrentNodeState()
        return

    kwargs = {
        "node": node,
        "choices": choices,
        "weights": weights
    }
        
    dialog = cregionDialog(hou.qt.mainWindow(), kwargs)

    result = ""

    dialog.show()
    
    offset = QtCore.QPoint(0, dialog.height() / 2.0)
    cursor_pos = QtGui.QCursor().pos()
    dialog.move(QtGui.QCursor().pos() - offset)

cregionFromSurface()
