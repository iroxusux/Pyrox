"""UI Panel physics body for in-scene interactive elements.

Provides static, non-colliding physics bodies for UI panels, buttons,
and other interactive scene elements that should never interact with
game physics.
"""
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
)
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class UIPanelBody(BasePhysicsBody):
    """UI Panel that exists in the scene but never collides with anything.

    UI panels are STATIC bodies with the UI collision layer that has an
    empty collision mask, ensuring they never participate in physics
    collisions. Perfect for in-scene control panels, buttons, and displays.

    Attributes:
        interactive: Whether the panel responds to user interaction
        panel_type: Type of UI panel (panel, button, slider, etc.)
    """

    def __init__(
        self,
        name: str = "UI Panel",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 50.0,
        interactive: bool = True,
        panel_type: str = "panel",
        material: Material | None = None,
    ):
        """Initialize UI panel body.

        Args:
            name: Name of the UI element
            x: X position in scene coordinates
            y: Y position in scene coordinates
            width: Width of the panel
            height: Height of the panel
            interactive: Whether this panel accepts user input
            panel_type: Type of UI element (panel, button, slider, etc.)
            material: Material properties (not used for physics, only visual)
        """
        # UI panels use minimal material properties (no physics interaction)
        if material is None:
            material = Material(
                density=0.0,      # No mass
                restitution=0.0,  # No bounce
                friction=0.0,     # No friction
                drag=0.0          # No drag
            )

        BasePhysicsBody.__init__(
            self=self,
            name=name,
            tags=["ui", panel_type],
            body_type=BodyType.STATIC,
            enabled=True,
            sleeping=False,
            mass=0.0,  # UI elements have no mass
            collider_type=ColliderType.RECTANGLE,
            collision_layer=CollisionLayer.UI,
            collision_mask=[],  # Empty mask = never collides with anything
            is_trigger=False,   # Not a trigger, simply non-colliding
            x=x,
            y=y,
            width=width,
            height=height,
            material=material,
        )

        self.interactive = interactive
        self.panel_type = panel_type

    def set_interactive(self, interactive: bool) -> None:
        """Set whether the panel accepts user interaction.

        Args:
            interactive: True to enable interaction, False to disable
        """
        self.interactive = interactive

    def is_interactive(self) -> bool:
        """Check if the panel accepts user interaction.

        Returns:
            True if interactive, False otherwise
        """
        return self.interactive


class UIButtonBody(UIPanelBody):
    """UI Button that can be clicked for interaction.

    Buttons are UI panels with additional state tracking for
    pressed/released states and visual feedback.

    Attributes:
        pressed: Whether the button is currently pressed
        enabled: Whether the button can be clicked
        toggle: Whether button stays pressed when clicked (toggle mode)
    """

    def __init__(
        self,
        name: str = "UI Button",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 80.0,
        height: float = 30.0,
        toggle: bool = False,
        enabled: bool = True,
        **kwargs
    ):
        """Initialize UI button.

        Args:
            name: Name of the button
            x: X position in scene coordinates
            y: Y position in scene coordinates
            width: Width of the button
            height: Height of the button
            toggle: If True, button stays pressed when clicked (toggle mode)
            enabled: If True, button can be clicked
            **kwargs: Additional arguments passed to UIPanelBody
        """
        super().__init__(
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
            interactive=enabled,
            panel_type="button",
            **kwargs
        )

        self._pressed = False
        self._enabled = enabled
        self._toggle = toggle

    @property
    def pressed(self) -> bool:
        """Get whether button is currently pressed."""
        return self._pressed

    def set_pressed(self, pressed: bool) -> None:
        """Set button pressed state.

        Args:
            pressed: True for pressed, False for released
        """
        if self._enabled:
            self._pressed = pressed

    def toggle_pressed(self) -> None:
        """Toggle button pressed state (for toggle mode)."""
        if self._enabled and self._toggle:
            self._pressed = not self._pressed

    def press(self) -> None:
        """Press the button."""
        if self._enabled:
            if self._toggle:
                self.toggle_pressed()
            else:
                self._pressed = True

    def release(self) -> None:
        """Release the button (non-toggle mode only)."""
        if self._enabled and not self._toggle:
            self._pressed = False

    def is_enabled(self) -> bool:
        """Check if button can be clicked."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Set whether button can be clicked.

        Args:
            enabled: True to enable, False to disable
        """
        self._enabled = enabled
        self.set_interactive(enabled)

    def is_toggle(self) -> bool:
        """Check if button is in toggle mode."""
        return self._toggle


# Register templates in factory
PhysicsSceneFactory.register_template(
    template_name="UI Panel",
    template=PhysicsSceneTemplate(
        name="UI Panel",
        body_class=UIPanelBody,
        description="Static UI panel for in-scene interactive elements. Never collides with game objects.",
        default_kwargs={
            "width": 100.0,
            "height": 50.0,
            "interactive": True,
            "panel_type": "panel",
        },
        category="UI"
    )
)

PhysicsSceneFactory.register_template(
    template_name="UI Button",
    template=PhysicsSceneTemplate(
        name="UI Button",
        body_class=UIButtonBody,
        description="Interactive button for in-scene UI. Can be toggle or momentary.",
        default_kwargs={
            "width": 80.0,
            "height": 30.0,
            "toggle": False,
            "enabled": True,
        },
        category="UI"
    )
)
