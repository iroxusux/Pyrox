"""Unit tests for pyrox.models.scene module."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from pyrox.interfaces import ISceneObject
from pyrox.models.scene import Scene, SceneObject, SceneObjectFactory


class TestScene(unittest.TestCase):
    """Test cases for Scene class."""

    def setUp(self):
        """Set up test fixtures."""

        class TestSceneObject(SceneObject):
            """Test scene_object implementation."""

            def update(self, delta_time: float) -> None:
                """Test implementation."""
                pass

            def read_inputs(self) -> Dict[str, Any]:
                """Test implementation."""
                return {}

            def write_outputs(self) -> Dict[str, Any]:
                """Test implementation."""
                return {}

        self.TestSceneObject = TestSceneObject
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
            name="TestDev"
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
            name="SceneObject1"
        )
        scene_object2 = self.TestSceneObject(
            id="dev_003",
            scene_object_type="TestSceneObject",
            name="SceneObject2"
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
            name="TestDev"
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
            name="TestDev"
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
            name="TestDev"
        )
        scene_object.properties["update_count"] = 0

        # Override update method
        def custom_update(delta_time):
            scene_object.properties["update_count"] += 1
            scene_object.properties["last_delta"] = delta_time

        scene_object.update = custom_update

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
            name="SceneObject1"
        )
        scene_object2 = self.TestSceneObject(
            id="dev_010",
            scene_object_type="TestSceneObject",
            name="SceneObject2"
        )

        scene_object1.properties["updated"] = False
        scene_object2.properties["updated"] = False

        def update1(delta_time: float):
            scene_object1.properties["updated"] = True

        def update2(delta_time: float):
            scene_object2.properties["updated"] = True

        scene_object1.update = update1
        scene_object2.update = update2

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
            name="TestDev"
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
            name="SaveDev"
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
            name="LoadDev"
        )
        original_scene.add_scene_object(scene_object)

        filepath = Path(self.test_dir) / "load_scene.json"
        original_scene.save(filepath)

        # Create factory and register scene_object type
        factory = SceneObjectFactory()
        factory.register("TestSceneObject", self.TestSceneObject)

        # Load the scene
        loaded_scene = Scene.load(filepath, factory=factory)

        self.assertEqual(loaded_scene.name, "LoadScene")
        self.assertEqual(loaded_scene.description, "Test load")
        self.assertEqual(len(loaded_scene.scene_objects), 1)
        self.assertIn("dev_013", loaded_scene.scene_objects)

    def test_load_without_factory_raises_error(self):
        """Test that loading without a factory raises ValueError."""
        filepath = Path(self.test_dir) / "no_factory.json"

        # Create a simple scene file
        with open(filepath, 'w') as f:
            json.dump({"name": "Test", "scene_objects": [], "tags": []}, f)

        with self.assertRaises(ValueError) as context:
            Scene.load(filepath, factory=None)  # type: ignore

        self.assertIn("scene_object_factory is required", str(context.exception))

    def test_scene_roundtrip(self):
        """Test that saving and loading a scene preserves data."""
        original = Scene(name="RoundtripScene", description="Full roundtrip test")

        # Add scene_object with tags
        scene_object = self.TestSceneObject(
            id="dev_014",
            scene_object_type="TestSceneObject",
            name="RoundtripDev",
            properties={"value": 123}
        )
        original.add_scene_object(scene_object)

        # Save
        filepath = Path(self.test_dir) / "roundtrip.json"
        original.save(filepath)

        # Load
        factory = SceneObjectFactory()
        factory.register("TestSceneObject", self.TestSceneObject)
        loaded = Scene.load(filepath, factory=factory)

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
            name="Dev"
        )
        scene.add_scene_object(scene_object)

        repr_str = repr(scene)

        self.assertIn("ReprScene", repr_str)
        self.assertIn("scene_objects=1", repr_str)

    def test_set_scene_object_factory(self):
        """Test Scene.set_scene_object_factory() method."""
        scene = Scene()
        factory = SceneObjectFactory()

        scene.set_scene_object_factory(factory)

        self.assertEqual(scene._scene_object_factory, factory)

    def test_get_scene_objects(self):
        """Test Scene.get_scene_objects() method."""
        scene = Scene()
        scene_object1 = self.TestSceneObject(
            id="obj_001",
            scene_object_type="TestSceneObject",
            name="Object1"
        )
        scene_object2 = self.TestSceneObject(
            id="obj_002",
            scene_object_type="TestSceneObject",
            name="Object2"
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
            name="Object3"
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

    def test_get_scene_object_factory(self):
        """Test Scene.get_scene_object_factory() method."""
        factory = SceneObjectFactory()
        scene = Scene(scene_object_factory=factory)

        retrieved_factory = scene.get_scene_object_factory()
        self.assertEqual(retrieved_factory, factory)


class TestSceneObject(unittest.TestCase):
    """Test cases for SceneObject class."""

    def test_init_with_required_params(self):
        """Test SceneObject initialization with required parameters."""
        obj = SceneObject(
            id="test_001",
            name="TestObject",
            scene_object_type="TestType"
        )

        self.assertEqual(obj.get_id(), "test_001")
        self.assertEqual(obj.get_name(), "TestObject")
        self.assertEqual(obj.get_scene_object_type(), "TestType")
        self.assertEqual(obj.get_description(), "")
        self.assertIsInstance(obj.get_properties(), dict)
        self.assertEqual(len(obj.get_properties()), 0)

    def test_init_with_all_params(self):
        """Test SceneObject initialization with all parameters."""
        properties = {"key1": "value1", "key2": 42}
        obj = SceneObject(
            id="test_002",
            name="FullObject",
            scene_object_type="FullType",
            description="Test description",
            properties=properties,
            x=10.0,
            y=20.0,
            width=100.0,
            height=50.0,
            roll=5.0,
            pitch=10.0,
            yaw=15.0
        )

        self.assertEqual(obj.get_id(), "test_002")
        self.assertEqual(obj.get_name(), "FullObject")
        self.assertEqual(obj.get_scene_object_type(), "FullType")
        self.assertEqual(obj.get_description(), "Test description")
        self.assertEqual(obj.get_properties(), properties)
        self.assertEqual(obj.get_x(), 10.0)
        self.assertEqual(obj.get_y(), 20.0)
        self.assertEqual(obj.get_width(), 100.0)
        self.assertEqual(obj.get_height(), 50.0)
        self.assertEqual(obj.get_roll(), 5.0)
        self.assertEqual(obj.get_pitch(), 10.0)
        self.assertEqual(obj.get_yaw(), 15.0)

    def test_get_id(self):
        """Test SceneObject.get_id() method."""
        obj = SceneObject(id="id_test", name="Name", scene_object_type="Type")
        self.assertEqual(obj.get_id(), "id_test")

    def test_set_id(self):
        """Test SceneObject.set_id() method."""
        obj = SceneObject(id="old_id", name="Name", scene_object_type="Type")
        obj.set_id("new_id")
        self.assertEqual(obj.get_id(), "new_id")

    def test_id_property(self):
        """Test SceneObject id property access."""
        obj = SceneObject(id="prop_id", name="Name", scene_object_type="Type")
        self.assertEqual(obj.id, "prop_id")

    def test_get_properties(self):
        """Test SceneObject.get_properties() method."""
        properties = {"test": "value", "number": 123}
        obj = SceneObject(
            id="test",
            name="Name",
            scene_object_type="Type",
            properties=properties
        )

        result = obj.get_properties()
        self.assertEqual(result, properties)
        self.assertIsInstance(result, dict)

    def test_set_properties(self):
        """Test SceneObject.set_properties() method."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type")
        new_props = {"new_key": "new_value"}

        obj.set_properties(new_props)
        self.assertEqual(obj.get_properties(), new_props)

    def test_set_properties_invalid_type_raises_error(self):
        """Test that set_properties raises error for non-dict."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type")

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
            properties=properties
        )
        self.assertEqual(obj.properties, properties)

    def test_get_scene_object_type(self):
        """Test SceneObject.get_scene_object_type() method."""
        obj = SceneObject(id="test", name="Name", scene_object_type="CustomType")
        self.assertEqual(obj.get_scene_object_type(), "CustomType")

    def test_set_scene_object_type(self):
        """Test SceneObject.set_scene_object_type() method."""
        obj = SceneObject(id="test", name="Name", scene_object_type="OldType")
        obj.set_scene_object_type("NewType")
        self.assertEqual(obj.get_scene_object_type(), "NewType")

    def test_scene_object_type_property(self):
        """Test SceneObject scene_object_type property access."""
        obj = SceneObject(id="test", name="Name", scene_object_type="PropType")
        self.assertEqual(obj.scene_object_type, "PropType")

    def test_to_dict(self):
        """Test SceneObject.to_dict() method."""
        properties = {"key": "value", "num": 42}
        obj = SceneObject(
            id="dict_test",
            name="DictObject",
            scene_object_type="DictType",
            description="Dict description",
            properties=properties
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
        self.assertEqual(obj.get_properties(), {"loaded": True})

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
        self.assertEqual(obj.get_properties(), {})

    def test_update_method_exists(self):
        """Test that update method exists and is callable."""
        obj = SceneObject(id="test", name="Name", scene_object_type="Type")

        self.assertTrue(hasattr(obj, 'update'))
        self.assertTrue(callable(obj.update))

        # Should not raise
        obj.update(0.016)

    def test_inheritance_from_core_mixin(self):
        """Test that SceneObject inherits from CoreMixin."""
        from pyrox.models import CoreMixin
        obj = SceneObject(id="test", name="Name", scene_object_type="Type")

        self.assertIsInstance(obj, CoreMixin)
        # Should have CoreMixin methods
        self.assertTrue(hasattr(obj, 'get_name'))
        self.assertTrue(hasattr(obj, 'get_description'))

    def test_inheritance_from_spatial2d(self):
        """Test that SceneObject inherits from Spatial2D."""
        from pyrox.models.abc.protocols.spatial import Spatial2D
        obj = SceneObject(id="test", name="Name", scene_object_type="Type")

        self.assertIsInstance(obj, Spatial2D)
        # Should have Spatial2D methods
        self.assertTrue(hasattr(obj, 'get_x'))
        self.assertTrue(hasattr(obj, 'get_y'))
        self.assertTrue(hasattr(obj, 'get_width'))
        self.assertTrue(hasattr(obj, 'get_height'))
        self.assertTrue(hasattr(obj, 'get_rotation'))

    def test_spatial_position_methods(self):
        """Test that spatial position methods work."""
        obj = SceneObject(
            id="test",
            name="Name",
            scene_object_type="Type",
            x=50.0,
            y=100.0
        )

        self.assertEqual(obj.get_x(), 50.0)
        self.assertEqual(obj.get_y(), 100.0)
        self.assertEqual(obj.get_position(), (50.0, 100.0))

    def test_spatial_size_methods(self):
        """Test that spatial size methods work."""
        obj = SceneObject(
            id="test",
            name="Name",
            scene_object_type="Type",
            width=200.0,
            height=150.0
        )

        self.assertEqual(obj.get_width(), 200.0)
        self.assertEqual(obj.get_height(), 150.0)
        self.assertEqual(obj.get_size(), (200.0, 150.0))

    def test_spatial_rotation_methods(self):
        """Test that spatial rotation methods work."""
        obj = SceneObject(
            id="test",
            name="Name",
            scene_object_type="Type",
            roll=10.0,
            pitch=20.0,
            yaw=30.0
        )

        self.assertEqual(obj.get_roll(), 10.0)
        self.assertEqual(obj.get_pitch(), 20.0)
        self.assertEqual(obj.get_yaw(), 30.0)
        self.assertEqual(obj.get_rotation(), (20.0, 30.0, 10.0))  # (pitch, yaw, roll)

    def test_roundtrip_to_dict_from_dict(self):
        """Test roundtrip conversion to/from dict."""
        original = SceneObject(
            id="roundtrip",
            name="RoundtripObject",
            scene_object_type="RoundtripType",
            description="Roundtrip test",
            properties={"value": 123, "text": "test"}
        )

        data = original.to_dict()
        loaded = SceneObject.from_dict(data)

        self.assertEqual(loaded.get_id(), original.get_id())
        self.assertEqual(loaded.get_name(), original.get_name())
        self.assertEqual(loaded.get_scene_object_type(), original.get_scene_object_type())
        self.assertEqual(loaded.get_description(), original.get_description())
        self.assertEqual(loaded.get_properties(), original.get_properties())


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
        factory = SceneObjectFactory()

        self.assertIsInstance(factory._registry, dict)
        self.assertEqual(len(factory._registry), 0)

    def test_register(self):
        """Test SceneObjectFactory.register() method."""
        factory = SceneObjectFactory()

        factory.register("TypeA", self.TestObjectA)

        self.assertIn("TypeA", factory._registry)
        self.assertEqual(factory._registry["TypeA"], self.TestObjectA)

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate type raises ValueError."""
        factory = SceneObjectFactory()

        factory.register("DuplicateType", self.TestObjectA)

        with self.assertRaises(ValueError) as context:
            factory.register("DuplicateType", self.TestObjectB)

        self.assertIn("already registered", str(context.exception))
        self.assertIn("DuplicateType", str(context.exception))

    def test_unregister(self):
        """Test SceneObjectFactory.unregister() method."""
        factory = SceneObjectFactory()

        factory.register("TypeA", self.TestObjectA)
        self.assertIn("TypeA", factory._registry)

        factory.unregister("TypeA")
        self.assertNotIn("TypeA", factory._registry)

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent type doesn't raise error."""
        factory = SceneObjectFactory()

        # Should not raise
        factory.unregister("NonExistent")

    def test_get_registered_types(self):
        """Test SceneObjectFactory.get_registered_types() method."""
        factory = SceneObjectFactory()

        self.assertEqual(factory.get_registered_types(), [])

        factory.register("TypeA", self.TestObjectA)
        factory.register("TypeB", self.TestObjectB)

        types = factory.get_registered_types()

        self.assertIsInstance(types, list)
        self.assertEqual(len(types), 2)
        self.assertIn("TypeA", types)
        self.assertIn("TypeB", types)

    def test_create_scene_object(self):
        """Test SceneObjectFactory.create_scene_object() method."""
        factory = SceneObjectFactory()
        factory.register("TypeA", self.TestObjectA)

        data = {
            "id": "created_obj",
            "name": "CreatedObject",
            "scene_object_type": "TypeA",
            "description": "Created via factory",
            "properties": {"created": True}
        }

        obj = factory.create_scene_object(data)

        self.assertIsInstance(obj, self.TestObjectA)
        self.assertEqual(obj.get_id(), "created_obj")
        self.assertEqual(obj.get_name(), "CreatedObject")
        self.assertEqual(obj.get_scene_object_type(), "TypeA")
        self.assertEqual(obj.get_properties(), {"created": True})

    def test_create_scene_object_unregistered_type_raises_error(self):
        """Test creating object with unregistered type raises ValueError."""
        factory = SceneObjectFactory()

        data = {
            "id": "test",
            "name": "Test",
            "scene_object_type": "UnregisteredType"
        }

        with self.assertRaises(ValueError) as context:
            factory.create_scene_object(data)

        self.assertIn("not registered", str(context.exception))
        self.assertIn("UnregisteredType", str(context.exception))
        self.assertIn("Available types", str(context.exception))

    def test_create_multiple_different_types(self):
        """Test creating multiple objects of different types."""
        factory = SceneObjectFactory()
        factory.register("TypeA", self.TestObjectA)
        factory.register("TypeB", self.TestObjectB)

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

        obj_a = factory.create_scene_object(data_a)
        obj_b = factory.create_scene_object(data_b)

        self.assertIsInstance(obj_a, self.TestObjectA)
        self.assertIsInstance(obj_b, self.TestObjectB)
        self.assertNotEqual(type(obj_a), type(obj_b))

    def test_factory_with_scene_integration(self):
        """Test factory integration with Scene class."""
        factory = SceneObjectFactory()
        factory.register("TypeA", self.TestObjectA)

        scene = Scene(scene_object_factory=factory)

        # Create object via factory
        data = {
            "id": "integrated_obj",
            "name": "IntegratedObject",
            "scene_object_type": "TypeA"
        }

        obj = factory.create_scene_object(data)
        scene.add_scene_object(obj)

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertIn("integrated_obj", scene.scene_objects)

    def test_multiple_registrations(self):
        """Test registering multiple types."""
        factory = SceneObjectFactory()

        factory.register("Type1", self.TestObjectA)
        factory.register("Type2", self.TestObjectB)
        factory.register("Type3", SceneObject)

        types = factory.get_registered_types()
        self.assertEqual(len(types), 3)
        self.assertIn("Type1", types)
        self.assertIn("Type2", types)
        self.assertIn("Type3", types)

    def test_register_then_unregister_then_register(self):
        """Test register, unregister, then register again."""
        factory = SceneObjectFactory()

        factory.register("Type", self.TestObjectA)
        self.assertIn("Type", factory._registry)

        factory.unregister("Type")
        self.assertNotIn("Type", factory._registry)

        # Should be able to register again after unregister
        factory.register("Type", self.TestObjectB)
        self.assertIn("Type", factory._registry)
        self.assertEqual(factory._registry["Type"], self.TestObjectB)


if __name__ == '__main__':
    unittest.main()
