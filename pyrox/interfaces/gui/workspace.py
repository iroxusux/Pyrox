"""Workspace interface module.
Defines the IWorkspace interface for GUI workspaces.
"""
from abc import abstractmethod
from pyrox.interfaces.protocols import ICoreRunnableMixin
from .component import IGuiComponent


class IWorkspace(
    IGuiComponent,
    ICoreRunnableMixin
):
    """Interface for a GUI Workspace.
    """

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
