"""Unit tests for SceneObject class."""
import unittest
from typing import Any, Dict
from pyrox.interfaces import (
    BodyType,
    CardinalDirection,
    ColliderType,
    CollisionLayer,
    Connection,
)
from pyrox.models import (
    SceneObject,
    BasePhysicsBody,
    Material,
)


class TestSceneObject(unittest.TestCase):
    """Test cases for SceneObject class."""

    def setUp(self):
        """Set up test fixtures."""

        class TestSceneObject(SceneObject):
            """Test scene_object implementation."""

            def update(self, dt: float) -> None:
                """Test implementation."""
                pass

            def read_inputs(self) -> Dict[str, Any]:
                """Test implementation."""
                return {}

            def write_outputs(self) -> Dict[str, Any]:
                """Test implementation."""
                return {}

        class TestBasePhysicsBody(BasePhysicsBody):
            """Test physics body implementation."""

            def __init__(
                self,
                name: str = "TestBody",
                x: float = 0.0,
                y: float = 0.0,
                width: float = 10.0,
                height: float = 10.0,
                mass: float = 1.0,
                roll: float = 5.0,
                pitch: float = 10.0,
                yaw: float = 15.0,
                collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
                collision_mask: list[CollisionLayer] | None = None,
                material: Material | None = None,
            ):
                """Initialize test physics body."""
                super().__init__(
                    name=name,
                    template_name="Base Physics Body",
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    mass=mass,
                    roll=roll,
                    pitch=pitch,
                    yaw=yaw,
                    body_type=BodyType.DYNAMIC,
                    collider_type=ColliderType.RECTANGLE,
                    collision_layer=collision_layer,
                    collision_mask=collision_mask,
                    material=material,
                )

        self.TestSceneObject = TestSceneObject
        self.TestPhysicsBody = TestBasePhysicsBody

    def test_init_with_required_params(self):
        """Test SceneObject initialization with required parameters."""
        obj = SceneObject(
            name="TestObject",
            scene_object_type="TestType",
            physics_body=self.TestPhysicsBody()
        )

        obj_id = obj.get_id()
        self.assertIsNotNone(obj_id)
        self.assertEqual(obj.get_name(), "TestObject")
        self.assertEqual(obj.get_scene_object_type(), "TestType")
        self.assertEqual(obj.get_description(), "")
        self.assertIsInstance(obj.get_properties(), dict)
        self.assertGreater(len(obj.get_properties()), 4)

    def test_init_with_all_params(self):
        """Test SceneObject initialization with all parameters."""
        properties = {"custom_key": "custom_value", "number": 42}

        body = self.TestPhysicsBody(
            x=10.0,
            y=20.0,
            width=100.0,
            height=50.0,
            mass=5.0,
        )
        obj = SceneObject(
            name="FullObject",
            scene_object_type="FullType",
            physics_body=body,
            description="Test description",
            properties=properties,
        )

        obj_id = obj.get_id()
        self.assertIsNotNone(obj_id)
        self.assertEqual(obj.get_name(), "FullObject")
        self.assertEqual(obj.get_scene_object_type(), "FullType")
        self.assertEqual(obj.get_description(), "Test description")
        self.assertEqual(obj.get_properties(), properties)
        self.assertEqual(obj.physics_body.get_x(), 10.0)
        self.assertEqual(obj.physics_body.get_y(), 20.0)
        self.assertEqual(obj.physics_body.get_width(), 100.0)
        self.assertEqual(obj.physics_body.get_height(), 50.0)

    def test_get_id(self):
        """Test SceneObject.get_id() method."""
        obj = SceneObject(
            name="Name",
            scene_object_type="Type",
            physics_body=self.TestPhysicsBody()
        )
        obj_id = obj.get_id()
        self.assertIsNotNone(obj_id)
        self.assertIsInstance(obj_id, str)

    def test_set_id(self):
        """Test SceneObject.set_id() method raises NotImplementedError."""
        obj = SceneObject(name="Name", scene_object_type="Type", physics_body=self.TestPhysicsBody())
        obj.set_id("new_id")

    def test_id_property(self):
        """Test SceneObject id property access."""
        obj = SceneObject(name="Name", scene_object_type="Type", physics_body=self.TestPhysicsBody())
        obj_id = obj.id
        self.assertIsNotNone(obj_id)
        self.assertIsInstance(obj_id, str)

    def test_get_properties(self):
        """Test SceneObject.get_properties() method."""
        properties = {"test": "value", "number": 123}
        obj = SceneObject(
            name="Name",
            scene_object_type="Type",
            properties=properties,
            physics_body=self.TestPhysicsBody()
        )

        result = obj.get_properties()
        self.assertEqual(result, properties)
        self.assertIsInstance(result, dict)

    def test_set_properties(self):
        """Test SceneObject.set_properties() method."""
        obj = SceneObject(name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody()
                          )
        new_props = {"new_key": "new_value"}

        obj.set_properties(new_props)
        self.assertEqual(obj.get_properties(), new_props)

    def test_set_properties_invalid_type_raises_error(self):
        """Test that set_properties raises error for non-dict."""
        obj = SceneObject(name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())

        with self.assertRaises(ValueError) as context:
            obj.set_properties("not a dict")  # type: ignore

        self.assertIn("must be a dictionary", str(context.exception))

    def test_properties_property(self):
        """Test SceneObject properties property access."""
        properties = {"key": "value"}
        obj = SceneObject(
            name="Name",
            scene_object_type="Type",
            properties=properties,
            physics_body=self.TestPhysicsBody()
        )
        self.assertEqual(obj.properties, properties)

    def test_get_scene_object_type(self):
        """Test SceneObject.get_scene_object_type() method."""
        obj = SceneObject(name="Name", scene_object_type="CustomType",
                          physics_body=self.TestPhysicsBody())
        self.assertEqual(obj.get_scene_object_type(), "CustomType")

    def test_set_scene_object_type(self):
        """Test SceneObject.set_scene_object_type() method."""
        obj = SceneObject(name="Name", scene_object_type="OldType",
                          physics_body=self.TestPhysicsBody())
        obj.set_scene_object_type("NewType")
        self.assertEqual(obj.get_scene_object_type(), "NewType")

    def test_scene_object_type_property(self):
        """Test SceneObject scene_object_type property access."""
        obj = SceneObject(name="Name", scene_object_type="PropType",
                          physics_body=self.TestPhysicsBody())
        self.assertEqual(obj.scene_object_type, "PropType")

    def test_to_dict(self):
        """Test SceneObject.to_dict() method."""
        properties = {"key": "value", "num": 42}
        obj = SceneObject(
            name="DictObject",
            scene_object_type="DictType",
            description="Dict description",
            properties=properties,
            physics_body=self.TestPhysicsBody()
        )

        result = obj.to_dict()
        obj_id = obj.get_id()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], obj_id)
        self.assertEqual(result["name"], "DictObject")
        self.assertEqual(result["scene_object_type"], "DictType")
        self.assertEqual(result["description"], "Dict description")
        self.assertEqual(result["properties"], properties)

    def test_from_dict(self):
        """Test SceneObject.from_dict() class method."""
        data = {
            "id": "from_dict_test",
            "name": "Base Physics Body",
            "scene_object_type": "FromDictType",
            "description": "From dict description",
            "properties": {"loaded": True},
            "body": {
                "template_name": "Base Physics Body",
                "name": "TestBody",
                "body_type": "DYNAMIC",
                "collision_layer": "DEFAULT",
                "collider_type": "RECTANGLE",
                "x": 0.0,
                "y": 0.0,
                "width": 10.0,
                "height": 10.0,
                "mass": 1.0,
            }
        }

        obj = SceneObject.from_dict(data)

        # ID comes from physics body, not from dict
        self.assertIsNotNone(obj.get_id())
        self.assertEqual(obj.get_name(), "Base Physics Body")
        self.assertEqual(obj.get_scene_object_type(), "FromDictType")
        self.assertEqual(obj.get_description(), "From dict description")
        self.assertEqual(obj.get_properties()['loaded'], True)

    def test_from_dict_with_defaults(self):
        """Test SceneObject.from_dict() with missing optional fields."""
        data = {
            "id": "minimal",
            "name": "Base Physics Body",
            "scene_object_type": "MinimalType",
            "body": {
                "template_name": "Base Physics Body",
                "name": "TestBody",
                "body_type": "DYNAMIC",
                "collision_layer": "DEFAULT",
                "collider_type": "RECTANGLE",
                "x": 0.0,
                "y": 0.0,
                "width": 10.0,
                "height": 10.0,
                "mass": 1.0,
            }
        }

        obj = SceneObject.from_dict(data)

        # ID comes from physics body, not from dict
        self.assertIsNotNone(obj.get_id())
        self.assertEqual(obj.get_name(), "Base Physics Body")
        self.assertEqual(obj.get_scene_object_type(), "MinimalType")
        self.assertEqual(obj.get_description(), "")
        self.assertIsInstance(obj.get_properties(), dict)

    def test_update_method_exists(self):
        """Test that update method exists and is callable."""
        obj = SceneObject(name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())

        self.assertTrue(hasattr(obj, 'update'))
        self.assertTrue(callable(obj.update))

        # Should not raise
        obj.update(0.016)

    def test_roundtrip_to_dict_from_dict(self):
        """Test roundtrip conversion to/from dict."""
        original = SceneObject(
            name="Base Physics Body",
            scene_object_type="RoundtripType",
            description="Roundtrip test",
            properties={"value": 123, "text": "test"},
            physics_body=self.TestPhysicsBody()
        )

        data = original.to_dict()
        loaded = SceneObject.from_dict(data)

        # ID will be different since loaded creates new physics body
        # But other properties should match
        self.assertEqual(loaded.get_name(), original.get_name())
        self.assertEqual(loaded.get_scene_object_type(), original.get_scene_object_type())
        self.assertEqual(loaded.get_description(), original.get_description())
        self.assertEqual(loaded.get_properties(), original.get_properties())

    def test_set_property_sets_attribute_and_dictionary(self):
        """Test that set_property updates the physics body attribute directly.

        The properties snapshot reflects the new value on the next call to
        get_properties() (via _compile_properties), not via a direct write.
        """
        obj = SceneObject(name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())

        obj.set_property("x", 10)

        self.assertEqual(obj.physics_body.get_x(), 10)
        self.assertEqual(obj.properties.get("x"), 10)


# ---------------------------------------------------------------------------
# Visual properties: sprite_path and bg_color
# ---------------------------------------------------------------------------

class TestSceneObjectVisualProperties(unittest.TestCase):
    """Tests for sprite_path and bg_color on SceneObject."""

    def setUp(self):
        self.body = BasePhysicsBody(
            name="Body",
            template_name="Base Physics Body",
            x=0.0, y=0.0, width=10.0, height=10.0,
        )

    def _make(self, **kwargs) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
            **kwargs,
        )

    # ---- sprite_path ----

    def test_sprite_path_default_is_none(self):
        obj = self._make()
        self.assertIsNone(obj.sprite_path)

    def test_sprite_path_from_constructor(self):
        obj = self._make(sprite_path="/imgs/gate.png")
        self.assertEqual(obj.sprite_path, "/imgs/gate.png")

    def test_sprite_path_setter(self):
        obj = self._make()
        obj.sprite_path = "/imgs/piston.png"
        self.assertEqual(obj.sprite_path, "/imgs/piston.png")

    def test_sprite_path_can_be_cleared(self):
        obj = self._make(sprite_path="/imgs/gate.png")
        obj.sprite_path = None
        self.assertIsNone(obj.sprite_path)

    def test_sprite_path_from_properties_dict(self):
        """sprite_path in the properties dict is honoured when no constructor arg given."""
        obj = self._make(properties={"sprite_path": "/imgs/from_dict.png"})
        self.assertEqual(obj.sprite_path, "/imgs/from_dict.png")

    def test_sprite_path_constructor_overrides_properties_dict(self):
        obj = self._make(
            sprite_path="/imgs/explicit.png",
            properties={"sprite_path": "/imgs/in_dict.png"},
        )
        self.assertEqual(obj.sprite_path, "/imgs/explicit.png")

    # ---- bg_color ----

    def test_bg_color_default(self):
        obj = self._make()
        self.assertEqual(obj.bg_color, "#4a9eff")

    def test_bg_color_from_constructor(self):
        obj = self._make(bg_color="#ff0000")
        self.assertEqual(obj.bg_color, "#ff0000")

    def test_bg_color_setter(self):
        obj = self._make()
        obj.bg_color = "#00ff00"
        self.assertEqual(obj.bg_color, "#00ff00")

    def test_bg_color_from_properties_dict_color_key(self):
        """Legacy 'color' key in properties dict is used as bg_color fallback."""
        obj = self._make(properties={"color": "#aabbcc"})
        self.assertEqual(obj.bg_color, "#aabbcc")

    def test_bg_color_from_properties_dict_bg_color_key(self):
        obj = self._make(properties={"bg_color": "#112233"})
        self.assertEqual(obj.bg_color, "#112233")

    # ---- compile_properties ----

    def test_compile_properties_includes_sprite_path(self):
        obj = self._make(sprite_path="/imgs/gate.png")
        props = obj.get_properties()
        self.assertEqual(props.get("sprite_path"), "/imgs/gate.png")

    def test_compile_properties_includes_bg_color(self):
        obj = self._make(bg_color="#cafeba")
        props = obj.get_properties()
        self.assertEqual(props.get("bg_color"), "#cafeba")

    def test_compile_properties_backward_compat_color_alias(self):
        """'color' key should equal bg_color for backward compatibility."""
        obj = self._make(bg_color="#cafeba")
        props = obj.get_properties()
        self.assertEqual(props.get("color"), "#cafeba")

    def test_compile_properties_sprite_path_none_preserved(self):
        obj = self._make()
        props = obj.get_properties()
        self.assertIn("sprite_path", props)
        self.assertIsNone(props["sprite_path"])

    # ---- to_dict / from_dict roundtrip ----

    def test_to_dict_includes_sprite_path(self):
        obj = self._make(sprite_path="/imgs/gate.png")
        data = obj.to_dict()
        self.assertEqual(data["properties"]["sprite_path"], "/imgs/gate.png")

    def test_to_dict_includes_bg_color(self):
        obj = self._make(bg_color="#ff8800")
        data = obj.to_dict()
        self.assertEqual(data["properties"]["bg_color"], "#ff8800")

    def test_roundtrip_sprite_path(self):
        obj = self._make(sprite_path="/imgs/piston.png")
        data = obj.to_dict()
        loaded = SceneObject.from_dict(data)
        self.assertEqual(loaded.sprite_path, "/imgs/piston.png")

    def test_roundtrip_bg_color(self):
        obj = self._make(bg_color="#123456")
        data = obj.to_dict()
        loaded = SceneObject.from_dict(data)
        self.assertEqual(loaded.bg_color, "#123456")

    def test_roundtrip_defaults_preserved(self):
        obj = self._make()
        data = obj.to_dict()
        loaded = SceneObject.from_dict(data)
        self.assertIsNone(loaded.sprite_path)
        self.assertEqual(loaded.bg_color, "#4a9eff")


# ---------------------------------------------------------------------------
# Animator integration on SceneObject
# ---------------------------------------------------------------------------

def _obj_advance(obj, total_dt: float, step: float = 0.05) -> None:
    """Simulate *total_dt* seconds by calling obj.update() in small increments.

    Because SceneAnimator.update() caps each call at 0.1 s (real-time guard),
    tests that want to simulate several seconds must use this helper.
    """
    remaining = total_dt
    while remaining > 1e-9:
        dt = min(remaining, step)
        obj.update(dt)
        remaining -= dt


class TestSceneObjectAnimator(unittest.TestCase):
    """Tests that SceneObject exposes and ticks a SceneAnimator correctly."""

    def _make(self) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
        )

    def _gate_clip(self, mode=None):
        from pyrox.models.scene.animation import AnimationClip, AnimationMode, AnimationTrack, AnimationEasing
        clip = AnimationClip("gate_open", 1.0, mode or AnimationMode.ONCE)
        clip.add_track(
            AnimationTrack("x", easing=AnimationEasing.LINEAR)
            .add_keyframe(0.0, 0.0)
            .add_keyframe(1.0, 90.0)
        )
        return clip

    def test_animator_property_returns_scene_animator(self):
        from pyrox.models.scene.animation import SceneAnimator
        obj = self._make()
        self.assertIsInstance(obj.animator, SceneAnimator)

    def test_each_object_has_independent_animator(self):
        obj1 = self._make()
        obj2 = self._make()
        self.assertIsNot(obj1.animator, obj2.animator)

    def test_update_ticks_animator_when_playing(self):
        """update(dt) should advance the animator and write property values."""
        obj = self._make()
        obj.animator.add_clip(self._gate_clip())
        obj.animator.play("gate_open")

        _obj_advance(obj, 0.5)  # half-way through 1 s clip → yaw = 45
        self.assertAlmostEqual(obj.physics_body.x, 45.0, places=1)

    def test_update_at_full_duration_stops_once_clip(self):
        from pyrox.models.scene.animation import AnimationMode
        obj = self._make()
        obj.animator.add_clip(self._gate_clip(AnimationMode.ONCE))
        obj.animator.play("gate_open")

        _obj_advance(obj, 2.0)  # past end
        self.assertFalse(obj.animator.is_playing)
        self.assertAlmostEqual(obj.physics_body.x, 90.0, places=1)

    def test_update_does_nothing_when_not_playing(self):
        obj = self._make()
        obj.update(0.5)  # no clip registered → should not raise
        # yaw stays at initial value
        self.assertAlmostEqual(obj.physics_body.x, 0.0, places=3)

    def test_piston_ping_pong_returns_to_origin(self):
        from pyrox.models.scene.animation import AnimationClip, AnimationMode, AnimationTrack
        clip = AnimationClip("piston", 0.8, AnimationMode.PING_PONG)
        clip.add_track(
            AnimationTrack("x")
            .add_keyframe(0.0, 0.0)
            .add_keyframe(0.8, 50.0)
        )
        obj = self._make()
        obj.animator.add_clip(clip)
        obj.animator.play("piston")

        # forward 0.8 + backward 0.8 = 1.6 s → back at x == 0
        _obj_advance(obj, 1.6)
        self.assertAlmostEqual(obj.x, 0.0, places=0)

    def test_on_complete_callback_via_object_update(self):
        from unittest.mock import MagicMock
        obj = self._make()
        obj.animator.add_clip(self._gate_clip())
        cb = MagicMock()
        obj.animator.add_on_complete(cb)
        obj.animator.play("gate_open")

        _obj_advance(obj, 2.0)  # fires completion
        cb.assert_called_once()


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

class TestSceneObjectTags(unittest.TestCase):
    """Tests for the tag system on SceneObject."""

    def _make(self, **kwargs) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
            **kwargs,
        )

    def test_tags_default_empty(self):
        obj = self._make()
        self.assertEqual(obj.get_tags(), [])

    def test_tags_from_constructor(self):
        obj = self._make(tags=["mobile", "interactive"])
        self.assertIn("mobile", obj.get_tags())
        self.assertIn("interactive", obj.get_tags())

    def test_set_tags(self):
        obj = self._make(tags=["old"])
        obj.set_tags(["new1", "new2"])
        self.assertEqual(obj.get_tags(), ["new1", "new2"])

    def test_has_tag_true(self):
        obj = self._make(tags=["enemy"])
        self.assertTrue(obj.has_tag("enemy"))

    def test_has_tag_false(self):
        obj = self._make()
        self.assertFalse(obj.has_tag("enemy"))

    def test_add_tag(self):
        obj = self._make()
        obj.add_tag("pickup")
        self.assertIn("pickup", obj.get_tags())

    def test_add_tag_no_duplicate(self):
        obj = self._make(tags=["unique"])
        obj.add_tag("unique")
        self.assertEqual(obj.get_tags().count("unique"), 1)

    def test_remove_tag(self):
        obj = self._make(tags=["temp"])
        obj.remove_tag("temp")
        self.assertNotIn("temp", obj.get_tags())

    def test_remove_tag_absent_is_no_op(self):
        obj = self._make()
        obj.remove_tag("nonexistent")  # should not raise

    def test_tags_property(self):
        obj = self._make(tags=["a", "b"])
        self.assertEqual(obj.tags, ["a", "b"])

    def test_to_dict_includes_tags(self):
        obj = self._make(tags=["foo", "bar"])
        data = obj.to_dict()
        self.assertIn("tags", data)
        self.assertEqual(data["tags"], ["foo", "bar"])

    def test_from_dict_restores_tags(self):
        obj = self._make(tags=["restored"])
        data = obj.to_dict()
        loaded = SceneObject.from_dict(data)
        self.assertIn("restored", loaded.get_tags())

    def test_tags_constructor_is_independent_copy(self):
        """Mutating the original list after construction should not affect the object."""
        source = ["a", "b"]
        obj = self._make(tags=source)
        source.append("c")
        self.assertNotIn("c", obj.get_tags())


# ---------------------------------------------------------------------------
# Parent-child relationships
# ---------------------------------------------------------------------------

class TestSceneObjectParentChild(unittest.TestCase):
    """Tests for parent-child hierarchy on SceneObject."""

    def _make(self, name="Obj") -> SceneObject:
        return SceneObject(
            name=name,
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
        )

    def test_parent_default_none(self):
        obj = self._make()
        self.assertIsNone(obj.get_parent())

    def test_children_default_empty(self):
        obj = self._make()
        self.assertEqual(obj.get_children(), {})

    def test_set_parent(self):
        parent = self._make("Parent")
        child = self._make("Child")
        child.set_parent(parent)
        self.assertIs(child.get_parent(), parent)

    def test_parent_property(self):
        parent = self._make("Parent")
        child = self._make("Child")
        child.parent = parent
        self.assertIs(child.parent, parent)

    def test_add_child_sets_parent(self):
        parent = self._make("Parent")
        child = self._make("Child")
        parent.add_child(child)
        self.assertIs(child.get_parent(), parent)

    def test_add_child_appears_in_children(self):
        parent = self._make("Parent")
        child = self._make("Child")
        parent.add_child(child)
        self.assertIn(child.id, parent.get_children())

    def test_remove_child(self):
        parent = self._make("Parent")
        child = self._make("Child")
        parent.add_child(child)
        parent.remove_child(child.id)
        self.assertNotIn(child.id, parent.get_children())
        self.assertIsNone(child.get_parent())

    def test_get_child_by_id(self):
        parent = self._make("Parent")
        child = self._make("Child")
        parent.add_child(child)
        result = parent.get_child(child.id)
        self.assertIs(result, child)

    def test_get_child_not_found_returns_none(self):
        parent = self._make("Parent")
        self.assertIsNone(parent.get_child("nonexistent_id"))

    def test_children_property(self):
        parent = self._make("Parent")
        child = self._make("Child")
        parent.add_child(child)
        self.assertIn(child.id, parent.children)

    def test_set_parent_removes_from_old_parent(self):
        parent1 = self._make("Parent1")
        parent2 = self._make("Parent2")
        child = self._make("Child")
        parent1.add_child(child)
        child.set_parent(parent2)
        self.assertNotIn(child.id, parent1.get_children())
        self.assertIs(child.get_parent(), parent2)

    def test_set_parent_none_clears_parent(self):
        parent = self._make("Parent")
        child = self._make("Child")
        parent.add_child(child)
        child.set_parent(None)
        self.assertIsNone(child.get_parent())


# ---------------------------------------------------------------------------
# Layering (z-order)
# ---------------------------------------------------------------------------

class TestSceneObjectLayer(unittest.TestCase):
    """Tests for layer (z-order) management on SceneObject."""

    def _make(self, **kwargs) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
            **kwargs,
        )

    def test_layer_default_zero(self):
        obj = self._make()
        self.assertEqual(obj.get_layer(), 0)

    def test_layer_from_constructor(self):
        obj = self._make(layer=50)
        self.assertEqual(obj.get_layer(), 50)

    def test_set_layer(self):
        obj = self._make()
        obj.set_layer(100)
        self.assertEqual(obj.get_layer(), 100)

    def test_layer_property_get(self):
        obj = self._make(layer=25)
        self.assertEqual(obj.layer, 25)

    def test_layer_property_set(self):
        obj = self._make()
        obj.layer = 75
        self.assertEqual(obj.layer, 75)

    def test_move_layer_up(self):
        obj = self._make(layer=5)
        obj.move_layer_up()
        self.assertEqual(obj.get_layer(), 6)

    def test_move_layer_down(self):
        obj = self._make(layer=5)
        obj.move_layer_down()
        self.assertEqual(obj.get_layer(), 4)

    def test_bring_to_front(self):
        obj = self._make(layer=0)
        obj.bring_to_front()
        self.assertEqual(obj.get_layer(), 1000)

    def test_send_to_back(self):
        obj = self._make(layer=0)
        obj.send_to_back()
        self.assertEqual(obj.get_layer(), -1000)

    def test_layer_in_compile_properties(self):
        obj = self._make(layer=42)
        props = obj.get_properties()
        self.assertEqual(props.get("layer"), 42)


# ---------------------------------------------------------------------------
# Group ID
# ---------------------------------------------------------------------------

class TestSceneObjectGroupId(unittest.TestCase):
    """Tests for group_id on SceneObject."""

    def _make(self, **kwargs) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
            **kwargs,
        )

    def test_group_id_default_none(self):
        obj = self._make()
        self.assertIsNone(obj.get_group_id())

    def test_group_id_from_constructor(self):
        obj = self._make(group_id="group-123")
        self.assertEqual(obj.get_group_id(), "group-123")

    def test_set_group_id(self):
        obj = self._make()
        obj.set_group_id("my-group")
        self.assertEqual(obj.get_group_id(), "my-group")

    def test_group_id_property_get(self):
        obj = self._make(group_id="gid")
        self.assertEqual(obj.group_id, "gid")

    def test_group_id_property_set(self):
        obj = self._make()
        obj.group_id = "new-gid"
        self.assertEqual(obj.group_id, "new-gid")

    def test_group_id_can_be_cleared(self):
        obj = self._make(group_id="group-1")
        obj.set_group_id(None)
        self.assertIsNone(obj.get_group_id())

    def test_group_id_in_compile_properties(self):
        obj = self._make(group_id="g99")
        props = obj.get_properties()
        self.assertEqual(props.get("group_id"), "g99")


# ---------------------------------------------------------------------------
# Click events
# ---------------------------------------------------------------------------

class TestSceneObjectClickEvents(unittest.TestCase):
    """Tests for the click event system on SceneObject."""

    def _make(self) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
        )

    def test_not_clickable_by_default(self):
        obj = self._make()
        self.assertFalse(obj.is_clickable())

    def test_set_clickable_true(self):
        obj = self._make()
        obj.set_clickable(True)
        self.assertTrue(obj.is_clickable())

    def test_set_clickable_false(self):
        obj = self._make()
        obj.set_clickable(True)
        obj.set_clickable(False)
        self.assertFalse(obj.is_clickable())

    def test_add_on_click_handler(self):
        obj = self._make()
        obj.set_clickable(True)
        calls = []
        def handler(o, x, y): return calls.append((o, x, y))
        obj.add_on_click_handler(handler)
        obj.trigger_click(5.0, 7.0)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], obj)
        self.assertAlmostEqual(calls[0][1], 5.0)
        self.assertAlmostEqual(calls[0][2], 7.0)

    def test_remove_on_click_handler(self):
        obj = self._make()
        obj.set_clickable(True)
        calls = []
        def handler(o, x, y): return calls.append(1)
        obj.add_on_click_handler(handler)
        obj.remove_on_click_handler(handler)
        obj.trigger_click(0.0, 0.0)
        self.assertEqual(calls, [])

    def test_add_duplicate_handler_ignored(self):
        obj = self._make()
        obj.set_clickable(True)
        calls = []
        def handler(o, x, y): return calls.append(1)
        obj.add_on_click_handler(handler)
        obj.add_on_click_handler(handler)
        obj.trigger_click(0.0, 0.0)
        self.assertEqual(len(calls), 1)

    def test_trigger_click_not_clickable_does_nothing(self):
        obj = self._make()
        calls = []
        obj.add_on_click_handler(lambda o, x, y: calls.append(1))
        obj.trigger_click(0.0, 0.0)
        self.assertEqual(calls, [])

    def test_trigger_click_multiple_handlers(self):
        obj = self._make()
        obj.set_clickable(True)
        calls = []
        obj.add_on_click_handler(lambda o, x, y: calls.append("h1"))
        obj.add_on_click_handler(lambda o, x, y: calls.append("h2"))
        obj.trigger_click(1.0, 2.0)
        self.assertIn("h1", calls)
        self.assertIn("h2", calls)


# ---------------------------------------------------------------------------
# contains_point
# ---------------------------------------------------------------------------

class TestSceneObjectContainsPoint(unittest.TestCase):
    """Tests for SceneObject.contains_point()."""

    def _make(self, x=10.0, y=10.0, width=20.0, height=20.0) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=x, y=y, width=width, height=height,
            ),
        )

    def test_contains_interior_point(self):
        obj = self._make()
        self.assertTrue(obj.contains_point(20.0, 20.0))

    def test_does_not_contain_point_left_of_x(self):
        obj = self._make()
        self.assertFalse(obj.contains_point(5.0, 20.0))

    def test_does_not_contain_point_right_of_x(self):
        obj = self._make()
        self.assertFalse(obj.contains_point(35.0, 20.0))

    def test_does_not_contain_point_above_y(self):
        obj = self._make()
        self.assertFalse(obj.contains_point(20.0, 5.0))

    def test_does_not_contain_point_below_y(self):
        obj = self._make()
        self.assertFalse(obj.contains_point(20.0, 35.0))

    def test_contains_point_on_left_edge(self):
        obj = self._make()
        self.assertTrue(obj.contains_point(10.0, 20.0))

    def test_contains_point_on_right_edge(self):
        obj = self._make()
        self.assertTrue(obj.contains_point(30.0, 20.0))

    def test_contains_point_on_top_edge(self):
        obj = self._make()
        self.assertTrue(obj.contains_point(20.0, 10.0))

    def test_contains_point_on_bottom_edge(self):
        obj = self._make()
        self.assertTrue(obj.contains_point(20.0, 30.0))

    def test_contains_corner(self):
        obj = self._make()
        self.assertTrue(obj.contains_point(10.0, 10.0))


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------

class TestSceneObjectConnections(unittest.TestCase):
    """Tests for connection management on SceneObject."""

    def _make(self) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
        )

    def _conn(self, source_id="a", target_id="b") -> Connection:
        return Connection(
            source_id=source_id,
            source_output="on_activate",
            target_id=target_id,
            target_input="run",
        )

    def test_connections_default_empty(self):
        obj = self._make()
        self.assertEqual(obj.get_connections(), [])

    def test_connections_property(self):
        obj = self._make()
        self.assertIsInstance(obj.connections, list)

    def test_set_connections(self):
        obj = self._make()
        conns = [self._conn()]
        obj.set_connections(conns)
        self.assertEqual(len(obj.get_connections()), 1)

    def test_set_connections_stores_copy(self):
        """Mutating the original list should not affect the stored connections."""
        obj = self._make()
        conns = [self._conn()]
        obj.set_connections(conns)
        conns.append(self._conn("c", "d"))
        self.assertEqual(len(obj.get_connections()), 1)


# ---------------------------------------------------------------------------
# Template name
# ---------------------------------------------------------------------------

class TestSceneObjectTemplateName(unittest.TestCase):
    """Tests for template_name on SceneObject."""

    def _make(self, **kwargs) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
            **kwargs,
        )

    def test_template_name_default_empty(self):
        obj = self._make()
        self.assertEqual(obj.get_template_name(), "")

    def test_template_name_from_constructor(self):
        obj = self._make(template_name="MyTemplate")
        self.assertEqual(obj.get_template_name(), "MyTemplate")

    def test_set_template_name(self):
        obj = self._make()
        obj.set_template_name("Updated")
        self.assertEqual(obj.get_template_name(), "Updated")

    def test_template_name_property_get(self):
        obj = self._make(template_name="T1")
        self.assertEqual(obj.template_name, "T1")

    def test_template_name_property_set(self):
        obj = self._make()
        obj.template_name = "T2"
        self.assertEqual(obj.template_name, "T2")

    def test_to_dict_includes_template_name(self):
        obj = self._make(template_name="TmplA")
        data = obj.to_dict()
        self.assertEqual(data["template_name"], "TmplA")


# ---------------------------------------------------------------------------
# Physics body convenience properties (x, y, width, height, yaw)
# ---------------------------------------------------------------------------

class TestSceneObjectPhysicsConvenience(unittest.TestCase):
    """Tests for the physics-body convenience properties on SceneObject."""

    def _make(self, x=5.0, y=10.0, width=20.0, height=15.0, yaw=30.0) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=x, y=y, width=width, height=height, yaw=yaw,
            ),
        )

    def test_x_property_reads_from_body(self):
        obj = self._make(x=7.0)
        self.assertAlmostEqual(obj.x, 7.0)

    def test_x_setter_writes_to_body(self):
        obj = self._make()
        obj.x = 99.0
        self.assertAlmostEqual(obj.physics_body.x, 99.0)

    def test_get_x_set_x(self):
        obj = self._make()
        obj.set_x(42.0)
        self.assertAlmostEqual(obj.get_x(), 42.0)

    def test_y_property_reads_from_body(self):
        obj = self._make(y=13.0)
        self.assertAlmostEqual(obj.y, 13.0)

    def test_y_setter_writes_to_body(self):
        obj = self._make()
        obj.y = 55.0
        self.assertAlmostEqual(obj.physics_body.y, 55.0)

    def test_get_y_set_y(self):
        obj = self._make()
        obj.set_y(77.0)
        self.assertAlmostEqual(obj.get_y(), 77.0)

    def test_width_property(self):
        obj = self._make(width=40.0)
        self.assertAlmostEqual(obj.width, 40.0)

    def test_width_setter(self):
        obj = self._make()
        obj.width = 60.0
        self.assertAlmostEqual(obj.physics_body.width, 60.0)

    def test_height_property(self):
        obj = self._make(height=25.0)
        self.assertAlmostEqual(obj.height, 25.0)

    def test_height_setter(self):
        obj = self._make()
        obj.height = 35.0
        self.assertAlmostEqual(obj.physics_body.height, 35.0)


# ---------------------------------------------------------------------------
# Direction (CardinalDirection)
# ---------------------------------------------------------------------------

class TestSceneObjectDirection(unittest.TestCase):
    """Tests for direction (CardinalDirection) on SceneObject."""

    def _make(self, **kwargs) -> SceneObject:
        return SceneObject(
            name="Obj",
            scene_object_type="Type",
            physics_body=BasePhysicsBody(
                name="Body",
                template_name="Base Physics Body",
                x=0.0, y=0.0, width=10.0, height=10.0,
            ),
            **kwargs,
        )

    def test_direction_default_is_north(self):
        """When no direction is given, get_direction() defaults to NORTH."""
        obj = self._make()
        self.assertEqual(obj.get_direction(), CardinalDirection.NORTH)

    def test_direction_from_constructor(self):
        obj = self._make(direction=CardinalDirection.EAST)
        self.assertEqual(obj.get_direction(), CardinalDirection.EAST)

    def test_set_direction(self):
        """set_direction only applies when the new direction is perpendicular.

        The default direction is NORTH.  EAST is perpendicular to NORTH
        (difference of 1 position on the cardinal compass), so the change
        should be stored and the physics body dimensions should be swapped.
        """
        obj = self._make()
        original_width = obj.width
        original_height = obj.height
        obj.set_direction(CardinalDirection.EAST)
        self.assertEqual(obj.get_direction(), CardinalDirection.EAST)
        # Rotating NORTH → EAST swaps width/height
        self.assertAlmostEqual(obj.width, original_height)
        self.assertAlmostEqual(obj.height, original_width)

    def test_set_direction_non_perpendicular(self):
        """Setting a direction that is NOT perpendicular to the current one is set."""
        obj = self._make()
        obj.set_direction(CardinalDirection.SOUTH)  # SOUTH is opposite to NORTH, not perpendicular
        self.assertEqual(obj.get_direction(), CardinalDirection.SOUTH)

    def test_direction_from_properties_dict(self):
        """Passing direction via properties dict falls back when no constructor arg given."""
        obj = self._make(properties={"direction": "WEST"})
        self.assertEqual(obj.get_direction(), CardinalDirection.WEST)

    def test_constructor_direction_overrides_properties_dict(self):
        obj = self._make(
            direction=CardinalDirection.NORTH,
            properties={"direction": "EAST"},
        )
        self.assertEqual(obj.get_direction(), CardinalDirection.NORTH)


if __name__ == '__main__':
    unittest.main()
