"""
Interface for design-locked composite scene objects (Type 2 grouping).

A CompositeSceneObject is the sole scene-registered object.  Its children
(components) are owned internally and are stored with relative offsets from
the composite's origin.  Components cannot be extracted or ungrouped —
the composition is intentional by design (e.g. a control panel with buttons).
"""
from abc import abstractmethod
from pyrox.interfaces.enums import CardinalDirection
from pyrox.interfaces.scene.sceneobject import ISceneObject


class ICompositeSceneObject(ISceneObject):
    """A design-locked scene object that owns child components at fixed offsets.

    The composite itself is the only object registered in the Scene.
    Each component is positioned relative to the composite's origin:

        world_x = composite.x + component_offset_x
        world_y = composite.y + component_offset_y

    Components are not independently selectable or movable by the user.
    Events (clicks, updates) are dispatched to the appropriate component
    by the composite.
    """

    # ------------------------------------------------------------------
    # Overloads
    # ------------------------------------------------------------------

    def set_direction(self, direction: CardinalDirection | str | int | None) -> None:
        parsed = CardinalDirection.try_parse(direction) if direction is not None else None
        if self._direction == parsed:
            return  # No change, skip

        old_direction = self._direction
        old_w = self.width
        old_h = self.height
        super().set_direction(direction)
        # If a perpendicular rotation occurred, rotate all component offsets and
        # dimensions in-place so physics body identity is never broken.
        if (old_direction is not None and self._direction is not None
                and CardinalDirection.is_perpendicular(old_direction, self._direction)):
            clockwise = CardinalDirection.next_clockwise(old_direction) == self._direction
            self._rotate_components_in_place(old_w, old_h, clockwise)

    def _rotate_components_in_place(
        self,
        old_composite_w: float,
        old_composite_h: float,
        clockwise: bool,
    ) -> None:
        """Rotate all component offsets and physics body dimensions in-place by 90°.

        Uses standard 2D rectangle rotation within the composite bounding box so
        that the component layout mirrors the composite's own rotation.  Physics
        body *identity* is preserved — no new bodies are created and the physics
        engine needs no updates.

        Derived classes may override this to handle direction-dependent component
        properties (e.g. animation axes on a conveyor belt).

        Args:
            old_composite_w: Composite width *before* the rotation.
            old_composite_h: Composite height *before* the rotation.
            clockwise:        True for 90° CW, False for 90° CCW.
        """
        new_components: dict = {}
        for name, obj in self._components.items():
            old_cw = obj.width
            old_ch = obj.height
            # Swap component dimensions via set_direction → rotate_area.
            # old_cw / old_ch are kept purely for the offset math below;
            # the dimension swap itself is handled by the set_direction call.
            obj.set_direction(
                CardinalDirection.next_clockwise(obj.direction)
                if clockwise else CardinalDirection.next_counterclockwise(obj.direction)
            )
            # Rotate offset within the old composite bounding box
            if clockwise:
                # CW: (off_x, off_y) -> (off_y, old_W - off_x - old_cw)
                new_off_x = obj._parent_offset_y
                new_off_y = old_composite_w - obj._parent_offset_x - old_cw
            else:
                # CCW: (off_x, off_y) -> (old_H - off_y - old_ch, off_x)
                new_off_x = old_composite_h - obj._parent_offset_y - old_ch
                new_off_y = obj._parent_offset_x
            new_components[name] = obj
            # apply offsets to components
            obj.set_x(self.x + new_off_x)
            obj.set_y(self.y + new_off_y)
        self._components = new_components

    # ------------------------------------------------------------------
    # ICompositeSceneObject — component management
    # ------------------------------------------------------------------

    def build_components(self):
        """Override this method in derived classes to build the kinematic components and register them as children."""
        ...

    def add_component(
        self,
        name: str,
        obj: ISceneObject
    ) -> None:
        """Register a child component at a relative offset."""
        if name in self._components:
            raise ValueError(
                f"A component named '{name}' already exists in '{self.name}'."
            )
        self._components[name] = obj

    def remove_component(self, name: str) -> None:
        """Remove a component by logical name."""
        if name in self._components:
            del self._components[name]

    def get_component(self, name: str) -> ISceneObject | None:
        entry = self._components.get(name)
        return entry

    def get_components(self) -> dict[str, ISceneObject]:
        return dict(self._components)

    def get_component_names(self) -> list[str]:
        return list(self._components.keys())

    def has_component(self, name: str) -> bool:
        return name in self._components

    def set_components(self, components: dict[str, ISceneObject]) -> None:
        self._components = dict(components)

    def clear_components(self) -> None:
        self._components.clear()

    def get_component_world_position(
        self, name: str
    ) -> tuple[float, float] | None:
        """Return the world-space position of the named component."""
        entry = self._components.get(name)
        if not entry:
            return None
        return (self.x + entry._parent_offset_x, self.y + entry._parent_offset_y)

    def get_component_at_point(
        self, x: float, y: float
    ) -> ISceneObject | None:
        """Find the topmost component whose bounds contain the given point.

        Components are checked in descending layer order (foreground first).
        """
        # Sort by component layer descending for foreground-first hit-testing
        candidates = sorted(
            self._components.values(),
            key=lambda entry: entry.get_layer(),
            reverse=True,
        )
        for obj in candidates:
            wx = self.x + obj._parent_offset_x
            wy = self.y + obj._parent_offset_y
            if wx <= x <= wx + obj.width and wy <= y <= wy + obj.height:
                return obj
        return None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the composite and all its components.

        Each component's physics body position is synchronised to its world
        position (composite origin + component offset) before the component
        is ticked, so the collision/spatial systems always see correct bounds.
        """
        ...

    # ---------- Rendering contract ----------

    @property
    def is_animating(self) -> bool:
        """Return True if this composite changes component positions every frame.

        The renderer uses this flag to decide whether to rebuild the
        QGraphicsItems for this composite on every tick.  Override and return
        ``True`` in any composite whose ``update()`` method mutates component
        offsets directly (i.e. does **not** use the SceneAnimator system).

        Composites that only animate via SceneAnimator clips do **not** need to
        override this — the renderer already detects ``animator.is_playing``.
        This property exists specifically for custom per-frame update logic
        (e.g. scrolling belt stripes, rotating parts, progress indicators).

        Returns:
            False by default; override to return True for continuously
            animated composites.
        """
        return False


__all__ = ["ICompositeSceneObject"]
