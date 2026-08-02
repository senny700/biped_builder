# maya
from maya import cmds

# built-ins
import traceback, importlib, os
# 이 모듈에 rig를 build하는 데에 필요한 기능을 저장함.

# HACK: 툴 작성 중 test할 때 reload가 안 되어서 오류가 남. 일시적으로 자동으로 reload해주는 코드.
def load_components():
    current_dir = os.path.dirname(__file__)
    for file_ in os.listdir(current_dir):
        if file_.endswith(".py") and not file_.startswith("__"):
            mod_name = file_.split(".")[0]
            module_ = importlib.import_module(f"{__name__}.{mod_name}")
            importlib.reload(module_)

name_rule = "{name}_{side}{index}_{description}_{extension}"

center = "C"
left = "L"
right = "R"

guide_extension = "guide"
root_extension = "root"
joint_extension = "jnt"
constoller_extension = "ctl"
group_extension = "grp"
npo_extension = "npo"
loc_extension = "loc"
output_extension = "out"
curve_extension = "crv"
ikh_extension = "ikh"
psd_extension = "psd"

def create_name(name="", side="", index="", description="", extension=""):
    name = f"{name}_{side}{index}_{description}_{extension}"
    name = "_".join([x for x in name.split("_") if x])
    return name

def add_attr(node, **attr_args):
    """
    longName : {flag: value}로 이루어진 attributes 딕셔너리를
    아래와 같은 방식으로 분해하여 사용합니다.
    for attr in attributes:
        core.add_attr(node, longName=attr, **attributes[attr])
    """
    def solve_type(_type):
        datatypes = ["string",
                    "stringArray",
                    "matrix",
                    "reflectanceRGB",
                    "spectrumRGB",
                    "doubleArray",
                    "floatArray",
                    "Int32Array",
                    "vectorArray",
                    "nurbsCurve",
                    "nurbsSurface",
                    "mesh",
                    "lattice",
                    "pointArray"]
        attribute_types = ["bool",
                        "long",
                        "short",
                        "byte",
                        "char",
                        "enum",
                        "float",
                        "double",
                        "doubleAngle",
                        "doubleLinear",
                        "compound",
                        "message",
                        "time",
                        "fltMatrix",
                        "reflectance",
                        "spectrum",
                        "float2",
                        "float3",
                        "double2",
                        "double3",
                        "long2",
                        "long3",
                        "short2",
                        "short3"]
        if _type in datatypes:
            return {"dataType": _type}
        elif _type in attribute_types:
            return {"attributeType": _type}
    if cmds.attributeQuery(attr_args["longName"], node=node, exists=True):
        return None
    attr_args.update(solve_type(attr_args.pop("type")))
    cmds.addAttr(node, **attr_args)
    return node + "." + attr_args["longName"]

def set_value(node, values):
    non_numerics = [
        "short2",
        "short3",
        "long2",
        "long3",
        "Int32Array",
        "float2",
        "float3",
        "double2",
        "double3",
        "doubleArray",
        "matrix",
        "pointArray",
        "vectorArray",
        "string",
        "stringArray",
        "sphere",
        "cone",
        "reflectanceRGB",
        "spectrumRGB",
        "componentList",
        "attributeAlias",
        "nurbsCurve",
        "nurbsSurface",
        "nurbsTrimface",
        "polyFaces",
        "mesh",
        "lattice"
        ]
    for k, v in values.items():
        try:
            _type = cmds.getAttr(node + f".{k}", type=True)
            if _type in non_numerics:
                cmds.setAttr(node + f".{k}", v, type=_type)
            else:
                cmds.setAttr(node + f".{k}", v)
        except:
            print("# 존재하지 않는 attribute가 있습니다.")
            print(traceback.print_exc())
        




load_components()