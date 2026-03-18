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
# IN PROGRESS / NEXT
# -----------------------------------------------------------------------------
#
# DONE-SCENE-08: Reconsider IConnectable on IBasePhysicsBody
#   IConnectable removed from IBasePhysicsBody and Connectable removed from
#   BasePhysicsBody (replaced with HasId for id tracking).
#   get_inputs/get_outputs kept on IBasePhysicsBody/BasePhysicsBody as
#   standalone endpoint-discovery methods.
#   ISceneObject now carries the connection contract (get_connections,
#   set_connections, get_inputs, get_outputs); SceneObject implements it,
#   delegating get_inputs/get_outputs to its physics body.
#   ConnectionEditor updated to use scene_obj.get_inputs/outputs().
#
# DONE-SCENE-09: Audit / complete _compile_properties
#   _compile_properties docstring updated: self._properties is a lazy
#   serialisation snapshot built on demand (reads from live attrs).
#   Subclass contract documented: overrides MUST call
#   super()._compile_properties() — already followed by PistonSceneObject.
#   Dual-write removed from set_property: known properties (with a live attr
#   on self or the physics body) are now updated only via setattr; the
#   snapshot is refreshed by _compile_properties on the next get_properties()
#   call.  Truly custom properties (no live attr) still fall through to an
#   else-branch that writes directly to self._properties so they survive
#   serialisation.
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
