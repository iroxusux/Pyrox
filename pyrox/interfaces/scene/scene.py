"""
Scene management for field scene_object simulations.
"""
from abc import abstractmethod
from pathlib import Path
from typing import (
    Callable,
    Protocol,
    TypeVar,
)
from pyrox.interfaces import (
    ICoreMixin,
    IBasePhysicsBody,
    IPhysicsBody2D,
    IConnectionRegistry,
)
from pyrox.interfaces.scene.sceneobject import ISceneObject
from pyrox.interfaces.scene.compositesceneobject import ICompositeSceneObject
from pyrox.interfaces.scene.scenegroup import ISceneGroup


T = TypeVar("T", bound=ISceneObject | ICompositeSceneObject | ISceneGroup)


class IScene(ICoreMixin):
    """
    Scene Interface for managing scene objects within a scene.
    """

    def get_scene_object(self, scene_object_id: str) -> ISceneObject | ICompositeSceneObject | ISceneGroup | None: ...
    def get_scene_objects(self) -> dict[str, ISceneObject | ICompositeSceneObject | ISceneGroup]: ...
    def set_scene_objects(self, scene_objects: dict[str, T]) -> None: ...
    def add_scene_object(self, scene_object: ISceneObject | ICompositeSceneObject | ISceneGroup) -> None: ...
    def get_on_scene_object_added(self) -> list[Callable]: ...
    def remove_scene_object(self, scene_object_id: str) -> None: ...
    def get_on_scene_object_removed(self) -> list[Callable]: ...
    def get_connection_registry(self) -> "IConnectionRegistry": ...
    def set_connection_registry(self, registry: "IConnectionRegistry") -> None: ...
    def get_on_scene_updated(self) -> list[Callable]: ...
    def update(self, delta_time: float) -> None: ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "IScene": ...
    def save(self, filepath: str | Path) -> None: ...
    @classmethod
    def load(cls, filepath: str | Path) -> "IScene": ...

    # ------------------------------------------------------------------
    # Group convenience helpers
    # ------------------------------------------------------------------

    def group_objects(self, object_ids: list[str], name: str = "Group", layer: int = 0) -> "ISceneGroup": ...
    def ungroup(self, group_id: str) -> list[ISceneObject]: ...

    # ------------------------------------------------------------------
    # Property accessors
    # ------------------------------------------------------------------
    scene_objects = property(get_scene_objects, set_scene_objects)
    on_scene_object_added = property(get_on_scene_object_added)
    on_scene_object_removed = property(get_on_scene_object_removed)
    on_scene_updated = property(get_on_scene_updated)

    @property
    def connection_registry(self) -> "IConnectionRegistry":
        return self.get_connection_registry()

    @connection_registry.setter
    def connection_registry(self, registry: "IConnectionRegistry") -> None:
        self.set_connection_registry(registry)


class ISceneRunnerService(Protocol):
    """ Service interface for running and managing scenes.
    """

    @classmethod
    @abstractmethod
    def get_scene(cls) -> IScene | None:
        """Get the scene being managed.

        Returns:
            IScene: The scene instance.
        """
        ...

    @classmethod
    @abstractmethod
    def set_scene(cls, scene: IScene | None) -> None:
        """Set the scene to be managed.

        Args:
            scene (IScene): The scene instance to set.
        """
        ...

    @classmethod
    @abstractmethod
    def get_scene_filepath(cls) -> Path | None:
        """Return the filepath of the currently loaded/saved scene, or None.

        Set automatically by load_scene and save_scene; cleared by new_scene.
        """
        ...

    @classmethod
    @abstractmethod
    def load_scene(cls, filepath: str | Path | None = None) -> None:
        """Load a scene from a file.

        Args:
            filepath: Path to the scene file.  When *None* a file-open dialog
                      is presented to the user.
        """
        ...

    @classmethod
    @abstractmethod
    def save_scene(cls, filepath: str | Path | None = None) -> None:
        """Save the current scene to a file.

        When *filepath* is *None* the service first tries the last known
        filepath (enabling quick-save); only if that is also unknown is a
        file-save dialog presented.

        Args:
            filepath: Destination path.  Omit for quick-save behaviour.
        """
        ...

    @classmethod
    @abstractmethod
    def get_physics_engine(cls) -> object | None:
        """Get the physics engine being used.

        Returns:
            The physics engine instance, or None if physics is disabled.
        """
        ...

    @classmethod
    @abstractmethod
    def set_physics_engine(cls, physics_engine) -> None:
        """Set the physics engine to be used.

        Args:
            physics_engine: The physics engine instance to set.
        """
        ...

    @classmethod
    @abstractmethod
    def get_environment(cls) -> object | None:
        """Get the environment service being used.

        Returns:
            The environment service instance, or None if physics is disabled.
        """
        ...

    @classmethod
    @abstractmethod
    def set_environment(cls, environment: object) -> None:
        """Set the environment service to be used.

        Args:
            environment: The environment service instance to set.
        """
        ...

    @classmethod
    @abstractmethod
    def set_update_rate(cls, fps: float) -> None:
        """Set the update rate for the scene runner.

        Args:
            fps (float): The desired frames per second.
        """
        ...

    @classmethod
    @abstractmethod
    def get_update_rate(cls) -> float:
        """Get the current update rate for the scene runner.

        Returns:
            float: The current frames per second.
        """
        ...

    @classmethod
    @abstractmethod
    def add_physics_body(cls, body: IBasePhysicsBody | IPhysicsBody2D) -> None:
        """Add a physics body to the simulation.

        Args:
            body: Object implementing IBasePhysicsBody protocol
        """
        ...

    @classmethod
    @abstractmethod
    def remove_physics_body(cls, body: IBasePhysicsBody) -> None:
        """Remove a physics body from the simulation.

        Args:
            body: Object to remove
        """
        ...

    @classmethod
    @abstractmethod
    def get_physics_stats(cls) -> dict:
        """Get physics engine statistics.

        Returns:
            dictionary with physics stats, or empty dict if physics disabled
        """
        ...


__all__ = ["IScene"]
