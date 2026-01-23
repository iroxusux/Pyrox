"""Unit tests for controlrox.models.simulation.scene module."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

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


if __name__ == '__main__':
    unittest.main()
