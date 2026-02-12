"""Unit tests for pyrox.models.scene module."""
import json
import os
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
                    template_name="Base Physics Body",
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
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertIn(obj_id, scene.scene_objects)
        self.assertEqual(scene.scene_objects[obj_id], scene_object)

    def test_add_scene_object_duplicate_id_raises_error(self):
        """Test that adding a scene_object with duplicate ID raises ValueError."""
        scene = Scene()
        # Use same physics body to force same ID
        shared_physics = self.TestPhysicsBody()
        scene_object1 = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="SceneObject1",
            physics_body=shared_physics
        )
        scene_object2 = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="SceneObject2",
            physics_body=shared_physics
        )

        scene.add_scene_object(scene_object1)
        obj_id = scene_object1.get_id()

        with self.assertRaises(ValueError) as context:
            scene.add_scene_object(scene_object2)

        self.assertIn("already exists", str(context.exception))
        self.assertIn(obj_id, str(context.exception))

    def test_remove_scene_object(self):
        """Test Scene.remove_scene_object() method."""
        scene = Scene()
        scene_object = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()
        self.assertEqual(len(scene.scene_objects), 1)

        scene.remove_scene_object(obj_id)
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
            scene_object_type="TestSceneObject",
            name="TestDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()

        result = scene.get_scene_object(obj_id)
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
            scene_object_type="TestSceneObject",
            name="SceneObject1",
            physics_body=self.TestPhysicsBody()
        )
        scene_object2 = self.TestSceneObject(
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
            scene_object_type="TestSceneObject",
            name="Base Physics Body",
            physics_body=self.TestPhysicsBody()
        )
        original_scene.add_scene_object(scene_object)

        filepath = Path(self.test_dir) / "load_scene.json"
        original_scene.save(filepath)

        # Load the scene
        loaded_scene = Scene.load(filepath)

        self.assertEqual(loaded_scene.name, "LoadScene")
        self.assertEqual(loaded_scene.description, "Test load")
        self.assertEqual(len(loaded_scene.scene_objects), 1)
        # Check that the object exists (ID may differ after load)
        self.assertGreater(len(loaded_scene.scene_objects), 0)

    def test_scene_roundtrip(self):
        """Test that saving and loading a scene preserves data."""
        original = Scene(name="RoundtripScene", description="Full roundtrip test")

        # Add scene_object with tags
        scene_object = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="Base Physics Body",
            properties={"value": 123},
            physics_body=self.TestPhysicsBody()
        )
        original.add_scene_object(scene_object)

        # Save
        filepath = Path(self.test_dir) / "roundtrip.json"
        original.save(filepath)

        # Load
        loaded = Scene.load(filepath)

        # Verify
        self.assertEqual(loaded.name, original.name)
        self.assertEqual(loaded.description, original.description)
        self.assertEqual(len(loaded.scene_objects), len(original.scene_objects))

        # Get the loaded object (ID may differ)
        loaded_objects = list(loaded.scene_objects.values())
        self.assertEqual(len(loaded_objects), 1)
        loaded_scene_object = loaded_objects[0]
        self.assertEqual(loaded_scene_object.name, "Base Physics Body")
        self.assertEqual(loaded_scene_object.properties["value"], 123)

    def test_repr(self):
        """Test Scene.__repr__() method."""
        scene = Scene(name="ReprScene")

        scene_object = self.TestSceneObject(
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
            scene_object_type="TestSceneObject",
            name="Object1",
            physics_body=self.TestPhysicsBody()
        )
        scene_object2 = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="Object2",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object1)
        scene.add_scene_object(scene_object2)
        obj_id1 = scene_object1.get_id()
        obj_id2 = scene_object2.get_id()

        objects = scene.get_scene_objects()

        self.assertIsInstance(objects, dict)
        self.assertEqual(len(objects), 2)
        self.assertIn(obj_id1, objects)
        self.assertIn(obj_id2, objects)

    def test_set_scene_objects(self):
        """Test Scene.set_scene_objects() method."""
        scene = Scene()
        scene_object1 = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="Object3",
            physics_body=self.TestPhysicsBody()
        )
        obj_id = scene_object1.get_id()

        objects_dict: Dict[str, ISceneObject] = {obj_id: scene_object1}
        scene.set_scene_objects(objects_dict)

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertIn(obj_id, scene.scene_objects)

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
            scene_object_type="TestSceneObject",
            name="CallbackDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()

        self.assertIn(obj_id, called)

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
            scene_object_type="TestSceneObject",
            name="CallbackDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()
        scene.remove_scene_object(obj_id)

        self.assertIn(obj_id, called)

    def test_register_scene_object_in_connection_registry(self):
        """Test that adding a scene_object registers it in the connection registry."""
        scene = Scene()

        scene_object = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="RegDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()

        registered_obj = scene._connection_registry._objects.get(obj_id)  # type: ignore
        self.assertIsNotNone(registered_obj)
        self.assertEqual(registered_obj, scene_object)

    def test_unregister_scene_object_in_connection_registry(self):
        """Test that removing a scene_object unregisters it from the connection registry."""
        scene = Scene()

        scene_object = self.TestSceneObject(
            scene_object_type="TestSceneObject",
            name="UnregDev",
            physics_body=self.TestPhysicsBody()
        )

        scene.add_scene_object(scene_object)
        obj_id = scene_object.get_id()

        # Ensure it's registered
        registered_obj = scene._connection_registry._objects.get(obj_id)  # type: ignore
        self.assertIsNotNone(registered_obj)

        # Remove the scene object
        scene.remove_scene_object(obj_id)

        # Ensure it's unregistered
        registered_obj_after = scene._connection_registry._objects.get(obj_id)  # type: ignore
        self.assertIsNone(registered_obj_after)


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

        with self.assertRaises(NotImplementedError):
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
        """Test that set_property sets both attribute and properties dict."""
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


if __name__ == '__main__':
    unittest.main()
