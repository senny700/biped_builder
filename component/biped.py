# maya
from maya import cmds

# biped_builder
from .. import component, core
from ..core import controller, matrix, joint

# built-ins
import copy


class Guide(component.Guide):

    def __init__(self):
        super().__init__()

    def create(self):
        # NOTE: 한 컴포넌트가 아닌, biped 전체의 가이드를 생성합니다.
        # 그러나 컴포넌트별로 is guide인 노드를 찾아 data를 긁어 attribute를 생성해야 합니다.
        # 고로, 이 함수에서는 전체 guide를 생성하지만, 중간중간 컴포넌트의 최상위 노드에는 따로 attribute를 넣도록 합니다.

        # assembly
        assembly_attributes = copy.deepcopy(component.attributes)
        assembly_values = copy.deepcopy(component.values)
        assembly_attributes.update(
            {
                "is_guide": {"type": "bool"},
                "origin_ctl_size": {"type": "float", "minValue": 0},
                "sub_ctl_count": {"type": "long", "minValue": 0, "defaultValue": 2},
            }
        )
        assembly_attributes.pop("side")
        assembly_values.update(
            {"component": "assembly", "name": "biped", "origin_ctl_size": 5}
        )
        assembly = self.create_guide(name="biped")
        self.attirbute(assembly, assembly_attributes, assembly_values)
        controller.box_controller(name=None, size=3, parent=assembly)
        for attr in ["t", "r", "s"]:
            cmds.setAttr(f"{assembly}.{attr}", lock=True)
        guide_line_grp = (
            cmds.createNode("transform", name="gLine_grp", parent=assembly)
            if not cmds.objExists("gLine_grp")
            else "gLine_grp"
        )
        cmds.setAttr(guide_line_grp + ".hiddenInOutliner", True)
        cmds.setAttr(guide_line_grp + ".overrideEnabled", True)
        cmds.setAttr(guide_line_grp + ".overrideDisplayType", 2)  # reference

        # body - 몸통 전체를 움직임. 사지의 ik를 제외하고 움직인다.
        def control_guide(name, side, index, parent=None):
            control_attributes = copy.deepcopy(component.attributes)
            control_values = copy.deepcopy(component.values)

            control = self.create_guide(
                name=name, side=side, index=index, parent=parent if parent else None
            )

            control_attributes.update({"is_guide": {"type": "bool"}})
            control_values.update(
                {"component": "control", "name": name, "side": side, "index": index}
            )
            controller.box_controller(size=1, parent=control)
            self.attirbute(control, control_attributes, control_values)
            return control

        body = control_guide("body", "C", 0, assembly)
        cmds.xform(body, worldSpace=True, translation=(0, 8, 0))

        # spine
        def spine_guide(name, side, index, parent=None):
            spine_attributes = copy.deepcopy(component.attributes)
            spine_values = copy.deepcopy(component.values)

            spine = self.create_guide(
                name="spine", side="C", index=0, parent=parent if parent else None
            )

            spine_attributes.update(
                {
                    "is_guide": {"type": "bool"},
                    "max_stretch": {"type": "double"},
                    "max_squash": {"type": "double"},
                }
            )
            spine_values.update(
                {
                    "component": "spine",
                    "name": name,
                    "side": side,
                    "index": index,
                    "max_stretch": 1.2,
                    "max_squash": 0.95,
                }
            )

            controller.box_controller(name=None, size=1, parent=spine)
            self.attirbute(spine, spine_attributes, spine_values)
            cmds.xform(spine, worldSpace=True, translation=(0, 10, 0))
            spine_1 = core.create_name(
                name=name,
                side=side,
                index=index,
                description="1",
                extension="pos",
            )
            spine_1 = cmds.createNode("transform", name=spine_1, parent=spine)
            controller.cross_controller(parent=spine_1)
            cmds.setAttr(spine_1 + ".t", 0, 1, 0)
            spine_2 = core.create_name(
                name=name,
                side=side,
                index=0,
                description="2",
                extension="pos",
            )
            spine_2 = cmds.createNode("transform", name=spine_2, parent=spine_1)
            controller.cross_controller(parent=spine_2)
            cmds.setAttr(spine_2 + ".t", 0, 1, 0)
            spine_end = core.create_name(
                name=name,
                side=side,
                index=0,
                description="",
                extension="end",
            )
            spine_end = cmds.createNode("transform", name=spine_end, parent=spine_2)
            controller.cross_controller(parent=spine_end)
            cmds.setAttr(spine_end + ".t", 0, 1, 0)
            controller.guide_line(
                positions=[spine, spine_1, spine_2, spine_end], parent=guide_line_grp
            )

            for i, x in enumerate([spine, spine_1, spine_2, spine_end]):
                cmds.connectAttr(x + ".worldMatrix", spine + f".matrices[{i}]")
            return spine, spine_1, spine_2, spine_end

        spine_list = spine_guide(name="spine", side="C", index=0, parent=body)

        # arm - left
        def arm_guide(name, side, index, parent):
            arm_attributes = copy.deepcopy(component.attributes)
            arm_values = copy.deepcopy(component.values)

            arm = self.create_guide(
                name=name, side=side, index=index, parent=parent if parent else None
            )

            arm_attributes.update(
                {
                    "is_guide": {"type": "bool"},
                    "fk_ik": {"type": "double", "minValue": 0, "maxValue": 1},
                    "max_stretch": {
                        "type": "double",
                        "minValue": 1,
                        "defaultValue": 1.5,
                    },
                    "elbow_pin": {"type": "double", "minValue": 0, "maxValue": 1},
                    "pv_matrix": {"type": "matrix"},
                    "pv_distance": {"type": "double", "minValue": 0.1, "keyable": True},
                }
            )
            arm_values.update(
                {
                    "component": "arm",
                    "name": name,
                    "side": side,
                    "index": index,
                    "fk_ik": 0,
                    "max_stretch": 1.5,
                    "elbow_pin": 0,
                    "pv_distance": 3,
                }
            )

            controller.box_controller(size=1, parent=arm)
            self.attirbute(arm, arm_attributes, arm_values)
            cmds.xform(arm, worldSpace=True, rotation=(0, 0, 0))
            cmds.setAttr(arm + ".t", 2, 0, 0)
            humerus = core.create_name(
                name=name, side=side, index=index, description="1", extension="pos"
            )
            humerus = cmds.createNode("transform", name=humerus, parent=arm)
            controller.cross_controller(parent=humerus)
            cmds.setAttr(humerus + ".t", 2, 0, 0)
            elbow = core.create_name(
                name=name, side=side, index=index, description="2", extension="pops"
            )
            elbow = cmds.createNode("transform", name=elbow, parent=humerus)
            controller.cross_controller(parent=elbow)
            cmds.setAttr(elbow + ".t", 2, 0, -1)
            wrist = core.create_name(
                name=name, side=side, index=index, description="3", extension="pos"
            )
            wrist = cmds.createNode("transform", name=wrist, parent=elbow)
            controller.cross_controller(parent=wrist)
            cmds.setAttr(wrist + ".t", 2, 0, 1)
            controller.guide_line(
                positions=[arm, humerus, elbow, wrist], parent=guide_line_grp
            )
            elbow_pv = core.create_name(
                name=name,
                side=side,
                index=index,
                description="pv",
                extension="pos",
            )
            elbow_pv = cmds.createNode("transform", name=elbow_pv)
            controller.cross_controller(parent=elbow_pv)
            self.pole_vector_guide(arm, [humerus, elbow, wrist], elbow_pv)
            controller.guide_line(positions=[elbow, elbow_pv], parent=guide_line_grp)
            for i, x in enumerate([arm, humerus, elbow, wrist]):
                cmds.connectAttr(x + ".worldMatrix", arm + f".matrices[{i}]")
            cmds.connectAttr(elbow_pv + ".worldMatrix", arm + ".pv_matrix")
            return arm, humerus, elbow, wrist

        arm_list = arm_guide("arm", "L", 0, parent=spine_list[-1])

        # hand - left
        def hand_guide(name, side, index, parent=None):
            hand_attributes = copy.deepcopy(component.attributes)
            hand_values = copy.deepcopy(component.values)

            hand = self.create_guide(
                name=name, side=side, index=index, parent=parent if parent else None
            )

            hand_attributes.update({"is_guide": {"type": "bool"}})
            hand_values.update(
                {"component": "hand", "name": hand, "side": side, "index": index}
            )
            controller.box_controller(size=1, parent=hand)
            self.attirbute(hand, hand_attributes, hand_values)
            cmds.connectAttr(hand + ".worldMatrix", hand + ".matrices[0]")
            return hand

        hand = hand_guide("hand", "L", 0, arm_list[-1])

        # leg - left
        def leg_guide(name, side, index, parent=None):
            leg_attributes = copy.deepcopy(component.attributes)
            leg_values = copy.deepcopy(component.values)

            leg = self.create_guide(
                name=name, side=side, index=index, parent=parent if parent else None
            )

            leg_attributes.update(
                {
                    "is_guide": {"type": "bool"},
                    "fk_ik": {"type": "double", "minValue": 0, "maxValue": 1},
                    "max_stretch": {"type": "double", "minValue": 1},
                    "knee_pin": {"type": "double", "minValue": 0, "maxValue": 1},
                    "pv_matrix": {"type": "matrix"},
                    "pv_distance": {"type": "double", "minValue": 0.1, "keyable": True},
                }
            )
            # NOTE: 실제 component로 나눠서 작업하여 템플릿화 할 때는 ref index를 spine이 시작하는 0번으로 설정합니다.
            leg_values.update(
                {
                    "component": "leg",
                    "name": name,
                    "side": side,
                    "index": index,
                    "fk_ik": 1,
                    "max_stretch": 1.5,
                    "knee_pin": 0,
                    "pv_distance": 3,
                }
            )

            self.attirbute(leg, leg_attributes, leg_values)
            controller.box_controller(size=1, parent=leg)
            cmds.xform(leg, worldSpace=True, translation=(2, 10, 0))
            knee = core.create_name(
                name="knee", side=side, index=index, extension=core.guide_extension
            )
            knee = cmds.createNode("transform", name=knee, parent=leg)
            controller.cross_controller(parent=knee)
            cmds.setAttr(knee + ".t", 0, -5, 1)
            ankle = core.create_name(
                name="ankle", side=side, index=index, extension=core.guide_extension
            )
            ankle = cmds.createNode("transform", name=ankle, parent=knee)
            controller.cross_controller(parent=ankle)
            cmds.setAttr(ankle + ".t", 0, -5, -1)
            controller.guide_line(positions=[leg, knee, ankle], parent=guide_line_grp)
            knee_pv = core.create_name(
                name="knee",
                side=side,
                index=index,
                description="pv",
                extension=core.guide_extension,
            )
            knee_pv = cmds.createNode("transform", name=knee_pv)
            controller.cross_controller(parent=knee_pv)
            self.pole_vector_guide(leg, [leg, knee, ankle], knee_pv)
            controller.guide_line(positions=[knee, knee_pv], parent=guide_line_grp)

            for i, x in enumerate([leg, knee, ankle]):
                cmds.connectAttr(x + ".worldMatrix", leg + f".matrices[{i}]")
            cmds.connectAttr(knee_pv + ".worldMatrix", leg + ".pv_matrix")
            return leg, knee, ankle

        leg_list = leg_guide("leg", "L", 0, spine_list[0])

        # foot - left
        def foot_guide(name, side, index, parent=None):
            foot_attributes = copy.deepcopy(component.attributes)
            foot_values = copy.deepcopy(component.values)

            foot = self.create_guide(
                name=name, side=side, index=index, parent=parent if parent else None
            )

            foot_attributes.update(
                {
                    "is_guide": {"type": "bool"},
                }
            )
            foot_values.update(
                {
                    "component": "foot",
                    "name": name,
                    "side": side,
                    "index": index,
                }
            )
            controller.box_controller(size=1, parent=foot)
            self.attirbute(foot, foot_attributes, foot_values)
            cmds.connectAttr(foot + ".worldMatrix", foot + ".matrices[0]")
            return foot

        foot = foot_guide("foot", "L", 0, leg_list[-1])

        # right arm
        arm_r_list = arm_guide("arm", "R", 0, parent=spine_list[-1])
        self.set_mirror(arm_list, arm_r_list)

        hand_r = hand_guide("hand", "R", 0, parent=arm_r_list[-1])
        self.set_mirror(hand, hand_r)

        leg_r_list = leg_guide("leg", "R", 0, parent=spine_list[0])
        self.set_mirror(leg_list, leg_r_list)

        foot_r = foot_guide("foot", "R", 0, parent=leg_r_list[-1])
        self.set_mirror(foot, foot_r)

        # TODO: neck, head, eyes, finger는 추후에 구성함.
        # neck
        neck_attributes = copy.deepcopy(component.attributes)
        neck_values = copy.deepcopy(component.values)

        # head
        head_attributes = copy.deepcopy(component.attributes)
        head_values = copy.deepcopy(component.values)


class Rig(component.Rig):

    def __init__(self, guide):
        super().__init__()
        # NOTE: 현재는 Rig class안에서 hierarchy를 한꺼번에 받지만,
        # 추후에 component화 할 때는 hierarchy를 우선으로 구한 뒤, component별로 build합니다.
        # 현재는 hierarchy 데이터가 의미가 없지만, 추후에 컴포넌트를 나눌시 이 데이터를 기반으로 구조를 생성합니다.
        self.hierarchy = component.get_guide_hierarchy(guide)

    def objects(self):

        assembly_guide = "biped_guide"
        asset_name = "_".join(assembly_guide.split("_")[:-1])
        # asset grp
        self.asset_grp = cmds.createNode(
            "transform", name="{0}_{1}".format(asset_name, core.group_extension)
        )
        self.cache_grp = cmds.createNode(
            "transform",
            name="{0}_cache_{1}".format(asset_name, core.group_extension),
            parent=self.asset_grp,
        )
        self.rig_grp = cmds.createNode(
            "transform",
            name="{0}_rig_{1}".format(asset_name, core.group_extension),
            parent=self.asset_grp,
        )
        self.skeleton = cmds.createNode(
            "transform", name="skeleton", parent=self.rig_grp
        )
        self.roots = cmds.createNode("transform", name="roots", parent=self.rig_grp)
        self.xxx = cmds.createNode("transform", name="xxx", parent=self.rig_grp)

        # assembly
        # assembly component인 guide이름을 인자로 넣으면 assembly setting하기.
        def assembly(guide, asset_name):
            root = cmds.createNode(
                "transform",
                name=asset_name + "_" + core.root_extension,
                parent=self.roots,
            )
            assembly_attributes, assembly_values = component.get_guide_attributes(guide)
            self.attribute(root, assembly_attributes, assembly_values)
            sub_ctl_count = assembly_values["sub_ctl_count"] or None
            origin_ctl_size = assembly_values["origin_ctl_size"]

            # controller
            origin_ctl = cmds.circle(
                radius=origin_ctl_size,
                normal=(0, 1, 0),
                name=self.generate_name(
                    name="origin", extension=core.controller_extension
                ),
                constructionHistory=False,
            )[0]
            origin_npo = cmds.createNode(
                "transform",
                name=self.generate_name(name="origin", extension=core.npo_extension),
                parent=root,
            )
            origin_ctl = cmds.parent(origin_ctl, origin_npo)[0]
            # TODO: sub ctl count 값을 받아서 그 숫자만큼 sub ctl를 생성해야 합니다.
            origin_ref = cmds.createNode(
                "transform",
                name=self.generate_name(name="origin", extension=core.ref_extension),
                parent=origin_ctl,
            )

            # joint
            origin_jnt = cmds.createNode(
                "joint",
                name=self.generate_name(name="origin", extension=core.joint_extension),
            )
            return root, origin_npo, origin_ctl, origin_ref, origin_jnt

        (
            self.origin_root,
            self.origin_npo,
            self.origin_ctl,
            self.origin_ref,
            self.origin_jnt,
        ) = assembly(assembly_guide, asset_name)

        # spine
        # NOTE: 링크드인에 있는 spine 게시물 보고 따라해보기 -> 그냥 nurbs에 spline 올려서 하자..
        spine_guide = "spine_C0_guide"

        def spine(guide):
            spine_attributes, spine_values = component.get_guide_attributes(guide)
            name = spine_values["name"]
            side = spine_values["side"]
            index = spine_values["index"]
            root = cmds.createNode(
                "transform",
                name=self.generate_name(
                    name, side, index, "", component.root_extension
                ),
            )

            self.attribute(root, spine_attributes, spine_values)
            matrices = [
                cmds.getAttr(f"{root}.{x}")
                for x in cmds.listAttr(root + ".matrices", multi=True)
            ]
            cmds.xform(root, worldSpace=True, matrix=matrices[0])

            # skeleton hierarchy 만들기
            skeletons = [
                self.generate_name(name, side, index, x, core.joint_extension)
                for x in ["0", "1", "2", "end"]
            ]
            core.joint.joint_chain(skeletons, matrices)

            # TODO: spine의 matrices를 어떤 방식으로 받을지 생각해보자.
            # spline ik joint hierarchy 만들기

            # 하위 fk hierarchy 만들기

            # controller 만들기.

            # nurbs surface 만들기.

        spine(spine_guide)

        # arm - left
        left_arm = cmds.createNode("transform", name="arm_L0_root")
        left_arm_attributes, left_arm_values = component.get_guide_attributes(
            "arm_L0_guide"
        )
        self.attribute(left_arm, left_arm_attributes, left_arm_values)

    def attributes(self):
        pass

    def operates(self):
        pass

    def connections(self):
        pass
