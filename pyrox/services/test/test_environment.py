"""Unit tests for environment service."""

import unittest

from pyrox.services.environment import (
    EnvironmentPreset,
    EnvironmentService,
)


class TestEnvironmentPreset(unittest.TestCase):
    """Test cases for EnvironmentPreset dataclass."""

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        preset = EnvironmentPreset(
            name='Test',
            gravity=(0.0, -9.81),
            air_density=1.225,
            default_friction=0.5,
            default_restitution=0.3,
            description='Test preset'
        )

        self.assertEqual(preset.name, 'Test')
        self.assertEqual(preset.gravity, (0.0, -9.81))
        self.assertEqual(preset.air_density, 1.225)
        self.assertEqual(preset.default_friction, 0.5)
        self.assertEqual(preset.default_restitution, 0.3)
        self.assertEqual(preset.description, 'Test preset')

    def test_init_without_description(self):
        """Test initialization without description (default empty string)."""
        preset = EnvironmentPreset(
            name='Test',
            gravity=(0.0, 0.0),
            air_density=1.0,
            default_friction=0.5,
            default_restitution=0.3
        )

        self.assertEqual(preset.description, '')


class TestEnvironmentService(unittest.TestCase):
    """Test cases for EnvironmentService class."""

    def test_init_with_default_preset(self):
        """Test initialization with default 'earth' preset."""
        env = EnvironmentService()

        self.assertEqual(env.gravity, (0.0, -9.81))
        self.assertEqual(env.air_density, 1.225)
        self.assertEqual(env.default_friction, 0.5)
        self.assertEqual(env.default_restitution, 0.3)

    def test_init_with_earth_preset(self):
        """Test initialization with earth preset."""
        env = EnvironmentService(preset='earth')

        self.assertEqual(env.gravity, (0.0, -9.81))
        self.assertAlmostEqual(env.air_density, 1.225)
        self.assertEqual(env.default_friction, 0.5)
        self.assertEqual(env.default_restitution, 0.3)

    def test_init_with_space_preset(self):
        """Test initialization with space preset."""
        env = EnvironmentService(preset='space')

        self.assertEqual(env.gravity, (0.0, 0.0))
        self.assertEqual(env.air_density, 0.0)
        self.assertEqual(env.default_friction, 0.0)
        self.assertEqual(env.default_restitution, 0.9)

    def test_init_with_moon_preset(self):
        """Test initialization with moon preset."""
        env = EnvironmentService(preset='moon')

        self.assertEqual(env.gravity, (0.0, -1.62))
        self.assertEqual(env.air_density, 0.0)
        self.assertEqual(env.default_friction, 0.3)
        self.assertEqual(env.default_restitution, 0.4)

    def test_init_with_underwater_preset(self):
        """Test initialization with underwater preset."""
        env = EnvironmentService(preset='underwater')

        self.assertEqual(env.gravity, (0.0, -9.81))
        self.assertEqual(env.air_density, 1000.0)
        self.assertEqual(env.default_friction, 0.8)
        self.assertEqual(env.default_restitution, 0.1)

    def test_init_with_platformer_preset(self):
        """Test initialization with platformer preset."""
        env = EnvironmentService(preset='platformer')

        self.assertEqual(env.gravity, (0.0, -20.0))
        self.assertEqual(env.air_density, 0.5)
        self.assertEqual(env.default_friction, 0.6)
        self.assertEqual(env.default_restitution, 0.0)

    def test_init_with_top_down_preset(self):
        """Test initialization with top_down preset."""
        env = EnvironmentService(preset='top_down')

        self.assertEqual(env.gravity, (0.0, 0.0))
        self.assertEqual(env.air_density, 2.0)
        self.assertEqual(env.default_friction, 0.7)
        self.assertEqual(env.default_restitution, 0.2)

    def test_init_with_invalid_preset_raises_error(self):
        """Test that invalid preset raises ValueError."""
        with self.assertRaises(ValueError) as context:
            EnvironmentService(preset='invalid')

        self.assertIn("Unknown preset", str(context.exception))
        self.assertIn("invalid", str(context.exception))

    def test_init_with_custom_gravity(self):
        """Test initialization with custom gravity overriding preset."""
        env = EnvironmentService(preset='earth', gravity=(5.0, -15.0))

        self.assertEqual(env.gravity, (5.0, -15.0))
        # Other preset values should remain
        self.assertEqual(env.air_density, 1.225)

    def test_init_with_custom_air_density(self):
        """Test initialization with custom air density."""
        env = EnvironmentService(preset='earth', air_density=2.5)

        self.assertEqual(env.air_density, 2.5)
        self.assertEqual(env.gravity, (0.0, -9.81))

    def test_init_with_custom_friction(self):
        """Test initialization with custom friction."""
        env = EnvironmentService(preset='earth', default_friction=0.8)

        self.assertEqual(env.default_friction, 0.8)

    def test_init_with_custom_restitution(self):
        """Test initialization with custom restitution."""
        env = EnvironmentService(preset='earth', default_restitution=0.9)

        self.assertEqual(env.default_restitution, 0.9)

    def test_init_with_all_custom_params(self):
        """Test initialization with all custom parameters."""
        env = EnvironmentService(
            preset='earth',
            gravity=(1.0, -2.0),
            air_density=3.0,
            default_friction=0.4,
            default_restitution=0.6
        )

        self.assertEqual(env.gravity, (1.0, -2.0))
        self.assertEqual(env.air_density, 3.0)
        self.assertEqual(env.default_friction, 0.4)
        self.assertEqual(env.default_restitution, 0.6)

    def test_gravity_property_getter(self):
        """Test gravity property getter."""
        env = EnvironmentService()
        gravity = env.gravity

        self.assertIsInstance(gravity, tuple)
        self.assertEqual(len(gravity), 2)

    def test_gravity_property_setter(self):
        """Test gravity property setter."""
        env = EnvironmentService()
        env.gravity = (10.0, -20.0)

        self.assertEqual(env.gravity, (10.0, -20.0))

    def test_air_density_property_getter(self):
        """Test air density property getter."""
        env = EnvironmentService()
        density = env.air_density

        self.assertIsInstance(density, float)

    def test_air_density_property_setter(self):
        """Test air density property setter."""
        env = EnvironmentService()
        env.air_density = 5.0

        self.assertEqual(env.air_density, 5.0)

    def test_air_density_negative_raises_error(self):
        """Test that negative air density raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.air_density = -1.0

        self.assertIn("non-negative", str(context.exception))

    def test_default_friction_property_getter(self):
        """Test default friction property getter."""
        env = EnvironmentService()
        friction = env.default_friction

        self.assertIsInstance(friction, float)

    def test_default_friction_property_setter(self):
        """Test default friction property setter."""
        env = EnvironmentService()
        env.default_friction = 0.7

        self.assertEqual(env.default_friction, 0.7)

    def test_default_friction_out_of_range_raises_error(self):
        """Test that friction outside [0.0, 1.0] raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.default_friction = 1.5

        self.assertIn("between 0.0 and 1.0", str(context.exception))

        with self.assertRaises(ValueError):
            env.default_friction = -0.1

    def test_default_restitution_property_getter(self):
        """Test default restitution property getter."""
        env = EnvironmentService()
        restitution = env.default_restitution

        self.assertIsInstance(restitution, float)

    def test_default_restitution_property_setter(self):
        """Test default restitution property setter."""
        env = EnvironmentService()
        env.default_restitution = 0.8

        self.assertEqual(env.default_restitution, 0.8)

    def test_default_restitution_out_of_range_raises_error(self):
        """Test that restitution outside [0.0, 1.0] raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.default_restitution = 1.5

        self.assertIn("between 0.0 and 1.0", str(context.exception))

        with self.assertRaises(ValueError):
            env.default_restitution = -0.1

    def test_terminal_velocity_property_getter(self):
        """Test terminal velocity property getter."""
        env = EnvironmentService()
        terminal_vel = env.terminal_velocity

        self.assertIsInstance(terminal_vel, float)
        self.assertEqual(terminal_vel, 200.0)

    def test_terminal_velocity_property_setter(self):
        """Test terminal velocity property setter."""
        env = EnvironmentService()
        env.terminal_velocity = 150.0

        self.assertEqual(env.terminal_velocity, 150.0)

    def test_terminal_velocity_zero_or_negative_raises_error(self):
        """Test that non-positive terminal velocity raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.terminal_velocity = 0.0

        self.assertIn("must be positive", str(context.exception))

        with self.assertRaises(ValueError):
            env.terminal_velocity = -100.0

    def test_sleep_threshold_property_getter(self):
        """Test sleep threshold property getter."""
        env = EnvironmentService()
        threshold = env.sleep_threshold

        self.assertIsInstance(threshold, float)
        self.assertEqual(threshold, 0.01)

    def test_sleep_threshold_property_setter(self):
        """Test sleep threshold property setter."""
        env = EnvironmentService()
        env.sleep_threshold = 0.05

        self.assertEqual(env.sleep_threshold, 0.05)

    def test_sleep_threshold_negative_raises_error(self):
        """Test that negative sleep threshold raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.sleep_threshold = -0.01

        self.assertIn("non-negative", str(context.exception))

    def test_collision_iterations_property_getter(self):
        """Test collision iterations property getter."""
        env = EnvironmentService()
        iterations = env.collision_iterations

        self.assertIsInstance(iterations, int)
        self.assertEqual(iterations, 8)

    def test_collision_iterations_property_setter(self):
        """Test collision iterations property setter."""
        env = EnvironmentService()
        env.collision_iterations = 10

        self.assertEqual(env.collision_iterations, 10)

    def test_collision_iterations_less_than_one_raises_error(self):
        """Test that collision iterations < 1 raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.collision_iterations = 0

        self.assertIn("at least 1", str(context.exception))

        with self.assertRaises(ValueError):
            env.collision_iterations = -5

    def test_apply_drag_force_zero_velocity(self):
        """Test drag force calculation with zero velocity."""
        env = EnvironmentService()
        drag = env.apply_drag_force((0.0, 0.0), drag_coefficient=0.5, area=1.0)

        self.assertEqual(drag, (0.0, 0.0))

    def test_apply_drag_force_horizontal_velocity(self):
        """Test drag force with horizontal velocity."""
        env = EnvironmentService()
        drag = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.5, area=1.0)

        # Drag should oppose motion (negative x direction)
        self.assertLess(drag[0], 0.0)
        self.assertEqual(drag[1], 0.0)

    def test_apply_drag_force_vertical_velocity(self):
        """Test drag force with vertical velocity."""
        env = EnvironmentService()
        drag = env.apply_drag_force((0.0, 20.0), drag_coefficient=0.5, area=1.0)

        # Drag should oppose motion (negative y direction)
        self.assertEqual(drag[0], 0.0)
        self.assertLess(drag[1], 0.0)

    def test_apply_drag_force_diagonal_velocity(self):
        """Test drag force with diagonal velocity."""
        env = EnvironmentService()
        drag = env.apply_drag_force((10.0, 10.0), drag_coefficient=0.5, area=1.0)

        # Both components should be negative (opposing motion)
        self.assertLess(drag[0], 0.0)
        self.assertLess(drag[1], 0.0)

    def test_apply_drag_force_increases_with_speed(self):
        """Test that drag force increases with speed."""
        env = EnvironmentService()

        drag_slow = env.apply_drag_force((5.0, 0.0), drag_coefficient=0.5, area=1.0)
        drag_fast = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.5, area=1.0)

        # Faster velocity should produce more drag
        self.assertLess(drag_fast[0], drag_slow[0])

    def test_apply_drag_force_with_different_drag_coefficients(self):
        """Test drag force with different drag coefficients."""
        env = EnvironmentService()

        drag_low = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.2, area=1.0)
        drag_high = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.8, area=1.0)

        # Higher drag coefficient should produce more drag
        self.assertLess(drag_high[0], drag_low[0])

    def test_apply_drag_force_with_different_areas(self):
        """Test drag force with different cross-sectional areas."""
        env = EnvironmentService()

        drag_small = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.5, area=0.5)
        drag_large = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.5, area=2.0)

        # Larger area should produce more drag
        self.assertLess(drag_large[0], drag_small[0])

    def test_apply_drag_force_in_space(self):
        """Test that drag is zero in space (no air density)."""
        env = EnvironmentService(preset='space')
        drag = env.apply_drag_force((100.0, 100.0), drag_coefficient=0.5, area=1.0)

        # No air density = no drag
        self.assertEqual(drag, (0.0, 0.0))

    def test_apply_drag_force_underwater(self):
        """Test drag force in underwater environment."""
        env = EnvironmentService(preset='underwater')
        drag = env.apply_drag_force((10.0, 0.0), drag_coefficient=0.5, area=1.0)

        # High water density should produce significant drag
        self.assertLess(drag[0], -100.0)  # Should be substantial

    def test_calculate_combined_friction_equal_values(self):
        """Test combined friction with equal values."""
        env = EnvironmentService()
        combined = env.calculate_combined_friction(0.5, 0.5)

        self.assertEqual(combined, 0.5)

    def test_calculate_combined_friction_different_values(self):
        """Test combined friction with different values."""
        env = EnvironmentService()
        combined = env.calculate_combined_friction(0.4, 0.9)

        # Geometric mean should be between the two values
        self.assertGreater(combined, 0.4)
        self.assertLess(combined, 0.9)
        self.assertAlmostEqual(combined, (0.4 * 0.9) ** 0.5)

    def test_calculate_combined_friction_zero_value(self):
        """Test combined friction with one zero value."""
        env = EnvironmentService()
        combined = env.calculate_combined_friction(0.0, 0.8)

        self.assertEqual(combined, 0.0)

    def test_calculate_combined_friction_both_zero(self):
        """Test combined friction with both zero."""
        env = EnvironmentService()
        combined = env.calculate_combined_friction(0.0, 0.0)

        self.assertEqual(combined, 0.0)

    def test_calculate_combined_friction_both_one(self):
        """Test combined friction with both at maximum."""
        env = EnvironmentService()
        combined = env.calculate_combined_friction(1.0, 1.0)

        self.assertEqual(combined, 1.0)

    def test_calculate_combined_restitution_equal_values(self):
        """Test combined restitution with equal values."""
        env = EnvironmentService()
        combined = env.calculate_combined_restitution(0.5, 0.5)

        self.assertEqual(combined, 0.5)

    def test_calculate_combined_restitution_different_values(self):
        """Test combined restitution uses maximum."""
        env = EnvironmentService()
        combined = env.calculate_combined_restitution(0.3, 0.8)

        # Should return the maximum value
        self.assertEqual(combined, 0.8)

    def test_calculate_combined_restitution_zero_and_nonzero(self):
        """Test combined restitution with one zero value."""
        env = EnvironmentService()
        combined = env.calculate_combined_restitution(0.0, 0.7)

        self.assertEqual(combined, 0.7)

    def test_calculate_combined_restitution_both_zero(self):
        """Test combined restitution with both zero."""
        env = EnvironmentService()
        combined = env.calculate_combined_restitution(0.0, 0.0)

        self.assertEqual(combined, 0.0)

    def test_calculate_combined_restitution_both_one(self):
        """Test combined restitution with both at maximum."""
        env = EnvironmentService()
        combined = env.calculate_combined_restitution(1.0, 1.0)

        self.assertEqual(combined, 1.0)

    def test_get_config(self):
        """Test getting configuration as dictionary."""
        env = EnvironmentService(preset='earth')
        config = env.get_config()

        self.assertIsInstance(config, dict)
        self.assertIn('gravity', config)
        self.assertIn('air_density', config)
        self.assertIn('default_friction', config)
        self.assertIn('default_restitution', config)
        self.assertIn('terminal_velocity', config)
        self.assertIn('sleep_threshold', config)
        self.assertIn('collision_iterations', config)

    def test_get_config_values(self):
        """Test that get_config returns correct values."""
        env = EnvironmentService(preset='moon')
        config = env.get_config()

        self.assertEqual(config['gravity'], (0.0, -1.62))
        self.assertEqual(config['air_density'], 0.0)
        self.assertEqual(config['default_friction'], 0.3)
        self.assertEqual(config['default_restitution'], 0.4)
        self.assertEqual(config['terminal_velocity'], 200.0)
        self.assertEqual(config['sleep_threshold'], 0.01)
        self.assertEqual(config['collision_iterations'], 8)

    def test_set_preset_earth(self):
        """Test setting preset to earth."""
        env = EnvironmentService(preset='space')
        self.assertEqual(env.gravity, (0.0, 0.0))

        env.set_preset('earth')
        self.assertEqual(env.gravity, (0.0, -9.81))
        self.assertEqual(env.air_density, 1.225)

    def test_set_preset_space(self):
        """Test setting preset to space."""
        env = EnvironmentService(preset='earth')

        env.set_preset('space')
        self.assertEqual(env.gravity, (0.0, 0.0))
        self.assertEqual(env.air_density, 0.0)

    def test_set_preset_invalid_raises_error(self):
        """Test that invalid preset name raises ValueError."""
        env = EnvironmentService()

        with self.assertRaises(ValueError) as context:
            env.set_preset('invalid_preset')

        self.assertIn("Unknown preset", str(context.exception))
        self.assertIn("invalid_preset", str(context.exception))

    def test_set_preset_changes_all_values(self):
        """Test that set_preset updates all environment values."""
        env = EnvironmentService(preset='earth')

        env.set_preset('underwater')

        self.assertEqual(env.gravity, (0.0, -9.81))
        self.assertEqual(env.air_density, 1000.0)
        self.assertEqual(env.default_friction, 0.8)
        self.assertEqual(env.default_restitution, 0.1)

    def test_list_presets_class_method(self):
        """Test list_presets class method."""
        presets = EnvironmentService.list_presets()

        self.assertIsInstance(presets, dict)
        self.assertIn('earth', presets)
        self.assertIn('space', presets)
        self.assertIn('moon', presets)
        self.assertIn('underwater', presets)
        self.assertIn('platformer', presets)
        self.assertIn('top_down', presets)

    def test_list_presets_contains_descriptions(self):
        """Test that list_presets returns descriptions."""
        presets = EnvironmentService.list_presets()

        for name, description in presets.items():
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)

    def test_all_presets_accessible(self):
        """Test that all presets can be initialized."""
        preset_names = ['earth', 'space', 'moon', 'underwater', 'platformer', 'top_down']

        for preset_name in preset_names:
            env = EnvironmentService(preset=preset_name)
            self.assertIsNotNone(env.gravity)
            self.assertIsNotNone(env.air_density)

    def test_presets_have_valid_friction_range(self):
        """Test that all presets have friction in valid range."""
        for preset_name in EnvironmentService.PRESETS.keys():
            env = EnvironmentService(preset=preset_name)
            self.assertGreaterEqual(env.default_friction, 0.0)
            self.assertLessEqual(env.default_friction, 1.0)

    def test_presets_have_valid_restitution_range(self):
        """Test that all presets have restitution in valid range."""
        for preset_name in EnvironmentService.PRESETS.keys():
            env = EnvironmentService(preset=preset_name)
            self.assertGreaterEqual(env.default_restitution, 0.0)
            self.assertLessEqual(env.default_restitution, 1.0)

    def test_presets_have_non_negative_air_density(self):
        """Test that all presets have non-negative air density."""
        for preset_name in EnvironmentService.PRESETS.keys():
            env = EnvironmentService(preset=preset_name)
            self.assertGreaterEqual(env.air_density, 0.0)


if __name__ == '__main__':
    unittest.main()
