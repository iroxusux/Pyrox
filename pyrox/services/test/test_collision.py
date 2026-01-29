"""Unit tests for collision service."""

import unittest
from unittest.mock import Mock

from pyrox.models.protocols.physics import PhysicsBody2D

from pyrox.services.collision import (
    CollisionInfo,
    SpatialGrid,
    CollisionService,
)
from pyrox.interfaces.protocols.physics import (
    BodyType,
    CollisionLayer,
)


class MockEnvironmentService:
    """Mock environment service for testing."""

    def __init__(self):
        self.default_restitution = 0.3

    def calculate_combined_restitution(self, r1: float, r2: float) -> float:
        """Calculate combined restitution."""
        return (r1 + r2) / 2

    def calculate_combined_friction(self, f1: float, f2: float) -> float:
        """Calculate combined friction."""
        return (f1 * f2) ** 0.5


class TestCollisionInfo(unittest.TestCase):
    """Test cases for CollisionInfo dataclass."""

    def test_init(self):
        """Test CollisionInfo initialization."""
        body_a = PhysicsBody2D()
        body_b = PhysicsBody2D()

        info = CollisionInfo(
            body_a=body_a,
            body_b=body_b,
            penetration_depth=5.0,
            normal=(1.0, 0.0),
            contact_point=(10.0, 20.0)
        )

        self.assertEqual(info.body_a, body_a)
        self.assertEqual(info.body_b, body_b)
        self.assertEqual(info.penetration_depth, 5.0)
        self.assertEqual(info.normal, (1.0, 0.0))
        self.assertEqual(info.contact_point, (10.0, 20.0))

    def test_collision_info_attributes(self):
        """Test that all attributes are accessible."""
        body_a = PhysicsBody2D()
        body_b = PhysicsBody2D()

        info = CollisionInfo(
            body_a=body_a,
            body_b=body_b,
            penetration_depth=3.5,
            normal=(0.0, 1.0),
            contact_point=(5.0, 15.0)
        )

        self.assertIsNotNone(info.body_a)
        self.assertIsNotNone(info.body_b)
        self.assertIsInstance(info.penetration_depth, float)
        self.assertIsInstance(info.normal, tuple)
        self.assertIsInstance(info.contact_point, tuple)


class TestSpatialGrid(unittest.TestCase):
    """Test cases for SpatialGrid class."""

    def test_init_default_cell_size(self):
        """Test initialization with default cell size."""
        grid = SpatialGrid()
        self.assertEqual(grid.cell_size, 100.0)
        self.assertEqual(len(grid._grid), 0)

    def test_init_custom_cell_size(self):
        """Test initialization with custom cell size."""
        grid = SpatialGrid(cell_size=50.0)
        self.assertEqual(grid.cell_size, 50.0)

    def test_get_cell_coords(self):
        """Test converting world coordinates to cell coordinates."""
        grid = SpatialGrid(cell_size=100.0)

        self.assertEqual(grid._get_cell_coords(0.0, 0.0), (0, 0))
        self.assertEqual(grid._get_cell_coords(50.0, 50.0), (0, 0))
        self.assertEqual(grid._get_cell_coords(100.0, 100.0), (1, 1))
        self.assertEqual(grid._get_cell_coords(250.0, 350.0), (2, 3))
        self.assertEqual(grid._get_cell_coords(-50.0, -50.0), (-1, -1))

    def test_get_cells_for_bounds_single_cell(self):
        """Test getting cells for bounds that fit in one cell."""
        grid = SpatialGrid(cell_size=100.0)

        cells = grid._get_cells_for_bounds(10.0, 20.0, 30.0, 40.0)
        self.assertEqual(len(cells), 1)
        self.assertIn((0, 0), cells)

    def test_get_cells_for_bounds_multiple_cells(self):
        """Test getting cells for bounds that span multiple cells."""
        grid = SpatialGrid(cell_size=100.0)

        cells = grid._get_cells_for_bounds(50.0, 50.0, 150.0, 250.0)
        self.assertIn((0, 0), cells)
        self.assertIn((1, 0), cells)
        self.assertIn((0, 1), cells)
        self.assertIn((1, 1), cells)
        self.assertIn((0, 2), cells)
        self.assertIn((1, 2), cells)

    def test_insert_body(self):
        """Test inserting a body into the grid."""
        grid = SpatialGrid(cell_size=100.0)
        body = PhysicsBody2D(x=10.0, y=20.0, width=30.0, height=40.0)

        grid.insert(body)

        # Body should be in cell (0, 0)
        self.assertIn((0, 0), grid._grid)
        self.assertIn(body, grid._grid[(0, 0)])

    def test_insert_body_spanning_multiple_cells(self):
        """Test inserting a body that spans multiple cells."""
        grid = SpatialGrid(cell_size=100.0)
        body = PhysicsBody2D(x=50.0, y=50.0, width=100.0, height=100.0)

        grid.insert(body)

        # Body spans cells (0,0), (1,0), (0,1), (1,1)
        self.assertIn(body, grid._grid[(0, 0)])
        self.assertIn(body, grid._grid[(1, 0)])
        self.assertIn(body, grid._grid[(0, 1)])
        self.assertIn(body, grid._grid[(1, 1)])

    def test_insert_multiple_bodies(self):
        """Test inserting multiple bodies."""
        grid = SpatialGrid(cell_size=100.0)
        body1 = PhysicsBody2D(x=10.0, y=10.0, width=10.0, height=10.0)
        body2 = PhysicsBody2D(x=20.0, y=20.0, width=10.0, height=10.0)

        grid.insert(body1)
        grid.insert(body2)

        self.assertEqual(len(grid._grid[(0, 0)]), 2)
        self.assertIn(body1, grid._grid[(0, 0)])
        self.assertIn(body2, grid._grid[(0, 0)])

    def test_remove_body(self):
        """Test removing a body from the grid."""
        grid = SpatialGrid(cell_size=100.0)
        body = PhysicsBody2D(x=10.0, y=10.0, width=10.0, height=10.0)

        grid.insert(body)
        self.assertIn(body, grid._grid[(0, 0)])

        grid.remove(body)
        self.assertNotIn(body, grid._grid[(0, 0)])

    def test_remove_body_from_multiple_cells(self):
        """Test removing a body that was in multiple cells."""
        grid = SpatialGrid(cell_size=100.0)
        body = PhysicsBody2D(x=50.0, y=50.0, width=100.0, height=100.0)

        grid.insert(body)
        grid.remove(body)

        # Body should be removed from all cells
        for cell_bodies in grid._grid.values():
            self.assertNotIn(body, cell_bodies)

    def test_query_nearby_single_cell(self):
        """Test querying nearby bodies in the same cell."""
        grid = SpatialGrid(cell_size=100.0)
        body1 = PhysicsBody2D(x=10.0, y=10.0, width=10.0, height=10.0)
        body2 = PhysicsBody2D(x=20.0, y=20.0, width=10.0, height=10.0)
        body3 = PhysicsBody2D(x=200.0, y=200.0, width=10.0, height=10.0)

        grid.insert(body1)
        grid.insert(body2)
        grid.insert(body3)

        nearby = grid.query_nearby(body1)

        self.assertIn(body2, nearby)
        self.assertNotIn(body3, nearby)
        self.assertNotIn(body1, nearby)  # Should not include self

    def test_query_nearby_multiple_cells(self):
        """Test querying nearby bodies across multiple cells."""
        grid = SpatialGrid(cell_size=100.0)
        body1 = PhysicsBody2D(x=90.0, y=90.0, width=20.0, height=20.0)  # Spans cells
        body2 = PhysicsBody2D(x=95.0, y=95.0, width=10.0, height=10.0)  # In overlap
        body3 = PhysicsBody2D(x=300.0, y=300.0, width=10.0, height=10.0)  # Far away

        grid.insert(body1)
        grid.insert(body2)
        grid.insert(body3)

        nearby = grid.query_nearby(body1)

        self.assertIn(body2, nearby)
        self.assertNotIn(body3, nearby)

    def test_query_nearby_empty_grid(self):
        """Test querying when grid is empty."""
        grid = SpatialGrid(cell_size=100.0)
        body = PhysicsBody2D(x=10.0, y=10.0, width=10.0, height=10.0)

        nearby = grid.query_nearby(body)
        self.assertEqual(len(nearby), 0)

    def test_clear(self):
        """Test clearing the grid."""
        grid = SpatialGrid(cell_size=100.0)
        body1 = PhysicsBody2D(x=10.0, y=10.0, width=10.0, height=10.0)
        body2 = PhysicsBody2D(x=20.0, y=20.0, width=10.0, height=10.0)

        grid.insert(body1)
        grid.insert(body2)
        self.assertGreater(len(grid._grid), 0)

        grid.clear()
        self.assertEqual(len(grid._grid), 0)


class TestCollisionService(unittest.TestCase):
    """Test cases for CollisionService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = CollisionService(cell_size=100.0)
        self.env = MockEnvironmentService()

    def test_init(self):
        """Test CollisionService initialization."""
        service = CollisionService(cell_size=50.0)

        self.assertEqual(service._spatial_grid.cell_size, 50.0)
        self.assertEqual(len(service._registered_bodies), 0)
        self.assertEqual(len(service._colliding_pairs), 0)

    def test_register_body(self):
        """Test registering a body."""
        body = PhysicsBody2D()

        self.service.register_body(body)

        self.assertIn(body, self.service._registered_bodies)

    def test_register_body_duplicate(self):
        """Test that registering the same body twice doesn't duplicate."""
        body = PhysicsBody2D()

        self.service.register_body(body)
        self.service.register_body(body)

        # Should only appear once
        self.assertEqual(self.service._registered_bodies.count(body), 1)

    def test_unregister_body(self):
        """Test unregistering a body."""
        body = PhysicsBody2D()

        self.service.register_body(body)
        self.assertIn(body, self.service._registered_bodies)

        self.service.unregister_body(body)
        self.assertNotIn(body, self.service._registered_bodies)

    def test_unregister_nonexistent_body(self):
        """Test unregistering a body that wasn't registered."""
        body = PhysicsBody2D()

        # Should not raise error
        self.service.unregister_body(body)

    def test_update_spatial_grid(self):
        """Test updating spatial grid after bodies move."""
        body1 = PhysicsBody2D(x=10.0, y=10.0, width=10.0, height=10.0)
        body2 = PhysicsBody2D(x=20.0, y=20.0, width=10.0, height=10.0)

        self.service.register_body(body1)
        self.service.register_body(body2)

        # Move bodies
        body1.x = 200.0
        body1.y = 200.0

        # Update grid
        self.service.update_spatial_grid()

        # Bodies should be in new locations in grid
        nearby_to_body1 = self.service._spatial_grid.query_nearby(body1)
        self.assertNotIn(body2, nearby_to_body1)

    def test_detect_collisions_no_collision(self):
        """Test detecting collisions when bodies don't overlap."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=10.0, height=10.0)
        body2 = PhysicsBody2D(x=100.0, y=100.0, width=10.0, height=10.0)

        self.service.register_body(body1)
        self.service.register_body(body2)

        collisions = self.service.detect_collisions()

        self.assertEqual(len(collisions), 0)

    def test_detect_collisions_with_collision(self):
        """Test detecting collisions when bodies overlap."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        self.service.register_body(body1)
        self.service.register_body(body2)

        collisions = self.service.detect_collisions()

        self.assertEqual(len(collisions), 1)
        self.assertIsInstance(collisions[0], CollisionInfo)

    def test_detect_collisions_skips_disabled_bodies(self):
        """Test that disabled bodies are skipped."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0, enabled=False)

        self.service.register_body(body1)
        self.service.register_body(body2)

        collisions = self.service.detect_collisions()

        self.assertEqual(len(collisions), 0)

    def test_detect_collisions_skips_sleeping_bodies(self):
        """Test that sleeping bodies are skipped."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0, sleeping=True)

        self.service.register_body(body1)
        self.service.register_body(body2)

        collisions = self.service.detect_collisions()

        self.assertEqual(len(collisions), 0)

    def test_collision_callbacks_on_enter(self):
        """Test collision enter callbacks are triggered."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        # Track callback calls with mocks
        body1.on_collision_enter = Mock()
        body2.on_collision_enter = Mock()

        self.service.register_body(body1)
        self.service.register_body(body2)

        self.service.detect_collisions()

        self.assertEqual(body1.on_collision_enter.call_count, 1)
        self.assertEqual(body2.on_collision_enter.call_count, 1)
        body1.on_collision_enter.assert_called_once_with(body2)
        body2.on_collision_enter.assert_called_once_with(body1)

    def test_collision_callbacks_on_stay(self):
        """Test collision stay callbacks are triggered."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        # Track callback calls with mocks
        body1.on_collision_enter = Mock()
        body2.on_collision_enter = Mock()
        body1.on_collision_stay = Mock()
        body2.on_collision_stay = Mock()

        self.service.register_body(body1)
        self.service.register_body(body2)

        # First detection - enter
        self.service.detect_collisions()

        # Second detection - stay
        self.service.detect_collisions()

        self.assertEqual(body1.on_collision_stay.call_count, 1)
        self.assertEqual(body2.on_collision_stay.call_count, 1)

    def test_collision_callbacks_on_exit(self):
        """Test collision exit callbacks are triggered."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        # Track callback calls with mocks
        body1.on_collision_enter = Mock()
        body2.on_collision_enter = Mock()
        body1.on_collision_exit = Mock()
        body2.on_collision_exit = Mock()

        self.service.register_body(body1)
        self.service.register_body(body2)

        # First detection - collision
        self.service.detect_collisions()

        # Move apart
        body2.x = 200.0
        body2.y = 200.0
        self.service.update_spatial_grid()

        # Second detection - no collision
        self.service.detect_collisions()

        self.assertEqual(body1.on_collision_exit.call_count, 1)
        self.assertEqual(body2.on_collision_exit.call_count, 1)

    def test_should_collide_with_layers(self):
        """Test collision layer filtering."""
        body1 = PhysicsBody2D(
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[CollisionLayer.ENEMY]
        )
        body2 = PhysicsBody2D(
            collision_layer=CollisionLayer.ENEMY,
            collision_mask=[CollisionLayer.PLAYER]
        )

        should_collide = self.service._should_collide(body1, body2)
        self.assertTrue(should_collide)

    def test_should_not_collide_with_layers(self):
        """Test that bodies on filtered layers don't collide."""
        body1 = PhysicsBody2D(
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[CollisionLayer.TERRAIN]  # Doesn't include ENEMY
        )
        body2 = PhysicsBody2D(
            collision_layer=CollisionLayer.ENEMY,
            collision_mask=[CollisionLayer.PLAYER]
        )

        should_collide = self.service._should_collide(body1, body2)
        self.assertFalse(should_collide)

    def test_should_collide_empty_mask_collides_with_all(self):
        """Test that empty collision mask collides with all layers."""
        body1 = PhysicsBody2D(
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[]  # Empty mask = collide with all
        )
        body2 = PhysicsBody2D(
            collision_layer=CollisionLayer.ENEMY,
            collision_mask=[]
        )

        should_collide = self.service._should_collide(body1, body2)
        self.assertTrue(should_collide)

    def test_check_collision_overlapping(self):
        """Test narrow-phase collision detection with overlap."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        collision = self.service._check_collision(body1, body2)

        self.assertIsNotNone(collision)
        self.assertEqual(collision.body_a, body1)  # type: ignore
        self.assertEqual(collision.body_b, body2)  # type: ignore
        self.assertGreater(collision.penetration_depth, 0)  # type: ignore

    def test_check_collision_no_overlap(self):
        """Test narrow-phase collision detection without overlap."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=10.0, height=10.0)
        body2 = PhysicsBody2D(x=100.0, y=100.0, width=10.0, height=10.0)

        collision = self.service._check_collision(body1, body2)

        self.assertIsNone(collision)

    def test_check_collision_calculates_normal(self):
        """Test that collision normal is calculated correctly."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=40.0, y=0.0, width=50.0, height=50.0)  # To the right

        collision = self.service._check_collision(body1, body2)

        self.assertIsNotNone(collision)
        # Normal should point in X direction
        self.assertEqual(collision.normal[1], 0.0)  # type: ignore
        self.assertNotEqual(collision.normal[0], 0.0)  # type: ignore

    def test_resolve_collision_applies_impulse(self):
        """Test that collision resolution applies impulses."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0, mass=1.0)
        body2 = PhysicsBody2D(x=25.0, y=0.0, width=50.0, height=50.0, mass=1.0)

        body1.set_linear_velocity(10.0, 0.0)
        body2.set_linear_velocity(-10.0, 0.0)

        collision = self.service._check_collision(body1, body2)
        self.assertIsNotNone(collision)

        self.service.resolve_collision(collision, self.env)  # type: ignore

        # Velocities should have changed
        vel1_x, vel1_y = body1.get_linear_velocity()
        vel2_x, vel2_y = body2.get_linear_velocity()
        self.assertNotEqual(vel1_x, 10.0)
        self.assertNotEqual(vel2_x, -10.0)

    def test_resolve_collision_skips_triggers(self):
        """Test that triggers don't resolve collisions."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0, is_trigger=True)
        body2 = PhysicsBody2D(x=25.0, y=0.0, width=50.0, height=50.0)

        body1.set_linear_velocity(10.0, 0.0)
        body2.set_linear_velocity(0.0, 0.0)

        collision = self.service._check_collision(body1, body2)
        self.assertIsNotNone(collision)

        self.service.resolve_collision(collision, self.env)  # type: ignore

        # Velocities should not change for triggers
        vel1_x, vel1_y = body1.get_linear_velocity()
        vel2_x, vel2_y = body2.get_linear_velocity()
        self.assertEqual(vel1_x, 10.0)
        self.assertEqual(vel2_x, 0.0)

    def test_resolve_collision_static_bodies(self):
        """Test collision resolution with static bodies."""
        body1 = PhysicsBody2D(
            x=0.0, y=0.0, width=50.0, height=50.0,
            body_type=BodyType.DYNAMIC, mass=1.0
        )
        body2 = PhysicsBody2D(
            x=25.0, y=0.0, width=50.0, height=50.0,
            body_type=BodyType.STATIC, mass=0.0
        )

        body1.set_linear_velocity(10.0, 0.0)

        collision = self.service._check_collision(body1, body2)
        self.assertIsNotNone(collision)

        initial_vel_x, initial_vel_y = body1.get_linear_velocity()
        self.service.resolve_collision(collision, self.env)  # type: ignore

        # Dynamic body should bounce off static body
        vel_x, vel_y = body1.get_linear_velocity()
        self.assertNotEqual(vel_x, initial_vel_x)

    def test_resolve_collision_separating_velocities(self):
        """Test that separating velocities don't get resolved."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=0.0, width=50.0, height=50.0)

        # Bodies moving apart
        body1.set_linear_velocity(-10.0, 0.0)
        body2.set_linear_velocity(10.0, 0.0)

        collision = self.service._check_collision(body1, body2)
        self.assertIsNotNone(collision)

        initial_vel1_x, initial_vel1_y = body1.get_linear_velocity()
        initial_vel2_x, initial_vel2_y = body2.get_linear_velocity()

        self.service.resolve_collision(collision, self.env)  # type: ignore

        # Velocities should not change
        vel1_x, vel1_y = body1.get_linear_velocity()
        vel2_x, vel2_y = body2.get_linear_velocity()
        self.assertEqual(vel1_x, initial_vel1_x)
        self.assertEqual(vel2_x, initial_vel2_x)

    def test_correct_positions(self):
        """Test position correction to prevent sinking."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0, mass=1.0)
        body2 = PhysicsBody2D(x=45.0, y=0.0, width=50.0, height=50.0, mass=1.0)

        initial_x1 = body1.x
        initial_x2 = body2.x

        collision = self.service._check_collision(body1, body2)
        self.assertIsNotNone(collision)

        inv_mass1 = body1.inverse_mass
        inv_mass2 = body2.inverse_mass

        self.service._correct_positions(collision, inv_mass1, inv_mass2)  # type: ignore

        # Positions should have been corrected
        # Bodies should be moved apart
        distance_before = abs(initial_x2 - initial_x1)
        distance_after = abs(body2.x - body1.x)
        self.assertGreater(distance_after, distance_before)

    def test_correct_positions_with_static_body(self):
        """Test position correction with one static body."""
        body1 = PhysicsBody2D(
            x=0.0, y=0.0, width=50.0, height=50.0,
            body_type=BodyType.DYNAMIC, mass=1.0
        )
        body2 = PhysicsBody2D(
            x=45.0, y=0.0, width=50.0, height=50.0,
            body_type=BodyType.STATIC, mass=0.0
        )

        initial_x1 = body1.x
        initial_x2 = body2.x

        collision = self.service._check_collision(body1, body2)
        self.assertIsNotNone(collision)

        inv_mass1 = body1.inverse_mass
        inv_mass2 = body2.inverse_mass

        self.service._correct_positions(collision, inv_mass1, inv_mass2)  # type: ignore

        # Only dynamic body should move
        self.assertNotEqual(body1.x, initial_x1)
        self.assertEqual(body2.x, initial_x2)

    def test_clear(self):
        """Test clearing collision service state."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        self.service.register_body(body1)
        self.service.register_body(body2)
        self.service.detect_collisions()

        self.assertGreater(len(self.service._registered_bodies), 0)

        self.service.clear()

        self.assertEqual(len(self.service._registered_bodies), 0)
        self.assertEqual(len(self.service._colliding_pairs), 0)

    def test_multiple_collisions_detected(self):
        """Test detecting multiple simultaneous collisions."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=0.0, width=50.0, height=50.0)
        body3 = PhysicsBody2D(x=40.0, y=0.0, width=50.0, height=50.0)

        self.service.register_body(body1)
        self.service.register_body(body2)
        self.service.register_body(body3)

        collisions = self.service.detect_collisions()

        # Should detect body1-body2, body2-body3, and possibly body1-body3
        self.assertGreaterEqual(len(collisions), 2)

    def test_collision_info_penetration_depth(self):
        """Test that penetration depth is calculated correctly."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=40.0, y=0.0, width=50.0, height=50.0)

        collision = self.service._check_collision(body1, body2)

        self.assertIsNotNone(collision)
        # Overlap is 10 units (50 - 40)
        self.assertEqual(collision.penetration_depth, 10.0)  # type: ignore

    def test_collision_info_contact_point(self):
        """Test that contact point is calculated correctly."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=40.0, y=0.0, width=50.0, height=50.0)

        collision = self.service._check_collision(body1, body2)

        self.assertIsNotNone(collision)
        contact_x, contact_y = collision.contact_point  # type: ignore

        # Contact should be in overlap region
        self.assertGreaterEqual(contact_x, 40.0)
        self.assertLessEqual(contact_x, 50.0)

    def test_collision_detection_order_independence(self):
        """Test that collision detection order doesn't matter."""
        body1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        body2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)

        collision1 = self.service._check_collision(body1, body2)
        collision2 = self.service._check_collision(body2, body1)

        self.assertIsNotNone(collision1)
        self.assertIsNotNone(collision2)
        # Should detect collision regardless of order
        self.assertEqual(collision1.penetration_depth, collision2.penetration_depth)  # type: ignore


if __name__ == '__main__':
    unittest.main()
