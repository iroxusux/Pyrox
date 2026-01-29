"""Unit tests for physics.py protocols module."""

import unittest

from pyrox.models.protocols.physics import (
    Material,
    Collider2D,
    RigidBody2D,
    PhysicsBody2D,
)
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IMaterial,
    ICollider2D,
    IRigidBody2D,
    IPhysicsBody2D,
)


class TestMaterial(unittest.TestCase):
    """Test cases for Material class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        mat = Material()
        self.assertEqual(mat.get_density(), 1.0)
        self.assertEqual(mat.get_restitution(), 0.3)
        self.assertEqual(mat.get_friction(), 0.5)
        self.assertEqual(mat.get_drag(), 0.1)

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        mat = Material(density=2.5, restitution=0.8, friction=0.7, drag=0.2)
        self.assertEqual(mat.get_density(), 2.5)
        self.assertEqual(mat.get_restitution(), 0.8)
        self.assertEqual(mat.get_friction(), 0.7)
        self.assertEqual(mat.get_drag(), 0.2)

    def test_restitution_clamping(self):
        """Test that restitution is clamped between 0.0 and 1.0."""
        mat = Material(restitution=1.5)
        self.assertEqual(mat.get_restitution(), 1.0)

        mat = Material(restitution=-0.5)
        self.assertEqual(mat.get_restitution(), 0.0)

    def test_friction_clamping(self):
        """Test that friction is clamped between 0.0 and 1.0."""
        mat = Material(friction=2.0)
        self.assertEqual(mat.get_friction(), 1.0)

        mat = Material(friction=-1.0)
        self.assertEqual(mat.get_friction(), 0.0)

    def test_set_density_valid(self):
        """Test setting valid density values."""
        mat = Material()
        mat.set_density(5.0)
        self.assertEqual(mat.get_density(), 5.0)

        mat.set_density(0.0)
        self.assertEqual(mat.get_density(), 0.0)

    def test_set_density_negative_raises_error(self):
        """Test that negative density raises ValueError."""
        mat = Material()
        with self.assertRaises(ValueError) as context:
            mat.set_density(-1.0)
        self.assertIn("non-negative", str(context.exception))

    def test_set_restitution_clamping(self):
        """Test that set_restitution clamps values."""
        mat = Material()
        mat.set_restitution(1.5)
        self.assertEqual(mat.get_restitution(), 1.0)

        mat.set_restitution(-0.5)
        self.assertEqual(mat.get_restitution(), 0.0)

    def test_set_friction_clamping(self):
        """Test that set_friction clamps values."""
        mat = Material()
        mat.set_friction(2.0)
        self.assertEqual(mat.get_friction(), 1.0)

        mat.set_friction(-1.0)
        self.assertEqual(mat.get_friction(), 0.0)

    def test_set_drag_valid(self):
        """Test setting valid drag values."""
        mat = Material()
        mat.set_drag(0.5)
        self.assertEqual(mat.get_drag(), 0.5)

    def test_set_drag_negative_raises_error(self):
        """Test that negative drag raises ValueError."""
        mat = Material()
        with self.assertRaises(ValueError) as context:
            mat.set_drag(-0.1)
        self.assertIn("non-negative", str(context.exception))

    def test_implements_imaterial_protocol(self):
        """Test that Material implements IMaterial protocol."""
        mat = Material()
        self.assertIsInstance(mat, IMaterial)

    def test_density_property(self):
        """Test density property access."""
        mat = Material(density=3.0)
        self.assertEqual(mat.density, 3.0)

    def test_restitution_property(self):
        """Test restitution property access."""
        mat = Material(restitution=0.5)
        self.assertEqual(mat.restitution, 0.5)

    def test_friction_property(self):
        """Test friction property access."""
        mat = Material(friction=0.6)
        self.assertEqual(mat.friction, 0.6)

    def test_drag_property(self):
        """Test drag property access."""
        mat = Material(drag=0.2)
        self.assertEqual(mat.drag, 0.2)


class TestCollider(unittest.TestCase):
    """Test cases for Collider class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        col = Collider2D()
        self.assertEqual(col.get_collider_type(), ColliderType.RECTANGLE)
        self.assertEqual(col.get_collision_layer(), CollisionLayer.DEFAULT)
        self.assertEqual(col.get_collision_mask(), [])
        self.assertFalse(col.get_is_trigger())

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        col = Collider2D(
            collider_type=ColliderType.CIRCLE,
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[CollisionLayer.ENEMY, CollisionLayer.TERRAIN],
            is_trigger=True,
            x=100.0,
            y=200.0,
            width=50.0,
            height=75.0
        )
        self.assertEqual(col.get_collider_type(), ColliderType.CIRCLE)
        self.assertEqual(col.get_collision_layer(), CollisionLayer.PLAYER)
        self.assertEqual(len(col.get_collision_mask()), 2)
        self.assertTrue(col.get_is_trigger())

    def test_get_bounds(self):
        """Test getting bounding box."""
        col = Collider2D(x=10.0, y=20.0, width=30.0, height=40.0)
        bounds = col.get_bounds()
        self.assertEqual(bounds, (10.0, 20.0, 40.0, 60.0))

    def test_check_collision_overlapping(self):
        """Test collision detection with overlapping colliders."""
        col1 = Collider2D(x=0.0, y=0.0, width=50.0, height=50.0)
        col2 = Collider2D(x=25.0, y=25.0, width=50.0, height=50.0)
        self.assertTrue(col1.check_collision(col2))
        self.assertTrue(col2.check_collision(col1))

    def test_check_collision_not_overlapping(self):
        """Test collision detection with non-overlapping colliders."""
        col1 = Collider2D(x=0.0, y=0.0, width=10.0, height=10.0)
        col2 = Collider2D(x=50.0, y=50.0, width=10.0, height=10.0)
        self.assertFalse(col1.check_collision(col2))
        self.assertFalse(col2.check_collision(col1))

    def test_check_collision_touching_edge(self):
        """Test collision detection with touching edges."""
        col1 = Collider2D(x=0.0, y=0.0, width=10.0, height=10.0)
        col2 = Collider2D(x=10.0, y=0.0, width=10.0, height=10.0)
        self.assertTrue(col1.check_collision(col2))

    def test_set_collider_type(self):
        """Test setting collider type."""
        col = Collider2D()
        col.set_collider_type(ColliderType.POLYGON)
        self.assertEqual(col.get_collider_type(), ColliderType.POLYGON)

    def test_set_collision_layer(self):
        """Test setting collision layer."""
        col = Collider2D()
        col.set_collision_layer(CollisionLayer.ENEMY)
        self.assertEqual(col.get_collision_layer(), CollisionLayer.ENEMY)

    def test_set_collision_mask(self):
        """Test setting collision mask."""
        col = Collider2D()
        mask = [CollisionLayer.PLAYER, CollisionLayer.PROJECTILE]
        col.set_collision_mask(mask)
        self.assertEqual(col.get_collision_mask(), mask)

    def test_set_is_trigger(self):
        """Test setting trigger flag."""
        col = Collider2D()
        col.set_is_trigger(True)
        self.assertTrue(col.get_is_trigger())

    def test_implements_icollider_protocol(self):
        """Test that Collider implements ICollider protocol."""
        col = Collider2D()
        self.assertIsInstance(col, ICollider2D)

    def test_collider_type_property(self):
        """Test collider_type property access."""
        col = Collider2D(collider_type=ColliderType.CIRCLE)
        self.assertEqual(col.collider_type, ColliderType.CIRCLE)
        col.collider_type = ColliderType.POLYGON
        self.assertEqual(col.collider_type, ColliderType.POLYGON)

    def test_collision_layer_property(self):
        """Test collision_layer property access."""
        col = Collider2D(collision_layer=CollisionLayer.PLAYER)
        self.assertEqual(col.collision_layer, CollisionLayer.PLAYER)
        col.collision_layer = CollisionLayer.ENEMY
        self.assertEqual(col.collision_layer, CollisionLayer.ENEMY)

    def test_collision_mask_property(self):
        """Test collision_mask property access."""
        mask = [CollisionLayer.TERRAIN]
        col = Collider2D(collision_mask=mask)
        self.assertEqual(col.collision_mask, mask)

    def test_is_trigger_property(self):
        """Test is_trigger property access."""
        col = Collider2D(is_trigger=True)
        self.assertTrue(col.is_trigger)
        col.is_trigger = False
        self.assertFalse(col.is_trigger)


class TestRigidBody2D(unittest.TestCase):
    """Test cases for RigidBody class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        rb = RigidBody2D()
        self.assertEqual(rb.get_mass(), 1.0)
        self.assertEqual(rb.get_inverse_mass(), 1.0)
        self.assertEqual(rb.get_moment_of_inertia(), 1.0)
        self.assertEqual(rb.get_linear_velocity(), (0.0, 0.0))
        self.assertEqual(rb.get_angular_velocity(), 0.0)

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        rb = RigidBody2D(
            mass=2.0,
            moment_of_inertia=5.0,
            velocity_x=10.0,
            velocity_y=5.0,
            angular_velocity=1.5
        )
        self.assertEqual(rb.get_mass(), 2.0)
        self.assertEqual(rb.get_inverse_mass(), 0.5)
        self.assertEqual(rb.get_moment_of_inertia(), 5.0)
        self.assertEqual(rb.get_linear_velocity(), (10.0, 5.0))
        self.assertEqual(rb.get_angular_velocity(), 1.5)

    def test_set_mass_updates_inverse_mass(self):
        """Test that setting mass updates inverse mass."""
        rb = RigidBody2D()
        rb.set_mass(4.0)
        self.assertEqual(rb.get_mass(), 4.0)
        self.assertEqual(rb.get_inverse_mass(), 0.25)

    def test_set_mass_zero_gives_zero_inverse(self):
        """Test that zero mass gives zero inverse mass."""
        rb = RigidBody2D()
        rb.set_mass(0.0)
        self.assertEqual(rb.get_inverse_mass(), 0.0)

    def test_set_mass_negative_raises_error(self):
        """Test that negative mass raises ValueError."""
        rb = RigidBody2D()
        with self.assertRaises(ValueError) as context:
            rb.set_mass(-1.0)
        self.assertIn("non-negative", str(context.exception))

    def test_set_linear_velocity(self):
        """Test setting linear velocity."""
        rb = RigidBody2D()
        rb.set_linear_velocity(20.0, 15.0)
        self.assertEqual(rb.get_linear_velocity(), (20.0, 15.0))
        rb.set_velocity_x(30.0)
        self.assertEqual(rb.get_linear_velocity(), (30.0, 15.0))
        rb.set_velocity_y(25.0)
        self.assertEqual(rb.get_linear_velocity(), (30.0, 25.0))

    def test_set_angular_velocity(self):
        """Test setting angular velocity."""
        rb = RigidBody2D()
        rb.set_angular_velocity(3.14)
        self.assertEqual(rb.get_angular_velocity(), 3.14)

    def test_set_linear_acceleration(self):
        """Test setting linear acceleration."""
        rb = RigidBody2D()
        rb.set_linear_acceleration(2.0, 3.0)
        self.assertEqual(rb.get_linear_acceleration(), (2.0, 3.0))
        rb.set_acceleration_x(4.0)
        self.assertEqual(rb.get_linear_acceleration(), (4.0, 3.0))
        rb.set_acceleration_y(5.0)
        self.assertEqual(rb.get_linear_acceleration(), (4.0, 5.0))

    def test_apply_force(self):
        """Test applying force accumulates."""
        rb = RigidBody2D()
        rb.apply_force(10.0, 5.0)
        self.assertEqual(rb.get_force(), (10.0, 5.0))

        rb.apply_force(5.0, 10.0)
        self.assertEqual(rb.get_force(), (15.0, 15.0))

    def test_apply_impulse(self):
        """Test applying impulse changes velocity."""
        rb = RigidBody2D(mass=2.0)
        rb.apply_impulse(10.0, 20.0)
        # impulse / mass = velocity change
        # 10.0 / 2.0 = 5.0, 20.0 / 2.0 = 10.0
        self.assertEqual(rb.get_linear_velocity(), (5.0, 10.0))

    def test_apply_impulse_zero_inverse_mass(self):
        """Test applying impulse with zero inverse mass does nothing."""
        rb = RigidBody2D(mass=0.0)
        rb.apply_impulse(10.0, 20.0)
        self.assertEqual(rb.get_linear_velocity(), (0.0, 0.0))

    def test_apply_torque(self):
        """Test applying torque accumulates."""
        rb = RigidBody2D()
        rb.apply_torque(5.0)
        self.assertEqual(rb.get_torque(), 5.0)

        rb.apply_torque(3.0)
        self.assertEqual(rb.get_torque(), 8.0)

    def test_clear_forces(self):
        """Test clearing forces resets to zero."""
        rb = RigidBody2D()
        rb.apply_force(10.0, 20.0)
        rb.apply_torque(5.0)

        rb.clear_forces()
        self.assertEqual(rb.get_force(), (0.0, 0.0))
        self.assertEqual(rb.get_torque(), 0.0)

    def test_set_force(self):
        """Test setting force directly."""
        rb = RigidBody2D()
        rb.set_force(100.0, 200.0)
        self.assertEqual(rb.get_force(), (100.0, 200.0))

    def test_set_torque(self):
        """Test setting torque directly."""
        rb = RigidBody2D()
        rb.set_torque(50.0)
        self.assertEqual(rb.get_torque(), 50.0)

    def test_implements_irigidbody_protocol(self):
        """Test that RigidBody implements IRigidBody protocol."""
        rb = RigidBody2D()
        self.assertIsInstance(rb, IRigidBody2D)

    def test_mass_property(self):
        """Test mass property access."""
        rb = RigidBody2D(mass=3.0)
        self.assertEqual(rb.mass, 3.0)
        rb.mass = 5.0
        self.assertEqual(rb.mass, 5.0)

    def test_angular_velocity_property(self):
        """Test angular_velocity property access."""
        rb = RigidBody2D(angular_velocity=2.0)
        self.assertEqual(rb.angular_velocity, 2.0)
        rb.angular_velocity = 3.0
        self.assertEqual(rb.angular_velocity, 3.0)


class TestPhysicsBody(unittest.TestCase):
    """Test cases for PhysicsBody class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        pb = PhysicsBody2D()
        self.assertEqual(pb.get_body_type(), BodyType.DYNAMIC)
        self.assertTrue(pb.get_enabled())
        self.assertFalse(pb.get_sleeping())
        self.assertEqual(pb.get_mass(), 1.0)
        self.assertEqual(pb.get_collider_type(), ColliderType.RECTANGLE)

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        mat = Material(density=2.0, restitution=0.9)
        pb = PhysicsBody2D(
            body_type=BodyType.STATIC,
            enabled=False,
            sleeping=True,
            mass=5.0,
            x=100.0,
            y=200.0,
            width=50.0,
            height=75.0,
            collision_layer=CollisionLayer.TERRAIN,
            material=mat
        )
        self.assertEqual(pb.get_body_type(), BodyType.STATIC)
        self.assertFalse(pb.get_enabled())
        self.assertTrue(pb.get_sleeping())
        self.assertEqual(pb.get_mass(), 5.0)
        self.assertEqual(pb.x, 100.0)
        self.assertEqual(pb.y, 200.0)
        self.assertEqual(pb.get_restitution(), 0.9)

    def test_set_body_type_static_updates_inverse_mass(self):
        """Test that setting body type to STATIC zeros inverse mass."""
        pb = PhysicsBody2D(mass=2.0)
        self.assertEqual(pb.get_inverse_mass(), 0.5)

        pb.set_body_type(BodyType.STATIC)
        self.assertEqual(pb.get_inverse_mass(), 0.0)

    def test_init_body_type_static_sets_inverse_mass_zero(self):
        """Test that initializing with STATIC body type sets inverse mass to zero."""
        pb = PhysicsBody2D(mass=3.0, body_type=BodyType.STATIC)
        self.assertEqual(pb.get_inverse_mass(), 0.0)

    def test_set_body_type_dynamic_restores_inverse_mass(self):
        """Test that setting body type to DYNAMIC restores inverse mass."""
        pb = PhysicsBody2D(mass=2.0, body_type=BodyType.STATIC)
        self.assertEqual(pb.get_inverse_mass(), 0.0)

        pb.set_body_type(BodyType.DYNAMIC)
        self.assertEqual(pb.get_inverse_mass(), 0.5)

    def test_delegates_to_rigid_body(self):
        """Test that PhysicsBody delegates rigid body methods."""
        pb = PhysicsBody2D()
        pb.set_mass(3.0)
        self.assertEqual(pb.get_mass(), 3.0)

        pb.set_linear_velocity(10.0, 20.0)
        self.assertEqual(pb.get_linear_velocity(), (10.0, 20.0))

        pb.apply_force(5.0, 10.0)
        self.assertEqual(pb.get_force(), (5.0, 10.0))

    def test_delegates_to_collider(self):
        """Test that PhysicsBody delegates collider methods."""
        pb = PhysicsBody2D()
        pb.set_collision_layer(CollisionLayer.PLAYER)
        self.assertEqual(pb.get_collision_layer(), CollisionLayer.PLAYER)

        pb.set_is_trigger(True)
        self.assertTrue(pb.get_is_trigger())

    def test_delegates_to_material(self):
        """Test that PhysicsBody delegates material methods."""
        pb = PhysicsBody2D()
        pb.set_restitution(0.8)
        self.assertEqual(pb.get_restitution(), 0.8)

        pb.set_friction(0.6)
        self.assertEqual(pb.get_friction(), 0.6)

    def test_position_updates_collider(self):
        """Test that updating position updates collider bounds."""
        pb = PhysicsBody2D(x=0.0, y=0.0, width=10.0, height=10.0)
        self.assertEqual(pb.get_bounds(), (0.0, 0.0, 10.0, 10.0))

        pb.x = 50.0
        pb.y = 100.0
        self.assertEqual(pb.get_bounds(), (50.0, 100.0, 60.0, 110.0))

    def test_collision_detection(self):
        """Test collision detection between physics bodies."""
        pb1 = PhysicsBody2D(x=0.0, y=0.0, width=50.0, height=50.0)
        pb2 = PhysicsBody2D(x=25.0, y=25.0, width=50.0, height=50.0)
        pb3 = PhysicsBody2D(x=100.0, y=100.0, width=50.0, height=50.0)

        self.assertTrue(pb1.check_collision(pb2))
        self.assertFalse(pb1.check_collision(pb3))

    def test_update_method_exists(self):
        """Test that update method exists and is callable."""
        pb = PhysicsBody2D()
        self.assertTrue(hasattr(pb, 'update'))
        self.assertTrue(callable(pb.update))
        pb.update(0.016)  # Should not raise

    def test_collision_callbacks_exist(self):
        """Test that collision callback methods exist."""
        pb = PhysicsBody2D()
        self.assertTrue(hasattr(pb, 'on_collision_enter'))
        self.assertTrue(hasattr(pb, 'on_collision_stay'))
        self.assertTrue(hasattr(pb, 'on_collision_exit'))

    def test_implements_iphysicsbody_protocol(self):
        """Test that PhysicsBody implements IPhysicsBody protocol."""
        pb = PhysicsBody2D()
        self.assertIsInstance(pb, IPhysicsBody2D)

    def test_implements_all_component_protocols(self):
        """Test that PhysicsBody implements all component protocols."""
        pb = PhysicsBody2D()
        self.assertIsInstance(pb, IRigidBody2D)
        self.assertIsInstance(pb, ICollider2D)
        self.assertIsInstance(pb, IMaterial)

    def test_body_type_property(self):
        """Test body_type property access."""
        pb = PhysicsBody2D(body_type=BodyType.KINEMATIC)
        self.assertEqual(pb.body_type, BodyType.KINEMATIC)
        pb.set_body_type(BodyType.STATIC)
        self.assertEqual(pb.body_type, BodyType.STATIC)

    def test_enabled_property(self):
        """Test enabled property access."""
        pb = PhysicsBody2D(enabled=False)
        self.assertFalse(pb.enabled)
        pb.set_enabled(True)
        self.assertTrue(pb.enabled)

    def test_sleeping_property(self):
        """Test sleeping property access."""
        pb = PhysicsBody2D(sleeping=True)
        self.assertTrue(pb.sleeping)
        pb.set_sleeping(False)
        self.assertFalse(pb.sleeping)


class TestIntegration(unittest.TestCase):
    """Integration tests for physics components working together."""

    def test_material_affects_physics_body(self):
        """Test that material properties affect physics body behavior."""
        rubber = Material(restitution=0.9, friction=0.3)
        steel = Material(restitution=0.2, friction=0.7)

        ball1 = PhysicsBody2D(material=rubber)
        ball2 = PhysicsBody2D(material=steel)

        self.assertEqual(ball1.restitution, 0.9)
        self.assertEqual(ball2.restitution, 0.2)
        self.assertEqual(ball1.friction, 0.3)
        self.assertEqual(ball2.friction, 0.7)

    def test_collision_layers_interaction(self):
        """Test collision layer and mask interaction."""
        player = PhysicsBody2D(
            collision_layer=CollisionLayer.PLAYER,
            collision_mask=[CollisionLayer.TERRAIN, CollisionLayer.ENEMY]
        )

        _ = PhysicsBody2D(collision_layer=CollisionLayer.TERRAIN)
        _ = PhysicsBody2D(collision_layer=CollisionLayer.ENEMY)
        _ = PhysicsBody2D(collision_layer=CollisionLayer.TRANSPARENT)

        self.assertIn(CollisionLayer.TERRAIN, player.collision_mask)
        self.assertIn(CollisionLayer.ENEMY, player.collision_mask)
        self.assertNotIn(CollisionLayer.TRANSPARENT, player.collision_mask)

    def test_force_accumulation_and_clearing(self):
        """Test force accumulation and clearing cycle."""
        body = PhysicsBody2D()

        # Apply multiple forces
        body.apply_force(10.0, 5.0)
        body.apply_force(5.0, 10.0)
        body.apply_torque(2.0)
        body.apply_torque(3.0)

        self.assertEqual(body.force, (15.0, 15.0))
        self.assertEqual(body.get_torque(), 5.0)

        # Clear forces
        body.clear_forces()
        self.assertEqual(body.force, (0.0, 0.0))
        self.assertEqual(body.get_torque(), 0.0)

    def test_impulse_changes_velocity_based_on_mass(self):
        """Test that impulse effect depends on mass."""
        light = PhysicsBody2D(mass=1.0)
        heavy = PhysicsBody2D(mass=10.0)

        light.apply_impulse(10.0, 0.0)
        heavy.apply_impulse(10.0, 0.0)

        # Same impulse, different mass = different velocity change
        self.assertEqual(light.linear_velocity, (10.0, 0.0))
        self.assertEqual(heavy.linear_velocity, (1.0, 0.0))


if __name__ == '__main__':
    unittest.main()
