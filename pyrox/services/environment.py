"""Environment service for physics world configuration.

Provides presets and configuration for environmental physics constants
like gravity, drag, and default material properties.
"""
from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class EnvironmentPreset:
    """Predefined environment configuration."""
    name: str
    gravity: Tuple[float, float]
    air_density: float
    default_friction: float
    default_restitution: float
    description: str = ""


class EnvironmentService:
    """Manages environmental physics parameters.

    Provides presets for different environments (normal, space, underwater, etc.)
    and allows custom configuration of physics constants.

    Attributes:
        gravity: Global gravity vector (gx, gy) in m/s²
        air_density: Fluid density for drag calculations in kg/m³
        default_friction: Default friction coefficient for materials
        default_restitution: Default bounciness for materials
        terminal_velocity: Maximum falling speed in m/s
    """

    # Standard environment presets
    PRESETS: Dict[str, EnvironmentPreset] = {
        'earth': EnvironmentPreset(
            name='Earth (Normal)',
            gravity=(0.0, -9.81),  # Standard earth gravity downward
            air_density=1.225,      # Sea level air density
            default_friction=0.5,
            default_restitution=0.3,
            description='Standard earth conditions'
        ),
        'space': EnvironmentPreset(
            name='Space (Zero-G)',
            gravity=(0.0, 0.0),
            air_density=0.0,
            default_friction=0.0,
            default_restitution=0.9,
            description='Zero gravity, no atmosphere'
        ),
        'moon': EnvironmentPreset(
            name='Moon',
            gravity=(0.0, -1.62),   # Moon gravity is ~1/6 of Earth
            air_density=0.0,
            default_friction=0.3,
            default_restitution=0.4,
            description='Lunar gravity, no atmosphere'
        ),
        'underwater': EnvironmentPreset(
            name='Underwater',
            gravity=(0.0, -9.81),
            air_density=1000.0,     # Water density
            default_friction=0.8,
            default_restitution=0.1,
            description='Underwater with high drag'
        ),
        'platformer': EnvironmentPreset(
            name='Platformer (Game)',
            gravity=(0.0, -20.0),   # Stronger gravity for tight platformer feel
            air_density=0.5,
            default_friction=0.6,
            default_restitution=0.0,
            description='Classic platformer physics'
        ),
        'top_down': EnvironmentPreset(
            name='Top-Down (2D)',
            gravity=(0.0, 0.0),     # No gravity for top-down games
            air_density=2.0,        # Higher drag for more friction-like movement
            default_friction=0.7,
            default_restitution=0.2,
            description='Top-down game with friction'
        ),
    }

    def __init__(
        self,
        preset: str = 'earth',
        gravity: Tuple[float, float] | None = None,
        air_density: float | None = None,
        default_friction: float | None = None,
        default_restitution: float | None = None,
    ):
        """Initialize the environment service.

        Args:
            preset: Name of preset to use. Overridden by explicit parameters.
            gravity: Custom gravity vector (gx, gy) in m/s²
            air_density: Custom air/fluid density in kg/m³
            default_friction: Custom default friction coefficient
            default_restitution: Custom default bounciness
        """
        # Load preset
        if preset not in self.PRESETS:
            raise ValueError(f"Unknown preset '{preset}'. Available: {list(self.PRESETS.keys())}")

        preset_config = self.PRESETS[preset]

        # Apply preset or custom values
        self._gravity = gravity if gravity is not None else preset_config.gravity
        self._air_density = air_density if air_density is not None else preset_config.air_density
        self._default_friction = default_friction if default_friction is not None else preset_config.default_friction
        self._default_restitution = default_restitution if default_restitution is not None else preset_config.default_restitution

        # Additional physics parameters
        self._terminal_velocity = 200.0  # m/s - prevents objects from falling infinitely fast
        self._sleep_threshold = 0.01     # m/s - objects slower than this may sleep
        self._collision_iterations = 8    # Number of constraint solver iterations

    @property
    def gravity(self) -> Tuple[float, float]:
        """Get gravity vector (gx, gy) in m/s²."""
        return self._gravity

    @gravity.setter
    def gravity(self, value: Tuple[float, float]) -> None:
        """Set gravity vector."""
        self._gravity = value

    @property
    def air_density(self) -> float:
        """Get air/fluid density in kg/m³."""
        return self._air_density

    @air_density.setter
    def air_density(self, value: float) -> None:
        """Set air/fluid density."""
        if value < 0:
            raise ValueError("Air density must be non-negative")
        self._air_density = value

    @property
    def default_friction(self) -> float:
        """Get default friction coefficient."""
        return self._default_friction

    @default_friction.setter
    def default_friction(self, value: float) -> None:
        """Set default friction coefficient."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("Friction must be between 0.0 and 1.0")
        self._default_friction = value

    @property
    def default_restitution(self) -> float:
        """Get default restitution (bounciness)."""
        return self._default_restitution

    @default_restitution.setter
    def default_restitution(self, value: float) -> None:
        """Set default restitution."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("Restitution must be between 0.0 and 1.0")
        self._default_restitution = value

    @property
    def terminal_velocity(self) -> float:
        """Get terminal velocity in m/s."""
        return self._terminal_velocity

    @terminal_velocity.setter
    def terminal_velocity(self, value: float) -> None:
        """Set terminal velocity."""
        if value <= 0:
            raise ValueError("Terminal velocity must be positive")
        self._terminal_velocity = value

    @property
    def sleep_threshold(self) -> float:
        """Get sleep threshold velocity in m/s."""
        return self._sleep_threshold

    @sleep_threshold.setter
    def sleep_threshold(self, value: float) -> None:
        """Set sleep threshold."""
        if value < 0:
            raise ValueError("Sleep threshold must be non-negative")
        self._sleep_threshold = value

    @property
    def collision_iterations(self) -> int:
        """Get number of collision solver iterations."""
        return self._collision_iterations

    @collision_iterations.setter
    def collision_iterations(self, value: int) -> None:
        """Set collision solver iterations."""
        if value < 1:
            raise ValueError("Must have at least 1 collision iteration")
        self._collision_iterations = value

    def apply_drag_force(self, velocity: Tuple[float, float], drag_coefficient: float, area: float) -> Tuple[float, float]:
        """Calculate drag force based on velocity.

        Uses the drag equation: F_drag = 0.5 * ρ * v² * C_d * A

        Args:
            velocity: Current velocity (vx, vy) in m/s
            drag_coefficient: Object's drag coefficient
            area: Cross-sectional area in m²

        Returns:
            Drag force (fx, fy) in Newtons, opposing velocity
        """
        vx, vy = velocity
        speed = (vx**2 + vy**2)**0.5

        if speed < 0.001:  # Avoid division by zero
            return (0.0, 0.0)

        # Drag magnitude
        drag_magnitude = 0.5 * self._air_density * speed * speed * drag_coefficient * area

        # Apply in opposite direction of motion
        drag_x = -drag_magnitude * (vx / speed)
        drag_y = -drag_magnitude * (vy / speed)

        return (drag_x, drag_y)

    def calculate_combined_friction(self, friction_a: float, friction_b: float) -> float:
        """Calculate combined friction between two materials.

        Uses geometric mean: μ = √(μ_a * μ_b)

        Args:
            friction_a: Friction of first material
            friction_b: Friction of second material

        Returns:
            Combined friction coefficient
        """
        return (friction_a * friction_b) ** 0.5

    def calculate_combined_restitution(self, restitution_a: float, restitution_b: float) -> float:
        """Calculate combined restitution between two materials.

        Uses maximum: e = max(e_a, e_b)
        (Most physics engines use max for more predictable bounces)

        Args:
            restitution_a: Restitution of first material
            restitution_b: Restitution of second material

        Returns:
            Combined restitution coefficient
        """
        return max(restitution_a, restitution_b)

    def get_config(self) -> Dict[str, Any]:
        """Get current environment configuration as dictionary.

        Returns:
            Dictionary with all environment parameters
        """
        return {
            'gravity': self._gravity,
            'air_density': self._air_density,
            'default_friction': self._default_friction,
            'default_restitution': self._default_restitution,
            'terminal_velocity': self._terminal_velocity,
            'sleep_threshold': self._sleep_threshold,
            'collision_iterations': self._collision_iterations,
        }

    def set_preset(self, preset_name: str) -> None:
        """Apply a preset configuration.

        Args:
            preset_name: Name of preset to apply
        """
        if preset_name not in self.PRESETS:
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(self.PRESETS.keys())}")

        preset = self.PRESETS[preset_name]
        self._gravity = preset.gravity
        self._air_density = preset.air_density
        self._default_friction = preset.default_friction
        self._default_restitution = preset.default_restitution

    @classmethod
    def list_presets(cls) -> Dict[str, str]:
        """Get list of available presets with descriptions.

        Returns:
            Dictionary mapping preset names to descriptions
        """
        return {name: preset.description for name, preset in cls.PRESETS.items()}
