"""Top-down sliding door composite scene object.

A sliding door consists of three components:

* **post_a** — frame post at the *A* edge of the door frame.
* **post_b** — frame post at the *B* edge of the door frame.
* **door**   — the door panel that slides from the opening (closed) to
               the outside of Post A (open).

The :attr:`is_open` property drives the animation:

* ``True``  → plays the ``"open"`` clip (panel slides to outside of Post A).
* ``False`` → plays the ``"close"`` clip (panel slides back to fill the
              opening).

The door can slide in any of the four cardinal directions.  *Direction*
indicates which way the door panel travels when opening:

    LEFT  → panel slides left;  Post A = left post,  Post B = right post
    RIGHT → panel slides right; Post A = left post,  Post B = right post
    UP    → panel slides up;    Post A = top  post,  Post B = bottom post
    DOWN  → panel slides down;  Post A = top  post,  Post B = bottom post

For ``LEFT`` and ``RIGHT`` the composite origin is the **top-left corner of
the left-side Post A**.  For ``UP`` and ``DOWN`` it is the **top-left corner
of the top-side Post A**.

The ``total_width`` parameter is the full span – Post A outer edge to Post B
outer edge – along the opening axis.  ``door_height`` is the size of the
frame on the perpendicular axis.

Example::

    door = SlidingDoorSceneObject.create(
        name="Bay Door",
        x=300.0,
        y=200.0,
        total_width=120.0,
        door_height=20.0,
        post_size=12.0,
    )
    scene.add_scene_object(door)

    # Open the door (triggers the "open" animation):
    door.is_open = True

    # In the render / update loop:
    door.update(dt)
"""
from pyrox.interfaces import IBasePhysicsBody, BodyType, CardinalDirection, CollisionLayer
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.scene.assets.topdown._compkinemetic import ActivatableCompositeKinematicSceneObject
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate

SCENE_OBJECT_TYPE_SLIDING_DOOR = "sliding_door"
SCENE_OBJECT_TEMPLATE_NAME_SLIDING_DOOR = "Top-Down Sliding Door"


class SlidingDoorSceneObject(ActivatableCompositeKinematicSceneObject):
    """Top-down composite sliding door with animated door panel.

    The composite's origin is the **top-left corner of Post A**.  The three
    child components are:

    * ``"post_a"`` — first frame post (left for LEFT/RIGHT, top for UP/DOWN).
    * ``"post_b"`` — second frame post (right for LEFT/RIGHT, bottom for UP/DOWN).
    * ``"door"``   — the door panel whose slide offset is driven by animation
                     clips registered on the composite's own animator.

    The slide position is stored in ``_door_slide_pos`` (a plain float
    attribute on ``self``).  The composite animator calls
    :meth:`~pyrox.models.scene.sceneobject.SceneObject.set_property` each
    frame, which resolves to ``setattr(self, "_door_slide_pos", value)``
    – the same mechanism the piston uses for its rod width.

    Attributes:
        CLIP_OPEN:  Name of the open animation clip.
        CLIP_CLOSE: Name of the close animation clip.
    """

    CLIP_OPEN = "open"
    CLIP_CLOSE = "close"

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        direction: CardinalDirection = CardinalDirection.LEFT,
        total_width: float = 100.0,
        door_height: float = 16.0,
        post_size: float = 10.0,
        animation_duration: float = 0.6,
        post_color: str = "#444444",
        door_color: str = "#888888",
        layer: int = 0,
        properties: dict = dict(),
        **kwargs,
    ) -> None:
        """Initialise the sliding door with the given parameters.

        .. tip::
            Prefer :meth:`create` when you do not need to supply a custom
            physics body — it handles body sizing automatically.

        Args:
            name:               Identifier for this door.
            physics_body:       Physics body for the composite (defines world
                                position and overall bounding box).
            direction:          Direction the door panel slides when opening.
            total_width:        Full span of the frame along the opening axis,
                                including both posts.
            door_height:        Size of the door frame on the perpendicular axis.
            post_size:          Width of each post along the opening axis.
            animation_duration: Seconds for a full open or close stroke.
            post_color:         CSS hex fill colour for the frame posts.
            door_color:         CSS hex fill colour for the door panel.
            layer:              Render layer (z-order).
        """
        self._total_width = float(total_width)
        self._door_height = float(door_height)
        self._post_size = float(post_size)
        self._post_color = post_color
        self._door_color = door_color
        self._door_slide_pos = 0.0  # Updated by the animator each frame
        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            scene_object_type=SCENE_OBJECT_TYPE_SLIDING_DOOR,
            template_name=SCENE_OBJECT_TEMPLATE_NAME_SLIDING_DOOR,
            layer=layer,
            direction=direction,
            animation_duration=animation_duration,
            properties=properties,
        )

    def current_animator_position(self) -> float:
        return self._door_slide_pos

    # ------------------------------------------------------------------
    # Build Methods
    # ------------------------------------------------------------------

    def build_components(self):
        # ------------------------------------------------------------------
        # Component geometry
        # ------------------------------------------------------------------
        opening = self._total_width - 2.0 * self._post_size

        if self.is_horizontal:
            post_w, post_h = self._post_size, self._door_height
            door_panel_w = opening
            door_panel_h = self._door_height
            post_b_ox = self._total_width - self._post_size
            post_b_oy = 0.0
        else:  # UP / DOWN
            post_w, post_h = self._door_height, self._post_size
            door_panel_w = self._door_height
            door_panel_h = opening
            post_b_ox = 0.0
            post_b_oy = self._total_width - self._post_size

        # ------------------------------------------------------------------
        # Slide-axis offsets
        #
        # closed: door fills the opening (inner face of Post A → inner face of Post B)
        # open  : door is entirely outside Post A (or Post B for RIGHT/DOWN)
        #
        # For LEFT  : closed = post_size, open = -opening  (door clears past Post A)
        # For RIGHT : closed = post_size, open = total_width  (door clears past Post B)
        # For UP    : closed = post_size, open = -opening
        # For DOWN  : closed = post_size, open = total_width
        # ------------------------------------------------------------------
        match self.direction:
            case CardinalDirection.LEFT | CardinalDirection.UP:
                closed_offset = self._post_size
                open_offset = -opening
            case CardinalDirection.RIGHT | CardinalDirection.DOWN:
                closed_offset = self._post_size
                open_offset = self._total_width

        self._door_closed_offset = float(closed_offset)
        self._door_open_offset = float(open_offset)

        # Mutable slide position — written each frame by self.animator via
        # set_property("_door_slide_pos", value).
        self._door_slide_pos = self._door_closed_offset

        # ------------------------------------------------------------------
        # Post A
        # ------------------------------------------------------------------
        self._post_a = self.create_simple_component(
            name="post_a",
            template_name="Door Post",
            body_type=BodyType.KINEMATIC,
            width=post_w,
            height=post_h,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=self.default_collision_mask,
            bg_color=self._post_color,
            layer=self._layer,
        )

        # ------------------------------------------------------------------
        # Post B
        # ------------------------------------------------------------------
        self._post_b = self.create_simple_component(
            name="post_b",
            template_name="Door Post",
            body_type=BodyType.KINEMATIC,
            width=post_w,
            height=post_h,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=self.default_collision_mask,
            bg_color=self._post_color,
            layer=self._layer,
        )

        # ------------------------------------------------------------------
        # Door panel
        # ------------------------------------------------------------------
        self._door = self.create_simple_component(
            name="door",
            template_name="Door Panel",
            body_type=BodyType.KINEMATIC,
            width=door_panel_w,
            height=door_panel_h,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=self.default_collision_mask,
            bg_color=self._door_color,
            layer=self._layer,
        )

        # ------------------------------------------------------------------
        # Animation clips — registered on the composite's own animator so
        # that super().update(dt) drives _door_slide_pos automatically.
        # ------------------------------------------------------------------
        self.create_clips_on_property(
            tracking_property='_door_slide_pos',
            target1=self._door_closed_offset,
            target2=self._door_open_offset,
            animation_duration=self._animation_duration,
        )

        # ------------------------------------------------------------------
        # Register components at initial (closed) offsets
        # ------------------------------------------------------------------
        if self.is_horizontal:
            door_init_ox, door_init_oy = self._door_closed_offset, 0.0
        else:
            door_init_ox, door_init_oy = 0.0, self._door_closed_offset

        self.add_component("post_a", self._post_a, 0.0,          0.0)
        self.add_component("post_b", self._post_b, post_b_ox,    post_b_oy)
        self.add_component("door",   self._door,   door_init_ox, door_init_oy)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def direction(self) -> CardinalDirection:
        """The direction the door panel slides when opening."""
        return self._direction

    @property
    def is_open(self) -> bool:
        """``True`` when the door is open (or in the process of opening)."""
        return self._is_open_state

    @is_open.setter
    def is_open(self, value: bool) -> None:
        """Trigger the open or close animation.

        If called mid-animation the new clip starts from the current panel
        position so transitions are always smooth regardless of timing.

        Args:
            value: ``True`` to open, ``False`` to close.
        """
        if value == self._is_open_state:
            return
        self._is_open_state = value
        clip_name = self.CLIP_OPEN if value else self.CLIP_CLOSE
        self._snap_animation_start(clip_name)
        self.animator.play(clip_name)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance animations and keep the door panel aligned to its slide position.

        Calls :meth:`CompositeSceneObject.update` (which ticks both the post
        and door animators *and* the composite's own animator that writes
        ``_door_slide_pos``).  The door component's world position is then
        overridden using the freshly-updated slide position, eliminating the
        one-frame lag that would otherwise arise from the stale offset stored
        in ``_components``.

        Args:
            dt: Elapsed wall-clock seconds since the last call.
        """
        super().update(dt)

        if self.is_horizontal:
            door_ox, door_oy = self._door_slide_pos, 0.0
        else:
            door_ox, door_oy = 0.0, self._door_slide_pos

        # Sync door world position immediately (removes stale-offset lag)
        self._door.x = self.x + door_ox
        self._door.y = self.y + door_oy

        # Keep _components in sync so external offset queries are accurate
        self._components["door"] = (self._door, door_ox, door_oy)

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        direction: CardinalDirection = CardinalDirection.LEFT,
        total_width: float = 100.0,
        door_height: float = 16.0,
        post_size: float = 10.0,
        animation_duration: float = 0.6,
        post_color: str = "#444444",
        door_color: str = "#888888",
        layer: int = 0,
        body_dict: dict | None = None,
        **kwargs,
    ) -> "SlidingDoorSceneObject":
        """Create a :class:`SlidingDoorSceneObject` without manually building a physics body.

        The composite bounding box is sized to cover the full door frame
        (``total_width`` × ``door_height`` for horizontal doors).

        Args:
            name:               Identifier for this door.
            x:                  Scene X of the composite origin (top-left of Post A).
            y:                  Scene Y of the composite origin (top-left of Post A).
            direction:          Direction the door panel slides when opening.
            total_width:        Full span of the frame including both posts.
            door_height:        Cross-section size of the door frame.
            post_size:          Width of each post along the opening axis.
            animation_duration: Seconds for a full open or close stroke.
            post_color:         CSS hex fill colour for the frame posts.
            door_color:         CSS hex fill colour for the door panel.
            layer:              Render layer (z-order).

        Returns:
            A fully-initialised :class:`SlidingDoorSceneObject`.
        """
        body_dict = body_dict or kwargs.get("body")
        if body_dict:
            body = BasePhysicsBody.from_dict(body_dict)
            body.get_collider().set_collision_layer(CollisionLayer.TRANSPARENT)
            body.get_collider().set_collision_mask([])
        else:
            is_horizontal = direction in (CardinalDirection.LEFT, CardinalDirection.RIGHT)
            bw = total_width if is_horizontal else door_height
            bh = door_height if is_horizontal else total_width
            body = BasePhysicsBody(
                name=f"{name}_body",
                template_name='Base Physics Body',
                x=float(x),
                y=float(y),
                width=bw,
                height=bh,
                collision_layer=CollisionLayer.TRANSPARENT,
                collision_mask=[],
            )
        return cls(
            name=name,
            physics_body=body,
            direction=direction,
            total_width=total_width,
            door_height=door_height,
            post_size=post_size,
            animation_duration=animation_duration,
            post_color=post_color,
            door_color=door_color,
            layer=layer,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compile_properties(self) -> None:
        super()._compile_properties()
        self._properties.update({
            "total_width": self._total_width,
            "door_height": self._door_height,
            "post_size":   self._post_size,
        })

    def _snap_animation_start(self, clip_name: str) -> None:
        """Snap the first keyframe of *clip_name* to the current door position.

        Ensures smooth mid-stroke reversals — the new animation always starts
        from where the panel currently is rather than jumping to a preset value.

        Args:
            clip_name: ``CLIP_OPEN`` or ``CLIP_CLOSE``.
        """
        clip = self.animator.get_clip(clip_name)
        if clip is None:
            return
        current_pos = self._door_slide_pos
        for track in clip.tracks:
            if track.keyframes:
                track.keyframes[0].value = current_pos


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SCENE_OBJECT_TEMPLATE_NAME_SLIDING_DOOR,
        scene_object_class=SlidingDoorSceneObject,
        description="Composite sliding door with two frame posts and animated panel (top-down view)",
        factory_func=SlidingDoorSceneObject.create,
        default_kwargs={
            "name":               SCENE_OBJECT_TEMPLATE_NAME_SLIDING_DOOR,
            "direction":          CardinalDirection.LEFT,
            "total_width":        100.0,
            "door_height":        16.0,
            "post_size":          10.0,
            "animation_duration": 0.6,
            "post_color":         "#444444",
            "door_color":         "#888888",
            "layer":              0,
        },
        category="Machinery",
    )
)
