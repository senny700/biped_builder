# maya
from maya import cmds
import maya.api.OpenMaya as om

# biped_builder
from .. import core
from ..core import *

# built=ins
import json, uuid, os, importlib

# load components
# 솔직히.. 아직은 왜 COMPONENTS가 있어야 하는지 ㅁㄹ겠다.
COMPONENTS = {}


def load_components():
    current_dir = os.path.dirname(__file__)
    for file_ in os.listdir(current_dir):
        if file_.endswith(".py") and not file_.startswith("__"):
            mod_name = file_.split(".")[0]
            module_ = importlib.import_module(f"{__name__}.{mod_name}")
            importlib.reload(module_)
            COMPONENTS[mod_name] = module_


# 이 모듈의 biped의 전체 guide를 생성.

attributes = {
    "component": {"type": "string"},
    "name": {"type": "string"},
    "side": {"type": "string"},
    "index": {"type": "long"},
    "componentID": {"type": "string"},
    "ref_index": {"type": "long"},
    "RGB_ik": {"type": "float3"},
    "RGB_fk": {"type": "float3"},
    "color_ik": {"type": "long", "minValue": 0, "maxValue": 31},
    "color_fk": {"type": "long", "minValue": 0, "maxValue": 31},
    "matrices": {"type": "matrix", "multi": True},
}
values = {"componentID": str(uuid.uuid4()), "ref_index": -1}


class Guide:

    def __init__(self):
        pass

    def create_guide(self, name="", side="", index="", parent=None):
        guide = cmds.createNode(
            "transform",
            name=core.create_name(name, side, index, "", core.guide_extension),
        )
        if parent:
            guide = cmds.parent(guide, parent)[0]
            cmds.setAttr(guide + ".t", 0, 0, 0)
            cmds.setAttr(guide + ".r", 0, 0, 0)
        return guide

    def attirbute(self, node, attributes, values):
        """
        for 구문을 돌려 attributes와 value에 있는 longName: {flag: value} 형식의 딕셔너리 데이터를
        순차적으로 core.add_attr(node, longName, attributes[attr])로 실행합니다.
        """
        for attr in attributes.keys():
            core.add_attr(node, longName=attr, **attributes[attr])
        for value in values:
            core.set_value(node, values)

    def pole_vector_guide(self, guide=None, points=None, pv=None):
        """
        arm과 leg 등 guide가 움직임에 따라 pole vector가 위치하는 가이드를 만들어 줍니다.
        rig를 build할 때 이 위치를 참조합니다. pole vector 노드는 컴포넌트 가이드 하위에 들어갑니다.
        distance값은 guide 컴포넌트의 pv_distance 속성과 연결되어 관리됩니다.
        """
        if not len(points) == 3:
            raise ValueError("Make sure to put the value into the three points.")
        if not cmds.objExists(guide + ".pv_distance"):
            cmds.warning("Can only apply guide which has attribute named : pv_distance")
            return
        point1, point2, point3 = points

        dmp1 = cmds.createNode("decomposeMatrix")
        dmp2 = cmds.createNode("decomposeMatrix")
        dmp3 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(point1 + ".worldMatrix", dmp1 + ".inputMatrix")
        cmds.connectAttr(point2 + ".worldMatrix", dmp2 + ".inputMatrix")
        cmds.connectAttr(point3 + ".worldMatrix", dmp3 + ".inputMatrix")

        pma1 = cmds.createNode("plusMinusAverage") # point1 - point2
        pma2 = cmds.createNode("plusMinusAverage") # point1 - point3
        cmds.setAttr(pma1 + ".operation", 2) # subtract
        cmds.connectAttr(dmp2 + ".outputTranslate", pma1 + ".input3D[0]")
        cmds.connectAttr(dmp1 + ".outputTranslate", pma1 + ".input3D[1]")
        cmds.setAttr(pma2 + ".operation", 2)
        cmds.connectAttr(dmp3 + ".outputTranslate", pma2 + ".input3D[0]")
        cmds.connectAttr(dmp1 + ".outputTranslate", pma2 + ".input3D[1]")

        normalize = cmds.createNode("vectorProduct")
        cmds.setAttr(normalize + ".normalizeOutput", True)
        cmds.setAttr(normalize + ".operation", 0) # no operation
        cmds.connectAttr(pma2 + ".output3D", normalize + ".input1")

        dot_ = cmds.createNode("vectorProduct")
        cmds.connectAttr(normalize + ".output", dot_ + ".input1")
        cmds.connectAttr(pma1 + ".output3D", dot_ + ".input2")

        dot_pos = cmds.createNode("multiplyDivide")
        cmds.connectAttr(dot_ + ".output", dot_pos + ".input1")
        cmds.connectAttr(normalize + ".output", dot_pos + ".input2")

        pma3 = cmds.createNode("plusMinusAverage")
        cmds.setAttr(pma3 + ".operation", 2)
        cmds.connectAttr(pma1 + ".output3D", pma3 + ".input3D[0]")
        cmds.connectAttr(dot_pos + ".output", pma3 + ".input3D[1]")

        value_ = cmds.createNode("multiplyDivide")
        cmds.connectAttr(pma3 + ".output3D", value_ + ".input1")
        cmds.connectAttr(guide + ".pv_distance", value_ + ".input2X")
        cmds.connectAttr(guide + ".pv_distance", value_ + ".input2Y")
        cmds.connectAttr(guide + ".pv_distance", value_ + ".input2Z")

        sum_ = cmds.createNode("plusMinusAverage")
        cmds.connectAttr(dmp1 + ".outputTranslate", sum_ + ".input3D[0]")
        cmds.connectAttr(dot_pos + ".output", sum_ + ".input3D[1]")
        cmds.connectAttr(value_ + ".output", sum_ + ".input3D[2]")

        cmp = cmds.createNode("composeMatrix")
        cmds.connectAttr(sum_ + ".output3D", cmp + ".inputTranslate")

        mult = cmds.createNode("multMatrix")
        cmds.connectAttr(cmp + ".outputMatrix", mult + ".matrixIn[0]")
        cmds.connectAttr(guide + ".worldInverseMatrix", mult + ".matrixIn[1]")

        if not cmds.listRelatives(pv, parent=True) or not guide in cmds.listRelatives(pv, parent=True):
            cmds.parent(pv, guide)
        cmds.connectAttr(mult + ".matrixSum", pv + ".offsetParentMatrix")

        cmds.setAttr(pv + ".t", 0, 0, 0)
        cmds.setAttr(pv + ".t", lock=True)
        cmds.setAttr(pv + ".r", 0, 0, 0)
        cmds.setAttr(pv + ".r", lock=True)

    # TODO: 추후에 컴포넌트화 할 때, world가 아닌 local로 mirror합니다.
    # 또한 컴포넌트 종류를 인자로 받아서 set mirror 함수에서 guide를 생성합니다.
    def set_mirror(self, source_guide, target_guide):
        if not type(source_guide) == list and not type(source_guide) == tuple:
            source_guide = [source_guide]
        if not type(target_guide) == list and not type(target_guide) == tuple:
            target_guide = [target_guide]
        for source, target in zip(source_guide, target_guide):
            source_m = cmds.xform(source, query=True, worldSpace=True, matrix=True)
            target_m = core.matrix.get_mirror_matrix(source_m)
            cmds.xform(target, worldSpace=True, matrix=target_m)


class Rig:
    # Guide에 있는 data들을 모아서 실제 리그 데이터로 빌드합니다.

    def __init__(self):
        pass

    def generate_name(self, name="", side="", index="", description="", extension=""):
        name = f"{name}_{side}{index}_{description}_{extension}"
        name = "_".join([x for x in name.split("_") if x])
        return name


load_components()
