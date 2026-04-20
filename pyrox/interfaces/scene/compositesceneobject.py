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
        """Override to rotate component offsets whenever the composite changes direction.

        ``ISceneObject.set_direction`` bypasses ``IDirectional2D.set_direction`` (and therefore
        never calls ``rotate_area``), so we intercept here, delegate the physics-body update via
        ``super()``, and then trigger ``rotate_components`` with the pre-rotation direction.
        """
        if not direction:
            super().set_direction(None)
            return
        direction = CardinalDirection.try_parse(direction)
        if direction is None:
            return
        if self.direction == direction:
            return  # No change — skip rotation entirely
        prev_direction = self.direction
        super().set_direction(direction)  # updates physics body direction + swaps its W/H
        self.rotate_components(prev_direction)

    def rotate_area(self, prev_direction) -> None:
        super().rotate_area(prev_direction=prev_direction)
        self.rotate_components(prev_direction)

    def rotate_components(
        self,
        prev_direction: CardinalDirection
    ) -> None:
        """Rotate component directions and recalculate their parent offsets.

        At the point this is called, ``super().rotate_area()`` has already swapped
        the composite's width and height, so:
            self.width  == old composite height
            self.height == old composite width

        Rotation formulas (screen-space, y-down, point = top-left of component):
            90° CW  (steps=1): new_ox = old_H − oy − h,  new_oy = ox
            90° CCW (steps=3): new_ox = oy,               new_oy = old_W − ox − w
            180°    (steps=2): new_ox = old_W − ox − w,   new_oy = old_H − oy − h
        """
        # How many 90° CW steps from prev_direction to self.direction
        rotation_steps = (self.direction.value - prev_direction.value) % 4

        for comp in self._components.values():
            # Capture state BEFORE rotating the component (set_direction swaps its W/H)
            ox = comp._parent_offset_x
            oy = comp._parent_offset_y
            w = comp.width
            h = comp.height

            # Rotate the component by the same number of CW steps as the composite
            # rather than snapping to the composite's absolute direction.  Snapping
            # produces a non-perpendicular transition whenever the component's own
            # direction differs from the composite's previous direction (e.g. a rod
            # stored at NORTH inside an EAST-facing piston), which means rotate_area
            # never fires and the component's w/h are left un-swapped.
            comp_new_dir = comp.direction
            for _ in range(rotation_steps):
                comp_new_dir = CardinalDirection.next_clockwise(comp_new_dir)
            comp.set_direction(comp_new_dir)

            if rotation_steps == 1:   # 90° clockwise
                # After swap: self.width = old_H, self.height = old_W
                # Transform: new_top_left = (oy,  old_W − ox − w)
                new_ox = oy
                new_oy = self.height - ox - w
            elif rotation_steps == 3:  # 90° counter-clockwise
                # Transform: new_top_left = (old_H − oy − h,  ox)
                new_ox = self.width - oy - h
                new_oy = ox
            elif rotation_steps == 2:  # 180°
                new_ox = self.height - ox - w
                new_oy = self.width - oy - h
            else:                      # 0° — no change
                new_ox = ox
                new_oy = oy

            comp.set_parent_offset(new_ox, new_oy)

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
