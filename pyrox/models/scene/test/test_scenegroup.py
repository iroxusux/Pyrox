"""Unit tests for SceneGroup (Type 1 grouping) and the IGroupable additions to SceneObject."""
import unittest

from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer,
)
from pyrox.models import (
    Scene,
    SceneObject,
    BasePhysicsBody,
)
from pyrox.models.scene.scenegroup import SceneGroup, SCENE_OBJECT_TYPE_GROUP


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

class _TestPhysicsBody(BasePhysicsBody):
    """Minimal concrete physics body for testing."""

    def __init__(
        self,
        name: str = "TestBody",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
    ):
        super().__init__(
            name=name,
            template_name="Base Physics Body",
            x=x,
            y=y,
            width=width,
            height=height,
            mass=1.0,
            body_type=BodyType.DYNAMIC,
            collider_type=ColliderType.RECTANGLE,
            collision_layer=CollisionLayer.DEFAULT,
        )


def _make_obj(name: str = "Obj", x: float = 0.0, y: float = 0.0,
              width: float = 10.0, height: float = 10.0) -> SceneObject:
    """Create a plain SceneObject with the given geometry."""
    return SceneObject(
        name=name,
        scene_object_type="test",
        physics_body=_TestPhysicsBody(name=name, x=x, y=y, width=width, height=height),
    )


def _make_group(name: str = "Group") -> SceneGroup:
    """Create a SceneGroup with a fresh physics body."""
    return SceneGroup(
        name=name,
        physics_body=_TestPhysicsBody(name=name),
    )


# ---------------------------------------------------------------------------
# IGroupable additions on SceneObject
# ---------------------------------------------------------------------------

class TestSceneObjectGroupId(unittest.TestCase):
    """Tests for the group_id field added to SceneObject."""

    def test_default_group_id_is_none(self):
        obj = _make_obj()
        self.assertIsNone(obj.get_group_id())

    def test_set_and_get_group_id(self):
        obj = _make_obj()
        obj.set_group_id("abc-123")
        self.assertEqual(obj.get_group_id(), "abc-123")

    def test_clear_group_id(self):
        obj = _make_obj()
        obj.set_group_id("abc-123")
        obj.set_group_id(None)
        self.assertIsNone(obj.get_group_id())

    def test_group_id_included_in_to_dict(self):
        obj = _make_obj()
        obj.set_group_id("grp-1")
        d = obj.to_dict()
        self.assertIn("group_id", d)
        self.assertEqual(d["group_id"], "grp-1")

    def test_group_id_none_included_in_to_dict(self):
        obj = _make_obj()
        d = obj.to_dict()
        self.assertIn("group_id", d)
        self.assertIsNone(d["group_id"])

    def test_group_id_roundtrip_from_dict(self):
        obj = _make_obj()
        obj.set_group_id("grp-restore")
        d = obj.to_dict()
        restored = SceneObject.from_dict(d)
        self.assertEqual(restored.get_group_id(), "grp-restore")

    def test_group_id_compiled_into_properties(self):
        obj = _make_obj()
        obj.set_group_id("grp-props")
        props = obj.get_properties()
        self.assertEqual(props.get("group_id"), "grp-props")


# ---------------------------------------------------------------------------
# SceneGroup construction
# ---------------------------------------------------------------------------

class TestSceneGroupInit(unittest.TestCase):

    def test_scene_object_type_is_group(self):
        g = _make_group()
        self.assertEqual(g.scene_object_type, SCENE_OBJECT_TYPE_GROUP)

    def test_initial_members_empty(self):
        g = _make_group()
        self.assertEqual(len(g.get_members()), 0)

    def test_has_valid_id(self):
        g = _make_group()
        self.assertIsNotNone(g.id)
        self.assertNotEqual(g.id, "")

    def test_name_set_correctly(self):
        g = _make_group("My Group")
        self.assertEqual(g.name, "My Group")


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

class TestSceneGroupMemberManagement(unittest.TestCase):

    def setUp(self):
        self.group = _make_group()
        self.obj_a = _make_obj("A", x=0, y=0, width=10, height=10)
        self.obj_b = _make_obj("B", x=20, y=0, width=10, height=10)

    def test_add_member(self):
        self.group.add_member(self.obj_a)
        self.assertIn(self.obj_a.id, self.group.get_members())

    def test_add_member_sets_group_id_on_object(self):
        self.group.add_member(self.obj_a)
        self.assertEqual(self.obj_a.get_group_id(), self.group.id)

    def test_add_self_raises(self):
        with self.assertRaises(ValueError):
            self.group.add_member(self.group)

    def test_remove_member(self):
        self.group.add_member(self.obj_a)
        self.group.remove_member(self.obj_a.id)
        self.assertNotIn(self.obj_a.id, self.group.get_members())

    def test_remove_member_clears_group_id(self):
        self.group.add_member(self.obj_a)
        self.group.remove_member(self.obj_a.id)
        self.assertIsNone(self.obj_a.get_group_id())

    def test_remove_nonexistent_member_is_noop(self):
        # Should not raise
        self.group.remove_member("nonexistent-id")

    def test_get_member_existing(self):
        self.group.add_member(self.obj_a)
        self.assertIs(self.group.get_member(self.obj_a.id), self.obj_a)

    def test_get_member_missing_returns_none(self):
        self.assertIsNone(self.group.get_member("missing"))

    def test_has_member_true(self):
        self.group.add_member(self.obj_a)
        self.assertTrue(self.group.has_member(self.obj_a.id))

    def test_has_member_false(self):
        self.assertFalse(self.group.has_member(self.obj_a.id))

    def test_get_member_ids(self):
        self.group.add_member(self.obj_a)
        self.group.add_member(self.obj_b)
        ids = self.group.get_member_ids()
        self.assertIn(self.obj_a.id, ids)
        self.assertIn(self.obj_b.id, ids)
        self.assertEqual(len(ids), 2)

    def test_get_members_returns_copy(self):
        self.group.add_member(self.obj_a)
        members = self.group.get_members()
        members.clear()
        # Internal dict should be unchanged
        self.assertEqual(len(self.group.get_members()), 1)


# ---------------------------------------------------------------------------
# Bounding box recomputation
# ---------------------------------------------------------------------------

class TestSceneGroupBounds(unittest.TestCase):

    def test_recompute_bounds_single_member(self):
        group = _make_group()
        obj = _make_obj(x=5, y=10, width=20, height=30)
        group.add_member(obj)
        self.assertAlmostEqual(group.x, 5.0)
        self.assertAlmostEqual(group.y, 10.0)
        self.assertAlmostEqual(group.width, 20.0)
        self.assertAlmostEqual(group.height, 30.0)

    def test_recompute_bounds_two_members(self):
        group = _make_group()
        # obj_a: x=0..10, y=0..10
        obj_a = _make_obj(x=0, y=0, width=10, height=10)
        # obj_b: x=20..40, y=5..25
        obj_b = _make_obj(x=20, y=5, width=20, height=20)
        group.add_member(obj_a)
        group.add_member(obj_b)
        # Expected bounding box: x=0, y=0, width=40, height=25
        self.assertAlmostEqual(group.x, 0.0)
        self.assertAlmostEqual(group.y, 0.0)
        self.assertAlmostEqual(group.width, 40.0)
        self.assertAlmostEqual(group.height, 25.0)

    def test_recompute_bounds_updates_after_remove(self):
        group = _make_group()
        obj_a = _make_obj(x=0, y=0, width=10, height=10)
        obj_b = _make_obj(x=100, y=100, width=10, height=10)
        group.add_member(obj_a)
        group.add_member(obj_b)
        group.remove_member(obj_b.id)
        # Bounds should now reflect only obj_a
        self.assertAlmostEqual(group.width, 10.0)
        self.assertAlmostEqual(group.height, 10.0)

    def test_recompute_bounds_no_members_is_noop(self):
        group = _make_group()
        # Should not raise
        group.recompute_bounds()


# ---------------------------------------------------------------------------
# move_delta
# ---------------------------------------------------------------------------

class TestSceneGroupMoveDelta(unittest.TestCase):

    def test_move_delta_translates_members(self):
        group = _make_group()
        obj = _make_obj(x=10, y=20, width=5, height=5)
        group.add_member(obj)
        group.move_delta(15, -5)
        self.assertAlmostEqual(obj.x, 25.0)
        self.assertAlmostEqual(obj.y, 15.0)

    def test_move_delta_translates_group_anchor(self):
        group = _make_group()
        obj = _make_obj(x=0, y=0, width=10, height=10)
        group.add_member(obj)
        initial_x = group.x
        initial_y = group.y
        group.move_delta(50, 30)
        self.assertAlmostEqual(group.x, initial_x + 50)
        self.assertAlmostEqual(group.y, initial_y + 30)

    def test_move_delta_zero_noop(self):
        group = _make_group()
        obj = _make_obj(x=5, y=5, width=5, height=5)
        group.add_member(obj)
        group.move_delta(0, 0)
        self.assertAlmostEqual(obj.x, 5.0)
        self.assertAlmostEqual(obj.y, 5.0)

    def test_move_delta_multiple_members(self):
        group = _make_group()
        obj_a = _make_obj(x=0, y=0, width=5, height=5)
        obj_b = _make_obj(x=10, y=10, width=5, height=5)
        group.add_member(obj_a)
        group.add_member(obj_b)
        group.move_delta(10, 20)
        self.assertAlmostEqual(obj_a.x, 10.0)
        self.assertAlmostEqual(obj_a.y, 20.0)
        self.assertAlmostEqual(obj_b.x, 20.0)
        self.assertAlmostEqual(obj_b.y, 30.0)


# ---------------------------------------------------------------------------
# disband
# ---------------------------------------------------------------------------

class TestSceneGroupDisband(unittest.TestCase):

    def test_disband_returns_all_members(self):
        group = _make_group()
        obj_a = _make_obj("A")
        obj_b = _make_obj("B")
        group.add_member(obj_a)
        group.add_member(obj_b)
        members = group.disband()
        self.assertEqual(len(members), 2)
        ids = {m.id for m in members}
        self.assertIn(obj_a.id, ids)
        self.assertIn(obj_b.id, ids)

    def test_disband_clears_group_id_from_members(self):
        group = _make_group()
        obj = _make_obj()
        group.add_member(obj)
        group.disband()
        self.assertIsNone(obj.get_group_id())

    def test_disband_empties_members(self):
        group = _make_group()
        group.add_member(_make_obj("A"))
        group.disband()
        self.assertEqual(len(group.get_members()), 0)

    def test_disband_empty_group(self):
        group = _make_group()
        members = group.disband()
        self.assertEqual(members, [])


# ---------------------------------------------------------------------------
# update delegate
# ---------------------------------------------------------------------------

class TestSceneGroupUpdate(unittest.TestCase):

    def test_update_calls_member_update(self):
        group = _make_group()
        updated = []

        class TrackingObj(SceneObject):
            def update(self, dt: float) -> None:
                updated.append(dt)

        obj = TrackingObj(
            name="tracker",
            scene_object_type="test",
            physics_body=_TestPhysicsBody(),
        )
        group.add_member(obj)
        group.update(0.016)
        self.assertEqual(updated, [0.016])


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSceneGroupSerialization(unittest.TestCase):

    def _make_populated_group(self):
        group = _make_group("Grp")
        obj_a = _make_obj("A", x=0, y=0, width=5, height=5)
        obj_b = _make_obj("B", x=10, y=0, width=5, height=5)
        group.add_member(obj_a)
        group.add_member(obj_b)
        return group, obj_a, obj_b

    def test_to_dict_contains_member_ids(self):
        group, obj_a, obj_b = self._make_populated_group()
        d = group.to_dict()
        self.assertIn("member_ids", d)
        self.assertIn(obj_a.id, d["member_ids"])
        self.assertIn(obj_b.id, d["member_ids"])

    def test_to_dict_scene_object_type(self):
        group = _make_group()
        d = group.to_dict()
        self.assertEqual(d["scene_object_type"], SCENE_OBJECT_TYPE_GROUP)

    def test_from_dict_creates_shell_with_pending_ids(self):
        group, obj_a, obj_b = self._make_populated_group()
        d = group.to_dict()
        shell = SceneGroup.from_dict(d)
        pending = object.__getattribute__(shell, "_pending_member_ids")
        self.assertIn(obj_a.id, pending)
        self.assertIn(obj_b.id, pending)

    def test_from_dict_no_members_in_from_dict_shell(self):
        group, _, _ = self._make_populated_group()
        d = group.to_dict()
        shell = SceneGroup.from_dict(d)
        # Members aren't linked yet — that's Pass 2 in Scene.from_dict
        self.assertEqual(len(shell.get_members()), 0)


# ---------------------------------------------------------------------------
# Scene.group_objects and Scene.ungroup
# ---------------------------------------------------------------------------

class TestSceneGroupHelpers(unittest.TestCase):

    def setUp(self):
        self.scene = Scene()
        self.obj_a = _make_obj("A", x=0, y=0, width=10, height=10)
        self.obj_b = _make_obj("B", x=20, y=0, width=10, height=10)
        self.scene.add_scene_object(self.obj_a)
        self.scene.add_scene_object(self.obj_b)

    def test_group_objects_creates_group_in_scene(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id], name="TestGroup")
        self.assertIn(group.id, self.scene.scene_objects)

    def test_group_objects_returns_scene_group(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        self.assertIsInstance(group, SceneGroup)

    def test_group_objects_members_are_tagged(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        self.assertEqual(self.obj_a.get_group_id(), group.id)
        self.assertEqual(self.obj_b.get_group_id(), group.id)

    def test_group_objects_members_remain_in_scene(self):
        self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        self.assertIn(self.obj_a.id, self.scene.scene_objects)
        self.assertIn(self.obj_b.id, self.scene.scene_objects)

    def test_group_objects_unknown_id_raises(self):
        with self.assertRaises(ValueError):
            self.scene.group_objects(["nonexistent-id"])

    def test_group_objects_empty_list_raises(self):
        with self.assertRaises(ValueError):
            self.scene.group_objects([])

    def test_ungroup_removes_group_from_scene(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        self.scene.ungroup(group.id)
        self.assertNotIn(group.id, self.scene.scene_objects)

    def test_ungroup_returns_members(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        members = self.scene.ungroup(group.id)
        ids = {m.id for m in members}
        self.assertIn(self.obj_a.id, ids)
        self.assertIn(self.obj_b.id, ids)

    def test_ungroup_clears_group_id_from_members(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        self.scene.ungroup(group.id)
        self.assertIsNone(self.obj_a.get_group_id())
        self.assertIsNone(self.obj_b.get_group_id())

    def test_ungroup_members_stay_in_scene(self):
        group = self.scene.group_objects([self.obj_a.id, self.obj_b.id])
        self.scene.ungroup(group.id)
        self.assertIn(self.obj_a.id, self.scene.scene_objects)
        self.assertIn(self.obj_b.id, self.scene.scene_objects)

    def test_ungroup_nonexistent_id_raises(self):
        with self.assertRaises(ValueError):
            self.scene.ungroup("nonexistent-id")

    def test_ungroup_non_group_raises(self):
        with self.assertRaises(ValueError):
            self.scene.ungroup(self.obj_a.id)


# ---------------------------------------------------------------------------
# Scene.from_dict two-pass load
# ---------------------------------------------------------------------------

class TestSceneFromDictTwoPass(unittest.TestCase):
    """Verify that Scene.from_dict correctly links group members (Pass 2)."""

    def _build_scene_dict(self):
        """Build a Scene dict containing a SceneGroup with two members."""
        obj_a = _make_obj("A", x=0, y=0)
        obj_b = _make_obj("B", x=20, y=0)
        scene = Scene()
        scene.add_scene_object(obj_a)
        scene.add_scene_object(obj_b)
        group = scene.group_objects([obj_a.id, obj_b.id], name="G")
        return scene.to_dict(), group.id, obj_a.id, obj_b.id

    def test_from_dict_creates_group(self):
        d, group_id, _, _ = self._build_scene_dict()
        restored = Scene.from_dict(d)
        self.assertIn(group_id, restored.scene_objects)

    def test_from_dict_group_has_members_linked(self):
        d, group_id, id_a, id_b = self._build_scene_dict()
        restored = Scene.from_dict(d)
        group = restored.get_scene_object(group_id)
        self.assertIsInstance(group, SceneGroup)
        self.assertTrue(group.has_member(id_a))  # type: ignore
        self.assertTrue(group.has_member(id_b))  # type: ignore

    def test_from_dict_members_are_in_scene(self):
        d, _, id_a, id_b = self._build_scene_dict()
        restored = Scene.from_dict(d)
        self.assertIn(id_a, restored.scene_objects)
        self.assertIn(id_b, restored.scene_objects)

    def test_from_dict_group_id_set_on_members(self):
        d, group_id, id_a, id_b = self._build_scene_dict()
        restored = Scene.from_dict(d)
        self.assertEqual(restored.get_scene_object(id_a).get_group_id(), group_id)  # type: ignore
        self.assertEqual(restored.get_scene_object(id_b).get_group_id(), group_id)  # type: ignore

    def test_from_dict_plain_objects_still_loaded(self):
        """Plain (non-group) objects continue to deserialize correctly."""
        obj = _make_obj("Plain")
        scene = Scene()
        scene.add_scene_object(obj)
        d = scene.to_dict()
        restored = Scene.from_dict(d)
        self.assertIn(obj.id, restored.scene_objects)


if __name__ == "__main__":
    unittest.main()
