"""Workspace interface module.
Defines the IWorkspace interface for GUI workspaces.
"""
from abc import abstractmethod
from pyrox.interfaces.protocols import ICoreRunnableMixin
from pyrox.interfaces.gui import ITaskFrame
from .component import IGuiComponent


class IWorkspace(
    IGuiComponent,
    ICoreRunnableMixin
):
    """Interface for a GUI Workspace.
    """

    @property
    def frames(self) -> list[ITaskFrame]:
        """Get all registered frames in the workspace.

        Returns:
            list[ITaskFrame]: List of registered frames.
        """
        return self.get_frames()

    @property
    def panels(self) -> list[IGuiComponent]:
        """Get all panels in the workspace.

        Returns:
            list[IGUIComponent]: List of panels in the workspace.
        """
        return self.get_panels()

    @property
    def status(self) -> str:
        """Get the current status message of the workspace.

        Returns:
            str: The current status message.
        """
        return self.get_status()

    @status.setter
    def status(
        self,
        status: str
    ) -> None:
        """Set the current status message of the workspace.

        Args:
            status (str): The status message to set.
        """
        self.set_status(status)

    @abstractmethod
    def get_frame(
        self,
        frame_name: str
    ) -> ITaskFrame | None:
        """Get a registered frame by name.

        Args:
            frame_name (str): The name of the frame to retrieve.

        Returns:
            ITaskFrame | None: The requested frame, or None if not found.
        """
        pass

    @abstractmethod
    def get_frames(self) -> list[ITaskFrame]:
        """Get all registered frames in the workspace.

        Returns:
            list[ITaskFrame]: List of registered frames.
        """
        pass

    @abstractmethod
    def set_frames(
        self,
        frames: list[ITaskFrame]
    ) -> None:
        """Set the registered frames in the workspace.

        Args:
            frames (list[ITaskFrame]): List of frames to register.
        """
        pass

    @abstractmethod
    def register_frame(
        self,
        frame: ITaskFrame,
        raise_frame: bool = True
    ) -> None:
        """Register a frame with the workspace.

        Args:
            frame (ITaskFrame): The frame to register.
            raise_frame (bool): Whether to bring the frame to the front upon registration.
        """
        pass

    @abstractmethod
    def unregister_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Unregister a frame from the workspace.

        Args:
            frame (ITaskFrame): The frame to unregister.
        """
        pass

    @abstractmethod
    def raise_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Bring a registered frame to the front.

        Args:
            frame (ITaskFrame): The frame to raise.
        """
        pass

    @abstractmethod
    def add_panel(
        self,
        panel: IGuiComponent,
        *args,
        **kwargs
    ) -> None:
        """Add a panel to the workspace.

        Args:
            panel (IGUIComponent): The panel to add.
        """
        pass

    @abstractmethod
    def remove_panel(
        self,
        panel: IGuiComponent
    ) -> None:
        """Remove a panel from the workspace.

        Args:
            panel (IGUIComponent): The panel to remove.
        """
        pass

    @abstractmethod
    def get_panels(self) -> list[IGuiComponent]:
        """Get all panels in the workspace.

        Returns:
            list[IGUIComponent]: List of panels in the workspace.
        """
        pass

    @abstractmethod
    def set_panel_height(
        self,
        panel_id: str,
        height: int
    ) -> None:
        """Set the height of a specific panel.

        Args:
            panel_id (str): The ID of the panel.
            height (int): The height to set for the panel.
        """
        pass

    @abstractmethod
    def get_panel_height(
        self,
        panel_id: str
    ) -> int:
        """Get the height of a specific panel.

        Args:
            panel_id (str): The ID of the panel.

        Returns:
            int: The height of the panel.
        """
        pass

    @abstractmethod
    def clear_panels(self) -> None:
        """Clear all panels from the workspace."""
        pass

    @abstractmethod
    def set_status(
        self,
        status: str
    ) -> None:
        """Set the status message of the workspace.

        Args:
            status (str): The status message to set.
        """
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get the current status message of the workspace.

        Returns:
            str: The current status message.
        """
        pass
