"""Scene object factory for creating and registering scene object templates.

Provides a factory pattern for managing scene object templates that can be
instantiated directly in the scene viewer or other contexts, without needing
to wrap a physics body first.
"""
from typing import Any, Callable, Dict, Optional, Type

from pyrox.interfaces import ISceneObject
from pyrox.services.logging import log
from pyrox.models.factory import MetaFactory


class SceneObjectTemplate:
    """Template definition for creating scene objects.

    Stores configuration and factory function for creating scene objects
    of a specific type.  Unlike :class:`PhysicsSceneTemplate`, the object
    produced is already a full :class:`ISceneObject` — no physics-body
    wrapping step is required.

    Attributes:
        name: Display name of the template
        description: Description of what this template creates
        scene_object_class: The scene object class to instantiate
        default_kwargs: Default keyword arguments for instantiation
        factory_func: Optional custom factory function (overrides scene_object_class)
        icon: Optional icon identifier
        category: Category for organisation (e.g. "Conveyor", "Sensor")
    """

    def __init__(
        self,
        name: str,
        scene_object_class: Type[ISceneObject],
        description: str = "",
        default_kwargs: Optional[Dict[str, Any]] = None,
        factory_func: Optional[Callable[..., ISceneObject]] = None,
        icon: str = "",
        category: str = "General",
    ):
        """Initialise a scene object template.

        Args:
            name: Display name
            scene_object_class: Scene object class to instantiate
            description: Human-readable description
            default_kwargs: Default constructor arguments
            factory_func: Custom factory function that overrides scene_object_class
            icon: Icon identifier for UI display
            category: Organisation category shown in the palette
        """
        self.name = name
        self.scene_object_class = scene_object_class
        self.description = description
        self.default_kwargs = default_kwargs or {}
        self.factory_func = factory_func
        self.icon = icon
        self.category = category

    def create(self, **override_kwargs: Any) -> ISceneObject:
        """Create a scene object instance from this template.

        Args:
            **override_kwargs: Arguments to override template defaults

        Returns:
            New scene object instance
        """
        kwargs = {**self.default_kwargs, **override_kwargs}
        if self.factory_func:
            return self.factory_func(**kwargs)
        return self.scene_object_class(**kwargs)

    def __repr__(self) -> str:
        return f"<SceneObjectTemplate '{self.name}' class={self.scene_object_class.__name__}>"


class SceneObjectFactory(MetaFactory):
    """Factory for managing scene object templates.

    Provides registration and creation of scene object templates using
    the factory pattern.  Use this when you want to place custom
    :class:`SceneObject` subclasses directly into a scene from the
    palette — as opposed to :class:`PhysicsSceneFactory` which creates
    bare physics bodies that are then wrapped in a generic scene object.

    Usage::

        class MyCraneObject(SceneObject):
            def __init__(self, x: float = 0.0, y: float = 0.0, **kwargs):
                body = BasePhysicsBody(x=x, y=y, width=60, height=80)
                super().__init__(
                    name="Crane",
                    scene_object_type="MyCraneObject",
                    physics_body=body,
                    **kwargs
                )

        SceneObjectFactory.register_template(
            "My Crane",
            SceneObjectTemplate(
                name="My Crane",
                scene_object_class=MyCraneObject,
                description="Industrial crane unit",
                default_kwargs={"x": 0.0, "y": 0.0},
                category="Equipment",
            )
        )

        # Templates registered above will appear automatically in the
        # scene viewer object palette under their category heading.
    """

    _templates: Dict[str, SceneObjectTemplate] = {}

    @classmethod
    def register_template(
        cls,
        template: SceneObjectTemplate,
    ) -> None:
        """Register a scene object template.

        Args:
            template_name: Unique name for the template
            template: SceneObjectTemplate instance
        """
        if template.name in cls._templates:
            log(cls).warning(f"Template '{template.name}' already registered, overwriting.")
        cls._templates[template.name] = template
        log(cls).debug(f"Registered scene object template: {template.name}")

    @classmethod
    def unregister_template(cls, template_name: str) -> bool:
        """Unregister a scene object template.

        Args:
            template_name: Name of the template to remove

        Returns:
            True if the template was removed, False if it was not found
        """
        if template_name in cls._templates:
            del cls._templates[template_name]
            log(cls).debug(f"Unregistered scene object template: {template_name}")
            return True
        return False

    @classmethod
    def get_template(cls, template_name: str) -> Optional[SceneObjectTemplate]:
        """Get a registered template by name.

        Args:
            template_name: Name of the template

        Returns:
            SceneObjectTemplate if found, None otherwise
        """
        return cls._templates.get(template_name)

    @classmethod
    def get_all_templates(cls) -> Dict[str, SceneObjectTemplate]:
        """Get all registered templates.

        Returns:
            Dictionary mapping template name to SceneObjectTemplate
        """
        return cls._templates.copy()

    @classmethod
    def get_templates_by_category(cls, category: str) -> Dict[str, SceneObjectTemplate]:
        """Get all templates in a specific category.

        Args:
            category: Category to filter by

        Returns:
            Dictionary of matching templates
        """
        return {
            name: tmpl
            for name, tmpl in cls._templates.items()
            if tmpl.category == category
        }

    @classmethod
    def get_categories(cls) -> list[str]:
        """Get list of all unique categories.

        Returns:
            Sorted list of category names
        """
        categories = {tmpl.category for tmpl in cls._templates.values()}
        return sorted(categories)

    @classmethod
    def create_from_template(
        cls,
        template_name: str,
        **kwargs: Any,
    ) -> Optional[ISceneObject]:
        """Create a scene object from a registered template.

        Args:
            template_name: Name of the template to use
            **kwargs: Arguments to override template defaults

        Returns:
            New scene object instance, or None if the template is not found
        """
        template = cls._templates.get(template_name)
        if not template:
            log(cls).warning(f"Template '{template_name}' not found in SceneObjectFactory.")
            return None
        return template.create(**kwargs)
