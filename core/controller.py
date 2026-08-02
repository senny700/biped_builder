# maya
from maya import cmds

# built-ins
import traceback

def box_controller(name=None, size=1, parent=None):
    box_id = [0, 1, 3, 2, 0, 6, 4, 2, 4, 5, 7, 1, 3, 5, 7, 6]
    box_ = cmds.polyCube(width=size, height=size, depth=size, constructionHistory=False)[0]
    box_points = [cmds.pointPosition(f"{box_}.vtx[{i}]") for i in box_id]

    curve_ = cmds.curve(degree=1, point=box_points, name=name if name else "curve")
    
    if parent:
        curve_shape = cmds.listRelatives(curve_, shapes=True)[0]
        cmds.parent(curve_shape, parent, relative=True, shape=True)
        cmds.rename(curve_shape, parent+"Shape")
        cmds.delete(curve_)

    cmds.delete(box_)
    return curve_

def cross_controller(name=None, size=1, parent=None):
    cross_pos = [(.5, .5, .5), (-.5, -.5, -.5), (0, 0, 0), (-.5, .5, .5), (.5, -.5, -.5), (0, 0, 0),
                 (.5, .5, -.5), (-.5, -.5, .5), (0, 0, 0), (-.5, .5, -.5), (.5, -.5, .5)]
    curve_ = cmds.curve(degree=1, point=cross_pos, name=name if name else "curve")

    curve_shape = cmds.listRelatives(curve_, shapes=True)[0]
    cmds.scale(size, size, size, curve_shape)

    if parent:
        cmds.parent(curve_shape, parent, relative=True, shape=True)
        cmds.delete(curve_)

    return curve_

def guide_line(positions, parent):
    if not parent:
        return
    if len(positions) == 1:
        raise ValueError("Please apply at least two points.")
        return

    points = [cmds.xform(x, query=True, worldSpace=True, translation=True) for x in positions]
    curve_ = cmds.curve(degree=1, point=points, name=parent+"_gLine")
    curve_ = cmds.parent(curve_, parent)[0]
    cmds.setAttr(curve_ + ".t", 0, 0, 0)
    cmds.setAttr(curve_ + ".r", 0, 0, 0)
    cmds.setAttr(curve_ + ".s", 1, 1, 1)
    for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
        cmds.setAttr(curve_ + "." + attr, lock=True, keyable=False, channelBox=False)

    for i, x in enumerate(positions):
        mult = cmds.createNode("multMatrix")
        decompose = cmds.createNode("decomposeMatrix")
        
        cmds.connectAttr(x + ".worldMatrix", mult + ".matrixIn[0]")
        cmds.connectAttr(parent + ".worldInverseMatrix", mult + ".matrixIn[1]")
        cmds.connectAttr(mult + ".matrixSum", decompose + ".inputMatrix")
        cmds.connectAttr(decompose + ".ot", curve_ + f".controlPoints[{i}]")

    return curve_


















