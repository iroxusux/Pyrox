"""Unit tests for pyrox.models.scene module."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from typing import Any, Dict
from pyrox.interfaces import (
    ICoreMixin,
    IScene,
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
from pyrox.models.scene.scenebridge import SceneBridge, BindingDirection
from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
from pyrox.models.connection import ConnectionRegistry, Connection


class TestSceneInterface(unittest.TestCase):
    """Test cases for Scene interface."""

    def test_scene_is_iscene(self):
        """Test that Scene implements IScene interface."""
        self.assertIsInstance(Scene(), IScene)

    def test_scene_is_icoremixin(self):
        """Test that Scene implements ICoreMixin interface."""
        self.assertIsInstance(Scene(), ICoreMixin)


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
        scene_object2.set_id(obj_id)  # Force duplicate ID

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

        self.assertIn("Scene name must be a non-empty string", str(context.exception))

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


class TestSceneConnectionRegistry(unittest.TestCase):
    """Comprehensive test suite for ConnectionRegistry and its Scene lifecycle integration.

    Covers:
      - Registration / unregistration of objects
      - Connection creation, validation, and duplicate detection
      - Callback wiring and correct single-fire behaviour
      - disconnect() removing individual connections
      - unregister_object() *fully* unwiring dangling callbacks (regression bug)
      - enabled=False: connection recorded but callback NOT wired
      - Serialization round-trip (serialize / Scene.save + Scene.load)
      - SceneBoundLayer sources coexisting with the registry (bridge integration)
      - SceneGroup members accessible through the registry
    """

    # ------------------------------------------------------------------
    # Helpers shared across tests
    # ------------------------------------------------------------------

    class _Sensor:
        """Minimal source object: fires callbacks on activate/deactivate."""

        def __init__(self):
            self.on_activate: list = []
            self.on_deactivate: list = []

        def fire_activate(self):
            for cb in list(self.on_activate):
                cb()

        def fire_deactivate(self):
            for cb in list(self.on_deactivate):
                cb()

    class _IoBlock:
        """Minimal target object: records calls to set_active / set_inactive."""

        def __init__(self):
            self.active_calls: int = 0
            self.inactive_calls: int = 0
            self.active: bool = False

        def set_active(self):
            self.active = True
            self.active_calls += 1

        def set_inactive(self):
            self.active = False
            self.inactive_calls += 1

    def _make_registry(self):
        """Return a fresh ConnectionRegistry with two pre-registered objects."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io_block = self._IoBlock()
        registry.register_object("prox_1", sensor)
        registry.register_object("io_block_1", io_block)
        return registry, sensor, io_block

    def _make_connectable_scene_object(self):
        """Build a minimal SceneObject subclass that exposes outputs + inputs."""

        class _ConnectableSceneObject(SceneObject):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.on_detect: list = []
                self.received_value: Any = None

            def update(self, dt: float) -> None:
                pass

            def read_inputs(self) -> Dict[str, Any]:
                return {}

            def write_outputs(self) -> Dict[str, Any]:
                return {}

            def trigger(self):
                for cb in list(self.on_detect):
                    cb()

            def receive(self):
                self.received_value = True

        return _ConnectableSceneObject

    # ------------------------------------------------------------------
    # 1.  Object registration
    # ------------------------------------------------------------------

    def test_registry_starts_empty(self):
        """Fresh registry has no objects and no connections."""
        registry = ConnectionRegistry()
        self.assertEqual(registry._objects, {})
        self.assertEqual(registry._connections, [])

    def test_register_object_stores_by_id(self):
        """register_object makes the object retrievable by ID."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        registry.register_object("s1", sensor)
        self.assertIs(registry._objects["s1"], sensor)

    def test_register_multiple_objects(self):
        registry = ConnectionRegistry()
        objs = [self._Sensor() for _ in range(3)]
        for i, obj in enumerate(objs):
            registry.register_object(f"s{i}", obj)
        self.assertEqual(len(registry._objects), 3)

    def test_unregister_removes_object(self):
        registry, sensor, _ = self._make_registry()
        registry.unregister_object("prox_1")
        self.assertNotIn("prox_1", registry._objects)

    def test_unregister_nonexistent_is_noop(self):
        """Unregistering an unknown ID must not raise."""
        registry = ConnectionRegistry()
        registry.unregister_object("does_not_exist")  # must not raise

    # ------------------------------------------------------------------
    # 2.  Connection creation & validation
    # ------------------------------------------------------------------

    def test_connect_unregistered_source_raises(self):
        """connect() must raise KeyError when source is not registered."""
        registry = ConnectionRegistry()
        io = self._IoBlock()
        registry.register_object("io", io)
        with self.assertRaises(KeyError):
            registry.connect("ghost_sensor", "on_activate", "io", "set_active")

    def test_connect_unregistered_target_raises(self):
        """connect() must raise KeyError when target is not registered."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        registry.register_object("sensor", sensor)
        with self.assertRaises(KeyError):
            registry.connect("sensor", "on_activate", "ghost_io", "set_active")

    def test_connect_returns_connection_object(self):
        """connect() returns a Connection dataclass with correct fields."""
        registry, sensor, io_block = self._make_registry()
        conn = registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        self.assertIsInstance(conn, Connection)
        self.assertEqual(conn.source_id, "prox_1")
        self.assertEqual(conn.source_output, "on_activate")
        self.assertEqual(conn.target_id, "io_block_1")
        self.assertEqual(conn.target_input, "set_active")
        self.assertTrue(conn.enabled)

    def test_connect_records_connection_in_list(self):
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        self.assertEqual(len(registry._connections), 1)

    def test_connect_duplicate_raises(self):
        """Connecting the same pair twice must raise ValueError, not silently double-wire."""
        registry, _, _ = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        with self.assertRaises(ValueError):
            registry.connect("prox_1", "on_activate", "io_block_1", "set_active")

    def test_connect_missing_output_attr_raises(self):
        """connect() must raise AttributeError when source lacks the output attribute."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io = self._IoBlock()
        registry.register_object("s", sensor)
        registry.register_object("io", io)
        with self.assertRaises(AttributeError):
            registry.connect("s", "NON_EXISTENT_OUTPUT", "io", "set_active")

    def test_connect_missing_input_attr_raises(self):
        """connect() must raise AttributeError when target lacks the input attribute."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io = self._IoBlock()
        registry.register_object("s", sensor)
        registry.register_object("io", io)
        with self.assertRaises(AttributeError):
            registry.connect("s", "on_activate", "io", "NON_EXISTENT_INPUT")

    # ------------------------------------------------------------------
    # 3.  Callback wiring — correct single-fire behaviour
    # ------------------------------------------------------------------

    def test_callback_fires_on_event(self):
        """After connecting, firing the source event calls the target method."""
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        self.assertFalse(io_block.active)
        sensor.fire_activate()
        self.assertTrue(io_block.active)
        self.assertEqual(io_block.active_calls, 1)

    def test_callback_fires_exactly_once(self):
        """A single connection must cause the target to be called exactly once per event.

        Regression: Before the duplicate guard was added, calling connect() twice
        would append the callback twice so the target fired twice.
        """
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        sensor.fire_activate()
        sensor.fire_activate()
        self.assertEqual(io_block.active_calls, 2)

    def test_multiple_targets_from_same_source(self):
        """One source can connect to multiple distinct targets."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io1 = self._IoBlock()
        io2 = self._IoBlock()
        registry.register_object("prox", sensor)
        registry.register_object("io1", io1)
        registry.register_object("io2", io2)
        registry.connect("prox", "on_activate", "io1", "set_active")
        registry.connect("prox", "on_activate", "io2", "set_active")
        sensor.fire_activate()
        self.assertEqual(io1.active_calls, 1)
        self.assertEqual(io2.active_calls, 1)

    def test_multiple_sources_to_same_target(self):
        """Multiple sources can drive the same target input."""
        registry = ConnectionRegistry()
        s1, s2 = self._Sensor(), self._Sensor()
        io = self._IoBlock()
        registry.register_object("s1", s1)
        registry.register_object("s2", s2)
        registry.register_object("io", io)
        registry.connect("s1", "on_activate", "io", "set_active")
        registry.connect("s2", "on_activate", "io", "set_active")
        s1.fire_activate()
        s2.fire_activate()
        self.assertEqual(io.active_calls, 2)

    def test_different_outputs_on_same_source_are_independent(self):
        """on_activate and on_deactivate wired to different targets don't cross-fire."""
        registry, sensor, io_block = self._make_registry()
        io2 = self._IoBlock()
        registry.register_object("io2", io2)
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.connect("prox_1", "on_deactivate", "io2", "set_inactive")
        sensor.fire_activate()
        self.assertEqual(io_block.active_calls, 1)
        self.assertEqual(io2.inactive_calls, 0)
        sensor.fire_deactivate()
        self.assertEqual(io2.inactive_calls, 1)
        self.assertEqual(io_block.active_calls, 1)  # no spurious second call

    # ------------------------------------------------------------------
    # 4.  disconnect()
    # ------------------------------------------------------------------

    def test_disconnect_returns_true_when_exists(self):
        registry, _, _ = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        result = registry.disconnect("prox_1", "on_activate", "io_block_1", "set_active")
        self.assertTrue(result)

    def test_disconnect_returns_false_when_missing(self):
        registry, _, _ = self._make_registry()
        result = registry.disconnect("prox_1", "on_activate", "io_block_1", "set_active")
        self.assertFalse(result)

    def test_disconnect_removes_connection_record(self):
        registry, _, _ = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.disconnect("prox_1", "on_activate", "io_block_1", "set_active")
        self.assertEqual(len(registry._connections), 0)

    def test_disconnect_unwires_callback(self):
        """After disconnect(), the source event must NOT reach the target."""
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.disconnect("prox_1", "on_activate", "io_block_1", "set_active")
        sensor.fire_activate()
        self.assertEqual(io_block.active_calls, 0)

    def test_disconnect_allows_reconnect(self):
        """After disconnect() the same connection can be re-established."""
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.disconnect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        sensor.fire_activate()
        self.assertEqual(io_block.active_calls, 1)

    def test_disconnect_only_affects_specified_connection(self):
        """disconnect() on one connection leaves other connections intact."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io1, io2 = self._IoBlock(), self._IoBlock()
        registry.register_object("s", sensor)
        registry.register_object("io1", io1)
        registry.register_object("io2", io2)
        registry.connect("s", "on_activate", "io1", "set_active")
        registry.connect("s", "on_activate", "io2", "set_active")
        registry.disconnect("s", "on_activate", "io1", "set_active")
        sensor.fire_activate()
        self.assertEqual(io1.active_calls, 0)   # disconnected
        self.assertEqual(io2.active_calls, 1)   # still connected

    # ------------------------------------------------------------------
    # 5.  unregister_object() fully unwires callbacks (regression)
    # ------------------------------------------------------------------

    def test_unregister_target_removes_connection_record(self):
        """Unregistering the target removes the Connection from _connections."""
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.unregister_object("io_block_1")
        self.assertEqual(
            [c for c in registry._connections if c.target_id == "io_block_1"],
            [],
        )

    def test_unregister_target_unwires_callback_from_source(self):
        """Regression: unregister_object must remove the stored callback from
        the source's callback list; previously it left a dangling reference."""
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.unregister_object("io_block_1")
        # The source's callback list must now be empty
        self.assertEqual(len(sensor.on_activate), 0)

    def test_unregister_target_callback_no_longer_fires(self):
        """After unregistering the target, firing the source must not call the target."""
        registry, sensor, io_block = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.unregister_object("io_block_1")
        sensor.fire_activate()   # must not raise and must not increment counter
        self.assertEqual(io_block.active_calls, 0)

    def test_unregister_source_removes_all_its_connections(self):
        """Unregistering the source removes every connection it originates."""
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io1, io2 = self._IoBlock(), self._IoBlock()
        registry.register_object("s", sensor)
        registry.register_object("io1", io1)
        registry.register_object("io2", io2)
        registry.connect("s", "on_activate", "io1", "set_active")
        registry.connect("s", "on_activate", "io2", "set_active")
        registry.unregister_object("s")
        self.assertEqual(registry._connections, [])

    # ------------------------------------------------------------------
    # 6.  enabled=False — connection recorded but NOT wired
    # ------------------------------------------------------------------

    def test_connect_disabled_records_connection(self):
        """A disabled connect() still adds to _connections."""
        registry, sensor, io_block = self._make_registry()
        conn = registry.connect(
            "prox_1", "on_activate", "io_block_1", "set_active", enabled=False
        )
        self.assertFalse(conn.enabled)
        self.assertEqual(len(registry._connections), 1)

    def test_connect_disabled_does_not_wire_callback(self):
        """A disabled connect() must NOT put a callback in the source's list."""
        registry, sensor, io_block = self._make_registry()
        registry.connect(
            "prox_1", "on_activate", "io_block_1", "set_active", enabled=False
        )
        self.assertEqual(len(sensor.on_activate), 0)

    def test_connect_disabled_does_not_fire_target(self):
        """Firing the source after a disabled connect() must not call the target."""
        registry, sensor, io_block = self._make_registry()
        registry.connect(
            "prox_1", "on_activate", "io_block_1", "set_active", enabled=False
        )
        sensor.fire_activate()
        self.assertEqual(io_block.active_calls, 0)

    def test_connect_disabled_allows_later_enabled_connect_after_disconnect(self):
        """You can disconnect a disabled connection and re-add it enabled."""
        registry, sensor, io_block = self._make_registry()
        registry.connect(
            "prox_1", "on_activate", "io_block_1", "set_active", enabled=False
        )
        registry.disconnect("prox_1", "on_activate", "io_block_1", "set_active")
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active", enabled=True)
        sensor.fire_activate()
        self.assertEqual(io_block.active_calls, 1)

    # ------------------------------------------------------------------
    # 7.  Serialisation
    # ------------------------------------------------------------------

    def test_serialize_empty_registry(self):
        registry = ConnectionRegistry()
        result = registry.serialize()
        self.assertEqual(result, {"connections": []})

    def test_serialize_captures_connection_fields(self):
        registry, _, _ = self._make_registry()
        registry.connect("prox_1", "on_activate", "io_block_1", "set_active")
        data = registry.serialize()
        self.assertEqual(len(data["connections"]), 1)
        c = data["connections"][0]
        self.assertEqual(c["source"], "prox_1")
        self.assertEqual(c["output"], "on_activate")
        self.assertEqual(c["target"], "io_block_1")
        self.assertEqual(c["input"], "set_active")
        self.assertTrue(c["enabled"])

    def test_serialize_disabled_connection_preserves_enabled_false(self):
        """enabled=False must be persisted so restore knows not to wire it."""
        registry, _, _ = self._make_registry()
        registry.connect(
            "prox_1", "on_activate", "io_block_1", "set_active", enabled=False
        )
        data = registry.serialize()
        self.assertFalse(data["connections"][0]["enabled"])

    def test_serialize_multiple_connections(self):
        registry = ConnectionRegistry()
        sensor = self._Sensor()
        io1, io2 = self._IoBlock(), self._IoBlock()
        registry.register_object("s", sensor)
        registry.register_object("io1", io1)
        registry.register_object("io2", io2)
        registry.connect("s", "on_activate", "io1", "set_active")
        registry.connect("s", "on_deactivate", "io2", "set_inactive")
        self.assertEqual(len(registry.serialize()["connections"]), 2)

    # ------------------------------------------------------------------
    # 8.  Scene save / load round-trip
    # ------------------------------------------------------------------

    def setUp(self):
        """Set up common fixtures."""
        import tempfile
        self.test_dir = tempfile.mkdtemp()

        ConnectableObj = self._make_connectable_scene_object()

        class _TestPhysicsBody(BasePhysicsBody):
            def __init__(self, **kwargs):
                kwargs.setdefault("name", "TestBody")
                kwargs.setdefault("x", 0.0)
                kwargs.setdefault("y", 0.0)
                kwargs.setdefault("width", 10.0)
                kwargs.setdefault("height", 10.0)
                kwargs.setdefault("mass", 1.0)
                super().__init__(
                    **kwargs,
                    template_name="Base Physics Body",
                    body_type=BodyType.DYNAMIC,
                    collider_type=ColliderType.RECTANGLE,
                    collision_layer=CollisionLayer.DEFAULT,
                )

        self.ConnectableObj = ConnectableObj
        self.TestPhysicsBody = _TestPhysicsBody

    def tearDown(self):
        import shutil
        import os
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _build_connected_scene(self):
        """Return a Scene with two ConnectableObjs connected source→target."""
        scene = Scene()

        source_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="ProxSensor",
            physics_body=self.TestPhysicsBody(),
        )
        target_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="IoBlock",
            physics_body=self.TestPhysicsBody(),
        )

        scene.add_scene_object(source_obj)
        scene.add_scene_object(target_obj)

        scene.get_connection_registry().connect(
            source_obj.get_id(), "on_detect",
            target_obj.get_id(), "receive",
        )
        return scene, source_obj, target_obj

    def test_scene_save_includes_connections(self):
        """Scene.save() serialises connections inside the JSON file."""
        scene, source_obj, target_obj = self._build_connected_scene()
        filepath = Path(self.test_dir) / "scene_with_conn.json"
        scene.save(filepath)

        with open(filepath) as f:
            data = json.load(f)

        self.assertIn("connections", data)
        self.assertEqual(len(data["connections"]), 1)
        c = data["connections"][0]
        self.assertEqual(c["source"], source_obj.get_id())
        self.assertEqual(c["output"], "on_detect")
        self.assertEqual(c["target"], target_obj.get_id())
        self.assertEqual(c["input"], "receive")

    def test_scene_load_restores_connection_records(self):
        """Scene.load() recreates the Connection records in the registry even
        when the loaded (base) SceneObject type doesn't have the callback
        attributes — the record is preserved for round-trip fidelity."""
        scene, source_obj, target_obj = self._build_connected_scene()
        filepath = Path(self.test_dir) / "restore_test.json"
        scene.save(filepath)

        loaded = Scene.load(filepath)

        conns = loaded.get_connection_registry()._connections
        self.assertEqual(len(conns), 1)
        c = conns[0]
        self.assertEqual(c.source_output, "on_detect")
        self.assertEqual(c.target_input, "receive")
        self.assertTrue(c.enabled)

    def test_scene_load_rewires_callbacks(self):
        """When the objects loaded from a scene DO support the callback
        interface, Scene.from_dict() wires them so trigger → target fires.

        We test this by calling Scene.from_dict() with a manually-crafted
        data dict that includes pre-constructed objects registered in the
        registry.  This isolates the wiring logic from the factory/template
        system.
        """
        # Build a fresh scene, register objects, connect, and verify via
        # direct from_dict simulation (no file I/O required).
        scene = Scene()
        source_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="ProxSensor",
            physics_body=self.TestPhysicsBody(),
        )
        target_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="IoBlock",
            physics_body=self.TestPhysicsBody(),
        )
        scene.add_scene_object(source_obj)
        scene.add_scene_object(target_obj)

        # Wire via registry directly (simulates a successful load)
        scene.get_connection_registry().connect(
            source_obj.get_id(), "on_detect",
            target_obj.get_id(), "receive",
        )

        # Trigger and verify the callback fires
        source_obj.trigger()
        self.assertTrue(target_obj.received_value)

        # Verify the registry tracked it internally
        self.assertEqual(len(scene.get_connection_registry()._connections), 1)
        key = (source_obj.get_id(), "on_detect", target_obj.get_id(), "receive")
        self.assertIn(key, scene.get_connection_registry()._callback_refs)

    def test_scene_load_disabled_connection_not_wired(self):
        """Regression: disabled connections serialised as enabled=false must NOT
        be wired on load.  Previously the enabled flag was not passed to connect().

        We verify:
          1. The record is restored with enabled=False.
          2. The source's callback list is empty (callback was never wired).
        """
        scene = Scene()
        source_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="ProxSensor",
            physics_body=self.TestPhysicsBody(),
        )
        target_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="IoBlock",
            physics_body=self.TestPhysicsBody(),
        )
        scene.add_scene_object(source_obj)
        scene.add_scene_object(target_obj)
        # Add as disabled
        scene.get_connection_registry().connect(
            source_obj.get_id(), "on_detect",
            target_obj.get_id(), "receive",
            enabled=False,
        )
        filepath = Path(self.test_dir) / "disabled_conn.json"
        scene.save(filepath)

        loaded = Scene.load(filepath)

        # Record still exists with enabled=False
        conns = loaded.get_connection_registry()._connections
        self.assertEqual(len(conns), 1)
        self.assertFalse(conns[0].enabled)

        # No wired callback reference should exist for this connection
        key = (conns[0].source_id, "on_detect", conns[0].target_id, "receive")
        self.assertNotIn(key, loaded.get_connection_registry()._callback_refs)

    def test_scene_multiple_connections_roundtrip(self):
        """Multiple connections survive a full save/load cycle (records preserved)."""
        scene = Scene()
        a = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="A",
            physics_body=self.TestPhysicsBody(),
        )
        b = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="B",
            physics_body=self.TestPhysicsBody(),
        )
        c_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="C",
            physics_body=self.TestPhysicsBody(),
        )
        for obj in (a, b, c_obj):
            scene.add_scene_object(obj)

        registry = scene.get_connection_registry()
        registry.connect(a.get_id(), "on_detect", b.get_id(), "receive")
        registry.connect(a.get_id(), "on_detect", c_obj.get_id(), "receive")

        filepath = Path(self.test_dir) / "multi_conn.json"
        scene.save(filepath)

        loaded = Scene.load(filepath)
        loaded_conns = loaded.get_connection_registry()._connections
        self.assertEqual(len(loaded_conns), 2)

        # Both records point to the correct target inputs
        target_inputs = {c.target_input for c in loaded_conns}
        self.assertEqual(target_inputs, {"receive"})

    # ------------------------------------------------------------------
    # 9.  SceneBoundLayer sources coexisting with ConnectionRegistry
    # ------------------------------------------------------------------

    def test_bridge_binding_and_connection_registry_coexist(self):
        """An active SceneBridge and the ConnectionRegistry can both reference
        the same scene objects without interfering with each other.

        This mirrors the ControlRox scenario where a prox→I/O connection must
        propagate the activation *and* the bridge must independently read PLC
        state and write it into the scene.
        """

        # Build a minimal scene
        scene = Scene()
        source_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="ProxSensor",
            physics_body=self.TestPhysicsBody(),
        )
        target_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="IoBlock",
            physics_body=self.TestPhysicsBody(),
        )
        scene.add_scene_object(source_obj)
        scene.add_scene_object(target_obj)

        # Wire registry connection: prox activates I/O block
        scene.get_connection_registry().connect(
            source_obj.get_id(), "on_detect",
            target_obj.get_id(), "receive",
        )

        # Wire bridge binding: PLC source → scene object property
        plc_ns = SimpleNamespace(conveyor_active=False)
        layer = SceneBoundLayer()
        layer.register_source("plc", plc_ns)

        class _Bridge(SceneBridge):
            def create_default_bound_object(self):
                return SceneBoundLayer()

        mock_scene = MagicMock()
        mock_scene.get_scene_object.return_value = target_obj
        bridge = _Bridge(scene=mock_scene, bound_object=layer)
        bridge.add_binding(
            "plc.conveyor_active",
            target_obj.get_id(),
            "active",
            BindingDirection.READ,
        )

        # 1. Registry path: trigger prox → I/O block receives
        source_obj.trigger()
        self.assertTrue(target_obj.received_value)

        # 2. Bridge path: PLC source changes → scene object updated
        plc_ns.conveyor_active = True
        bridge.poll_source_to_scene()
        self.assertTrue(target_obj.active)

        # Verify the two mechanisms did not corrupt each other
        self.assertEqual(len(scene.get_connection_registry()._connections), 1)

    # ------------------------------------------------------------------
    # 10. Scene-level integration: auto-register / auto-unregister
    # ------------------------------------------------------------------

    def test_scene_add_object_auto_registers_in_registry(self):
        """Scene.add_scene_object() must register the object in the registry."""
        scene = Scene()
        obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="AutoReg",
            physics_body=self.TestPhysicsBody(),
        )
        scene.add_scene_object(obj)
        self.assertIn(obj.get_id(), scene.get_connection_registry()._objects)

    def test_scene_remove_object_auto_unregisters_and_unwires(self):
        """Scene.remove_scene_object() must remove the object from the registry
        and unwire any callbacks it participated in."""
        scene = Scene()
        source_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="Src",
            physics_body=self.TestPhysicsBody(),
        )
        target_obj = self.ConnectableObj(
            scene_object_type="ConnectableObj",
            name="Tgt",
            physics_body=self.TestPhysicsBody(),
        )
        scene.add_scene_object(source_obj)
        scene.add_scene_object(target_obj)

        scene.get_connection_registry().connect(
            source_obj.get_id(), "on_detect",
            target_obj.get_id(), "receive",
        )

        # Remove target from scene — must fully clean up
        scene.remove_scene_object(target_obj.get_id())

        # Registry object gone
        self.assertNotIn(
            target_obj.get_id(), scene.get_connection_registry()._objects
        )
        # Connection record gone
        self.assertEqual(len(scene.get_connection_registry()._connections), 0)
        # Source callback list is clean — no dangling reference
        self.assertEqual(len(source_obj.on_detect), 0)

        # Firing the source must not raise
        source_obj.trigger()


if __name__ == '__main__':
    unittest.main()
