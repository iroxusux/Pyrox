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
# SERIALIZATION CONTRACT (target state):
#   SceneObject.to_dict() emits:
#     {
#       "name": ...,                  # owned by SceneObject (SCENE-01 done)
#       "scene_object_type": ...,
#       "template_name": ...,         # SceneObjectFactory lookup key (SCENE-02)
#       "id": ...,
#       "description": ...,
#       "layer": ...,
#       "group_id": ...,
#       "properties": { ... },
#       "body": {                     # emitted by BasePhysicsBody.to_dict()
#         "template_name": ...,       # PhysicsSceneFactory lookup key
#         "body_type": ...,
#         ...physics fields...
#       }
#     }
#
#   Deserialization order (Scene.from_dict → SceneObject.from_dict):
#     1. Read "template_name" → SceneObjectFactory.get_template()
#        → call template.scene_object_class.from_dict(data)
#        (falls back to base SceneObject.from_dict if no template registered)
#     2. Inside SceneObject.from_dict, read data["body"]["template_name"]
#        → PhysicsSceneFactory.get_template() → body_class.from_dict(body_data)
#     Both factories remain; each handles its own layer. No merging needed.
#
# TODO-SCENE-05: Remove redundant top-level "material" key from to_dict  [DONE]
#   Removed the "material" key from SceneObject.to_dict.  Material data is
#   already present inside data["body"]["material"] and all physics body
#   from_dict methods read it from there — the top-level key was never consumed.
#
# IN PROGRESS / NEXT
# -----------------------------------------------------------------------------
#
# TODO-SCENE-06: Replace __getattribute__ delegation with explicit properties
#   PROBLEM:  SceneObject.__getattribute__ catches every AttributeError and
#             silently falls back to the physics body.  This obscures stack
#             traces, hides the public API, and leaks physics internals as if
#             they were scene-level properties.
#   FIX:      Remove __getattribute__ override.  Explicitly expose the physics
#             properties that belong on SceneObject's public API as @property
#             accessors (x, y, width, height, yaw, velocity_x/y, etc.).
#             All other physics body access should go through scene_object.body.
#
# TODO-SCENE-07: Move tags from BasePhysicsBody to SceneObject
#   PROBLEM:  IBasePhysicsBody / BasePhysicsBody carry general-purpose tags
#             (get_tags, add_tag, …) used for gameplay / logic categorisation.
#             These are scene-entity concerns, not physics simulation concerns.
#             Physics-layer classification is already handled by collision_layer
#             and collision_mask.
#   FIX:      Move _tags and all tag methods to SceneObject.
#             Remove from IBasePhysicsBody and BasePhysicsBody.
#
# TODO-SCENE-08: Reconsider IConnectable on IBasePhysicsBody
#   PROBLEM:  IBasePhysicsBody extends IConnectable (inputs/outputs for the
#             connection graph).  Logical connections are a SceneObject concern;
#             the physics simulation (mass, velocity, collider) should not be
#             part of the connection registry.
#   FIX:      Remove IConnectable from IBasePhysicsBody.  Move connection
#             support to SceneObject or specialised subclasses as needed.
#
# TODO-SCENE-09: Audit / complete _compile_properties
#   PROBLEM:  SceneObject.get_properties() calls _compile_properties() but the
#             contract is undocumented.  set_property writes to both the live
#             attribute AND self._properties dict, creating two sources of truth.
#   FIX:      Document that self._properties is a serialisation snapshot built
#             on demand by _compile_properties (reads from live attrs).
#             Ensure all subclass overrides call super()._compile_properties().
#             Remove the dual-write in set_property.
#
# TODO-SCENE-10: CompositeSceneObject serialization round-trip
#   PROBLEM:  CompositeSceneObject.from_dict uses SceneObject.from_dict for
#             child components, which has the same dispatch problem as SCENE-03.
#             Unclear whether component offsets survive a full scene save/load.
#   FIX:      After SCENE-03, verify composite round-trip with an end-to-end
#             test.  Ensure offset_x/offset_y are included in to_dict and
#             correctly restored in from_dict.  Register CompositeSceneObject
#             in SceneObjectFactory so Scene.from_dict dispatch works.
# =============================================================================

from .sceneobject import SceneObject
from .scenegroup import SceneGroup
from .factory import SceneObjectFactory, SceneObjectTemplate
from .scene import Scene
from .scenebridge import (
    BindingDirection,
    SceneBinding,
    SceneBridge,
)
from .sceneboundlayer import SceneBoundLayer
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
