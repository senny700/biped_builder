# maya
from maya import cmds
import maya.api.OpenMaya as om


mirror_matrix = om.MMatrix([
    -1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
])

def get_mirror_matrix(input_matrix):
    if not type(input_matrix) == om.MMatrix:
        input_matrix = om.MMatrix(input_matrix)
    mirror_m = input_matrix * mirror_matrix
    return mirror_m






