import hou
from PySide2 import QtWidgets, QtCore, QtGui
import Bone
from hdatools import fkcontrol, hdaparmutils


def treeModelFromDict(d, model=None, cur_row=None):
    if not model:
        model = QtGui.QStandardItemModel()
    if not cur_row:
        cur_row = model.invisibleRootItem()

    for k in d.keys():
        item = QtGui.QStandardItem(k)
        cur_row.appendRow(item)
        treeModelFromDict(d[k], model=model, cur_row=item)

    return model


class FolderCompleter(QtWidgets.QCompleter):
    def __init__(self):
        super(FolderCompleter, self).__init__()

    def splitPath(self, path):
        return path.split('/')

    def pathFromIndex(self, index):
        result = []
        while index.isValid():
            result = [self.model().data(index, QtCore.Qt.DisplayRole)] + result
            index = index.parent()
        r = '/'.join(result)
        return r


class FolderSelect(QtWidgets.QWidget):
    def __init__(self, label):
        super(FolderSelect, self).__init__()

        layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label)
        self.field = QtWidgets.QListWidget()

        layout.addWidget(label)
        layout.addWidget(self.field)

        self.setLayout(layout)


class ControlType(QtWidgets.QWidget):
    def __init__(self, callback=None):
        super(ControlType, self).__init__()

        layout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel("Control Type")
        self.select = QtWidgets.QComboBox()

        self.select.insertItems(0, (
            "Null",
            "Circles",
            "Box",
            "Planes"
        ))

        if callback:
            self.select.currentIndexChanged.connect(callback)

        layout.addWidget(label)
        layout.addWidget(self.select)

        self.setLayout(layout)


class ControlOrient(QtWidgets.QWidget):
    def __init__(self):
        super(ControlOrient, self).__init__()

        layout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel("Orientation")
        self.select = QtWidgets.QComboBox()

        self.select.insertItems(0, (
            "All",
            "X",
            "Y",
            "Z"
        ))

        layout.addWidget(label)
        layout.addWidget(self.select)

        self.setLayout(layout)


class ToggleStrip(QtWidgets.QWidget):
    def __init__(self, labels, names=(), callback=None):

        super(ToggleStrip, self).__init__()

        layout = QtWidgets.QHBoxLayout()
        self.values = []
        self.names = names

        self.setStyleSheet("""
        QPushButton:hover{background:transparent}
        QPushButton:checked{background:rgb(230,125,0)}""")

        for n in labels:
            b = QtWidgets.QPushButton(n)
            b.setCheckable(True)
            b.setChecked(True)
            b.setAutoRepeat(False)
            if callback:
                b.toggled.connect(callback)
            layout.addWidget(b)
            self.values.append(b)

        self.setLayout(layout)

    def getValues(self):
        result = ""
        for v in self.values:
            if v.isChecked():
                result += "1"
            else:
                result += "0"

        return int(result, 2)

    def getNames(self):
        if self.names:
            result = ""
            for i, v in enumerate(self.values):
                if v.isChecked():
                    result += self.names[i]

            return result


class TransformMask(QtWidgets.QWidget):
    def __init__(self):
        super(TransformMask, self).__init__()

        names = tuple(n + i for n in "trs" for i in "xyz")

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("Parameter Mask")
        self.multitoggles = []

        multi = QtWidgets.QWidget()
        multi_layout = QtWidgets.QHBoxLayout()

        for i, n in enumerate(("Translate", "Rotate", "Scale")):
            b = QtWidgets.QPushButton(n)
            b.setAutoRepeat(False)
            b.setStyleSheet("")
            self.multitoggles.append(b)
            multi_layout.addWidget(b)

        self.multitoggles[0].clicked.connect(lambda: self.setMulti(0))
        self.multitoggles[1].clicked.connect(lambda: self.setMulti(1))
        self.multitoggles[2].clicked.connect(lambda: self.setMulti(2))

        multi.setLayout(multi_layout)

        self.strip = ToggleStrip(names)

        layout.addWidget(label)
        layout.addWidget(multi)
        layout.addWidget(self.strip)

        self.setLayout(layout)

    def setMulti(self, t):
        idx = t * 3

        initial = self.strip.values[idx].isChecked()

        for v in self.strip.values[idx:idx + 3]:
            v.setChecked(not initial)


class CtrlOrientation(QtWidgets.QWidget):
    def __init__(self, callback=None):
        super(CtrlOrientation, self).__init__()

        layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Control Orientation")
        labels = ("X", "Y", "Z")
        names = ("x", "y", "z")

        self.strip = ToggleStrip(labels, names, callback)

        layout.addWidget(label)
        layout.addWidget(self.strip)
        self.setLayout(layout)


class CtrlColor(QtWidgets.QWidget):
    def __init__(self, callback=None):
        super(CtrlColor, self).__init__()

        self.callback = callback

        layout = QtWidgets.QHBoxLayout()
        self.color = QtGui.QColor()
        self.color.setRgb(230, 125, 0)

        self.pickbutton = QtWidgets.QPushButton()
        self.pickbutton.setGeometry(0, 0, 100, 50)
        self._setbg()
        self.pickbutton.clicked.connect(self._pick)

        layout.addWidget(self.pickbutton)

        self.setLayout(layout)

    def _pick(self):
        self.color = QtWidgets.QColorDialog.getColor(self.color)
        self._setbg()
        if self.callback:
            self.callback()

    def _setbg(self):
        self.pickbutton.setStyleSheet("background: rgb" + str(self.color.toTuple()))


class CacheSlider(QtWidgets.QSlider):
    def __init__(self, callback=None, undogroup="Slider Value Changed"):
        super(CacheSlider, self).__init__()
        self.setTracking(True)
        self.startvalue = None
        self.endvalue = None
        self.callback = callback
        self.undogroup = undogroup

    def mousePressEvent(self, event):
        self.startvalue = self.value()
        value = float(event.x() * self.maximum()) / self.width()
        self.setValue(value)
        with hou.undos.disabler():
            self.callback()

    def mouseMoveEvent(self, event):
        value = float(event.x() * self.maximum()) / self.width()
        self.setValue(value)
        with hou.undos.disabler():
            self.callback()

    def mouseReleaseEvent(self, event):
        self.endvalue = self.value()
        with hou.undos.disabler():
            self.setValue(self.startvalue)
            self.callback()
        with hou.undos.group(self.undogroup):
            self.setValue(self.endvalue)
            self.callback()
        self.startvalue = None
        self.endvalue = None


class CtrlScale(QtWidgets.QWidget):
    def __init__(self, callback=None):
        super(CtrlScale, self).__init__()

        self.callback = callback

        layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Control Scale")

        self.slider = CacheSlider(callback=callback, undogroup="Change Control Scale")
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(10)

        self.setStyleSheet("""
            QSlider{
                height: 20px;
                width: 100px;
            }
            QSlider::groove:horizontal{
                border: none;
                height: 30px;
            }
            QSlider::sub-page{
                background: rgb(230,125,0);
            }
            QSlider::handle:horizontal{
                width: 10px;
                margin: -15px 0;
                background: white;
            }
        """)

        layout.addWidget(label)
        layout.addWidget(self.slider)

        self.setLayout(layout)

    def getValue(self):
        return self.slider.value() * 0.1


class FKInterface(QtWidgets.QDialog):
    def __init__(self, parent):
        super(FKInterface, self).__init__(parent)
        # self.setStyleSheet(hou.qt.styleSheet())

        self.selected_nodes = ()
        self.parent = None
        self.errors = ()
        self.error_display = QtWidgets.QLabel()
        self.error_display.setStyleSheet("color: red")

        self._getParent()

        hou.ui.addEventLoopCallback(self._updateSelection)

        layout = QtWidgets.QVBoxLayout()
        self.folder = None
        self.foldermodel = QtGui.QStandardItemModel()
        self.ctrls = ()

        self.riglabel = QtWidgets.QLabel()
        self.folderpath = QtWidgets.QLineEdit()
        self.completer = FolderCompleter()

        self.folderpath.setCompleter(self.completer)

        self.control_type = ControlType(self._onctrltype)
        self.mask = TransformMask()
        self.orientation = CtrlOrientation(callback=self._onorient)
        self.ctrlcolor = CtrlColor(callback=self._oncolor)
        self.ctrlscale = CtrlScale(callback=self._onscale)

        self.apply = QtWidgets.QPushButton("Create")
        self.clear_ctrls = QtWidgets.QPushButton("Clear Ctrls")
        self.apply.clicked.connect(self._onapply)
        self.clear_ctrls.clicked.connect(self._clearctrls)
        self.clear_ctrls.setVisible(False)

        self._updateSelection()

        layout.addWidget(self.riglabel)
        layout.addWidget(self.folderpath)
        layout.addWidget(self.error_display)
        layout.addWidget(self.control_type)
        layout.addWidget(self.orientation)
        layout.addWidget(self.ctrlcolor)
        layout.addWidget(self.ctrlscale)
        layout.addWidget(hou.qt.createSeparator())
        layout.addWidget(self.mask)
        layout.addWidget(self.apply)
        layout.addWidget(self.clear_ctrls)

        self.setLayout(layout)

    def _updateSelection(self):
        sel = hou.selectedNodes()
        try:
            if sel != self.selected_nodes:
                self.selected_nodes = sel
                if len(self.selected_nodes) > 0:
                    self._getParent()

                    out_text = "Current Rig: "

                    if not self.parent:
                        out_text += "None"
                    else:
                        out_text += self.parent.path()
                        self.foldermodel = treeModelFromDict(hdaparmutils.folderHierarchy(self.parent.parmTemplateGroup()))

                    self.riglabel.setText(out_text)

                    self.completer.setModel(self.foldermodel)

                    if len(self.errors) > 0:
                        self.apply.setDisabled(True)
                    else:
                        self.apply.setDisabled(False)

        except hou.ObjectWasDeleted:
            self.selected_nodes = ()

    def _getParent(self):
        self.errors = ()
        parent = None
        for n in self.selected_nodes:
            if not parent:
                parent = n.parent()
            else:
                if parent != n.parent():
                    s = "Currently selected nodes do not share the same parent"
                    self.errors += (s,)
                    parent = None

        if parent and not parent.isEditable():
            s = "Current parent node is not editable"
            self.errors += (s,)

        if parent == hou.node("/obj"):
            parent = None
            s = "Currently selected nodes have no parent"
            self.errors += (s,)

        self.parent = parent
        self._updateErrors()

    def _updateErrors(self):
        out_text = "\n".join(self.errors)
        self.error_display.setText(out_text)

    def test(self):
        print(self.orientation.strip.getNames())

    def _onctrltype(self):
        with hou.undos.group("Set Ctrl Type"):
            for n in self.ctrls:
                n.controltype = self.control_type.select.currentIndex()

    def _onorient(self):
        with hou.undos.group("Set Ctrl Orientation"):
            for n in self.ctrls:
                n.orientation = self.orientation.strip.getNames()

    def _oncolor(self):
        with hou.undos.group("Set Ctrl Color"):
            for ctrl in self.ctrls:
                # trim off alpha channel from QColor
                ctrl.dcolor = self.ctrlcolor.color.getRgbF()[0:3]

    def _onscale(self):
        for n in self.ctrls:
            n.geoscale = self.ctrlscale.getValue()

    def _clearctrls(self):
        self.ctrls = ()
        self.clear_ctrls.setVisible(False)
        self.apply.setVisible(True)
        self.mask.setDisabled(False)

    def _onapply(self):
        with hou.undos.group("Create FK Controls"):
            for n in hou.selectedNodes():
                if self.folderpath.text() == "":
                    folderpathtuple = ()
                else:
                    folderpathtuple = tuple(self.folderpath.text().split("/"))
                ctrl = fkcontrol.FKControl(n,
                                           self.mask.strip.getValues(),
                                           folder=folderpathtuple)
                self.ctrls += (ctrl,)
                ctrl.controltype = self.control_type.select.currentIndex()
                ctrl.orientation = self.orientation.strip.getNames()
                # trim off alpha channel from QColor
                ctrl.dcolor = self.ctrlcolor.color.getRgbF()[0:3]
                ctrl.geoscale = self.ctrlscale.getValue()
                self.apply.setVisible(False)
                self.mask.setDisabled(True)
                self.clear_ctrls.setVisible(True)

    def closeEvent(self, result):
        print("closed!")
        hou.ui.removeEventLoopCallback(self._updateSelection)