"""Helper functions for creating interactive UI scene objects.

Provides convenient factory functions for creating common UI patterns like
panels with buttons, control panels, and interactive displays.
"""
from typing import Callable, Optional
from pyrox.models.scene import SceneObject
from pyrox.models.physics.ui_panel import UIPanelBody, UIButtonBody
from pyrox.services import IdGeneratorService


def create_ui_panel(
    name: str = "Control Panel",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 200.0,
    height: float = 150.0,
    description: str = ""
) -> SceneObject:
    """Create a UI panel scene object.

    Args:
        name: Name of the panel
        x: X position in scene coordinates
        y: Y position in scene coordinates
        width: Width of the panel
        height: Height of the panel
        description: Optional description

    Returns:
        SceneObject with UIPanelBody that doesn't collide with game objects
    """
    panel_body = UIPanelBody(
        name=name,
        x=x,
        y=y,
        width=width,
        height=height,
        interactive=True,
        panel_type="panel"
    )

    panel = SceneObject(
        id=str(IdGeneratorService.get_id()),
        name=name,
        scene_object_type="ui_panel",
        physics_body=panel_body,
        description=description
    )

    # Panel is not directly clickable (children are)
    panel.set_clickable(False)

    return panel


def create_ui_button(
    name: str = "Button",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 80.0,
    height: float = 30.0,
    toggle: bool = False,
    on_click: Optional[Callable] = None,
    parent: Optional[SceneObject] = None
) -> SceneObject:
    """Create a UI button scene object.

    Args:
        name: Name of the button
        x: X position (relative to parent if parent provided)
        y: Y position (relative to parent if parent provided)
        width: Width of the button
        height: Height of the button
        toggle: If True, button stays pressed when clicked
        on_click: Optional click handler function(scene_object, x, y)
        parent: Optional parent scene object

    Returns:
        SceneObject with UIButtonBody
    """
    # Adjust position if parent provided
    if parent:
        x += parent.x
        y += parent.y

    button_body = UIButtonBody(
        name=name,
        x=x,
        y=y,
        width=width,
        height=height,
        toggle=toggle,
        enabled=True
    )

    button = SceneObject(
        id=str(IdGeneratorService.get_id()),
        name=name,
        scene_object_type="ui_button",
        physics_body=button_body,
        description=f"{'Toggle' if toggle else 'Push'} button"
    )

    # Make button clickable
    button.set_clickable(True)

    # Add click handler if provided
    if on_click:
        button.add_on_click_handler(on_click)

    # Set parent relationship if provided
    if parent:
        parent.add_child(button)

    return button


def create_control_panel_with_buttons(
    panel_name: str = "Control Panel",
    x: float = 0.0,
    y: float = 0.0,
    button_configs: Optional[list[dict]] = None
) -> tuple[SceneObject, list[SceneObject]]:
    """Create a control panel with multiple buttons.

    Args:
        panel_name: Name of the panel
        x: X position in scene coordinates
        y: Y position in scene coordinates
        button_configs: List of button configurations, each with:
            - name: Button name
            - offset_x: X offset from panel position (default: 10)
            - offset_y: Y offset from panel position (default: 10)
            - width: Button width (default: 80)
            - height: Button height (default: 30)
            - toggle: Toggle mode (default: False)
            - on_click: Click handler function

    Returns:
        Tuple of (panel, list of buttons)

    Example:
        >>> def on_start_clicked(obj, x, y):
        ...     print(f"Start button clicked at ({x}, {y})")
        ...
        >>> panel, buttons = create_control_panel_with_buttons(
        ...     panel_name="Machine Controls",
        ...     x=100, y=100,
        ...     button_configs=[
        ...         {"name": "Start", "offset_x": 10, "offset_y": 10, "on_click": on_start_clicked},
        ...         {"name": "Stop", "offset_x": 100, "offset_y": 10},
        ...         {"name": "Power", "offset_x": 10, "offset_y": 50, "toggle": True},
        ...     ]
        ... )
    """
    if button_configs is None:
        button_configs = [
            {"name": "Button 1", "offset_x": 10, "offset_y": 10},
            {"name": "Button 2", "offset_x": 100, "offset_y": 10},
        ]

    # Calculate panel size based on button layout
    max_x = max(cfg.get("offset_x", 10) + cfg.get("width", 80) for cfg in button_configs)
    max_y = max(cfg.get("offset_y", 10) + cfg.get("height", 30) for cfg in button_configs)
    panel_width = max_x + 10
    panel_height = max_y + 10

    # Create panel
    panel = create_ui_panel(
        name=panel_name,
        x=x,
        y=y,
        width=panel_width,
        height=panel_height,
        description=f"Control panel with {len(button_configs)} buttons"
    )

    # Create buttons
    buttons = []
    for config in button_configs:
        button = create_ui_button(
            name=config.get("name", "Button"),
            x=config.get("offset_x", 10),
            y=config.get("offset_y", 10),
            width=config.get("width", 80),
            height=config.get("height", 30),
            toggle=config.get("toggle", False),
            on_click=config.get("on_click"),
            parent=panel
        )
        buttons.append(button)

    return panel, buttons


# Example usage:
def example_create_interactive_panel():
    """Example showing how to create an interactive control panel."""

    # Define button click handlers
    def on_start_clicked(scene_object, x, y):
        print(f"START button clicked at ({x:.1f}, {y:.1f})")
        # Add your custom logic here
        # For example: start_machine()

    def on_stop_clicked(scene_object, x, y):
        print(f"STOP button clicked at ({x:.1f}, {y:.1f})")
        # Add your custom logic here
        # For example: stop_machine()

    def on_power_toggled(scene_object, x, y):
        button_body = scene_object.physics_body
        if hasattr(button_body, 'pressed'):
            state = "ON" if button_body.pressed else "OFF"
            print(f"POWER toggled to {state}")
            # Add your custom logic here
            # For example: set_power(button_body.pressed)

    # Create control panel with buttons
    panel, buttons = create_control_panel_with_buttons(
        panel_name="Machine Controls",
        x=100.0,
        y=100.0,
        button_configs=[
            {
                "name": "Start",
                "offset_x": 10,
                "offset_y": 10,
                "width": 80,
                "height": 30,
                "toggle": False,
                "on_click": on_start_clicked
            },
            {
                "name": "Stop",
                "offset_x": 100,
                "offset_y": 10,
                "width": 80,
                "height": 30,
                "toggle": False,
                "on_click": on_stop_clicked
            },
            {
                "name": "Power",
                "offset_x": 10,
                "offset_y": 50,
                "width": 170,
                "height": 30,
                "toggle": True,
                "on_click": on_power_toggled
            },
        ]
    )

    return panel, buttons
