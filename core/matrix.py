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

def get_plane_normal(p0, p1, p2):
    p0, p1, p2 = [om.MVector(p) for p in [p0, p1, p2]]
    vector0 = p1 - p0
    vector1 = p2 - p1
    vector0.normalize()
    vector1.normalize()

    normal = vector0 ^ vector1
    normal.normalize()

    # 두 벡터가 일직선 상에 놓여 있어 영벡터가 될 때, 임의로 보조 벡터 사용.
    sum_ = normal[0] + normal[1] + normal[2]
    if int(sum_) == 0:
        normal = get_orthogonal_vector(vector0)
    return normal

def get_orthogonal_vector(vector):
    vector = (vector).normal()

    abs_x, abs_y, abs_z = abs(vector.x), abs(vector.y), abs(vector.z)

    # x축의 절대값이 가장 작을 때 x축을 보조 벡터로 사용
    if abs_x <= abs_y and abs_x <= abs_z:
        ref_vector = om.MVector(1, 0, 0)
    # y축의 절대값이 가장 작을 때 y축을 보조 벡터로 사용
    elif abs_y <= abs_x and abs_y <= abs_z:
        ref_vector = om.MVector(0, 1, 0)
    # z축의 절대값이 가장 작을 때 z축을 보조 벡터로 사용 
    else:
        ref_vector = om.MVector(0, 0, 1)

    orthogonal_v = vector ^ ref_vector
    return orthogonal_v

def get_look_at_matrix(pos, look_at, up, axis=["x", "y"]):
    '''
    domino2의 get look at matrix 함수 copy.
    Args:
            pos (om.MVector): position vector
            lookAt (om.MVector): target vector
            up (om.MVector): up vector
            axis (list, optional): primary, secondary axis. Defaults to ["x", "y"]
    Returns:
        om.MMatrix: aim matrix

    Example:
        >>> all_axis = [
        >>>     ("x", "y"),
        >>>     ("x", "-y"),
        >>>     ("-x", "y"),
        >>>     ("-x", "-y"),
        >>>     ("y", "x"),
        >>>     ("y", "-x"),
        >>>     ("-y", "x"),
        >>>     ("-y", "-x"),
        >>>     ("x", "z"),
        >>>     ("x", "-z"),
        >>>     ("-x", "z"),
        >>>     ("-x", "-z"),
        >>>     ("z", "x"),
        >>>     ("z", "-x"),
        >>>     ("-z", "x"),
        >>>     ("-z", "-x"),
        >>>     ("y", "z"),
        >>>     ("y", "-z"),
        >>>     ("-y", "z"),
        >>>     ("-y", "-z"),
        >>>     ("z", "y"),
        >>>     ("z", "-y"),
        >>>     ("-z", "y"),
        >>>     ("-z", "-y"),
        >>> ]

        >>> pos = om.MVector((0, 0, 0))
        >>> look_at = om.MVector((2, 0, 0))
        >>> up = om.MVector((0, 2, 0))

        >>> for axis in all_axis:
        >>>    axis_obj = nurbscurve.create("axis", (0, 0, 0))
        >>>    axis_obj = cmds.rename(axis_obj, (axis[0] + axis[1]).replace("-", "m"))

        >>>    m = matrix.get_look_at_matrix(pos, look_at, up, axis=axis)
        >>>    cmds.xform(axis_obj, matrix=m)
    '''
    # primary - 위치에서 바라보는 위치의 벡터.
    # temp - primary벡터와 up 벡터의 임시 직교 벡터
    # secondary - 임시 직교 벡터와 primary의 직교 벡터.
    primary = (look_at - pos).normal()
    temp = (primary ^ up.normal()).normal()
    secondary = (temp ^ primary).normal()

    # primary 축 설정. 만약 음수 기호면 -1을 곱함.
    if "x" in axis[0]:
        X = primary
        if "-" in axis[0]:
            X *= -1
    if "y" in axis[0]:
        Y = primary
        if "-" in axis[0]:
            Y *= -1
    if "z" in axis[0]:
        Z = primary
        if "-" in axis[0]:
            Z *= -1

    # secondary 축 설정. 만약 음수 기호면 -1을 곱함.
    if "x" in axis[1]:
        X = secondary
        if "-" in axis[1]:
            X *= -1
    if "y" in axis[1]:
        Y = secondary
        if "-" in axis[1]:
            Y *= -1
    if "z" in axis[1]:
        Z = secondary
        if "-" in axis[1]:
            Z *= -1

    # primary와 secondary 축이 아닌 축은 두 축의 직교 벡터로 두기.
    all_axis = axis[0] + axis[1]
    if "x" in all_axis and "y" in all_axis:
        Z = (X ^ Y).normal()
    if "x" in all_axis and "z" in all_axis:
        # 마야에선 오른손 법칙을 사용하므로, x축과 z축의 직교를 위해서는
        # Z축에 X축을 외적해야 함.
        Y = (Z ^ X).normal()
    if "y" in all_axis and "z" in all_axis:
        X = (Y ^ Z).normal()

    # 모든 축의 normalized vector를 구했으니, pos를 붙여 메트릭스로 변환.
    m = []
    m.extend([X[0], X[1], X[2], 0.0])
    m.extend([Y[0], Y[1], Y[2], 0.0])
    m.extend([Z[0], Z[1], Z[2], 0.0])
    m.extend([pos[0], pos[1], pos[2], 1.0])
    return om.MMatrix(m)









