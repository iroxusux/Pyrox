"""Physics engine service for runtime simulation.

Main orchestrator for physics simulation, managing bodies, collisions,
and integration with fixed timestep updates.
"""
from typing import List
from pyrox.interfaces.protocols.physics import IPhysicsBody2D, IPhysicsEngine, BodyType
from pyrox.services.environment import EnvironmentService
from pyrox.services.collision import CollisionService


class PhysicsEngineService(IPhysicsEngine):
    """Main physics simulation engine.

    Coordinates physics updates using a fixed timestep approach with
    accumulator for frame-rate independent physics.

    Features:
    - Fixed timestep physics (prevents tunneling and ensures consistency)
    - Environment configuration (gravity, drag, etc.)
    - Collision detection and response
    - Sleep optimization for stationary objects
    - Time scaling for slow-motion/fast-forward effects

    Attributes:
        environment: EnvironmentService for physics constants
        collision: CollisionService for collision detection
        bodies: List of registered physics bodies
    """

    def __init__(
        self,
        environment: EnvironmentService | None = None,
        collision: CollisionService | None = None,
        physics_step: float = 1.0 / 60.0,  # 60 Hz physics
    ):
        """Initialize the physics engine.

        Args:
            environment: EnvironmentService instance (creates default if None)
            collision: CollisionService instance (creates default if None)
            physics_step: Fixed physics timestep in seconds
        """
        self._environment = environment or EnvironmentService()
        self._collision = collision or CollisionService()
        self._bodies: List[IPhysicsBody2D] = []

        # Fixed timestep parameters
        self._physics_step = physics_step
        self._accumulator = 0.0
        self._time_scale = 1.0

        # Performance tracking
        self._total_time = 0.0
        self._step_count = 0

    @property
    def environment(self) -> EnvironmentService:
        """Get the environment service."""
        return self._environment

    @property
    def collision(self) -> CollisionService:
        """Get the collision service."""
        return self._collision

    @property
    def bodies(self) -> List[IPhysicsBody2D]:
        """Get list of registered bodies."""
        return self._bodies.copy()

    # IPhysicsEngine protocol implementation

    def get_gravity(self) -> tuple[float, float]:
        """Get global gravity vector."""
        return self._environment.gravity

    def set_gravity(self, gx: float, gy: float) -> None:
        """Set global gravity vector."""
        self._environment.gravity = (gx, gy)

    def get_time_scale(self) -> float:
        """Get time scale multiplier."""
        return self._time_scale

    def set_time_scale(self, value: float) -> None:
        """Set time scale multiplier."""
        if value < 0:
            raise ValueError("Time scale must be non-negative")
        self._time_scale = value

    def get_physics_step(self) -> float:
        """Get fixed physics timestep."""
        return self._physics_step

    def set_physics_step(self, value: float) -> None:
        """Set fixed physics timestep."""
        if value <= 0:
            raise ValueError("Physics step must be positive")
        self._physics_step = value

    def register_body(self, body: IPhysicsBody2D) -> None:
        """Register a physics body with the engine.

        Args:
            body: The physics body to register
        """
        if not isinstance(body, IPhysicsBody2D):
            raise TypeError("Body must implement IPhysicsBody2D protocol")

        if body not in self._bodies:
            self._bodies.append(body)
            self._collision.register_body(body)

    def unregister_body(self, body: IPhysicsBody2D) -> None:
        """Remove a physics body from the engine.

        Args:
            body: The physics body to unregister
        """
        if body in self._bodies:
            self._bodies.remove(body)
            self._collision.unregister_body(body)

    def step(self, dt: float) -> None:
        """Advance physics simulation by dt seconds.

        Uses fixed timestep with accumulator to ensure consistent physics
        regardless of frame rate.

        Args:
            dt: Delta time in seconds (variable, from frame rate)
        """
        # Apply time scale
        dt *= self._time_scale

        # Add to accumulator
        self._accumulator += dt

        # Execute fixed timesteps
        steps_this_frame = 0
        max_steps = 10  # Prevent spiral of death

        while self._accumulator >= self._physics_step and steps_this_frame < max_steps:
            self._fixed_step(self._physics_step)
            self._accumulator -= self._physics_step
            steps_this_frame += 1
            self._step_count += 1

        # If we hit max steps, reset accumulator to prevent falling behind
        if steps_this_frame >= max_steps:
            self._accumulator = 0.0

    def _fixed_step(self, dt: float) -> None:
        """Perform one fixed timestep of physics simulation.

        Args:
            dt: Fixed timestep duration in seconds
        """
        # 1. Apply forces (gravity, drag)
        self._apply_forces(dt)

        # 2. Integrate velocities and update positions
        self._integrate(dt)

        # 3. Update spatial grid for collision detection
        self._collision.update_spatial_grid()

        # 4. Detect collisions
        collisions = self._collision.detect_collisions()

        # 5. Resolve collisions
        for collision in collisions:
            self._collision.resolve_collision(collision, self._environment)

        # 6. Call update on each body (for custom behavior)
        for body in self._bodies:
            if body.enabled and not body.sleeping:
                body.update(dt)

        # 7. Check for sleeping bodies
        self._update_sleep_state()

        self._total_time += dt

    def _apply_forces(self, dt: float) -> None:
        """Apply environmental forces to all bodies.

        Args:
            dt: Timestep duration in seconds
        """
        gx, gy = self._environment.gravity

        for body in self._bodies:
            if not body.enabled or body.sleeping:
                continue

            # Only apply forces to dynamic bodies
            if body.body_type != BodyType.DYNAMIC:
                continue

            # Apply gravity
            body.apply_force(gx * body.mass, gy * body.mass)

            # Apply drag (with clamping to prevent velocity reversal)
            vx, vy = body.linear_velocity
            drag_coef = body.material.drag

            # Scale area to reasonable physical units (game units -> m²)
            # Assuming game units are roughly pixels, 100 pixels ≈ 1 meter
            # So area needs to be scaled down by 100² = 10,000
            area_scale_factor = 0.0001  # Converts pixel² to m²
            area = body.width * body.height * area_scale_factor

            drag_x, drag_y = self._environment.apply_drag_force((vx, vy), drag_coef, area)

            # CRITICAL: Clamp drag force to prevent overcorrection
            # Drag should never reverse velocity direction in a single timestep
            # Maximum drag impulse = mass * velocity (to bring to zero)
            if body.inverse_mass > 0:  # Only clamp for finite mass
                max_impulse_x = abs(body.mass * vx / dt) if dt > 0 else float('inf')
                max_impulse_y = abs(body.mass * vy / dt) if dt > 0 else float('inf')

                # Clamp drag force magnitude per axis
                if abs(drag_x) > max_impulse_x:
                    drag_x = -max_impulse_x if vx > 0 else max_impulse_x
                if abs(drag_y) > max_impulse_y:
                    drag_y = -max_impulse_y if vy > 0 else max_impulse_y

            body.apply_force(drag_x, drag_y)

    def _integrate(self, dt: float) -> None:
        """Integrate velocities and update positions.

        Uses semi-implicit Euler integration (velocity first, then position).

        Args:
            dt: Timestep duration in seconds
        """
        for body in self._bodies:
            if not body.enabled or body.sleeping:
                continue

            body_type = body.body_type

            # Only integrate dynamic bodies
            if body_type != BodyType.DYNAMIC:
                # Kinematic bodies move but don't respond to forces
                if body_type == BodyType.KINEMATIC:
                    vx, vy = body.linear_velocity
                    body.x += vx * dt
                    body.y += vy * dt
                continue

            # Integrate forces -> acceleration -> velocity
            fx, fy = body.force

            if body.inverse_mass > 0:  # Skip if infinite mass
                # 1. Calculate acceleration from forces (F = ma, so a = F/m)
                ax = fx * body.inverse_mass
                ay = fy * body.inverse_mass

                # 2. Store acceleration in body for external access
                body.set_linear_acceleration(ax, ay)

                # 3. Update velocity from acceleration (semi-implicit Euler)
                vx, vy = body.linear_velocity
                vx += ax * dt
                vy += ay * dt

                # 4. Clamp to terminal velocity
                speed = (vx**2 + vy**2)**0.5
                if speed > self._environment.terminal_velocity:
                    scale = self._environment.terminal_velocity / speed
                    vx *= scale
                    vy *= scale

                # 5. Apply linear damping (ground friction/rolling resistance)
                # Reduces velocity by a fixed percentage per second
                # This simulates surface friction separate from air drag
                linear_damping = self._environment.linear_damping
                damping_factor = linear_damping ** dt  # Apply per timestep
                vx *= damping_factor
                vy *= damping_factor

                # 6. Apply velocity threshold to prevent infinite asymptotic decay
                # If velocity is very small, snap to zero (concrete-like stop)
                velocity_threshold = self._environment.velocity_threshold
                if abs(vx) < velocity_threshold:
                    vx = 0.0
                if abs(vy) < velocity_threshold:
                    vy = 0.0

                # 7. Store new velocity
                body.set_linear_velocity(vx, vy)

                # 8. Clear forces for next step
                body.clear_forces()
            else:
                # Zero acceleration for infinite mass bodies
                body.set_linear_acceleration(0.0, 0.0)
                # IMPORTANT: Clear forces even when mass is 0 to prevent accumulation
                # If forces aren't cleared, they accumulate and cause massive spikes
                # when mass changes from 0 to non-zero
                body.clear_forces()

            # Integrate velocity -> position
            vx, vy = body.linear_velocity
            body.x += vx * dt
            body.y += vy * dt

            # Integrate torque -> angular acceleration -> angular velocity -> rotation
            if hasattr(body, 'torque') and hasattr(body, 'moment_of_inertia'):
                torque = body.torque
                moi = body.moment_of_inertia

                if moi > 0:
                    # Angular acceleration = Torque / Moment of Inertia
                    angular_accel = torque / moi

                    # Update angular velocity
                    angular_vel = body.angular_velocity
                    angular_vel += angular_accel * dt
                    body.set_angular_velocity(angular_vel)

                    # Update rotation
                    body.roll += angular_vel * dt
                else:
                    # No moment of inertia - just update rotation from current velocity
                    angular_vel = body.angular_velocity
                    body.roll += angular_vel * dt
            else:
                # Fallback for bodies without torque support
                angular_vel = body.angular_velocity
                body.roll += angular_vel * dt

    def _update_sleep_state(self) -> None:
        """Update sleep state for bodies to optimize performance.

        Bodies with velocity below threshold for extended time can sleep
        to skip physics calculations.
        """
        threshold = self._environment.sleep_threshold

        for body in self._bodies:
            if not body.enabled:
                continue

            # Only dynamic bodies can sleep
            body_type = body.body_type
            if body_type != BodyType.DYNAMIC:
                continue

            # Check velocity
            vx, vy = body.linear_velocity
            speed = (vx**2 + vy**2)**0.5

            if speed < threshold:
                # Could add timer here to sleep after N frames below threshold
                pass  # For now, don't auto-sleep
            else:
                # Wake up if moving
                body.set_sleeping(False)

    def reset(self) -> None:
        """Reset the physics engine to initial state."""
        self._accumulator = 0.0
        self._total_time = 0.0
        self._step_count = 0

        # Clear forces on all bodies
        for body in self._bodies:
            body.clear_forces()

    def clear(self) -> None:
        """Remove all bodies and reset the engine."""
        self._bodies.clear()
        self._collision.clear()
        self.reset()

    # Additional utility methods

    def get_stats(self) -> dict:
        """Get physics engine statistics.

        Returns:
            Dictionary with engine statistics
        """
        return {
            'total_time': self._total_time,
            'step_count': self._step_count,
            'body_count': len(self._bodies),
            'active_bodies': sum(1 for b in self._bodies if b.enabled and not b.sleeping),
            'physics_step': self._physics_step,
            'time_scale': self._time_scale,
            'accumulator': self._accumulator,
        }

    def query_bodies_at_point(self, x: float, y: float) -> List[IPhysicsBody2D]:
        """Find all bodies at a given point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of bodies containing the point
        """
        result = []
        for body in self._bodies:
            min_x, min_y, max_x, max_y = body.get_bounds()
            if min_x <= x <= max_x and min_y <= y <= max_y:
                result.append(body)
        return result

    def query_bodies_in_area(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[IPhysicsBody2D]:
        """Find all bodies overlapping an area.

        Args:
            min_x: Minimum X coordinate
            min_y: Minimum Y coordinate
            max_x: Maximum X coordinate
            max_y: Maximum Y coordinate

        Returns:
            List of bodies overlapping the area
        """
        result = []
        for body in self._bodies:
            bmin_x, bmin_y, bmax_x, bmax_y = body.get_bounds()
            # Check AABB overlap
            if bmax_x >= min_x and bmin_x <= max_x and bmax_y >= min_y and bmin_y <= max_y:
                result.append(body)
        return result
