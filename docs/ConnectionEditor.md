# Connection Editor

A visual node-based editor for creating and managing connections between scene objects in Pyrox.

## Features

### Visual Node-Based Interface
- **Node Representation**: Each scene object is displayed as a node with a title
- **Input/Output Ports**: 
  - Output ports (orange) on the right side represent callbacks and events
  - Input ports (purple) on the left side represent methods and actions
- **Visual Connections**: Lines connect output ports to input ports, showing the wiring

### Connection Management
- **Drag-and-Drop**: Click and drag from an output port to an input port to create a connection
- **Delete Connections**: Right-click any connection and select "Delete Connection"
- **Test Connections**: Right-click a connection to test it, or use "Test All" to validate all connections
- **Clear All**: Remove all connections at once with the "Clear All" button

### Navigation
- **Pan**: Middle-click and drag to pan the canvas
- **Move Nodes**: Click and drag nodes to reposition them
- **Auto Layout**: Automatically arrange nodes in a grid layout
- **Reset View**: Return to default view

### Persistence
- **Save**: Save connections to the scene's connection registry
- **Reload**: Reload the scene and its connections
- **Serialization**: Connections can be serialized for saving to files

## Usage

### Basic Setup

```python
from pyrox.models.scene import Scene
from pyrox.models.gui import ConnectionEditor
from pyrox.models.connection import ConnectionRegistry

# Create scene with objects
scene = Scene(name="My Scene")
# ... add scene objects ...

# Create connection registry
registry = ConnectionRegistry()
for obj_id, obj in scene.scene_objects.items():
    registry.register_object(obj_id, obj)

# Create editor window
import tkinter as tk
root = tk.Tk()
editor = ConnectionEditor(root, scene=scene, connection_registry=registry)
editor.pack(fill=tk.BOTH, expand=True)
root.mainloop()
```

### Creating Connections

1. **Visually**: Click and drag from an output port (orange, right side) to an input port (purple, left side)
2. **Programmatically**: Use the ConnectionRegistry directly:

```python
registry.connect(
    source_id="sensor_001",
    output_name="on_activate_callbacks",
    target_id="conveyor_001",
    input_name="start"
)
```

### Example: Sensor-Controlled Conveyor

```python
from pyrox.models.physics.sensor import ProximitySensorBody
from pyrox.models.physics.conveyor import ConveyorBody

# Create sensor
sensor = SceneObject(
    name="Checkpoint",
    scene_object_type="Sensor",
    physics_body=ProximitySensorBody.create_checkpoint_sensor(x=0, y=0)
)

# Create conveyor
conveyor = SceneObject(
    name="Belt",
    scene_object_type="Conveyor",
    physics_body=ConveyorBody(x=0, y=50, width=200, height=20)
)

# Add to scene
scene.add_scene_object(sensor)
scene.add_scene_object(conveyor)

# In the ConnectionEditor, connect:
# - sensor.on_activate_callbacks → conveyor.start
# - sensor.on_deactivate_callbacks → conveyor.stop
```

## Port Types

### Output Ports (Orange, Right Side)
Typically callback lists or event emitters:
- `on_activate_callbacks`: Called when object activates
- `on_deactivate_callbacks`: Called when object deactivates
- `on_object_enter_callbacks`: Called when another object enters
- `on_object_exit_callbacks`: Called when another object exits

### Input Ports (Purple, Left Side)
Typically methods or actions:
- `start()`: Start/activate the object
- `stop()`: Stop/deactivate the object
- `set_speed(speed)`: Set speed
- `toggle()`: Toggle state

## Keyboard Shortcuts

- **Delete**: Delete selected connection (future)
- **Middle-Click + Drag**: Pan canvas
- **Escape**: Cancel current operation (future)

## API Reference

### ConnectionEditor

```python
class ConnectionEditor(ttk.Frame):
    def __init__(
        self,
        master=None,
        scene: Optional[IScene] = None,
        connection_registry: Optional[ConnectionRegistry] = None,
        **kwargs
    )
```

#### Methods

- `load_scene(scene, connection_registry)`: Load a scene into the editor
- `reload_scene()`: Reload the current scene
- `auto_layout()`: Arrange nodes in a grid
- `clear_all_connections()`: Remove all connections
- `test_all_connections()`: Validate all connections
- `save_connections()`: Save connections to scene
- `zoom_in()`: Zoom in (future)
- `zoom_out()`: Zoom out (future)
- `reset_view()`: Reset to default view

## Implementation Details

### Node Structure

```python
@dataclass
class VisualNode:
    obj_id: str
    scene_obj: ISceneObject
    x: float
    y: float
    width: float = 200.0
    height: float = 100.0
    ports: Dict[str, NodePort]
```

### Port Structure

```python
@dataclass
class NodePort:
    name: str
    is_output: bool
    x: float
    y: float
    canvas_id: int
```

### Connection Format

Connections are stored as bezier curves with smooth visual appearance:

```python
# Connection line with control points
canvas.create_line(
    x1, y1,          # Start point (output port)
    cx1, cy1,        # Control point 1
    cx2, cy2,        # Control point 2
    x2, y2,          # End point (input port)
    smooth=True
)
```

## Testing

The connection editor includes built-in testing capabilities:

```python
# Test a single connection by right-clicking it
# Or test all connections at once:
editor.test_all_connections()
```

Test results show:
- ✓ Valid connections (properly wired)
- ❌ Invalid connections (missing objects or methods)
- ❌ Not wired (exists in registry but not in callback list)

## Saving and Loading

### Save Connections

```python
editor.save_connections()  # Saves to scene.connection_registry

# Serialize for file storage
data = registry.serialize()
# Returns: {"connections": [...]}
```

### Load Connections

```python
# Connections are automatically loaded when loading a scene
editor.load_scene(scene, registry)

# Or load from serialized data
for conn_data in data["connections"]:
    registry.connect(
        conn_data["source"],
        conn_data["output"],
        conn_data["target"],
        conn_data["input"]
    )
```

## Future Enhancements

- [ ] Zoom in/out functionality
- [ ] Selection and multi-delete
- [ ] Copy/paste connections
- [ ] Connection labels/annotations
- [ ] Color-coded connections by type
- [ ] Minimap for large graphs
- [ ] Search/filter nodes
- [ ] Undo/redo support
- [ ] Export to image
- [ ] Connection validation on creation
- [ ] Port compatibility checking

## Troubleshooting

### "Cannot connect ports of same type"
You can only connect output ports (orange) to input ports (purple), not output-to-output or input-to-input.

### "Connection already exists"
A connection between those specific ports already exists. Delete it first if you want to recreate it.

### Nodes overlapping
Use the "Auto Layout" button to automatically arrange nodes in a grid.

### Connection not working
Right-click the connection and select "Test Connection" to verify it's properly wired. Check that the target object has the expected method.

## Examples

See `examples/connection_editor_example.py` for a complete working example.

Run the demo:
```bash
python pyrox/models/gui/connectioneditor.py
```

Or run the full example:
```bash
python examples/connection_editor_example.py
```
