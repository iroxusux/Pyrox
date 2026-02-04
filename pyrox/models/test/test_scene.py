"""Unit tests for pyrox.models.scene module."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from pyrox.interfaces import (
    ISceneObject,
    BodyType,
    ColliderType,
    CollisionLayer
)
from pyrox.models import (
    Scene,
    SceneObject,
    SceneObjectFactory,
    BasePhysicsBody,
    Material,
)


class TestScene(unittest.TestCase):
    """Test cases for Scene class."""

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
                collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
                collision_mask: list[CollisionLayer] | None = None,
                material: Material | None = None,
            ):
                """Initialize test physics body."""
                super().__init__(
                    name=name,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    mass=mass,
                    body_type=BodyType.DYNAMIC,
                    collider_type=ColliderType.RECTANGLE,
                    collision_layer=collision_layer,
                    collision_mask=collision_mask,
                    material=material,
                )

        self.TestSceneObject = TestSceneObject
        self.TestPhysicsBody = TestBasePhysicsBody
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_with_defaults(self):
        """Test Scene initialization with default values."""
        scene = Scene()

        self.assertEqual(scene.name, "Untitled Scene")
        self.assertEqual(scene.description, "")
        self.assertIsInstance(scene.scene_objects, dict)
        self.assertEqual(len(scene.scene_objects), 0)
        self.assertIsInstance(scene.on_scene_object_added, list)
        self.assertIsInstance(scene.on_scene_object_removed, list)
        self.assertEqual(len(scene.on_scene_object_added), 0)
        self.assertEqual(len(scene.on_scene_object_removed), 0)

    def test_init_with_params(self):
        """Test Scene initialization with parameters."""
        scene = Scene(
            name="Test Scene",
            description="A test scene description"
        )

        self.assertEqual(scene.name, "Test Scene")
        self.assertEqual(scene.description, "A test scene description")

    def test_add_scene_object(self):
        """Test Scene.add_scene_object() method."""
        scene = Scene()
        scene_object = self.TestSceneObject(
            id="dev_001",
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertIn("dev_001", scene.scene_objects)
        self.assertEqual(scene.scene_objects["dev_001"], scene_object)

    def test_add_scene_object_duplicate_id_raises_error(self):
        """Test that adding a scene_object with duplicate ID raises ValueError."""
        scene = Scene()
        scene_object1 = self.TestSceneObject(
            id="dev_003",
            scene_object_type="TestSceneObject",
            name="SceneObject1",
            physics_body=self.TestPhysicsBody()
        )
        scene_object2 = self.TestSceneObject(
            id="dev_003",
            scene_object_type="TestSceneObject",
            name="SceneObject2",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object1)

        with self.assertRaises(ValueError) as context:
            scene.add_scene_object(scene_object2)

        self.assertIn("already exists", str(context.exception))
        self.assertIn("dev_003", str(context.exception))

    def test_remove_scene_object(self):
        """Test Scene.remove_scene_object() method."""
        scene = Scene()
        scene_object = self.TestSceneObject(
            id="dev_004",
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        self.assertEqual(len(scene.scene_objects), 1)

        scene.remove_scene_object("dev_004")
        self.assertEqual(len(scene.scene_objects), 0)

    def test_remove_nonexistent_scene_object(self):
        """Test removing a scene_object that doesn't exist."""
        scene = Scene()

        # Should not raise an error
        scene.remove_scene_object("nonexistent")

    def test_get_scene_object(self):
        """Test Scene.get_scene_object() method."""
        scene = Scene()
        scene_object = self.TestSceneObject(
            id="dev_006",
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)

        result = scene.get_scene_object("dev_006")
        self.assertEqual(result, scene_object)

    def test_get_scene_object_not_exists(self):
        """Test get_scene_object with non-existent ID."""
        scene = Scene()

        result = scene.get_scene_object("nonexistent")
        self.assertIsNone(result)

    def test_update(self):
        """Test Scene.update() method."""
        scene = Scene()

        # Create scene_object that tracks updates
        scene_object = self.TestSceneObject(
            id="dev_008",
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )
        scene_object.properties["update_count"] = 0

        # Override update method
        def custom_update(delta_time):
            scene_object.properties["update_count"] += 1
            scene_object.properties["last_delta"] = delta_time

        scene_object.update = custom_update  # type: ignore

        scene.add_scene_object(scene_object)

        # Update scene
        scene.update(0.5)

        self.assertEqual(scene_object.properties["update_count"], 1)
        self.assertEqual(scene_object.properties["last_delta"], 0.5)

    def test_update_multiple_scene_objects(self):
        """Test updating multiple scene_objects."""
        scene = Scene()

        scene_object1 = self.TestSceneObject(
            id="dev_009",
            scene_object_type="TestSceneObject",
            name="SceneObject1",
            physics_body=self.TestPhysicsBody()
        )
        scene_object2 = self.TestSceneObject(
            id="dev_010",
            scene_object_type="TestSceneObject",
            name="SceneObject2",
            physics_body=self.TestPhysicsBody()
        )

        scene_object1.properties["updated"] = False
        scene_object2.properties["updated"] = False

        def update1(delta_time: float):
            scene_object1.properties["updated"] = True

        def update2(delta_time: float):
            scene_object2.properties["updated"] = True

        scene_object1.update = update1  # type: ignore
        scene_object2.update = update2  # type: ignore

        scene.add_scene_object(scene_object1)
        scene.add_scene_object(scene_object2)

        scene.update(0.1)

        self.assertTrue(scene_object1.properties["updated"])
        self.assertTrue(scene_object2.properties["updated"])

    def test_to_dict(self):
        """Test Scene.to_dict() method."""
        scene = Scene(name="DictScene", description="Test dict conversion")

        scene_object = self.TestSceneObject(
            id="dev_011",
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )
        scene.add_scene_object(scene_object)

        result = scene.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "DictScene")
        self.assertEqual(result["description"], "Test dict conversion")
        self.assertIn("scene_objects", result)
        self.assertEqual(len(result["scene_objects"]), 1)

    def test_save(self):
        """Test Scene.save() method."""
        scene = Scene(name="SaveScene", description="Test save")

        scene_object = self.TestSceneObject(
            id="dev_012",
            scene_object_type="TestSceneObject",
            name="SaveDev",
            physics_body=self.TestPhysicsBody()
        )
        scene.add_scene_object(scene_object)

        filepath = Path(self.test_dir) / "test_scene.json"
        scene.save(filepath)

        self.assertTrue(filepath.exists())

        # Verify JSON content
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["name"], "SaveScene")
        self.assertEqual(len(data["scene_objects"]), 1)

    def test_save_creates_directory(self):
        """Test that save creates parent directories if needed."""
        scene = Scene(name="DirScene")

        filepath = Path(self.test_dir) / "subdir" / "nested" / "scene.json"
        scene.save(filepath)

        self.assertTrue(filepath.exists())
        self.assertTrue(filepath.parent.exists())

    def test_load(self):
        """Test Scene.load() class method."""
        # Create and save a scene
        original_scene = Scene(name="LoadScene", description="Test load")
        scene_object = self.TestSceneObject(
            id="dev_013",
            scene_object_type="TestSceneObject",
            name="LoadDev",
            physics_body=self.TestPhysicsBody()
        )
        original_scene.add_scene_object(scene_object)

        filepath = Path(self.test_dir) / "load_scene.json"
        original_scene.save(filepath)

        # Create factory and register scene_object type
        SceneObjectFactory.register("TestSceneObject", self.TestSceneObject)

        # Load the scene
        loaded_scene = Scene.load(filepath)

        self.assertEqual(loaded_scene.name, "LoadScene")
        self.assertEqual(loaded_scene.description, "Test load")
        self.assertEqual(len(loaded_scene.scene_objects), 1)
        self.assertIn("dev_013", loaded_scene.scene_objects)

    def test_scene_roundtrip(self):
        """Test that saving and loading a scene preserves data."""
        original = Scene(name="RoundtripScene", description="Full roundtrip test")

        # Add scene_object with tags
        scene_object = self.TestSceneObject(
            id="dev_014",
            scene_object_type="TestSceneObject",
            name="RoundtripDev",
            properties={"value": 123},
            physics_body=self.TestPhysicsBody()
        )
        original.add_scene_object(scene_object)

        # Save
        filepath = Path(self.test_dir) / "roundtrip.json"
        original.save(filepath)

        # Load
        try:
            SceneObjectFactory.register("TestSceneObject", self.TestSceneObject)
        except ValueError:
            pass  # Already registered
        loaded = Scene.load(filepath)

        # Verify
        self.assertEqual(loaded.name, original.name)
        self.assertEqual(loaded.description, original.description)
        self.assertEqual(len(loaded.scene_objects), len(original.scene_objects))

        loaded_scene_object = loaded.get_scene_object("dev_014")
        self.assertIsNotNone(loaded_scene_object)
        self.assertEqual(loaded_scene_object.name, "RoundtripDev")  # type: ignore
        self.assertEqual(loaded_scene_object.properties["value"], 123)  # type: ignore

    def test_repr(self):
        """Test Scene.__repr__() method."""
        scene = Scene(name="ReprScene")

        scene_object = self.TestSceneObject(
            id="dev_015",
            scene_object_type="TestSceneObject",
            name="Dev",
            physics_body=self.TestPhysicsBody()
        )
        scene.add_scene_object(scene_object)

        repr_str = repr(scene)

        self.assertIn("ReprScene", repr_str)
        self.assertIn("scene_objects=1", repr_str)

    def test_get_scene_objects(self):
        """Test Scene.get_scene_objects() method."""
        scene = Scene()
        scene_object1 = self.TestSceneObject(
            id="obj_001",
            scene_object_type="TestSceneObject",
            name="Object1",
            physics_body=self.TestPhysicsBody()
        )
        scene_object2 = self.TestSceneObject(
            id="obj_002",
            scene_object_type="TestSceneObject",
            name="Object2",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object1)
        scene.add_scene_object(scene_object2)

        objects = scene.get_scene_objects()

        self.assertIsInstance(objects, dict)
        self.assertEqual(len(objects), 2)
        self.assertIn("obj_001", objects)
        self.assertIn("obj_002", objects)

    def test_set_scene_objects(self):
        """Test Scene.set_scene_objects() method."""
        scene = Scene()
        scene_object1 = self.TestSceneObject(
            id="obj_003",
            scene_object_type="TestSceneObject",
            name="Object3",
            physics_body=self.TestPhysicsBody()
        )

        objects_dict: Dict[str, ISceneObject] = {"obj_003": scene_object1}
        scene.set_scene_objects(objects_dict)

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertIn("obj_003", scene.scene_objects)

    def test_set_scene_objects_invalid_type(self):
        """Test that set_scene_objects raises error for non-dict."""
        scene = Scene()

        with self.assertRaises(ValueError) as context:
            scene.set_scene_objects([])  # type: ignore

        self.assertIn("must be a dictionary", str(context.exception))

    def test_set_name_empty_raises_error(self):
        """Test that setting empty name raises ValueError."""
        scene = Scene()

        with self.assertRaises(ValueError) as context:
            scene.set_name("")

        self.assertIn("cannot be empty", str(context.exception))

    def test_get_name(self):
        """Test Scene.get_name() method."""
        scene = Scene(name="TestName")
        self.assertEqual(scene.get_name(), "TestName")

    def test_get_description(self):
        """Test Scene.get_description() method."""
        scene = Scene(description="Test Description")
        self.assertEqual(scene.get_description(), "Test Description")

    def test_set_description(self):
        """Test Scene.set_description() method."""
        scene = Scene()
        scene.set_description("New Description")
        self.assertEqual(scene.get_description(), "New Description")

    def test_get_on_scene_object_added(self):
        """Test Scene.get_on_scene_object_added() method."""
        scene = Scene()

        callbacks = scene.get_on_scene_object_added()
        self.assertIsInstance(callbacks, list)
        self.assertEqual(len(callbacks), 0)

    def test_add_scene_object_calls_on_scene_object_added(self):
        """Test that adding a scene_object calls the on_scene_object_added callbacks."""
        scene = Scene()
        called = []

        def callback(so):
            called.append(so.get_id())

        scene.get_on_scene_object_added().append(callback)

        scene_object = self.TestSceneObject(
            id="dev_016",
            scene_object_type="TestSceneObject",
            name="CallbackDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)

        self.assertIn("dev_016", called)

    def test_get_on_scene_object_removed(self):
        """Test Scene.get_on_scene_object_removed() method."""
        scene = Scene()

        callbacks = scene.get_on_scene_object_removed()
        self.assertIsInstance(callbacks, list)
        self.assertEqual(len(callbacks), 0)

    def test_remove_scene_object_calls_on_scene_object_removed(self):
        """Test that removing a scene_object calls the on_scene_object_removed callbacks."""
        scene = Scene()
        called = []

        def callback(so):
            called.append(so.get_id())

        scene.get_on_scene_object_removed().append(callback)

        scene_object = self.TestSceneObject(
            id="dev_017",
            scene_object_type="TestSceneObject",
            name="CallbackDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        scene.remove_scene_object("dev_017")

        self.assertIn("dev_017", called)


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
            id="test_001",
            name="TestObject",
            scene_object_type="TestType",
            physics_body=self.TestPhysicsBody()
        )

        self.assertEqual(obj.get_id(), "test_001")
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
            id="test_002",
            name="FullObject",
            scene_object_type="FullType",
            physics_body=body,
            description="Test description",
            properties=properties,
        )

        self.assertEqual(obj.get_id(), "test_002")
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
            id="id_test",
            name="Name",
            scene_object_type="Type",
            physics_body=self.TestPhysicsBody()
        )
        self.assertEqual(obj.get_id(), "id_test")

    def test_set_id(self):
        """Test SceneObject.set_id() method."""
        obj = SceneObject(id="old_id", name="Name", scene_object_type="Type", physics_body=self.TestPhysicsBody())
        obj.set_id("new_id")
        self.assertEqual(obj.get_id(), "new_id")

    def test_id_property(self):
        """Test SceneObject id property access."""
        obj = SceneObject(id="prop_id", name="Name", scene_object_type="Type", physics_body=self.TestPhysicsBody())
        self.assertEqual(obj.id, "prop_id")

    def test_get_properties(self):
        """Test SceneObject.get_properties() method."""
        properties = {"test": "value", "number": 123}
        obj = SceneObject(
            id="test",
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
        obj = SceneObject(id="test", name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody()
                          )
        new_props = {"new_key": "new_value"}

        obj.set_properties(new_props)
        self.assertEqual(obj.get_properties(), new_props)

    def test_set_properties_invalid_type_raises_error(self):
        """Test that set_properties raises error for non-dict."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())

        with self.assertRaises(ValueError) as context:
            obj.set_properties("not a dict")  # type: ignore

        self.assertIn("must be a dictionary", str(context.exception))

    def test_properties_property(self):
        """Test SceneObject properties property access."""
        properties = {"key": "value"}
        obj = SceneObject(
            id="test",
            name="Name",
            scene_object_type="Type",
            properties=properties,
            physics_body=self.TestPhysicsBody()
        )
        self.assertEqual(obj.properties, properties)

    def test_get_scene_object_type(self):
        """Test SceneObject.get_scene_object_type() method."""
        obj = SceneObject(id="test", name="Name", scene_object_type="CustomType",
                          physics_body=self.TestPhysicsBody())
        self.assertEqual(obj.get_scene_object_type(), "CustomType")

    def test_set_scene_object_type(self):
        """Test SceneObject.set_scene_object_type() method."""
        obj = SceneObject(id="test", name="Name", scene_object_type="OldType",
                          physics_body=self.TestPhysicsBody())
        obj.set_scene_object_type("NewType")
        self.assertEqual(obj.get_scene_object_type(), "NewType")

    def test_scene_object_type_property(self):
        """Test SceneObject scene_object_type property access."""
        obj = SceneObject(id="test", name="Name", scene_object_type="PropType",
                          physics_body=self.TestPhysicsBody())
        self.assertEqual(obj.scene_object_type, "PropType")

    def test_to_dict(self):
        """Test SceneObject.to_dict() method."""
        properties = {"key": "value", "num": 42}
        obj = SceneObject(
            id="dict_test",
            name="DictObject",
            scene_object_type="DictType",
            description="Dict description",
            properties=properties,
            physics_body=self.TestPhysicsBody()
        )

        result = obj.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "dict_test")
        self.assertEqual(result["name"], "DictObject")
        self.assertEqual(result["scene_object_type"], "DictType")
        self.assertEqual(result["description"], "Dict description")
        self.assertEqual(result["properties"], properties)

    def test_from_dict(self):
        """Test SceneObject.from_dict() class method."""
        data = {
            "id": "from_dict_test",
            "name": "FromDictObject",
            "scene_object_type": "FromDictType",
            "description": "From dict description",
            "properties": {"loaded": True}
        }

        obj = SceneObject.from_dict(data)

        self.assertEqual(obj.get_id(), "from_dict_test")
        self.assertEqual(obj.get_name(), "FromDictObject")
        self.assertEqual(obj.get_scene_object_type(), "FromDictType")
        self.assertEqual(obj.get_description(), "From dict description")
        self.assertEqual(obj.get_properties()['loaded'], True)

    def test_from_dict_with_defaults(self):
        """Test SceneObject.from_dict() with missing optional fields."""
        data = {
            "id": "minimal",
            "name": "MinimalObject",
            "scene_object_type": "MinimalType"
        }

        obj = SceneObject.from_dict(data)

        self.assertEqual(obj.get_id(), "minimal")
        self.assertEqual(obj.get_name(), "MinimalObject")
        self.assertEqual(obj.get_scene_object_type(), "MinimalType")
        self.assertEqual(obj.get_description(), "")
        self.assertIsInstance(obj.get_properties(), dict)

    def test_update_method_exists(self):
        """Test that update method exists and is callable."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())

        self.assertTrue(hasattr(obj, 'update'))
        self.assertTrue(callable(obj.update))

        # Should not raise
        obj.update(0.016)

    def test_roundtrip_to_dict_from_dict(self):
        """Test roundtrip conversion to/from dict."""
        original = SceneObject(
            id="roundtrip",
            name="RoundtripObject",
            scene_object_type="RoundtripType",
            description="Roundtrip test",
            properties={"value": 123, "text": "test"},
            physics_body=self.TestPhysicsBody()
        )

        data = original.to_dict()
        loaded = SceneObject.from_dict(data)

        self.assertEqual(loaded.get_id(), original.get_id())
        self.assertEqual(loaded.get_name(), original.get_name())
        self.assertEqual(loaded.get_scene_object_type(), original.get_scene_object_type())
        self.assertEqual(loaded.get_description(), original.get_description())
        self.assertEqual(loaded.get_properties(), original.get_properties())

    def test_set_property_sets_attribute_and_dictionary(self):
        """Test that set_property sets both attribute and properties dict."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())

        obj.set_property("x", 10)

        self.assertEqual(obj.physics_body.get_x(), 10)
        self.assertEqual(obj.properties.get("x"), 10)

    def test_get_property_retrieves_attr_if_not_in_dict(self):
        """Test that get_property retrieves attribute if not in properties dict."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type",
                          physics_body=self.TestPhysicsBody())
        obj.physics_body.set_x(20)

        self.assertNotIn("bing_bong", obj.properties)
        obj.set_property("bing_bong", 15)

        self.assertEqual(obj.get_property('bing_bong'), 15)
        self.assertIn("bing_bong", obj.properties)


class TestSceneObjectFactory(unittest.TestCase):
    """Test cases for SceneObjectFactory class."""

    def setUp(self):
        """Set up test fixtures."""

        class TestObjectA(SceneObject):
            """Test scene object type A."""
            pass

        class TestObjectB(SceneObject):
            """Test scene object type B."""
            pass

        self.TestObjectA = TestObjectA
        self.TestObjectB = TestObjectB

    def test_init(self):
        """Test SceneObjectFactory initialization."""
        with self.assertRaises(ValueError):
            SceneObjectFactory()

    def test_register(self):
        """Test SceneObjectFactory.register() method."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)

        self.assertIn("TypeA", SceneObjectFactory._registry)
        self.assertEqual(SceneObjectFactory._registry["TypeA"], self.TestObjectA)

    def test_register_duplicate_does_not_raise_error(self):
        """Test that registering duplicate type does not raise error."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)

        # Registering again with same type should not raise
        SceneObjectFactory.register("TypeA", self.TestObjectA)

    def test_unregister(self):
        """Test SceneObjectFactory.unregister() method."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)
        self.assertIn("TypeA", SceneObjectFactory._registry)

        SceneObjectFactory.unregister("TypeA")
        self.assertNotIn("TypeA", SceneObjectFactory._registry)

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent type doesn't raise error."""
        # Should not raise
        SceneObjectFactory.unregister("NonExistent")

    def test_get_registered_types(self):
        """Test SceneObjectFactory.get_registered_types() method."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)
        SceneObjectFactory.register("TypeB", self.TestObjectB)

        types = SceneObjectFactory.get_registered_types()

        self.assertIsInstance(types, list)
        self.assertGreaterEqual(len(types), 2)
        self.assertIn("TypeA", types)
        self.assertIn("TypeB", types)

    def test_create_scene_object(self):
        """Test SceneObjectFactory.create_scene_object() method."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)

        data = {
            "id": "created_obj",
            "name": "CreatedObject",
            "scene_object_type": "TypeA",
            "description": "Created via factory",
            "properties": {"created": True}
        }

        obj = SceneObjectFactory.create_scene_object(data)

        self.assertIsInstance(obj, self.TestObjectA)
        self.assertEqual(obj.get_id(), "created_obj")
        self.assertEqual(obj.get_name(), "CreatedObject")
        self.assertEqual(obj.get_scene_object_type(), "TypeA")
        self.assertIsInstance(obj.get_properties(), dict)
        self.assertEqual(obj.get_properties().get("created"), True)

    def test_create_scene_object_unregistered_type_raises_error(self):
        """Test creating object with unregistered type raises ValueError."""
        data = {
            "id": "test",
            "name": "Test",
            "scene_object_type": "UnregisteredType"
        }

        with self.assertRaises(ValueError) as context:
            SceneObjectFactory.create_scene_object(data)

        self.assertIn("not registered", str(context.exception))
        self.assertIn("UnregisteredType", str(context.exception))
        self.assertIn("Available types", str(context.exception))

    def test_create_multiple_different_types(self):
        """Test creating multiple objects of different types."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)
        SceneObjectFactory.register("TypeB", self.TestObjectB)

        data_a = {
            "id": "obj_a",
            "name": "ObjectA",
            "scene_object_type": "TypeA"
        }

        data_b = {
            "id": "obj_b",
            "name": "ObjectB",
            "scene_object_type": "TypeB"
        }

        obj_a = SceneObjectFactory.create_scene_object(data_a)
        obj_b = SceneObjectFactory.create_scene_object(data_b)

        self.assertIsInstance(obj_a, self.TestObjectA)
        self.assertIsInstance(obj_b, self.TestObjectB)
        self.assertNotEqual(type(obj_a), type(obj_b))

    def test_factory_with_scene_integration(self):
        """Test factory integration with Scene class."""
        SceneObjectFactory.register("TypeA", self.TestObjectA)

        scene = Scene()

        # Create object via factory
        data = {
            "id": "integrated_obj",
            "name": "IntegratedObject",
            "scene_object_type": "TypeA"
        }

        obj = SceneObjectFactory.create_scene_object(data)
        scene.add_scene_object(obj)

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertIn("integrated_obj", scene.scene_objects)

    def test_multiple_registrations(self):
        """Test registering multiple types."""
        SceneObjectFactory.register("Type1", self.TestObjectA)
        SceneObjectFactory.register("Type2", self.TestObjectB)
        SceneObjectFactory.register("Type3", SceneObject)

        types = SceneObjectFactory.get_registered_types()
        self.assertGreaterEqual(len(types), 3)
        self.assertIn("Type1", types)
        self.assertIn("Type2", types)
        self.assertIn("Type3", types)

    def test_register_then_unregister_then_register(self):
        """Test register, unregister, then register again."""
        SceneObjectFactory.register("Type", self.TestObjectA)
        self.assertIn("Type", SceneObjectFactory._registry)

        SceneObjectFactory.unregister("Type")
        self.assertNotIn("Type", SceneObjectFactory._registry)

        # Should be able to register again after unregister
        SceneObjectFactory.register("Type", self.TestObjectB)
        self.assertIn("Type", SceneObjectFactory._registry)
        self.assertEqual(SceneObjectFactory._registry["Type"], self.TestObjectB)


class TestSceneObjectWithPhysics(unittest.TestCase):
    """Test cases for SceneObject class with physics body integration."""

    def test_init_with_required_params(self):
        """Test SceneObject initialization with required parameters."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(
            name="PhysicsObject",
            body_type=BodyType.DYNAMIC,
            mass=1.0,
        )

        obj = SceneObject(
            id="phys_001",
            name="PhysicsObject",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        self.assertEqual(obj.id, "phys_001")
        self.assertEqual(obj.name, "PhysicsObject")
        self.assertEqual(obj.get_scene_object_type(), "PhysicsType")
        self.assertEqual(obj.description, "")
        self.assertEqual(obj.physics_body.body_type, BodyType.DYNAMIC)
        self.assertEqual(obj.physics_body.mass, 1.0)

    def test_init_with_all_params(self):
        """Test SceneObject initialization with all parameters."""
        from pyrox.models.physics.base import BasePhysicsBody

        material = Material(density=2.0, restitution=0.8, friction=0.6, drag=0.2)
        physics_body = BasePhysicsBody(
            name="FullPhysicsObject",
            body_type=BodyType.STATIC,
            mass=5.0,
            x=100.0,
            y=200.0,
            width=50.0,
            height=75.0,
            roll=10.0,
            pitch=20.0,
            yaw=30.0,
            material=material,
            collider_type=ColliderType.CIRCLE,
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[CollisionLayer.TERRAIN, CollisionLayer.ENEMY],
            is_trigger=True,
        )

        obj = SceneObject(
            id="phys_002",
            name="FullPhysicsObject",
            scene_object_type="FullPhysicsType",
            description="Full physics object",
            properties={"custom": "value"},
            physics_body=physics_body
        )

        self.assertEqual(obj.id, "phys_002")
        self.assertEqual(obj.name, "FullPhysicsObject")
        self.assertEqual(obj.x, 100.0)
        self.assertEqual(obj.y, 200.0)
        self.assertEqual(obj.width, 50.0)
        self.assertEqual(obj.height, 75.0)
        self.assertEqual(obj.physics_body.body_type, BodyType.STATIC)
        self.assertEqual(obj.physics_body.mass, 5.0)
        self.assertEqual(obj.physics_body.material.restitution, 0.8)
        self.assertEqual(obj.physics_body.material.friction, 0.6)
        self.assertEqual(obj.physics_body.collider.collision_layer, CollisionLayer.PLAYER)
        self.assertTrue(obj.physics_body.collider.is_trigger)

    def test_physics_body_delegation(self):
        """Test that SceneObject delegates physics methods through physics_body."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(
            name="DelegateTest",
            body_type=BodyType.DYNAMIC,
            mass=1.0,
        )

        obj = SceneObject(
            id="phys_003",
            name="DelegateTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        # Test rigid body methods through physics_body
        obj.physics_body.set_mass(3.0)
        self.assertEqual(obj.physics_body.mass, 3.0)

        obj.physics_body.set_linear_velocity(10.0, 20.0)
        self.assertEqual(obj.physics_body.linear_velocity, (10.0, 20.0))

        obj.physics_body.apply_force(5.0, 10.0)
        self.assertEqual(obj.physics_body.force, (5.0, 10.0))

        # Test collider methods
        obj.physics_body.collider.set_collision_layer(CollisionLayer.ENEMY)
        self.assertEqual(obj.physics_body.collider.collision_layer, CollisionLayer.ENEMY)

        obj.physics_body.collider.set_is_trigger(True)
        self.assertTrue(obj.physics_body.collider.is_trigger)

        # Test material methods
        obj.physics_body.material.restitution = 0.9
        self.assertEqual(obj.physics_body.material.restitution, 0.9)

        obj.physics_body.material.friction = 0.7
        self.assertEqual(obj.physics_body.material.friction, 0.7)

    def test_collision_detection(self):
        """Test collision detection between physics scene objects."""
        from pyrox.models.physics.base import BasePhysicsBody

        body1 = BasePhysicsBody(
            name="Object1",
            x=0.0,
            y=0.0,
            width=50.0,
            height=50.0
        )

        obj1 = SceneObject(
            id="obj1",
            name="Object1",
            scene_object_type="PhysicsType",
            physics_body=body1
        )

        body2 = BasePhysicsBody(
            name="Object2",
            x=25.0,
            y=25.0,
            width=50.0,
            height=50.0
        )

        obj2 = SceneObject(
            id="obj2",
            name="Object2",
            scene_object_type="PhysicsType",
            physics_body=body2
        )

        body3 = BasePhysicsBody(
            name="Object3",
            x=100.0,
            y=100.0,
            width=50.0,
            height=50.0
        )

        obj3 = SceneObject(
            id="obj3",
            name="Object3",
            scene_object_type="PhysicsType",
            physics_body=body3
        )

        self.assertTrue(obj1.physics_body.check_collision(obj2.physics_body))
        self.assertFalse(obj1.physics_body.check_collision(obj3.physics_body))

    def test_to_dict(self):
        """Test SceneObject.to_dict() method with physics body."""
        from pyrox.models.physics.base import BasePhysicsBody

        material = Material(density=2.5, restitution=0.7, friction=0.5, drag=0.15)
        physics_body = BasePhysicsBody(
            name="DictPhysics",
            body_type=BodyType.KINEMATIC,
            mass=2.0,
            x=50.0,
            y=100.0,
            width=30.0,
            height=40.0,
            roll=5.0,
            pitch=10.0,
            yaw=15.0,
            material=material,
            collider_type=ColliderType.POLYGON,
            collision_layer=CollisionLayer.TERRAIN,
            is_trigger=True,
        )

        obj = SceneObject(
            id="phys_dict",
            name="DictPhysics",
            scene_object_type="PhysicsDict",
            description="Physics dict test",
            properties={"key": "value"},
            physics_body=physics_body
        )

        result = obj.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "phys_dict")
        self.assertEqual(result["name"], "DictPhysics")
        self.assertEqual(result["scene_object_type"], "PhysicsDict")
        self.assertEqual(result["body"]["x"], 50.0)
        self.assertEqual(result["body"]["y"], 100.0)
        self.assertEqual(result["body"]["body_type"], "KINEMATIC")
        self.assertEqual(result["body"]["mass"], 2.0)
        self.assertEqual(result["body"]["collider_type"], "POLYGON")
        self.assertEqual(result["body"]["collision_layer"], "TERRAIN")
        self.assertTrue(result["body"]["is_trigger"])
        self.assertEqual(result["material"]["restitution"], 0.7)
        self.assertEqual(result["material"]["friction"], 0.5)

    def test_from_dict(self):
        """Test SceneObject.from_dict() class method."""
        data = {
            "id": "from_dict_phys",
            "name": "FromDictPhysics",
            "scene_object_type": "PhysicsFromDict",
            "description": "From dict physics",
            "properties": {"loaded": True},
            "body": {
                "name": "FromDictPhysics",
                "tags": [],
                "body_type": "DYNAMIC",
                "enabled": True,
                "sleeping": False,
                "mass": 3.5,
                "moment_of_inertia": 1.0,
                "velocity_x": 0.0,
                "velocity_y": 0.0,
                "acceleration_x": 0.0,
                "acceleration_y": 0.0,
                "angular_velocity": 0.0,
                "collider_type": "CIRCLE",
                "collision_layer": "PLAYER",
                "collision_mask": ["DEFAULT"],
                "is_trigger": False,
                "x": 75.0,
                "y": 125.0,
                "width": 40.0,
                "height": 60.0,
                "roll": 12.0,
                "pitch": 24.0,
                "yaw": 36.0,
            },
            "material": {
                "density": 2.0,
                "restitution": 0.8,
                "friction": 0.6,
                "drag": 0.2,
            }
        }

        obj = SceneObject.from_dict(data)

        self.assertEqual(obj.id, "from_dict_phys")
        self.assertEqual(obj.name, "FromDictPhysics")
        self.assertEqual(obj.x, 75.0)
        self.assertEqual(obj.y, 125.0)
        self.assertEqual(obj.physics_body.body_type, BodyType.DYNAMIC)
        self.assertEqual(obj.physics_body.mass, 3.5)
        self.assertEqual(obj.physics_body.material.restitution, 0.8)
        self.assertEqual(obj.physics_body.material.friction, 0.6)
        self.assertEqual(obj.physics_body.collider.collision_layer, CollisionLayer.PLAYER)
        self.assertFalse(obj.physics_body.collider.is_trigger)

    def test_from_dict_with_defaults(self):
        """Test SceneObject.from_dict() with minimal fields."""
        from pyrox.models.physics.base import BasePhysicsBody

        data = {
            "id": "minimal_phys",
            "name": "MinimalPhysics",
            "scene_object_type": "MinimalPhysicsType",
            "body": {
                "name": "MinimalPhysics",
                "tags": [],
                "body_type": "DYNAMIC",
                "enabled": True,
                "sleeping": False,
                "mass": 1.0,
                "moment_of_inertia": 1.0,
                "velocity_x": 0.0,
                "velocity_y": 0.0,
                "acceleration_x": 0.0,
                "acceleration_y": 0.0,
                "angular_velocity": 0.0,
                "collider_type": "RECTANGLE",
                "collision_layer": "DEFAULT",
                "collision_mask": ["DEFAULT"],
                "is_trigger": False,
                "x": 0.0,
                "y": 0.0,
                "width": 10.0,
                "height": 10.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
            "material": {
                "density": 1.0,
                "restitution": 0.5,
                "friction": 0.5,
                "drag": 0.1,
            }
        }

        obj = SceneObject.from_dict(data)

        self.assertEqual(obj.id, "minimal_phys")
        self.assertEqual(obj.name, "MinimalPhysics")
        self.assertEqual(obj.physics_body.body_type, BodyType.DYNAMIC)
        self.assertEqual(obj.physics_body.mass, 1.0)
        self.assertEqual(obj.x, 0.0)
        self.assertEqual(obj.y, 0.0)

    def test_roundtrip_to_dict_from_dict(self):
        """Test roundtrip conversion to/from dict for SceneObject with physics."""
        from pyrox.models.physics.base import BasePhysicsBody

        material = Material(density=1.5, restitution=0.6, friction=0.7, drag=0.12)
        physics_body = BasePhysicsBody(
            name="RoundtripPhysics",
            body_type=BodyType.KINEMATIC,
            mass=2.5,
            x=80.0,
            y=90.0,
            width=35.0,
            height=45.0,
            material=material,
            collider_type=ColliderType.CIRCLE,
            collision_layer=CollisionLayer.PROJECTILE,
            is_trigger=True,
        )

        original = SceneObject(
            id="roundtrip_phys",
            name="RoundtripPhysics",
            scene_object_type="RoundtripPhysicsType",
            description="Roundtrip physics test",
            properties={"value": 456},
            physics_body=physics_body
        )

        data = original.to_dict()
        loaded = SceneObject.from_dict(data)

        self.assertEqual(loaded.id, original.id)
        self.assertEqual(loaded.name, original.name)
        self.assertEqual(loaded.x, original.x)
        self.assertEqual(loaded.y, original.y)
        self.assertEqual(loaded.physics_body.body_type, original.physics_body.body_type)
        self.assertEqual(loaded.physics_body.mass, original.physics_body.mass)
        self.assertEqual(loaded.physics_body.material.restitution, original.physics_body.material.restitution)
        self.assertEqual(loaded.physics_body.material.friction, original.physics_body.material.friction)
        self.assertEqual(loaded.physics_body.collider.collision_layer, original.physics_body.collider.collision_layer)
        self.assertEqual(loaded.physics_body.collider.is_trigger, original.physics_body.collider.is_trigger)

    def test_update_method_exists(self):
        """Test that update method exists and is callable."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(name="UpdateTest")

        obj = SceneObject(
            id="update_test",
            name="UpdateTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        self.assertTrue(hasattr(obj, 'update'))
        self.assertTrue(callable(obj.update))
        # Should not raise
        obj.update(0.016)

    def test_collision_callbacks_exist(self):
        """Test that collision callback methods exist on physics body."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(name="CallbackTest")

        obj = SceneObject(
            id="callback_test",
            name="CallbackTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        self.assertTrue(hasattr(obj.physics_body, 'on_collision_enter'))
        self.assertTrue(hasattr(obj.physics_body, 'on_collision_stay'))
        self.assertTrue(hasattr(obj.physics_body, 'on_collision_exit'))
        self.assertTrue(callable(obj.physics_body.on_collision_enter))
        self.assertTrue(callable(obj.physics_body.on_collision_stay))
        self.assertTrue(callable(obj.physics_body.on_collision_exit))

    def test_material_properties(self):
        """Test material property access through physics body."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(name="MaterialTest")

        obj = SceneObject(
            id="material_test",
            name="MaterialTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        obj.physics_body.material.density = 2.5
        self.assertEqual(obj.physics_body.material.density, 2.5)

        obj.physics_body.material.restitution = 0.9
        self.assertEqual(obj.physics_body.material.restitution, 0.9)

        obj.physics_body.material.friction = 0.8
        self.assertEqual(obj.physics_body.material.friction, 0.8)

        obj.physics_body.material.drag = 0.3
        self.assertEqual(obj.physics_body.material.drag, 0.3)

    def test_body_type_affects_inverse_mass(self):
        """Test that body type affects inverse mass calculation."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(
            name="MassTest",
            body_type=BodyType.DYNAMIC,
            mass=2.0
        )

        obj = SceneObject(
            id="mass_test",
            name="MassTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        # Dynamic body should have inverse mass
        self.assertEqual(obj.physics_body.inverse_mass, 0.5)

        # Static body should have zero inverse mass
        obj.physics_body.set_body_type(BodyType.STATIC)
        self.assertEqual(obj.physics_body.inverse_mass, 0.0)

        # Back to dynamic
        obj.physics_body.set_body_type(BodyType.DYNAMIC)
        self.assertEqual(obj.physics_body.inverse_mass, 0.5)

    def test_force_and_impulse_application(self):
        """Test applying forces and impulses through physics body."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(
            name="ForceTest",
            body_type=BodyType.DYNAMIC,
            mass=2.0
        )

        obj = SceneObject(
            id="force_test",
            name="ForceTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        # Apply force
        obj.physics_body.apply_force(10.0, 20.0)
        self.assertEqual(obj.physics_body.force, (10.0, 20.0))

        # Apply impulse (should change velocity)
        obj.physics_body.apply_impulse(4.0, 6.0)
        # impulse / mass = velocity change: (4.0/2.0, 6.0/2.0) = (2.0, 3.0)
        self.assertEqual(obj.physics_body.linear_velocity, (2.0, 3.0))

        # Clear forces
        obj.physics_body.clear_forces()
        self.assertEqual(obj.physics_body.force, (0.0, 0.0))

    def test_collision_layers_and_masks(self):
        """Test collision layer and mask functionality through physics body."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(
            name="LayerTest",
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[CollisionLayer.TERRAIN, CollisionLayer.ENEMY]
        )

        obj = SceneObject(
            id="layer_test",
            name="LayerTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        self.assertEqual(obj.physics_body.collider.collision_layer, CollisionLayer.PLAYER)

        mask = obj.physics_body.collider.collision_mask
        self.assertIn(CollisionLayer.TERRAIN, mask)
        self.assertIn(CollisionLayer.ENEMY, mask)
        self.assertEqual(len(mask), 2)

        # Update mask
        obj.physics_body.collider.set_collision_mask([CollisionLayer.PROJECTILE])
        mask = obj.physics_body.collider.collision_mask
        self.assertEqual(len(mask), 1)
        self.assertIn(CollisionLayer.PROJECTILE, mask)

    def test_integration_with_scene(self):
        """Test SceneObject with physics body integration with Scene."""
        from pyrox.models.physics.base import BasePhysicsBody

        scene = Scene(name="Physics Scene")

        body1 = BasePhysicsBody(
            name="PhysicsObj1",
            body_type=BodyType.DYNAMIC,
            mass=1.5
        )

        obj1 = SceneObject(
            id="phys_obj_1",
            name="PhysicsObj1",
            scene_object_type="PhysicsType",
            physics_body=body1
        )

        body2 = BasePhysicsBody(
            name="PhysicsObj2",
            body_type=BodyType.STATIC,
            mass=0.0
        )

        obj2 = SceneObject(
            id="phys_obj_2",
            name="PhysicsObj2",
            scene_object_type="PhysicsType",
            physics_body=body2
        )

        scene.add_scene_object(obj1)
        scene.add_scene_object(obj2)

        self.assertEqual(len(scene.scene_objects), 2)
        self.assertIn("phys_obj_1", scene.scene_objects)
        self.assertIn("phys_obj_2", scene.scene_objects)

    def test_save_and_load_physics_scene(self):
        """Test saving and loading scenes with SceneObject containing physics bodies."""
        # Create scene with physics objects
        original_scene = Scene(name="Physics Scene Test")

        physics_body = BasePhysicsBody(
            name="SavePhysics",
            body_type=BodyType.DYNAMIC,
            mass=2.0,
            x=100.0,
            y=200.0,
            collision_layer=CollisionLayer.PLAYER
        )

        obj = SceneObject(
            id="save_phys",
            name="SavePhysics",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        original_scene.add_scene_object(obj)

        # Save to file
        test_dir = tempfile.mkdtemp()
        filepath = Path(test_dir) / "physics_scene.json"
        original_scene.save(filepath)

        # Load from file
        SceneObjectFactory.register("PhysicsType", SceneObject)
        loaded_scene = Scene.load(filepath)

        # Verify
        self.assertEqual(loaded_scene.name, "Physics Scene Test")
        self.assertEqual(len(loaded_scene.scene_objects), 1)

        loaded_obj = loaded_scene.get_scene_object("save_phys")
        self.assertIsNotNone(loaded_obj)
        self.assertIsInstance(loaded_obj, SceneObject)
        self.assertEqual(loaded_obj.x, 100.0)  # type: ignore
        self.assertEqual(loaded_obj.y, 200.0)  # type: ignore
        self.assertEqual(loaded_obj.physics_body.mass, 2.0)  # type: ignore

        # Cleanup
        shutil.rmtree(test_dir)

    def test_properties_dict_access(self):
        """Test that properties dictionary works correctly."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(name="PropsTest")

        obj = SceneObject(
            id="props_test",
            name="PropsTest",
            scene_object_type="PhysicsType",
            properties={"custom_data": "test", "number": 123},
            physics_body=physics_body
        )

        self.assertEqual(obj.get_properties()["custom_data"], "test")
        self.assertEqual(obj.get_properties()["number"], 123)

        obj.set_properties({"new_key": "new_value"})
        self.assertEqual(obj.get_properties()["new_key"], "new_value")
        self.assertNotIn("custom_data", obj.get_properties())

    def test_position_properties_delegation(self):
        """Test that x, y, width, height properties delegate to physics_body."""
        from pyrox.models.physics.base import BasePhysicsBody

        physics_body = BasePhysicsBody(
            name="PositionTest",
            x=50.0,
            y=100.0,
            width=30.0,
            height=40.0
        )

        obj = SceneObject(
            id="pos_test",
            name="PositionTest",
            scene_object_type="PhysicsType",
            physics_body=physics_body
        )

        # Test reading through properties
        self.assertEqual(obj.x, 50.0)
        self.assertEqual(obj.y, 100.0)
        self.assertEqual(obj.width, 30.0)
        self.assertEqual(obj.height, 40.0)

        # Test writing through properties
        obj.x = 75.0
        obj.y = 125.0
        obj.width = 45.0
        obj.height = 55.0

        self.assertEqual(obj.physics_body.x, 75.0)
        self.assertEqual(obj.physics_body.y, 125.0)
        self.assertEqual(obj.physics_body.width, 45.0)
        self.assertEqual(obj.physics_body.height, 55.0)


if __name__ == '__main__':
    unittest.main()
