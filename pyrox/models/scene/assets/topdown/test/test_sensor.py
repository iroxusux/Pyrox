"""Unit tests for SensorSceneObject.

Tests cover initialisation, callback bridging, input/output endpoint
wiring, status properties, the ``create`` factory classmethod, the
``_compile_properties`` serialisation hook, and ``from_dict`` round-trip
deserialisation.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyrox.interfaces import CollisionLayer
from pyrox.models.physics.sensor import ProximitySensorBody
from pyrox.models.scene.assets.topdown.sensor import SensorSceneObject
from pyrox.models.scene.factory import SceneObjectFactory

SENSOR_DEF_COLOR = "#00ffff"


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_body(
    name: str = "sensor_body",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 10.0,
    height: float = 10.0,
) -> ProximitySensorBody:
    """Return a real :class:`ProximitySensorBody` for use in tests."""
    return ProximitySensorBody(name=name, x=x, y=y, width=width, height=height)


def _make_sensor(
    name: str = "sensor",
    sensor_color: str = SENSOR_DEF_COLOR,
    layer: int = 0,
    description: str = "",
    properties: dict | None = None,
    id: str | None = None,
    group_id: str | None = None,
    tags: list[str] | None = None,
    body: ProximitySensorBody | None = None,
) -> SensorSceneObject:
    """Construct a :class:`SensorSceneObject` using a real :class:`ProximitySensorBody`."""
    physics_body = body or _make_body()
    return SensorSceneObject(
        name=name,
        physics_body=physics_body,
        sensor_color=sensor_color,
        layer=layer,
        description=description,
        properties=properties,
        id=id,
        group_id=group_id,
        tags=tags,
    )


# ===========================================================================
# SensorSceneObject – initialisation
# ===========================================================================


class TestSensorSceneObjectInit(unittest.TestCase):

    def test_name_stored_correctly(self):
        obj = _make_sensor(name="my_sensor")
        self.assertEqual(obj.name, "my_sensor")

    def test_default_sensor_color(self):
        obj = _make_sensor()
        self.assertEqual(obj.bg_color, SENSOR_DEF_COLOR)

    def test_custom_sensor_color(self):
        obj = _make_sensor(sensor_color="#ff00ff")
        self.assertEqual(obj.bg_color, "#ff00ff")

    def test_sensor_color_from_properties_overrides_param(self):
        obj = _make_sensor(
            sensor_color="#111111",
            properties={"sensor_color": "#abcdef"},
        )
        self.assertEqual(obj.bg_color, "#abcdef")

    def test_default_layer_is_zero(self):
        obj = _make_sensor()
        self.assertEqual(obj._layer, 0)

    def test_custom_layer_stored(self):
        obj = _make_sensor(layer=7)
        self.assertEqual(obj._layer, 7)

    def test_description_stored(self):
        obj = _make_sensor(description="part present sensor")
        self.assertEqual(obj.description, "part present sensor")

    def test_physics_body_reference_stored(self):
        body = _make_body()
        obj = _make_sensor(body=body)
        self.assertIs(obj._sensor_body, body)

    def test_explicit_id_stored(self):
        obj = _make_sensor(id="sensor-abc")
        self.assertEqual(obj.id, "sensor-abc")

    def test_auto_id_generated_when_none(self):
        obj = _make_sensor(id=None)
        self.assertIsNotNone(obj.id)
        self.assertGreater(len(obj.id), 0)

    def test_group_id_stored(self):
        obj = _make_sensor(group_id="grp-007")
        self.assertEqual(obj._group_id, "grp-007")

    def test_group_id_none_by_default(self):
        obj = _make_sensor()
        self.assertIsNone(obj._group_id)

    def test_tags_stored(self):
        obj = _make_sensor(tags=["trigger", "zone"])
        self.assertIn("trigger", obj._tags)
        self.assertIn("zone", obj._tags)

    def test_tags_empty_by_default(self):
        obj = _make_sensor()
        self.assertEqual(obj._tags, [])

    def test_scene_object_type(self):
        obj = _make_sensor()
        self.assertEqual(obj._scene_object_type, SensorSceneObject._scene_object_type)

    def test_template_name(self):
        obj = _make_sensor()
        self.assertEqual(obj._template_name, SensorSceneObject._template_name)

    def test_callback_lists_initialised_empty(self):
        obj = _make_sensor()
        # Bridge callbacks are added to the physics body; the SceneObject's own
        # user-facing lists should start empty before any external wiring.
        self.assertEqual(obj._on_activate_callbacks, [])
        self.assertEqual(obj._on_deactivate_callbacks, [])
        self.assertEqual(obj._on_object_enter_callbacks, [])
        self.assertEqual(obj._on_object_exit_callbacks, [])

    def test_bridge_callbacks_registered_on_physics_body(self):
        body = _make_body()
        obj = _make_sensor(body=body)
        self.assertIn(obj._bridge_activate, body.on_activate_callbacks)
        self.assertIn(obj._bridge_deactivate, body.on_deactivate_callbacks)
        self.assertIn(obj._bridge_object_enter, body.on_object_enter_callbacks)
        self.assertIn(obj._bridge_object_exit, body.on_object_exit_callbacks)


# ===========================================================================
# SensorSceneObject – output properties
# ===========================================================================


class TestSensorSceneObjectOutputProperties(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_sensor()

    def test_on_activate_callbacks_returns_same_list(self):
        self.assertIs(self.obj.on_activate_callbacks, self.obj._on_activate_callbacks)

    def test_on_deactivate_callbacks_returns_same_list(self):
        self.assertIs(self.obj.on_deactivate_callbacks, self.obj._on_deactivate_callbacks)

    def test_on_object_enter_callbacks_returns_same_list(self):
        self.assertIs(self.obj.on_object_enter_callbacks, self.obj._on_object_enter_callbacks)

    def test_on_object_exit_callbacks_returns_same_list(self):
        self.assertIs(self.obj.on_object_exit_callbacks, self.obj._on_object_exit_callbacks)


# ===========================================================================
# SensorSceneObject – bridge methods
# ===========================================================================


class TestSensorSceneObjectBridge(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_sensor()

    def test_bridge_activate_calls_registered_callback(self):
        received = []
        self.obj._on_activate_callbacks.append(lambda state: received.append(state))
        self.obj._bridge_activate(True)
        self.assertEqual(received, [True])

    def test_bridge_deactivate_calls_registered_callback(self):
        received = []
        self.obj._on_deactivate_callbacks.append(lambda state: received.append(state))
        self.obj._bridge_deactivate(False)
        self.assertEqual(received, [False])

    def test_bridge_activate_no_callbacks_is_noop(self):
        self.obj._bridge_activate(True)  # must not raise

    def test_bridge_deactivate_no_callbacks_is_noop(self):
        self.obj._bridge_deactivate(False)  # must not raise

    def test_bridge_object_enter_passes_scene_object_not_body(self):
        """_bridge_object_enter replaces the sensor body arg with ``self``."""
        received_source = []
        received_obj = []

        def _cb(source, obj):
            received_source.append(source)
            received_obj.append(obj)

        self.obj._on_object_enter_callbacks.append(_cb)
        mock_body = MagicMock()
        mock_other = MagicMock()
        self.obj._bridge_object_enter(mock_body, mock_other)
        self.assertIs(received_source[0], self.obj)
        self.assertIs(received_obj[0], mock_other)

    def test_bridge_object_exit_passes_scene_object_not_body(self):
        received_source = []

        def _cb(source, obj):
            received_source.append(source)

        self.obj._on_object_exit_callbacks.append(_cb)
        self.obj._bridge_object_exit(MagicMock(), MagicMock())
        self.assertIs(received_source[0], self.obj)

    def test_bridge_activate_calls_multiple_callbacks(self):
        results = []
        self.obj._on_activate_callbacks.append(lambda s: results.append("first"))
        self.obj._on_activate_callbacks.append(lambda s: results.append("second"))
        self.obj._bridge_activate(True)
        self.assertEqual(results, ["first", "second"])


# ===========================================================================
# SensorSceneObject – input methods
# ===========================================================================


class TestSensorSceneObjectInputMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_sensor()

    def test_activate_fires_activate_callbacks(self):
        received = []
        self.obj._on_activate_callbacks.append(lambda s: received.append(s))
        self.obj.activate()
        self.assertEqual(received, [True])

    def test_deactivate_fires_deactivate_callbacks(self):
        received = []
        self.obj._on_deactivate_callbacks.append(lambda s: received.append(s))
        self.obj.deactivate()
        self.assertEqual(received, [False])

    def test_activate_accepts_extra_args(self):
        self.obj.activate("ignored_arg")  # must not raise

    def test_deactivate_accepts_extra_args(self):
        self.obj.deactivate("ignored_arg")  # must not raise

    def test_clear_calls_clear_detected_objects_on_body(self):
        mock_body = _make_body()
        obj = _make_sensor(body=mock_body)
        # Manually add an object to the body's detected set via collision
        fake_other = MagicMock()
        fake_other.body_type = MagicMock()
        mock_body.on_collision_enter(fake_other)
        self.assertTrue(mock_body.is_active)
        obj.clear()
        self.assertFalse(mock_body.is_active)
        self.assertEqual(mock_body.detection_count, 0)


# ===========================================================================
# SensorSceneObject – get_outputs / get_inputs
# ===========================================================================


class TestSensorSceneObjectEndpoints(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_sensor()

    def test_get_outputs_has_all_four_keys(self):
        outputs = self.obj.get_outputs()
        for key in (
            "on_activate_callbacks",
            "on_deactivate_callbacks",
            "on_object_enter_callbacks",
            "on_object_exit_callbacks",
        ):
            self.assertIn(key, outputs, msg=f"'{key}' missing from get_outputs()")

    def test_get_outputs_values_are_the_lists(self):
        outputs = self.obj.get_outputs()
        self.assertIs(outputs["on_activate_callbacks"], self.obj.on_activate_callbacks)
        self.assertIs(outputs["on_deactivate_callbacks"], self.obj.on_deactivate_callbacks)
        self.assertIs(outputs["on_object_enter_callbacks"], self.obj.on_object_enter_callbacks)
        self.assertIs(outputs["on_object_exit_callbacks"], self.obj.on_object_exit_callbacks)

    def test_get_inputs_has_activate(self):
        self.assertIn("activate", self.obj.get_inputs())

    def test_get_inputs_has_deactivate(self):
        self.assertIn("deactivate", self.obj.get_inputs())

    def test_get_inputs_has_clear(self):
        self.assertIn("clear", self.obj.get_inputs())

    def test_get_inputs_methods_are_callable(self):
        inputs = self.obj.get_inputs()
        for key in ("activate", "deactivate", "clear"):
            self.assertTrue(callable(inputs[key]), msg=f"'{key}' should be callable")

    def test_get_inputs_methods_are_bound_to_instance(self):
        inputs = self.obj.get_inputs()
        self.assertEqual(inputs["activate"], self.obj.activate)
        self.assertEqual(inputs["deactivate"], self.obj.deactivate)
        self.assertEqual(inputs["clear"], self.obj.clear)


# ===========================================================================
# SensorSceneObject – status properties
# ===========================================================================


class TestSensorSceneObjectStatus(unittest.TestCase):

    def test_is_active_delegates_to_body(self):
        body = _make_body()
        obj = _make_sensor(body=body)
        self.assertFalse(obj.is_active)
        fake_other = MagicMock()
        body.on_collision_enter(fake_other)
        self.assertTrue(obj.is_active)

    def test_detection_count_delegates_to_body(self):
        body = _make_body()
        obj = _make_sensor(body=body)
        self.assertEqual(obj.detection_count, 0)
        fake_a = MagicMock()
        fake_b = MagicMock()
        body.on_collision_enter(fake_a)
        body.on_collision_enter(fake_b)
        self.assertEqual(obj.detection_count, 2)

    def test_detection_count_decrements_on_exit(self):
        body = _make_body()
        obj = _make_sensor(body=body)
        fake = MagicMock()
        body.on_collision_enter(fake)
        body.on_collision_exit(fake)
        self.assertEqual(obj.detection_count, 0)

    def test_is_active_false_after_clear(self):
        body = _make_body()
        obj = _make_sensor(body=body)
        body.on_collision_enter(MagicMock())
        obj.clear()
        self.assertFalse(obj.is_active)


# ===========================================================================
# SensorSceneObject.create – classmethod factory
# ===========================================================================


class TestSensorSceneObjectCreate(unittest.TestCase):

    def test_returns_sensor_scene_object_instance(self):
        obj = SensorSceneObject.create(name="s")
        self.assertIsInstance(obj, SensorSceneObject)

    def test_name_passed_through(self):
        obj = SensorSceneObject.create(name="zone_sensor")
        self.assertEqual(obj.name, "zone_sensor")

    def test_default_position_is_origin(self):
        obj = SensorSceneObject.create(name="s")
        self.assertAlmostEqual(obj._sensor_body.x, 0.0)
        self.assertAlmostEqual(obj._sensor_body.y, 0.0)

    def test_custom_position_stored_in_body(self):
        obj = SensorSceneObject.create(name="s", x=15.0, y=25.0)
        self.assertAlmostEqual(obj._sensor_body.x, 15.0)
        self.assertAlmostEqual(obj._sensor_body.y, 25.0)

    def test_default_width(self):
        obj = SensorSceneObject.create(name="s")
        self.assertAlmostEqual(obj._sensor_body.width, 10.0)

    def test_default_height(self):
        obj = SensorSceneObject.create(name="s")
        self.assertAlmostEqual(obj._sensor_body.height, 10.0)

    def test_custom_dimensions(self):
        obj = SensorSceneObject.create(name="s", width=50.0, height=5.0)
        self.assertAlmostEqual(obj._sensor_body.width, 50.0)
        self.assertAlmostEqual(obj._sensor_body.height, 5.0)

    def test_default_sensor_color(self):
        obj = SensorSceneObject.create(name="s")
        self.assertEqual(obj.bg_color, SENSOR_DEF_COLOR)

    def test_custom_sensor_color(self):
        obj = SensorSceneObject.create(name="s", sensor_color="#123456")
        self.assertEqual(obj.bg_color, "#123456")

    def test_layer_passed_through(self):
        obj = SensorSceneObject.create(name="s", layer=2)
        self.assertEqual(obj._layer, 2)

    def test_id_passed_through(self):
        obj = SensorSceneObject.create(name="s", id="sens-42")
        self.assertEqual(obj.id, "sens-42")

    def test_description_passed_through(self):
        obj = SensorSceneObject.create(name="s", description="entry sensor")
        self.assertEqual(obj.description, "entry sensor")

    def test_group_id_passed_through(self):
        obj = SensorSceneObject.create(name="s", group_id="g-100")
        self.assertEqual(obj._group_id, "g-100")

    def test_tags_passed_through(self):
        obj = SensorSceneObject.create(name="s", tags=["a", "b"])
        self.assertIn("a", obj._tags)
        self.assertIn("b", obj._tags)

    def test_body_dict_creates_sensor_body_from_dict(self):
        body_data = {"name": "b", "x": 5.0, "y": 10.0, "width": 20.0, "height": 20.0}
        obj = SensorSceneObject.create(name="s", body=body_data)
        self.assertAlmostEqual(obj._sensor_body.x, 5.0)
        self.assertAlmostEqual(obj._sensor_body.y, 10.0)

    def test_collision_layer_default_is_sensor(self):
        obj = SensorSceneObject.create(name="s")
        self.assertEqual(
            obj._sensor_body.get_collider().collision_layer,
            CollisionLayer.SENSOR,
        )

    def test_custom_collision_layer_stored(self):
        obj = SensorSceneObject.create(name="s", collision_layer=CollisionLayer.DEFAULT)
        self.assertEqual(
            obj._sensor_body.get_collider().collision_layer,
            CollisionLayer.DEFAULT,
        )

    def test_bridge_callbacks_wired_after_create(self):
        obj = SensorSceneObject.create(name="s")
        self.assertIn(obj._bridge_activate, obj._sensor_body.on_activate_callbacks)


# ===========================================================================
# SensorSceneObject._compile_properties
# ===========================================================================


class TestSensorSceneObjectCompileProperties(unittest.TestCase):

    def test_compile_properties_adds_sensor_color_key(self):
        obj = _make_sensor(sensor_color="#303030")
        obj._compile_properties()
        self.assertIn("sensor_color", obj._properties)

    def test_compile_properties_sensor_color_matches_bg_color(self):
        obj = _make_sensor(sensor_color="#aabbcc")
        obj._compile_properties()
        self.assertEqual(obj._properties["sensor_color"], "#aabbcc")

    def test_compile_properties_sensor_color_updates_after_bg_color_change(self):
        obj = _make_sensor(sensor_color="#111111")
        obj.bg_color = "#ffffff"
        obj._compile_properties()
        self.assertEqual(obj._properties["sensor_color"], "#ffffff")


# ===========================================================================
# SensorSceneObject.from_dict
# ===========================================================================


class TestSensorSceneObjectFromDict(unittest.TestCase):

    def _minimal_dict(self, **overrides) -> dict:
        base: dict = {
            "name": "sensor_obj",
            "body": {"name": "b"},
            "properties": {},
        }
        base.update(overrides)
        return base

    def test_returns_sensor_scene_object_instance(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict())
        self.assertIsInstance(obj, SensorSceneObject)

    def test_restores_name(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict(name="restored"))
        self.assertEqual(obj.name, "restored")

    def test_restores_sensor_color_from_properties(self):
        data = self._minimal_dict(properties={"sensor_color": "#abcdef"})
        obj = SensorSceneObject.from_dict(data)
        self.assertEqual(obj.bg_color, "#abcdef")

    def test_default_sensor_color_when_absent(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj.bg_color, SENSOR_DEF_COLOR)

    def test_restores_layer(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict(layer=9))
        self.assertEqual(obj._layer, 9)

    def test_default_layer_when_absent(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj._layer, 0)

    def test_restores_description(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict(description="entry zone"))
        self.assertEqual(obj.description, "entry zone")

    def test_restores_id(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict(id="sensor-xyz"))
        self.assertEqual(obj.id, "sensor-xyz")

    def test_restores_group_id(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict(group_id="group-3"))
        self.assertEqual(obj._group_id, "group-3")

    def test_group_id_none_when_absent(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict())
        self.assertIsNone(obj._group_id)

    def test_restores_tags(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict(tags=["t1", "t2"]))
        self.assertIn("t1", obj._tags)
        self.assertIn("t2", obj._tags)

    def test_tags_empty_list_when_absent(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj._tags, [])

    def test_creates_proximity_sensor_body_from_body_dict(self):
        data = self._minimal_dict(body={"name": "sb", "width": 30.0, "height": 30.0})
        obj = SensorSceneObject.from_dict(data)
        self.assertIsInstance(obj._sensor_body, ProximitySensorBody)

    def test_body_dimensions_restored(self):
        data = self._minimal_dict(body={"name": "b", "width": 40.0, "height": 8.0})
        obj = SensorSceneObject.from_dict(data)
        self.assertAlmostEqual(obj._sensor_body.width, 40.0)
        self.assertAlmostEqual(obj._sensor_body.height, 8.0)

    def test_bridge_callbacks_wired_after_from_dict(self):
        obj = SensorSceneObject.from_dict(self._minimal_dict())
        self.assertIn(obj._bridge_activate, obj._sensor_body.on_activate_callbacks)


# ===========================================================================
# Factory template registration
# ===========================================================================


class TestSensorSceneObjectFactoryTemplate(unittest.TestCase):

    def test_template_is_registered(self):
        template = SceneObjectFactory.get_template(SensorSceneObject._template_name)
        self.assertIsNotNone(template)

    def test_template_name_matches_constant(self):
        template = SceneObjectFactory.get_template(SensorSceneObject._template_name)
        self.assertEqual(template.name, SensorSceneObject._template_name)

    def test_template_factory_func_returns_sensor_scene_object(self):
        template = SceneObjectFactory.get_template(SensorSceneObject._template_name)
        obj = template.factory_func(**template.default_kwargs)
        self.assertIsInstance(obj, SensorSceneObject)

    def test_template_default_color_is_cyan(self):
        template = SceneObjectFactory.get_template(SensorSceneObject._template_name)
        self.assertEqual(template.default_kwargs.get("sensor_color"), SENSOR_DEF_COLOR)


if __name__ == "__main__":
    unittest.main()
