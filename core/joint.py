# maya
from maya import cmds
import maya.api.OpenMaya as om

# built-ins
import traceback

# biped_builder
from . import matrix


def joint_chain(name_list, matrices):
    if not len(name_list) == len(matrices):
        cmds.warning("Dismatch length name list and matrices.")
        return
    if len(name_list) < 3:
        cmds.warning("Joint chain need at least 3 joints.")
        return
    joint_list = [cmds.createNode("joint", name=name) for name in name_list]
    for jnt, m in zip(joint_list, matrices):
        cmds.xform(jnt, worldSpace=True, matrix=m)
    p0, p1, p2 = [cmds.xform(x, query=True, worldSpace=True, translation=True) for x in joint_list[:3]]
    normal = matrix.get_plane_normal(p0, p1, p2)

    for i, jnt in enumerate(joint_list):
        if not joint_list[i] == joint_list[-1]:
            pos = om.MVector(cmds.xform(jnt, query=True, worldSpace=True, translation=True))
            look_at = om.MVector(cmds.xform(joint_list[i + 1], query=True, worldSpace=True, translation=True))
            m_ = matrix.get_look_at_matrix(pos, look_at, normal, ["x", "y"])
            cmds.xform(jnt, worldSpace=True, matrix=m_)
            rot = cmds.getAttr(jnt + ".rotate")[0]
            cmds.setAttr(jnt + ".rotate", 0, 0, 0)
            cmds.setAttr(jnt + ".jointOrient", *rot)            
        if not i == 0:
            cmds.parent(jnt, joint_list[i-1])
    cmds.setAttr(joint_list[-1] + ".jointOrient", 0, 0, 0)

    return joint_list
