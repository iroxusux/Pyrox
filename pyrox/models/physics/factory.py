"""Physics body factory for creating and registering physics body templates.

Provides a factory pattern for managing physics body templates that can be
instantiated in the scene viewer or other contexts.
"""
from typing import Any, Callable, Dict, Optional, Type
from pyrox.interfaces import IBasePhysicsBody
from pyrox.services.logging import log
from pyrox.models.factory import MetaFactory


class PhysicsSceneTemplate:
    """Template definition for creating physics bodies.

    Stores configuration and factory function for creating physics bodies
    of a specific type.

    Attributes:
        name: Display name of the template
        description: Description of what this template creates
        body_class: The physics body class to instantiate
        default_kwargs: Default keyword arguments for instantiation
        factory_func: Optional custom factory function
        icon: Optional icon identifier
        category: Category for organization (e.g., "Static", "Dynamic", "Special")
    """

    def __init__(
        self,
        name: str,
        body_class: Type[IBasePhysicsBody],
        description: str = "",
        default_kwargs: Optional[Dict[str, Any]] = None,
        factory_func: Optional[Callable[..., IBasePhysicsBody]] = None,
        icon: str = "",
        category: str = "General",
    ):
        """Initialize physics body template.

        Args:
            name: Display name
            body_class: Physics body class to instantiate
            description: Description of the template
            default_kwargs: Default constructor arguments
            factory_func: Custom factory function (overrides body_class if provided)
            icon: Icon identifier for UI
            category: Organization category
        """
        self.name = name
        self.body_class = body_class
        self.description = description
        self.default_kwargs = default_kwargs or {}
        self.factory_func = factory_func
        self.icon = icon
        self.category = category

    def create(self, **override_kwargs) -> IBasePhysicsBody:
        """Create an instance from this template.

        Args:
            **override_kwargs: Arguments to override defaults

        Returns:
            New physics body instance
        """
        # Merge default kwargs with overrides
        kwargs = {**self.default_kwargs, **override_kwargs}

        # Use custom factory function if provided
        if self.factory_func:
            return self.factory_func(**kwargs)

        # Otherwise instantiate the body class
        return self.body_class(**kwargs)

    def __repr__(self) -> str:
        return f"<PhysicsBodyTemplate '{self.name}' class={self.body_class.__name__}>"


class PhysicsSceneFactory(MetaFactory):
    """Factory for managing physics body templates.

    Provides registration and creation of physics body templates using
    the factory pattern. Templates can be registered programmatically
    or through configuration.

    Usage:
        # Register a template
        PhysicsBodyFactory.register_template(
            "Wooden Crate",
            PhysicsBodyTemplate(
                name="Wooden Crate",
                body_class=CrateBody,
                default_kwargs={"crate_type": "wooden", "mass": 10.0}
            )
        )

        # Create from template
        crate = PhysicsBodyFactory.create_from_template(
            "Wooden Crate",
            x=100.0,
            y=200.0
        )
    """

    _templates: Dict[str, PhysicsSceneTemplate] = {}

    @classmethod
    def register_template(
        cls,
        template_name: str,
        template: PhysicsSceneTemplate
    ) -> None:
        """Register a physics body template.

        Args:
            template_name: Unique name for the template
            template: PhysicsBodyTemplate instance
        """
        if template_name in cls._templates:
            log(cls).warning(f"Template '{template_name}' already registered, overwriting.")

        cls._templates[template_name] = template
        log(cls).debug(f"Registered physics body template: {template_name}")

    @classmethod
    def unregister_template(cls, template_name: str) -> bool:
        """Unregister a physics body template.

        Args:
            template_name: Name of template to remove

        Returns:
            True if template was removed, False if not found
        """
        if template_name in cls._templates:
            del cls._templates[template_name]
            log(cls).debug(f"Unregistered physics body template: {template_name}")
            return True
        return False

    @classmethod
    def get_template(cls, template_name: str) -> Optional[PhysicsSceneTemplate]:
        """Get a registered template by name.

        Args:
            template_name: Name of the template

        Returns:
            PhysicsBodyTemplate if found, None otherwise
        """
        return cls._templates.get(template_name)

    @classmethod
    def get_all_templates(cls) -> Dict[str, PhysicsSceneTemplate]:
        """Get all registered templates.

        Returns:
            Dictionary of template name to PhysicsBodyTemplate
        """
        return cls._templates.copy()

    @classmethod
    def get_templates_by_category(cls, category: str) -> Dict[str, PhysicsSceneTemplate]:
        """Get all templates in a specific category.

        Args:
            category: Category to filter by

        Returns:
            Dictionary of matching templates
        """
        return {
            name: template
            for name, template in cls._templates.items()
            if template.category == category
        }

    @classmethod
    def get_categories(cls) -> list[str]:
        """Get list of all unique categories.

        Returns:
            List of category names
        """
        categories = {template.category for template in cls._templates.values()}
        return sorted(categories)

    @classmethod
    def create_from_template(
        cls,
        template_name: str,
        **kwargs
    ) -> Optional[IBasePhysicsBody]:
        """Create a physics body from a registered template.

        Args:
            template_name: Name of the template to use
            **kwargs: Arguments to override template defaults

        Returns:
            New physics body instance, or None if template not found
        """
        template = cls.get_template(template_name)
        if not template:
            log(cls).error(f"Template '{template_name}' not found")
            return None

        try:
            return template.create(**kwargs)
        except Exception as e:
            log(cls).error(f"Failed to create body from template '{template_name}': {e}")
            return None


__all__ = [
    'PhysicsSceneTemplate',
    'PhysicsSceneFactory',
]
