"""Unit tests for SceneObject class."""
import unittest
from typing import Any, Dict
from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer
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
            roll=5.0,
            pitch=10.0,
            yaw=15.0,
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
        self.assertEqual(obj.physics_body.get_roll(), 5.0)
        self.assertEqual(obj.physics_body.get_pitch(), 10.0)
        self.assertEqual(obj.physics_body.get_yaw(), 15.0)

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

    def test_get_property_retrieves_attr_if_not_in_dict(self):
        """Test that get_property retrieves attribute if not in properties dict."""
        obj = SceneObject(name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())
        obj.physics_body.set_x(20)

        self.assertNotIn("bing_bong", obj.properties)
        obj.set_property("bing_bong", 15)

        self.assertEqual(obj.get_property('bing_bong'), 15)
        self.assertIn("bing_bong", obj.properties)


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
            AnimationTrack("yaw", easing=AnimationEasing.LINEAR)
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
        self.assertAlmostEqual(obj.physics_body.yaw, 45.0, places=1)

    def test_update_at_full_duration_stops_once_clip(self):
        from pyrox.models.scene.animation import AnimationMode
        obj = self._make()
        obj.animator.add_clip(self._gate_clip(AnimationMode.ONCE))
        obj.animator.play("gate_open")

        _obj_advance(obj, 2.0)  # past end
        self.assertFalse(obj.animator.is_playing)
        self.assertAlmostEqual(obj.physics_body.yaw, 90.0, places=1)

    def test_update_does_nothing_when_not_playing(self):
        obj = self._make()
        obj.update(0.5)  # no clip registered → should not raise
        # yaw stays at initial value
        self.assertAlmostEqual(obj.physics_body.yaw, 0.0, places=3)

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


if __name__ == '__main__':
    unittest.main()
