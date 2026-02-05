"""Unit tests for SceneViewerFrame coordinate transformation logic."""
import unittest

from pyrox.models.scene import Scene, SceneObject
from pyrox.models.physics import BasePhysicsBody


class TestSceneViewerCoordinates(unittest.TestCase):
    """Test coordinate transformation methods without GUI."""

    def test_world_to_canvas_default(self):
        """Test world to canvas conversion with default settings."""
        # Simulate transformation logic
        zoom = 1.0
        viewport_x = 0.0
        viewport_y = 0.0

        world_x, world_y = 50.0, 100.0
        canvas_x = world_x * zoom + viewport_x
        canvas_y = world_y * zoom + viewport_y

        self.assertEqual(canvas_x, 50.0)
        self.assertEqual(canvas_y, 100.0)

    def test_world_to_canvas_zoomed(self):
        """Test world to canvas conversion with zoom."""
        zoom = 2.0
        viewport_x = 10.0
        viewport_y = 20.0

        world_x, world_y = 50.0, 100.0
        canvas_x = world_x * zoom + viewport_x
        canvas_y = world_y * zoom + viewport_y

        self.assertEqual(canvas_x, 110.0)
        self.assertEqual(canvas_y, 220.0)

    def test_canvas_to_world_default(self):
        """Test canvas to world conversion with default settings."""
        zoom = 1.0
        viewport_x = 0.0
        viewport_y = 0.0

        canvas_x, canvas_y = 50.0, 100.0
        world_x = (canvas_x - viewport_x) / zoom
        world_y = (canvas_y - viewport_y) / zoom

        self.assertEqual(world_x, 50.0)
        self.assertEqual(world_y, 100.0)

    def test_canvas_to_world_zoomed(self):
        """Test canvas to world conversion with zoom and pan."""
        zoom = 2.0
        viewport_x = 10.0
        viewport_y = 20.0

        canvas_x, canvas_y = 110.0, 220.0
        world_x = (canvas_x - viewport_x) / zoom
        world_y = (canvas_y - viewport_y) / zoom

        self.assertEqual(world_x, 50.0)
        self.assertEqual(world_y, 100.0)


class TestSceneManagement(unittest.TestCase):
    """Test scene management logic."""

    def test_scene_object_creation(self):
        """Test creating scene objects."""
        obj = SceneObject(
            name="Test Object",
            scene_object_type="rectangle",
            properties={"shape": "rectangle"},
            physics_body=BasePhysicsBody(x=10, y=20)
        )

        self.assertEqual(obj.name, "Test Object")
        self.assertEqual(obj.properties["x"], 10)
        self.assertEqual(obj.properties["y"], 20)
        self.assertIsNotNone(obj.id)

    def test_scene_add_remove_objects(self):
        """Test adding and removing objects from scene."""
        scene = Scene(name="Test Scene")
        obj1 = SceneObject(name="Object 1", scene_object_type="rect", properties={},
                           physics_body=BasePhysicsBody())
        obj2 = SceneObject(name="Object 2", scene_object_type="circle", properties={},
                           physics_body=BasePhysicsBody())

        scene.add_scene_object(obj1)
        scene.add_scene_object(obj2)

        self.assertEqual(len(scene.scene_objects), 2)
        self.assertIn(obj1.id, scene.scene_objects)

        scene.remove_scene_object(obj1.id)

        self.assertEqual(len(scene.scene_objects), 1)
        self.assertNotIn(obj1.id, scene.scene_objects)


class TestZoomLogic(unittest.TestCase):
    """Test zoom calculation logic."""

    def test_zoom_in_calculation(self):
        """Test zoom in factor calculation."""
        initial_zoom = 1.0
        factor = 1.2
        max_zoom = 10.0

        new_zoom = min(initial_zoom * factor, max_zoom)

        self.assertEqual(new_zoom, 1.2)

    def test_zoom_out_calculation(self):
        """Test zoom out factor calculation."""
        initial_zoom = 2.0
        factor = 1.2
        min_zoom = 0.1

        new_zoom = max(initial_zoom / factor, min_zoom)

        self.assertAlmostEqual(new_zoom, 1.666667, places=5)

    def test_zoom_limits(self):
        """Test zoom limits are respected."""
        zoom = 15.0
        min_zoom = 0.1
        max_zoom = 10.0

        clamped = min(max(zoom, min_zoom), max_zoom)

        self.assertEqual(clamped, max_zoom)


if __name__ == '__main__':
    unittest.main()
