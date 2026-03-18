# =============================================================================
# SCENE WORKFLOW TODO
# =============================================================================
# The scene system has several structural issues that need to be addressed to
# make everything more consistent, less confusing, and easier to serialize.
# Work through these items one by one — each is a self-contained cleanup.
#
# RULE: Everything placed in a scene MUST be a SceneObject (or subclass).
#       Bare physics bodies are components owned by SceneObjects, never placed
#       directly as scene citizens.
#
# -----------------------------------------------------------------------------
# TODO-SCENE-01: SceneObject should own its own name  [DONE]
#   SceneObject now stores self._name and get_name/set_name use it directly.
#   IBasePhysicsBody no longer extends INameable — name is not part of the
#   physics body contract.  BasePhysicsBody keeps a 'name' field as a private
#   debugging label (used in __repr__ and ID generation) but it is no longer
#   written from SceneObject and is not part of the public interface.
#
# TODO-SCENE-02: template_name belongs on SceneObject, not the physics body
#   PROBLEM:  BasePhysicsBody carries _template_name which is used by
#             SceneObject.from_dict to look up PhysicsSceneFactory.  A
#             template name is a factory / serialization concern for the
#             scene entity, not a physics simulation concern.
#   FIX:      Add template_name to SceneObject (stored as self._template_name).
#             Remove it from BasePhysicsBody and IBasePhysicsBody.
#             Update to_dict / from_dict accordingly.
#
# TODO-SCENE-03: Unify the two factory systems into one
#   PROBLEM:  PhysicsSceneFactory (registers bare physics bodies that are then
#             wrapped in a generic SceneObject) and SceneObjectFactory (registers
#             full SceneObject subclasses) do the same job at different levels.
#             This split means custom SceneObject subclasses registered in
#             SceneObjectFactory cannot be reconstructed from a saved scene
#             (Scene.from_dict falls back to the physics-body path for plain
#             objects, bypassing SceneObjectFactory entirely).
#   FIX:      SceneObjectFactory becomes the single registration point.
#             SceneObjectTemplate references a SceneObject subclass (which
#             owns its physics body internally).  Deprecate / remove
#             PhysicsSceneFactory and PhysicsSceneTemplate.  Migrate all
#             existing physics-body templates to SceneObject subclasses.
#
# TODO-SCENE-04: Fix SceneObject.from_dict to use SceneObjectFactory
#   PROBLEM:  Currently looks up PhysicsSceneFactory by the body's
#             template_name, reconstructs the physics body, then wraps it.
#             Any custom SceneObject subclass is lost after a save/load cycle.
#   FIX:      After TODO-SCENE-02/03: from_dict looks up SceneObjectFactory
#             by scene_object_type (or template_name on SceneObject).  The
#             located template's class handles full reconstruction via its own
#             from_dict.  Base SceneObject.from_dict serves as the fallback.
#
# TODO-SCENE-05: Fix Scene.from_dict to use SceneObjectFactory for all types
#   PROBLEM:  Scene.from_dict has a hardcoded conditional — composites go via
#             SceneObjectFactory.create_from_template, but plain objects go
#             via SceneObject.from_dict → PhysicsSceneFactory.  The type
#             detection is also fragile (string comparison on scene_object_type
#             rather than factory lookup).
#   FIX:      After TODO-SCENE-03/04: Scene.from_dict dispatches every object
#             through SceneObjectFactory, with SceneObject.from_dict as the
#             fallback for any unknown type.  Remove the hardcoded type checks.
#
# TODO-SCENE-06: Remove redundant top-level "material" key from to_dict
#   PROBLEM:  SceneObject.to_dict emits "material" as a top-level key AND
#             it is already nested inside "body".  Inconsistent; one will
#             silently diverge from the other.
#   FIX:      Remove the top-level "material" key.  Consumers that need
#             material data should read from data["body"]["material"].
#
# TODO-SCENE-07: Replace __getattribute__ delegation with explicit properties
#   PROBLEM:  SceneObject.__getattribute__ catches every AttributeError and
#             silently tries the physics body.  This obscures stack traces,
#             makes the public API of SceneObject invisible, and leaks physics
#             internals as if they are scene-level properties.
#   FIX:      Remove __getattribute__ override.  Explicitly expose the physics
#             properties that belong on a SceneObject's public API as @property
#             accessors (x, y, width, height, yaw, velocity_x/y, etc.).
#             All other physics body access should go through scene_object.body.
#
# TODO-SCENE-08: Move tags from BasePhysicsBody to SceneObject
#   PROBLEM:  IBasePhysicsBody / BasePhysicsBody carry tags (get_tags, add_tag,
#             etc.) which are used for gameplay / logic categorisation ("enemy",
#             "destructible", …).  These are scene-entity concerns, not physics
#             simulation concerns.  Physics-layer classification already exists
#             via collision_layer / collision_mask.
#   FIX:      Move _tags, get_tags, set_tags, has_tag, add_tag, remove_tag to
#             SceneObject.  Remove from IBasePhysicsBody and BasePhysicsBody.
#
# TODO-SCENE-09: Reconsider IConnectable on IBasePhysicsBody
#   PROBLEM:  IBasePhysicsBody extends IConnectable (inputs/outputs for the
#             connection graph).  Logical connections between scene entities are
#             a SceneObject concern — the physics body (mass, velocity, collider)
#             should not be part of the connection registry.
#   FIX:      Remove IConnectable from IBasePhysicsBody.  SceneObject already
#             uses the connection registry via Scene; ensure SceneObject (or
#             specialised subclasses) implement IConnectable as needed instead.
#
# TODO-SCENE-10: Audit / complete _compile_properties
#   PROBLEM:  SceneObject.get_properties calls _compile_properties() but the
#             method's contract is unclear — subclasses override it but there
#             is no documented invariant for what it must populate or when it
#             is safe to call.  Also, set_property writes both to the live
#             attribute AND to self._properties dict, creating two sources of
#             truth.
#   FIX:      Clarify _compile_properties contract (write to self._properties
#             from live attrs); document that self._properties is a
#             serialisation snapshot, not the live store.  Ensure all
#             subclass overrides call super()._compile_properties() first.
#
# TODO-SCENE-11: CompositeSceneObject serialization round-trip
#   PROBLEM:  CompositeSceneObject has child components with relative offsets.
#             from_dict currently uses SceneObject.from_dict for each child,
#             which goes through PhysicsSceneFactory (same problem as SCENE-04).
#             Also unclear if offset data survives a full scene save/load cycle.
#   FIX:      After TODO-SCENE-03/04, verify composite round-trip end-to-end
#             with a test.  Ensure component offsets are included in to_dict
#             and restored in from_dict.
# =============================================================================

from .sceneobject import SceneObject
from .scene import Scene
from .factory import SceneObjectFactory, SceneObjectTemplate
from .scenebridge import (
    BindingDirection,
    SceneBinding,
    SceneBridge,
)
from .sceneboundlayer import SceneBoundLayer
from .scenegroup import SceneGroup
from .compositesceneobject import CompositeSceneObject
from .sources import KeyboardSource
from .animation import (
    AnimationClip,
    AnimationEasing,
    AnimationMode,
    AnimationTrack,
    Keyframe,
    SceneAnimator,
)
from . import assets, sources


__all__ = [
    "SceneObject",
    "Scene",
    "SceneObjectFactory",
    "SceneObjectTemplate",
    "BindingDirection",
    "SceneBinding",
    "SceneBridge",
    "SceneBoundLayer",
    "SceneGroup",
    "CompositeSceneObject",
    "KeyboardSource",
    "AnimationClip",
    "AnimationEasing",
    "AnimationMode",
    "AnimationTrack",
    "Keyframe",
    "SceneAnimator",
    "assets",
    "sources",
]
