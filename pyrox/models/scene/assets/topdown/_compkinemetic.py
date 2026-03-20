"""Composite kinematic scene object Mixin class.
"""
from typing import Callable
from pyrox.interfaces import IBasePhysicsBody, BodyType, CardinalDirection, CollisionLayer
from pyrox.models.physics import BasePhysicsBody
from pyrox.models.scene.sceneobject import SceneObject
from pyrox.models.scene.compositesceneobject import CompositeSceneObject
from pyrox.models.scene.animation import (
    AnimationClip,
    AnimationEasing,
    AnimationMode,
    AnimationTrack,
)


class CompositeKinematicSceneObject(CompositeSceneObject):
    """Mixin for composite scene objects with kinematic components.
    This mixin provides functionality to track the world position of kinematic components
        and derive their velocity based on position changes over time.

    It also keeps the SceneObject's physics body transparent to ensure that the kinematic components can move freely
        without being affected by physics collisions.
    """

    default_collision_mask = [
        CollisionLayer.DEFAULT,
        CollisionLayer.PLAYER,
        CollisionLayer.ENEMY,
    ]

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        scene_object_type: str,
        template_name: str,
        description: str = "",
        direction: CardinalDirection = CardinalDirection.RIGHT,
        layer: int = 0,
        properties: dict = dict(),
        components: list[dict] | dict | None = None,
        id: str | None = None,
        group_id: str | None = None,
        tags: list[str] | None = None,
    ):

        if physics_body:
            # Composite itself doesn't collide; the rod and head do.
            physics_body.get_collider().set_collision_layer(CollisionLayer.TRANSPARENT)
            physics_body.get_collider().set_collision_mask([])

        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            scene_object_type=scene_object_type,
            template_name=template_name,
            id=id,
            group_id=group_id,
            tags=tags,
            layer=layer,
            properties=properties,
            components=components,
        )
        self._direction = CardinalDirection.from_str(properties.get('direction', 'RIGHT')) or direction
        self.build_components()

    # ------------------------------------------------------------------
    # Build Methods
    # ------------------------------------------------------------------

    def build_components(self):
        """Override this method in derived classes to build the kinematic components and register them as children."""
        raise NotImplementedError("Derived classes must implement build_components() to create and register their kinematic components.")

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def create_simple_clip(
        self,
        clip_name: str,
        animation_duration: float,
        tracking_property: str,
        target1: float,
        target2: float,
        animation_mode: AnimationMode = AnimationMode.ONCE,
        animation_easing: AnimationEasing = AnimationEasing.EASE_IN_OUT,
    ) -> AnimationClip:
        """Helper method to create a simple animation clip for a kinematic component.
        This method creates a simple, 2 target animation clip that can be used to animate the position of a kinematic component
            between two states (e.g. extended and retracted).
        """
        return (
            AnimationClip(clip_name, animation_duration, animation_mode)
            .add_track(
                AnimationTrack(tracking_property, easing=animation_easing)
                .add_keyframe(0.0, target1)
                .add_keyframe(animation_duration, target2)
            )
        )

    def create_simple_component(
        self,
        name: str,
        template_name: str,
        body_type: BodyType,
        width: float,
        height: float,
        collision_layer: CollisionLayer,
        collision_mask: list[CollisionLayer],
        scene_object_type: str = "kinematic_component",
        bg_color: str = "#888888",
        layer: int = 0,
    ) -> SceneObject:
        """Helper method to create a simple kinematic component with a rectangular physics body."""
        physics_body = BasePhysicsBody(
            name=f"{self.name}_{name}_body",
            template_name=template_name,
            body_type=body_type,
            width=width,
            height=height,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
        )
        return SceneObject(
            name=f"{self.name}_{name}",
            scene_object_type=scene_object_type,
            physics_body=physics_body,
            bg_color=bg_color,
            layer=layer,
        )

    @classmethod
    def get_composite_body_from_dict(
        cls,
        comp_body_dict: dict
    ) -> BasePhysicsBody | None:
        """Helper method to create a physics body for a composite component from a dictionary.
        This method ensures that the created physics body has the correct collision layer and mask for kinematic components.
        """
        if comp_body_dict:
            comp_body = BasePhysicsBody.from_dict(comp_body_dict)
            comp_body.get_collider().set_collision_layer(CollisionLayer.TERRAIN)
            comp_body.get_collider().set_collision_mask(cls.default_collision_mask)
            return comp_body
        return None

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _compile_properties(self) -> None:
        super()._compile_properties()
        self._properties.update({
            'direction': self._direction.name,
        })

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def direction(self) -> CardinalDirection:
        """The direction in which the piston extends."""
        return self._direction

    @property
    def is_horizontal(self) -> bool:
        """Helper method to determine if the kinematic component is oriented horizontally based on its direction."""
        return self.direction in (CardinalDirection.LEFT, CardinalDirection.RIGHT)

    @property
    def is_vertical(self) -> bool:
        """Helper method to determine if the kinematic component is oriented vertically based on its direction."""
        return self.direction in (CardinalDirection.UP, CardinalDirection.DOWN)


class ActivatableCompositeKinematicSceneObject(CompositeKinematicSceneObject):
    """Extension of CompositeKinematicSceneObject that includes an 'active' state.
    This can be used for components that have an active/inactive state, such as a piston that can be extended or retracted.
    """

    CLIP_ACTIVATE = "activate"
    CLIP_DEACTIVATE = "deactivate"

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        scene_object_type: str,
        template_name: str,
        description: str = "",
        direction: CardinalDirection = CardinalDirection.RIGHT,
        layer: int = 0,
        animation_duration: float = 0.5,
        properties: dict = dict(),
        components: list[dict] | dict | None = None,
        id: str | None = None,
        group_id: str | None = None,
        tags: list[str] | None = None,
    ):
        self._active = properties.get('active', False)
        self._animation_duration = animation_duration
        super().__init__(
            name=name,
            physics_body=physics_body,
            scene_object_type=scene_object_type,
            template_name=template_name,
            description=description,
            direction=direction,
            id=id,
            group_id=group_id,
            tags=tags,
            layer=layer,
            properties=properties,
            components=components,
        )

        # ------------------------------------------------------------------
        # Restore active state if specified in properties (after registering components)
        # ------------------------------------------------------------------
        if self._active:
            self._active = False  # temporarily set to False so the setter logic runs
            self.active = True  # triggers the activate animation

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def active(self) -> bool:
        """Whether the component is currently active (e.g. piston is extended)."""
        return self._active

    @active.setter
    def active(self, value: bool):
        """Set the active state of the component."""
        if value == self._active:
            return
        self._active = value
        clip_name = self.CLIP_ACTIVATE if value else self.CLIP_DEACTIVATE
        self.snap_animation_start(clip_name)
        self.animator.play(clip_name)

    # ------------------------------------------------------------------
    # Active State Management
    # ------------------------------------------------------------------

    def current_animator_position(self) -> float:
        """Helper method to get the current position of the animator for the active component.
        This is used to snap the animation to the correct position when changing states.
        """
        # This method should be implemented by derived classes to return the current position of the relevant component's animator.
        # For example, if the piston rod is the component being animated, this method should return the current position of the rod's animator.
        raise NotImplementedError(
            "Derived classes must implement current_animator_position() to return the current position of the active component's animator.")

    def snap_animation_start(self, clip_name: str):
        """Helper method to snap the animation to the start of the specified clip.
        This is useful to ensure that when activating/deactivating, the animation starts from the correct position.
        """
        clip = self.animator.get_clip(clip_name)
        if not clip:
            return  # Clip not found; cannot snap animation.
        current_pos = self.current_animator_position()
        for track in clip.tracks:
            if track.keyframes:
                track.keyframes[0].value = current_pos

    def update_activate_deactivate_targets(self, target_active: float, target_inactive: float):
        """Helper method to update the target values of the activate and deactivate clips.
        This can be used to dynamically adjust the animation targets based on the current state of the component or other factors.
        """
        self.update_animation_start_end(self.CLIP_ACTIVATE, target_inactive, target_active)
        self.update_animation_start_end(self.CLIP_DEACTIVATE, target_active, target_inactive)

    def update_animation_start_end(self, clip_name: str, target_start: float, target_end: float):
        """Helper method to update the start and end keyframe values of an animation clip.
        This can be used to dynamically adjust the animation targets based on the current state of the component.
        """
        clip = self.animator.get_clip(clip_name)
        if not clip:
            return  # Clip not found; cannot update keyframes.
        for track in clip.tracks:
            if track.keyframes and len(track.keyframes) >= 2:
                track.keyframes[0].value = target_start
                track.keyframes[1].value = target_end

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def create_clips_on_property(
        self,
        tracking_property: str,
        target1: float,
        target2: float,
        animation_duration: float = 0.5,
        animation_mode: AnimationMode = AnimationMode.ONCE,
        animation_easing: AnimationEasing = AnimationEasing.EASE_IN_OUT,
    ) -> None:
        """Helper method to create activate/deactivate clips that animate a property between two target values."""
        activate_clip = self.create_simple_clip(
            clip_name=self.CLIP_ACTIVATE,
            animation_duration=animation_duration,
            tracking_property=tracking_property,
            target1=target1,
            target2=target2,
            animation_mode=animation_mode,
            animation_easing=animation_easing,
        )
        deactivate_clip = self.create_simple_clip(
            clip_name=self.CLIP_DEACTIVATE,
            animation_duration=animation_duration,
            tracking_property=tracking_property,
            target1=target2,  # reverse targets for deactivation
            target2=target1,
            animation_mode=animation_mode,
            animation_easing=animation_easing,
        )
        self.animator.add_clips([activate_clip, deactivate_clip])

    # ------------------------------------------------------------------
    # Input/Output Connections
    # ------------------------------------------------------------------

    def activate(self, *args, **kwargs):
        """Input method to activate the component."""
        self.active = True

    def deactivate(self, *args, **kwargs):
        """Input method to deactivate the component."""
        self.active = False

    def toggle(self, *args, **kwargs):
        """Input method to toggle the active state of the component."""
        self.active = not self.active

    def set_direction(self, direction: CardinalDirection):
        """Input method to set the direction of the component."""
        self._direction = direction
        self._compile_properties()  # Update properties to reflect new direction

    def get_inputs(self) -> dict[str, Callable[..., None]]:
        """Get available input connections.

        Returns dict mapping input names to methods, properties, or other connection endpoints.
        """
        return {
            "activate": self.activate,
            "deactivate": self.deactivate,
            "toggle": self.toggle,
            "set_direction": self.set_direction,
        }

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _compile_properties(self) -> None:
        super()._compile_properties()
        self._properties.update({
            'active': self._active,
        })
