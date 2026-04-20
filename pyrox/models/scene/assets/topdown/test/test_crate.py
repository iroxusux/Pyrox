"""Unit tests for CrateSceneObject.

Tests cover initialisation, the ``create`` factory classmethod, the
``crate_type`` / ``mass`` properties, the ``_compile_properties``
serialisation hook, and ``from_dict`` round-trip deserialisation.
"""
from __future__ import annotations

import unittest

from pyrox.interfaces import CollisionLayer
from pyrox.models.physics.crate import CrateBody
from pyrox.models.scene.assets.topdown.crate import (
    SCENE_OBJECT_DEF_COLOR,
    _CRATE_COLORS,
    CrateSceneObject,
)
from pyrox.models.scene.factory import SceneObjectFactory


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_body(
    name: str = "crate_body",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 20.0,
    height: float = 20.0,
    mass: float = 10.0,
    crate_type: str = "wooden",
) -> CrateBody:
    """Return a real :class:`CrateBody` for use in tests."""
    return CrateBody(name=name, x=x, y=y, width=width, height=height,
                     mass=mass, crate_type=crate_type)


def _make_crate(
    name: str = "crate",
    crate_color: str = SCENE_OBJECT_DEF_COLOR,
    layer: int = 0,
    description: str = "",
    properties: dict | None = None,
    id: str | None = None,
    group_id: str | None = None,
    tags: list[str] | None = None,
    body: CrateBody | None = None,
) -> CrateSceneObject:
    """Construct a :class:`CrateSceneObject` using a real :class:`CrateBody`."""
    physics_body = body or _make_body()
    return CrateSceneObject(
        name=name,
        physics_body=physics_body,
        crate_color=crate_color,
        layer=layer,
        description=description,
        properties=properties,
        id=id,
        group_id=group_id,
        tags=tags,
    )


# ===========================================================================
# CrateSceneObject – initialisation
# ===========================================================================


class TestCrateSceneObjectInit(unittest.TestCase):

    def test_name_stored_correctly(self):
        obj = _make_crate(name="my_crate")
        self.assertEqual(obj.name, "my_crate")

    def test_default_crate_color(self):
        obj = _make_crate()
        self.assertEqual(obj.bg_color, SCENE_OBJECT_DEF_COLOR)

    def test_custom_crate_color(self):
        obj = _make_crate(crate_color="#aabbcc")
        self.assertEqual(obj.bg_color, "#aabbcc")

    def test_crate_color_from_properties_overrides_param(self):
        obj = _make_crate(
            crate_color="#111111",
            properties={"crate_color": "#999999"},
        )
        self.assertEqual(obj.bg_color, "#999999")

    def test_default_layer_is_zero(self):
        obj = _make_crate()
        self.assertEqual(obj._layer, 0)

    def test_custom_layer_stored(self):
        obj = _make_crate(layer=3)
        self.assertEqual(obj._layer, 3)

    def test_description_stored(self):
        obj = _make_crate(description="a wooden crate")
        self.assertEqual(obj.description, "a wooden crate")

    def test_physics_body_reference_stored(self):
        body = _make_body()
        obj = _make_crate(body=body)
        self.assertIs(obj._crate_body, body)

    def test_explicit_id_stored(self):
        obj = _make_crate(id="crate-abc-123")
        self.assertEqual(obj.id, "crate-abc-123")

    def test_auto_id_generated_when_none(self):
        obj = _make_crate(id=None)
        self.assertIsNotNone(obj.id)
        self.assertGreater(len(obj.id), 0)

    def test_group_id_stored(self):
        obj = _make_crate(group_id="grp-001")
        self.assertEqual(obj._group_id, "grp-001")

    def test_group_id_none_by_default(self):
        obj = _make_crate()
        self.assertIsNone(obj._group_id)

    def test_tags_stored(self):
        obj = _make_crate(tags=["dynamic", "pushable"])
        self.assertIn("dynamic", obj._tags)
        self.assertIn("pushable", obj._tags)

    def test_tags_empty_by_default(self):
        obj = _make_crate()
        self.assertEqual(obj._tags, [])

    def test_scene_object_type(self):
        obj = _make_crate()
        self.assertEqual(obj._scene_object_type, CrateSceneObject._scene_object_type)

    def test_template_name(self):
        obj = _make_crate()
        self.assertEqual(obj._template_name, CrateSceneObject._template_name)


# ===========================================================================
# CrateSceneObject – introspection properties
# ===========================================================================


class TestCrateSceneObjectProperties(unittest.TestCase):

    def test_crate_type_wooden(self):
        body = _make_body(crate_type="wooden")
        obj = _make_crate(body=body)
        self.assertEqual(obj.crate_type, "wooden")

    def test_crate_type_metal(self):
        body = _make_body(crate_type="metal")
        obj = _make_crate(body=body)
        self.assertEqual(obj.crate_type, "metal")

    def test_crate_type_cardboard(self):
        body = _make_body(crate_type="cardboard")
        obj = _make_crate(body=body)
        self.assertEqual(obj.crate_type, "cardboard")

    def test_crate_type_plastic(self):
        body = _make_body(crate_type="plastic")
        obj = _make_crate(body=body)
        self.assertEqual(obj.crate_type, "plastic")

    def test_mass_reflects_body_mass(self):
        body = _make_body(mass=42.5)
        obj = _make_crate(body=body)
        self.assertAlmostEqual(obj.mass, 42.5)

    def test_mass_default(self):
        obj = _make_crate()
        self.assertAlmostEqual(obj.mass, 10.0)


# ===========================================================================
# CrateSceneObject.create – classmethod factory
# ===========================================================================


class TestCrateSceneObjectCreate(unittest.TestCase):

    def test_returns_crate_scene_object_instance(self):
        obj = CrateSceneObject.create(name="c")
        self.assertIsInstance(obj, CrateSceneObject)

    def test_name_passed_through(self):
        obj = CrateSceneObject.create(name="box_a")
        self.assertEqual(obj.name, "box_a")

    def test_default_position_is_origin(self):
        obj = CrateSceneObject.create(name="c")
        self.assertAlmostEqual(obj._crate_body.x, 0.0)
        self.assertAlmostEqual(obj._crate_body.y, 0.0)

    def test_custom_position_stored_in_body(self):
        obj = CrateSceneObject.create(name="c", x=30.0, y=60.0)
        self.assertAlmostEqual(obj._crate_body.x, 30.0)
        self.assertAlmostEqual(obj._crate_body.y, 60.0)

    def test_default_width(self):
        obj = CrateSceneObject.create(name="c")
        self.assertAlmostEqual(obj._crate_body.width, 20.0)

    def test_default_height(self):
        obj = CrateSceneObject.create(name="c")
        self.assertAlmostEqual(obj._crate_body.height, 20.0)

    def test_custom_dimensions(self):
        obj = CrateSceneObject.create(name="c", width=40.0, height=50.0)
        self.assertAlmostEqual(obj._crate_body.width, 40.0)
        self.assertAlmostEqual(obj._crate_body.height, 50.0)

    def test_default_mass(self):
        obj = CrateSceneObject.create(name="c")
        self.assertAlmostEqual(obj.mass, 10.0)

    def test_custom_mass(self):
        obj = CrateSceneObject.create(name="c", mass=25.0)
        self.assertAlmostEqual(obj.mass, 25.0)

    def test_default_crate_type_is_wooden(self):
        obj = CrateSceneObject.create(name="c")
        self.assertEqual(obj.crate_type, "wooden")

    def test_custom_crate_type(self):
        obj = CrateSceneObject.create(name="c", crate_type="metal")
        self.assertEqual(obj.crate_type, "metal")

    def test_color_defaults_to_crate_type_color_wooden(self):
        obj = CrateSceneObject.create(name="c", crate_type="wooden")
        self.assertEqual(obj.bg_color, _CRATE_COLORS["wooden"])

    def test_color_defaults_to_crate_type_color_metal(self):
        obj = CrateSceneObject.create(name="c", crate_type="metal")
        self.assertEqual(obj.bg_color, _CRATE_COLORS["metal"])

    def test_color_defaults_to_crate_type_color_cardboard(self):
        obj = CrateSceneObject.create(name="c", crate_type="cardboard")
        self.assertEqual(obj.bg_color, _CRATE_COLORS["cardboard"])

    def test_color_defaults_to_crate_type_color_plastic(self):
        obj = CrateSceneObject.create(name="c", crate_type="plastic")
        self.assertEqual(obj.bg_color, _CRATE_COLORS["plastic"])

    def test_explicit_crate_color_overrides_type_default(self):
        obj = CrateSceneObject.create(name="c", crate_type="wooden", crate_color="#ff0000")
        self.assertEqual(obj.bg_color, "#ff0000")

    def test_layer_passed_through(self):
        obj = CrateSceneObject.create(name="c", layer=4)
        self.assertEqual(obj._layer, 4)

    def test_id_passed_through(self):
        obj = CrateSceneObject.create(name="c", id="custom-id")
        self.assertEqual(obj.id, "custom-id")

    def test_description_passed_through(self):
        obj = CrateSceneObject.create(name="c", description="heavy crate")
        self.assertEqual(obj.description, "heavy crate")

    def test_group_id_passed_through(self):
        obj = CrateSceneObject.create(name="c", group_id="grp-99")
        self.assertEqual(obj._group_id, "grp-99")

    def test_tags_passed_through(self):
        obj = CrateSceneObject.create(name="c", tags=["a", "b"])
        self.assertIn("a", obj._tags)
        self.assertIn("b", obj._tags)

    def test_body_dict_creates_crate_body_from_dict(self):
        body_data = {"name": "b", "x": 5.0, "y": 10.0, "width": 30.0, "height": 30.0}
        obj = CrateSceneObject.create(name="c", body=body_data)
        self.assertAlmostEqual(obj._crate_body.x, 5.0)
        self.assertAlmostEqual(obj._crate_body.y, 10.0)

    def test_collision_layer_default_is_default_layer(self):
        obj = CrateSceneObject.create(name="c")
        self.assertEqual(
            obj._crate_body.get_collider().collision_layer,
            CollisionLayer.DEFAULT,
        )

    def test_custom_collision_layer_stored(self):
        obj = CrateSceneObject.create(name="c", collision_layer=CollisionLayer.ENEMY)
        self.assertEqual(
            obj._crate_body.get_collider().collision_layer,
            CollisionLayer.ENEMY,
        )


# ===========================================================================
# CrateSceneObject._compile_properties
# ===========================================================================


class TestCrateSceneObjectCompileProperties(unittest.TestCase):

    def test_compile_properties_adds_crate_color_key(self):
        obj = _make_crate(crate_color="#303030")
        obj._compile_properties()
        self.assertIn("crate_color", obj._properties)

    def test_compile_properties_crate_color_matches_bg_color(self):
        obj = _make_crate(crate_color="#aabbcc")
        obj._compile_properties()
        self.assertEqual(obj._properties["crate_color"], "#aabbcc")

    def test_compile_properties_crate_color_updates_after_bg_color_change(self):
        obj = _make_crate(crate_color="#111111")
        obj.bg_color = "#ffffff"
        obj._compile_properties()
        self.assertEqual(obj._properties["crate_color"], "#ffffff")

    def test_compile_properties_adds_crate_type_key(self):
        obj = _make_crate(body=_make_body(crate_type="metal"))
        obj._compile_properties()
        self.assertIn("crate_type", obj._properties)

    def test_compile_properties_crate_type_matches_body(self):
        obj = _make_crate(body=_make_body(crate_type="cardboard"))
        obj._compile_properties()
        self.assertEqual(obj._properties["crate_type"], "cardboard")


# ===========================================================================
# CrateSceneObject.from_dict
# ===========================================================================


class TestCrateSceneObjectFromDict(unittest.TestCase):

    def _minimal_dict(self, **overrides) -> dict:
        base: dict = {
            "name": "crate_obj",
            "body": {"name": "b"},
            "properties": {},
        }
        base.update(overrides)
        return base

    def test_returns_crate_scene_object_instance(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict())
        self.assertIsInstance(obj, CrateSceneObject)

    def test_restores_name(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict(name="restored_crate"))
        self.assertEqual(obj.name, "restored_crate")

    def test_restores_crate_color_from_properties(self):
        data = self._minimal_dict(properties={"crate_color": "#123456"})
        obj = CrateSceneObject.from_dict(data)
        self.assertEqual(obj.bg_color, "#123456")

    def test_default_crate_color_uses_crate_type_lookup(self):
        data = self._minimal_dict(properties={"crate_type": "metal"})
        obj = CrateSceneObject.from_dict(data)
        self.assertEqual(obj.bg_color, _CRATE_COLORS["metal"])

    def test_default_crate_color_falls_back_to_wooden(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj.bg_color, _CRATE_COLORS["wooden"])

    def test_restores_layer(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict(layer=6))
        self.assertEqual(obj._layer, 6)

    def test_default_layer_when_absent(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj._layer, 0)

    def test_restores_description(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict(description="storage crate"))
        self.assertEqual(obj.description, "storage crate")

    def test_restores_id(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict(id="crate-xyz"))
        self.assertEqual(obj.id, "crate-xyz")

    def test_restores_group_id(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict(group_id="group-2"))
        self.assertEqual(obj._group_id, "group-2")

    def test_group_id_none_when_absent(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict())
        self.assertIsNone(obj._group_id)

    def test_restores_tags(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict(tags=["x", "y"]))
        self.assertIn("x", obj._tags)
        self.assertIn("y", obj._tags)

    def test_tags_empty_list_when_absent(self):
        obj = CrateSceneObject.from_dict(self._minimal_dict())
        self.assertEqual(obj._tags, [])

    def test_creates_crate_body_from_body_dict(self):
        data = self._minimal_dict(body={"name": "crate_b", "width": 25.0, "height": 25.0})
        obj = CrateSceneObject.from_dict(data)
        self.assertIsInstance(obj._crate_body, CrateBody)

    def test_body_dimensions_restored(self):
        data = self._minimal_dict(body={"name": "b", "width": 35.0, "height": 15.0})
        obj = CrateSceneObject.from_dict(data)
        self.assertAlmostEqual(obj._crate_body.width, 35.0)
        self.assertAlmostEqual(obj._crate_body.height, 15.0)


# ===========================================================================
# Factory template registration
# ===========================================================================


class TestCrateSceneObjectFactoryTemplate(unittest.TestCase):

    def test_template_is_registered(self):
        template = SceneObjectFactory.get_template(CrateSceneObject._template_name)
        self.assertIsNotNone(template)

    def test_template_name_matches_constant(self):
        template = SceneObjectFactory.get_template(CrateSceneObject._template_name)
        self.assertEqual(template.name, CrateSceneObject._template_name)

    def test_template_factory_func_returns_crate_scene_object(self):
        template = SceneObjectFactory.get_template(CrateSceneObject._template_name)
        obj = template.factory_func(**template.default_kwargs)
        self.assertIsInstance(obj, CrateSceneObject)

    def test_template_default_crate_type_is_wooden(self):
        template = SceneObjectFactory.get_template(CrateSceneObject._template_name)
        self.assertEqual(template.default_kwargs.get("crate_type"), "wooden")


if __name__ == "__main__":
    unittest.main()
