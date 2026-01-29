"""Collision detection and response service.

Implements spatial partitioning for efficient broad-phase collision detection
and provides collision response calculations.
"""
from typing import List, Set, Tuple, Dict, Optional
from dataclasses import dataclass
from pyrox.interfaces.protocols.physics import (
    IPhysicsBody2D,
    BodyType
)


@dataclass
class CollisionInfo:
    """Information about a collision between two bodies."""
    body_a: IPhysicsBody2D
    body_b: IPhysicsBody2D
    penetration_depth: float
    normal: Tuple[float, float]  # Collision normal (points from A to B)
    contact_point: Tuple[float, float]


class SpatialGrid:
    """Spatial partitioning grid for efficient broad-phase collision detection.

    Divides the world into a grid of cells. Objects are assigned to cells based
    on their bounding box, and only objects in the same or adjacent cells are
    tested for collision.
    """

    def __init__(self, cell_size: float = 100.0):
        """Initialize the spatial grid.

        Args:
            cell_size: Size of each grid cell in world units
        """
        self.cell_size = cell_size
        self._grid: Dict[Tuple[int, int], Set[IPhysicsBody2D]] = {}

    def _get_cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid cell coordinates."""
        return (int(x // self.cell_size), int(y // self.cell_size))

    def _get_cells_for_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[Tuple[int, int]]:
        """Get all grid cells that a bounding box overlaps."""
        min_cell_x, min_cell_y = self._get_cell_coords(min_x, min_y)
        max_cell_x, max_cell_y = self._get_cell_coords(max_x, max_y)

        cells = []
        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cells.append((cx, cy))
        return cells

    def insert(self, body: IPhysicsBody2D) -> None:
        """Insert a body into the spatial grid."""
        min_x, min_y, max_x, max_y = body.get_bounds()
        cells = self._get_cells_for_bounds(min_x, min_y, max_x, max_y)

        for cell in cells:
            if cell not in self._grid:
                self._grid[cell] = set()
            self._grid[cell].add(body)

    def remove(self, body: IPhysicsBody2D) -> None:
        """Remove a body from the spatial grid."""
        for cell_bodies in self._grid.values():
            cell_bodies.discard(body)

    def query_nearby(self, body: IPhysicsBody2D) -> Set[IPhysicsBody2D]:
        """Find all bodies in cells near this body."""
        min_x, min_y, max_x, max_y = body.get_bounds()
        cells = self._get_cells_for_bounds(min_x, min_y, max_x, max_y)

        nearby = set()
        for cell in cells:
            if cell in self._grid:
                nearby.update(self._grid[cell])

        # Remove self
        nearby.discard(body)
        return nearby

    def clear(self) -> None:
        """Clear all bodies from the grid."""
        self._grid.clear()


class CollisionService:
    """Handles collision detection and response.

    Uses spatial partitioning for efficient broad-phase detection,
    then performs narrow-phase collision checks and calculates responses.
    """

    def __init__(
        self,
        cell_size: float = 100.0
    ):
        """Initialize the collision service.

        Args:
            cell_size: Size of spatial grid cells for broad-phase detection
        """
        self._spatial_grid = SpatialGrid(cell_size)
        self._registered_bodies: List[IPhysicsBody2D] = []
        self._colliding_pairs: Set[Tuple[IPhysicsBody2D, IPhysicsBody2D]] = set()

    def register_body(
        self,
        body: IPhysicsBody2D
    ) -> None:
        """Register a body for collision detection.

        Args:
            body: The physics body to register
        """
        if body not in self._registered_bodies:
            self._registered_bodies.append(body)
            self._spatial_grid.insert(body)

    def unregister_body(
        self,
        body: IPhysicsBody2D
    ) -> None:
        """Unregister a body from collision detection.

        Args:
            body: The physics body to unregister
        """
        if body in self._registered_bodies:
            self._registered_bodies.remove(body)
            self._spatial_grid.remove(body)

    def update_spatial_grid(self) -> None:
        """Rebuild the spatial grid after bodies have moved."""
        self._spatial_grid.clear()
        for body in self._registered_bodies:
            self._spatial_grid.insert(body)

    def detect_collisions(self) -> List[CollisionInfo]:
        """Detect all collisions between registered bodies.

        Returns:
            List of collision information for all detected collisions
        """
        collisions = []
        checked_pairs = set()
        current_colliding_pairs = set()

        for body in self._registered_bodies:
            # Skip disabled or sleeping bodies
            if not body.enabled or body.sleeping:
                continue

            # Get nearby bodies from spatial grid
            nearby = self._spatial_grid.query_nearby(body)

            for other in nearby:
                # Skip disabled or sleeping bodies
                if not other.enabled or other.sleeping:
                    continue

                # Create sorted pair to avoid duplicate checks
                pair = tuple(sorted([id(body), id(other)]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                # Check if collision should be tested based on layers
                if not self._should_collide(body, other):
                    continue

                # Narrow-phase collision detection
                collision_info = self._check_collision(body, other)
                if collision_info:
                    collisions.append(collision_info)
                    body_pair = (body, other)
                    current_colliding_pairs.add(body_pair)

                    # Trigger collision callbacks
                    if body_pair not in self._colliding_pairs:
                        # New collision
                        body.on_collision_enter(other)
                        other.on_collision_enter(body)
                    else:
                        # Continuing collision
                        body.on_collision_stay(other)
                        other.on_collision_stay(body)

        # Check for collisions that ended
        for body_pair in self._colliding_pairs:
            if body_pair not in current_colliding_pairs:
                body, other = body_pair
                body.on_collision_exit(other)
                other.on_collision_exit(body)

        self._colliding_pairs = current_colliding_pairs
        return collisions

    def _should_collide(
        self,
        body_a: IPhysicsBody2D,
        body_b: IPhysicsBody2D
    ) -> bool:
        """Check if two bodies should collide based on layers and masks."""

        layer_a = body_a.collider.collision_layer
        layer_b = body_b.collider.collision_layer
        mask_a = body_a.collider.collision_mask
        mask_b = body_b.collider.collision_mask

        # Check if each body's mask includes the other's layer
        a_collides_with_b = not mask_a or layer_b in mask_a
        b_collides_with_a = not mask_b or layer_a in mask_b

        return a_collides_with_b and b_collides_with_a

    def _check_collision(
        self,
        body_a: IPhysicsBody2D,
        body_b: IPhysicsBody2D
    ) -> Optional[CollisionInfo]:
        """Perform narrow-phase collision detection between two bodies.

        Returns:
            CollisionInfo if collision detected, None otherwise
        """
        # Get bounding boxes
        min_ax, min_ay, max_ax, max_ay = body_a.get_bounds()
        min_bx, min_by, max_bx, max_by = body_b.get_bounds()

        # AABB collision check
        if max_ax < min_bx or min_ax > max_bx or max_ay < min_by or min_ay > max_by:
            return None  # No collision

        # Calculate penetration depth and normal
        overlap_x = min(max_ax - min_bx, max_bx - min_ax)
        overlap_y = min(max_ay - min_by, max_by - min_ay)

        # Use smallest overlap as penetration axis
        if overlap_x < overlap_y:
            penetration = overlap_x
            normal = (1.0 if (min_ax + max_ax) < (min_bx + max_bx) else -1.0, 0.0)
        else:
            penetration = overlap_y
            normal = (0.0, 1.0 if (min_ay + max_ay) < (min_by + max_by) else -1.0)

        # Calculate contact point (center of overlap region)
        contact_x = max(min_ax, min_bx) + (min(max_ax, max_bx) - max(min_ax, min_bx)) / 2
        contact_y = max(min_ay, min_by) + (min(max_ay, max_by) - max(min_ay, min_by)) / 2

        return CollisionInfo(
            body_a=body_a,
            body_b=body_b,
            penetration_depth=penetration,
            normal=normal,
            contact_point=(contact_x, contact_y)
        )

    def resolve_collision(
        self,
        collision: CollisionInfo,
        environment
    ) -> None:
        """Resolve a collision by applying impulses.

        Args:
            collision: Information about the collision
            environment: EnvironmentService for friction/restitution calculation
        """
        body_a = collision.body_a
        body_b = collision.body_b

        # Skip if either is a trigger
        if body_a.collider.is_trigger or body_b.collider.is_trigger:
            return

        # Get body types
        type_a = body_a.body_type
        type_b = body_b.body_type

        # Static bodies don't move
        if type_a == BodyType.STATIC and type_b == BodyType.STATIC:
            return

        inv_mass_a = body_a.inverse_mass if type_a == BodyType.DYNAMIC else 0.0  # type: ignore
        inv_mass_b = body_b.inverse_mass if type_b == BodyType.DYNAMIC else 0.0  # type: ignore

        if inv_mass_a + inv_mass_b == 0:
            return  # Both infinite mass

        # Get velocities
        va_x, va_y = body_a.linear_velocity
        vb_x, vb_y = body_b.linear_velocity

        # Relative velocity
        rel_vel_x = vb_x - va_x
        rel_vel_y = vb_y - va_y

        # Velocity along collision normal
        normal_x, normal_y = collision.normal
        vel_along_normal = rel_vel_x * normal_x + rel_vel_y * normal_y

        # Don't resolve if velocities are separating
        if vel_along_normal > 0:
            return

        # Get restitution (bounciness)
        e = environment.calculate_combined_restitution(
            body_a.material.restitution,
            body_b.material.restitution
        )

        # Calculate impulse scalar
        j = -(1 + e) * vel_along_normal
        j /= (inv_mass_a + inv_mass_b)

        # Apply impulse
        impulse_x = j * normal_x
        impulse_y = j * normal_y

        body_a.apply_impulse(-impulse_x, -impulse_y)
        body_b.apply_impulse(impulse_x, impulse_y)

        # Position correction to prevent sinking
        self._correct_positions(collision, inv_mass_a, inv_mass_b)

    def _correct_positions(self, collision: CollisionInfo, inv_mass_a: float, inv_mass_b: float) -> None:
        """Correct overlapping positions to prevent sinking.

        Args:
            collision: Collision information
            inv_mass_a: Inverse mass of body A
            inv_mass_b: Inverse mass of body B
        """
        penetration = collision.penetration_depth
        normal_x, normal_y = collision.normal

        # Percentage to correct (usually 20-80%)
        correction_percent = 0.4
        # Slop to prevent jittering (usually 0.01-0.1)
        slop = 0.05

        correction = max(penetration - slop, 0.0) / (inv_mass_a + inv_mass_b) * correction_percent

        correction_x = correction * normal_x
        correction_y = correction * normal_y

        body_a = collision.body_a
        body_b = collision.body_b

        # Move bodies apart based on inverse mass ratio
        if inv_mass_a > 0:
            body_a.x -= correction_x * inv_mass_a
            body_a.y -= correction_y * inv_mass_a

        if inv_mass_b > 0:
            body_b.x += correction_x * inv_mass_b
            body_b.y += correction_y * inv_mass_b

    def clear(self) -> None:
        """Clear all registered bodies and collision state."""
        self._registered_bodies.clear()
        self._spatial_grid.clear()
        self._colliding_pairs.clear()
