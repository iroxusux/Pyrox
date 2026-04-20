"""Unit tests for FloorSceneObject.

Tests cover initialisation, the ``create`` factory classmethod, the
``_compile_properties`` serialisation hook, and ``from_dict`` round-trip
deserialisation.

Note on ``scene_object_type`` / ``template_name`` kwargs:
    ``FloorSceneObject.__init__`` forwards ``scene_object_type`` and
    ``template_name`` to ``SceneObject.__init__``.  ``SceneObject.__init__``
    does not declare those parameters, so they are silently absorbed only if
    ``SceneObject`` (or one of its bases) accepts ``**kwargs``.  The tests
    below exercise the public API (``create`` / ``from_dict``) and the
    constructor directly; if that assumption breaks, a ``TypeError`` will be
    raised with a clear message pointing here.
"""
from __future__ import annotations

import unittest

from pyrox.interfaces import CollisionLayer
from pyrox.models.physics.floor import FloorBody
from pyrox.models.scene.assets.topdown.floor import (
    SCENE_OBJECT_DEF_COLOR,
    FloorSceneObject,
)
from pyrox.models.scene.factory import SceneObjectFactory


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_body(
    name: str = "floor_body",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 100.0,
    height: float = 100.0,
) -> FloorBody:
    """Return a real :class:`FloorBody` for use in tests."""
    return FloorBody(name=name, x=x, y=y, width=width, height=height)


def _make_floor(
    name: str = "floor",
    floor_color: str = SCENE_OBJECT_DEF_COLOR,
    layer: int = 0,
    description: str = "",
    properties: dict | None = None,
    id: str | None = None,
    group_id: str | None = None,
    tags: list[str] | None = None,
    body: FloorBody | None = None,
) -> FloorSceneObject:
    """Construct a :class:`FloorSceneObject` using a real :class:`FloorBody`."""
    physics_body = body or _make_body()
    return FloorSceneObject(
        name=name,
        physics_body=physics_body,
        floor_color=floor_color,
        layer=layer,
        description=description,
        properties=properties,
        id=id,
        group_id=group_id,
        tags=tags,
    )


# ===========================================================================
# FloorSceneObject – initialisation
# ===========================================================================


class TestFloorSceneObjectInit(unittest.TestCase):

    def test_name_stored_correctly(self):
        obj = _make_floor(name="my_floor")
        self.assertEqual(obj.name, "my_floor")

    def test_default_floor_color(self):
        obj = _make_floor()
        self.assertEqual(obj.bg_color, SCENE_OBJECT_DEF_COLOR)

    def test_custom_floor_color(self):
        obj = _make_floor(floor_color="#aabbcc")
        self.assertEqual(obj.bg_color, "#aabbcc")

    def test_floor_color_from_properties_overrides_param(self):
        obj = _make_floor(
            floor_color="#111111",
            properties={"floor_color": "#999999"},
        )
        self.assertEqual(obj.bg_color, "#999999")

    def test_default_layer_is_zero(self):
        obj = _make_floor()
        self.assertEqual(obj._layer, 0)

    def test_custom_layer_stored(self):
        obj = _make_floor(layer=5)
        self.assertEqual(obj._layer, 5)

    def test_description_stored(self):
        obj = _make_floor(description="warehouse floor")
        self.assertEqual(obj.description, "warehouse floor")

    def test_physics_body_reference_stored(self):
        body = _make_body()
        obj = _make_floor(body=body)
        self.assertIs(obj._floor_body, body)

    def test_explicit_id_stored(self):
        obj = _make_floor(id="floor-abc-123")
        self.assertEqual(obj.id, "floor-abc-123")

    def test_auto_id_generated_when_none(self):
        obj = _make_floor(id=None)
        self.assertIsNotNone(obj.id)
        self.assertGreater(len(obj.id), 0)

    def test_group_id_stored(self):
        obj = _make_floor(group_id="grp-001")
        self.assertEqual(obj._group_id, "grp-001")

    def test_group_id_none_by_default(self):
        obj = _make_floor()
        self.assertIsNone(obj._group_id)

    def test_tags_stored(self):
        obj = _make_floor(tags=["static", "terrain"])
        self.assertIn("static", obj._tags)
        self.assertIn("terrain", obj._tags)

    def test_tags_empty_by_default(self):
        obj = _make_floor()
        self.assertEqual(obj._tags, [])

    def test_scene_object_type(self):
        obj = _make_floor()
        self.assertEqual(obj._scene_object_type, FloorSceneObject._scene_object_type)

    def test_template_name(self):
        obj = _make_floor()
        self.assertEqual(obj._template_name, FloorSceneObject._template_name)


# ===========================================================================
# FloorSceneObject.create – classmethod factory
# ===========================================================================


class TestFloorSceneObjectCreate(unittest.TestCase):

    def test_returns_floor_scene_object_instance(self):
        obj = FloorSceneObject.create(name="f")
        self.assertIsInstance(obj, FloorSceneObject)

    def test_name_passed_through(self):
        obj = FloorSceneObject.create(name="zone_a")
        self.assertEqual(obj.name, "zone_a")

    def test_default_position_is_origin(self):
        obj = FloorSceneObject.create(name="f")
        self.assertAlmostEqual(obj._floor_body.x, 0.0)
        self.assertAlmostEqual(obj._floor_body.y, 0.0)

    def test_custom_position_stored_in_body(self):
        obj = FloorSceneObject.create(name="f", x=50.0, y=75.0)
        self.assertAlmostEqual(obj._floor_body.x, 50.0)
        self.assertAlmostEqual(obj._floor_body.y, 75.0)

    def test_default_width(self):
        obj = FloorSceneObject.create(name="f")
        self.assertAlmostEqual(obj._floor_body.width, 10.0)

    def test_default_height(self):
        obj = FloorSceneObject.create(name="f")
        self.assertAlmostEqual(obj._floor_body.height, 10.0)

    def test_custom_dimensions(self):
        obj = FloorSceneObject.create(name="f", width=200.0, height=300.0)
        self.assertAlmostEqual(obj._floor_body.width, 200.0)
        self.assertAlmostEqual(obj._floor_body.height, 300.0)

    def test_floor_color_passed_through(self):
        obj = FloorSceneObject.create(name="f", floor_color="#ff0000")
        self.assertEqual(obj.bg_color, "#ff0000")

    def test_default_floor_color(self):
        obj = FloorSceneObject.create(name="f")
        self.assertEqual(obj.bg_color, SCENE_OBJECT_DEF_COLOR)

    def test_layer_passed_through(self):
        obj = FloorSceneObject.create(name="f", layer=3)
        self.assertEqual(obj._layer, 3)

    def test_id_passed_through(self):
        obj = FloorSceneObject.create(name="f", id="custom-id")
        self.assertEqual(obj.id, "custom-id")

    def test_description_passed_through(self):
        obj = FloorSceneObject.create(name="f", description="main floor")
        self.assertEqual(obj.description, "main floor")

    def test_group_id_passed_through(self):
        obj = FloorSceneObject.create(name="f", group_id="grp-42")
        self.assertEqual(obj._group_id, "grp-42")

    def test_tags_passed_through(self):
        obj = FloorSceneObject.create(name="f", tags=["floor", "zone"])
        self.assertIn("floor", obj._tags)
        self.assertIn("zone", obj._tags)

    def test_body_dict_creates_floor_body_from_dict(self):
        body_data = {"name": "b", "x": 5.0, "y": 10.0, "width": 50.0, "height": 50.0}
        obj = FloorSceneObject.create(name="f", body=body_data)
        self.assertAlmostEqual(obj._floor_body.x, 5.0)
        self.assertAlmostEqual(obj._floor_body.y, 10.0)

    def test_collision_layer_default_is_terrain(self):
        obj = FloorSceneObject.create(name="f")
        self.assertEqual(
            obj._floor_body.get_collider().collision_layer,
            CollisionLayer.TERRAIN,
        )


# ===========================================================================
# FloorSceneObject._compile_properties
# ===========================================================================


class TestFloorSceneObjectCompileProperties(unittest.TestCase):

    def test_compile_properties_adds_floor_color_key(self):
        obj = _make_floor(floor_color="#303030")
        obj._compile_properties()
        self.assertIn("floor_color", obj._properties)

    def test_compile_properties_floor_color_matches_bg_color(self):
        obj = _make_floor(floor_color="#aabbcc")
        obj._compile_properties()
        self.assertEqual(obj._properties["floor_color"], "#aabbcc")

    def test_compile_properties_floor_color_updates_after_bg_color_change(self):
        obj = _make_floor(floor_color="#111111")
        obj.bg_color = "#ffffff"
        obj._compile_properties()
        self.assertEqual(obj._properties["floor_color"], "#ffffff")


# ===========================================================================
# FloorSceneObject.from_dict
# ===========================================================================


class TestFloorSceneObjectFromDict(unittest.TestCase):

    def _minimal_dict(self, **overrides) -> dict:
        base = {
            "name": "floor_obj",
            "body": {"name": "b"},
            "properties": {},
        }
        base.update(overrides)
        return base

    def test_returns_floor_scene_object_instance(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict())
        self.assertIsInstance(obj, FloorSceneObject)

    def test_restores_name(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict(name="restored_floor"))
        self.assertEqual(obj.name, "restored_floor")

    def test_restores_floor_color_from_properties(self):
        data = self._minimal_dict(properties={"floor_color": "#123456"})
        obj = FloorSceneObject.from_dict(data)
        self.assertEqual(obj.bg_color, "#123456")

    def test_default_floor_color_when_absent(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj.bg_color, SCENE_OBJECT_DEF_COLOR)

    def test_restores_layer(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict(layer=7))
        self.assertEqual(obj._layer, 7)

    def test_default_layer_when_absent(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj._layer, 0)

    def test_restores_description(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict(description="loading bay"))
        self.assertEqual(obj.description, "loading bay")

    def test_restores_id(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict(id="floor-xyz"))
        self.assertEqual(obj.id, "floor-xyz")

    def test_restores_group_id(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict(group_id="group-1"))
        self.assertEqual(obj._group_id, "group-1")

    def test_group_id_none_when_absent(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict())
        self.assertIsNone(obj._group_id)

    def test_restores_tags(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict(tags=["a", "b"]))
        self.assertIn("a", obj._tags)
        self.assertIn("b", obj._tags)

    def test_tags_empty_list_when_absent(self):
        obj = FloorSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj._tags, [])

    def test_creates_floor_body_from_body_dict(self):
        data = self._minimal_dict(body={"name": "floor_b", "width": 500.0, "height": 500.0})
        obj = FloorSceneObject.from_dict(data)
        self.assertIsInstance(obj._floor_body, FloorBody)

    def test_body_dimensions_restored(self):
        data = self._minimal_dict(body={"name": "b", "width": 400.0, "height": 250.0})
        obj = FloorSceneObject.from_dict(data)
        self.assertAlmostEqual(obj._floor_body.width, 400.0)
        self.assertAlmostEqual(obj._floor_body.height, 250.0)


# ===========================================================================
# Factory template registration
# ===========================================================================


class TestFloorSceneObjectFactoryTemplate(unittest.TestCase):

    def test_template_is_registered(self):
        template = SceneObjectFactory.get_template(FloorSceneObject._template_name)
        self.assertIsNotNone(template)

    def test_template_name_matches_constant(self):
        template = SceneObjectFactory.get_template(FloorSceneObject._template_name)
        self.assertEqual(template.name, FloorSceneObject._template_name)

    def test_template_factory_func_returns_floor_scene_object(self):
        template = SceneObjectFactory.get_template(FloorSceneObject._template_name)
        obj = template.factory_func(**template.default_kwargs)
        self.assertIsInstance(obj, FloorSceneObject)

    def test_template_default_color_matches_constant(self):
        template = SceneObjectFactory.get_template(FloorSceneObject._template_name)
        self.assertEqual(template.default_kwargs.get("floor_color"), SCENE_OBJECT_DEF_COLOR)


if __name__ == "__main__":
    unittest.main()
