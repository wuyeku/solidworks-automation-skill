"""@brief SolidWorks 2025 镜像特征选择标记回归测试。"""

from scripts import sw_part


class _Feature:
    def __init__(self, type_name="Cut", name="凸台-拉伸1"):
        self.type_name = type_name
        self.Name = name

    def GetTypeName2(self):
        return self.type_name

    def Select2(self, append, mark):
        self.selection = (append, mark)
        return True


class _Body:
    Name = "实体1"

    def __init__(self):
        self.selection = None

    def Select(self, append, mark):
        self.selection = (append, mark)
        return True


class _Selector:
    def __init__(self, failures=()):
        self.failures = set(failures)
        self.calls = []

    def SelectByID2(self, name, entity_type, x, y, z, append, mark, callout, flags):
        self.calls.append((name, entity_type, append, mark))
        return name not in self.failures


class _FeatureManager:
    def __init__(self):
        self.arguments = None

    def InsertMirrorFeature2(self, *arguments):
        self.arguments = arguments
        return object()


class _Model:
    def __init__(self, selector, feature=None, bodies=None, feature_type="Cut"):
        self.Extension = selector
        self.FeatureManager = _FeatureManager()
        self.feature = feature or _Feature(feature_type)
        self.bodies = bodies if bodies is not None else []
        self.FirstFeature = self.feature

    def ClearSelection2(self, clear_all):
        self.cleared = clear_all
        return True

    def FeatureByName(self, _name):
        return self.feature

    def GetBodies2(self, _type, _visible):
        return tuple(self.bodies) if self.bodies else None


def test_mirror_feature_uses_solidworks_2025_feature_and_plane_marks():
    selector = _Selector()
    model = _Model(selector)

    result = sw_part.mirror_feature(model, "凸台-拉伸1", "Right Plane")

    assert result is not None
    assert selector.calls == [
        ("Right Plane", "PLANE", False, 2),
        ("凸台-拉伸1", "BODYFEATURE", True, 1),
    ]
    assert model.FeatureManager.arguments == (False, False, False, False, 0)


def test_mirror_feature_uses_localized_plane_alias():
    selector = _Selector(failures={"Right Plane"})
    model = _Model(selector)

    result = sw_part.mirror_feature(model, "凸台-拉伸1", "Right Plane")

    assert result is not None
    assert selector.calls[0] == ("Right Plane", "PLANE", False, 2)
    assert selector.calls[1] == ("右视基准面", "PLANE", False, 2)


def test_mirror_feature_reports_unselected_source_feature():
    selector = _Selector(failures={"不存在的特征"})
    model = _Model(selector)
    model.FeatureByName = lambda _name: None

    try:
        sw_part.mirror_feature(model, "不存在的特征", "Right Plane")
    except RuntimeError as error:
        assert "无法选择待镜像特征" in str(error)
    else:
        raise AssertionError("missing feature should raise a diagnostic error")


def test_mirror_feature_uses_body_mode_for_initial_extrusion():
    selector = _Selector()
    body = _Body()
    model = _Model(selector, bodies=[body], feature_type="Extrusion")

    result = sw_part.mirror_feature(model, "凸台-拉伸1", "Right Plane")

    assert result is not None
    assert body.selection == (True, 256)
    assert model.FeatureManager.arguments == (True, False, False, False, 0)


def test_mirror_feature_uses_geometry_pattern_for_fillet():
    selector = _Selector()
    model = _Model(selector, feature_type="Fillet")

    result = sw_part.mirror_feature(model, "圆角1", "Right Plane")

    assert result is not None
    assert model.FeatureManager.arguments == (False, True, False, False, 0)
