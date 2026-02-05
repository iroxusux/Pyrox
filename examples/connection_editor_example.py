"""
Example showing how to use the ConnectionEditor to wire scene objects together.

This example demonstrates:
1. Creating a scene with sensors and conveyors
2. Opening the connection editor
3. Creating visual connections between objects
4. Testing connections
5. Saving connections back to the scene
"""
import tkinter as tk
from pyrox.models.scene import Scene, SceneObject
from pyrox.models.physics.sensor import ProximitySensorBody
from pyrox.models.physics.conveyor import ConveyorBody
from pyrox.models.gui.connectioneditor import ConnectionEditor
from pyrox.models.connection import ConnectionRegistry


def main():
    """Main example function."""

    # Create a scene with objects
    scene = Scene(name="Factory Scene")

    # Create proximity sensors at checkpoints
    sensor1 = SceneObject(
        name="Entry Sensor",
        scene_object_type="Sensor",
        physics_body=ProximitySensorBody.create_checkpoint_sensor(
            x=0, y=0,
            name="Entry Sensor"
        )
    )

    sensor2 = SceneObject(
        name="Exit Sensor",
        scene_object_type="Sensor",
        physics_body=ProximitySensorBody.create_checkpoint_sensor(
            x=200, y=0,
            name="Exit Sensor"
        )
    )

    # Create conveyors that can be controlled
    conveyor1 = SceneObject(
        name="Main Conveyor",
        scene_object_type="Conveyor",
        physics_body=ConveyorBody(
            name="Main Conveyor",
            x=0, y=50,
            width=300, height=30,
            belt_speed=50.0
        )
    )

    conveyor2 = SceneObject(
        name="Side Conveyor",
        scene_object_type="Conveyor",
        physics_body=ConveyorBody(
            name="Side Conveyor",
            x=0, y=100,
            width=300, height=30,
            belt_speed=30.0
        )
    )

    # Add objects to scene
    scene.add_scene_object(sensor1)
    scene.add_scene_object(sensor2)
    scene.add_scene_object(conveyor1)
    scene.add_scene_object(conveyor2)

    # Create connection registry and register physics bodies (not SceneObjects)
    # The physics bodies have the actual callback lists and methods
    registry = ConnectionRegistry()
    for obj_id, obj in scene.scene_objects.items():
        registry.register_object(obj_id, obj.physics_body)

    # Example: Create a programmatic connection (optional)
    # This connects sensor1's activate callback to conveyor1's start method
    # registry.connect(
    #     sensor1.id, "on_activate_callbacks",
    #     conveyor1.id, "start"
    # )

    # Create the GUI window
    root = tk.Tk()
    root.title("Connection Editor Example")
    root.geometry("1400x900")
    root.configure(bg="#2b2b2b")

    # Add instructions
    instructions = tk.Label(
        root,
        text=(
            "CONNECTION EDITOR INSTRUCTIONS:\n\n"
            "1. CREATING CONNECTIONS: Click and drag from an OUTPUT port (orange, right side) "
            "to an INPUT port (purple, left side)\n"
            "2. MOVING NODES: Click and drag a node to reposition it\n"
            "3. PANNING: Middle-click and drag to pan the canvas\n"
            "4. DELETING: Right-click a connection line and select 'Delete Connection'\n"
            "5. TESTING: Right-click a connection and select 'Test Connection' or use 'Test All' button\n"
            "6. AUTO LAYOUT: Use the 'Auto Layout' button to organize nodes in a grid\n"
            "7. SAVING: Click 'Save' to persist connections to the scene"
        ),
        bg="#2b2b2b",
        fg="white",
        font=("Arial", 10),
        justify=tk.LEFT,
        padx=10,
        pady=10
    )
    instructions.pack(side=tk.TOP, fill=tk.X)

    # Create the connection editor
    editor = ConnectionEditor(
        root,
        scene=scene,
        connection_registry=registry
    )
    editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Example connections you can create:
    # - Entry Sensor (on_activate) → Main Conveyor (start)
    # - Entry Sensor (on_deactivate) → Main Conveyor (stop)
    # - Exit Sensor (on_activate) → Side Conveyor (start)
    # - Exit Sensor (on_object_enter) → Main Conveyor (stop)

    print("\n" + "="*60)
    print("CONNECTION EDITOR EXAMPLE")
    print("="*60)
    print("\nAvailable Objects:")
    for obj_id, obj in scene.scene_objects.items():
        print(f"  - {obj.name} ({obj_id})")
        outputs = obj.get_outputs()
        inputs = obj.get_inputs()
        if outputs:
            print(f"    Outputs: {', '.join(outputs.keys())}")
        if inputs:
            print(f"    Inputs: {', '.join(inputs.keys())}")

    print("\nTry creating connections in the GUI!")
    print("When done, click 'Save' to persist connections to the scene.\n")

    # Run the GUI
    root.mainloop()

    # After closing, show what was connected
    print("\n" + "="*60)
    print("FINAL CONNECTIONS")
    print("="*60)
    if registry._connections:
        for conn in registry._connections:
            print(f"  {conn.source_id}.{conn.source_output} → {conn.target_id}.{conn.target_input}")
        print(f"\nTotal connections: {len(registry._connections)}")
    else:
        print("  No connections were created")

    # Serialize connections for saving
    serialized = registry.serialize()
    print("\n" + "="*60)
    print("SERIALIZED FORMAT (for saving to file)")
    print("="*60)
    import json
    print(json.dumps(serialized, indent=2))


if __name__ == "__main__":
    main()
