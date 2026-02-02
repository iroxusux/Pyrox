"""Concrete physics body implementations.

This module provides specific physics body types that can be used in simulations,
such as conveyor belts, crates, platforms, and other interactive objects.

These are concrete implementations built on top of the PhysicsBody2D protocol
implementation from pyrox.models.protocols.physics.
"""
from .base import BasePhysicsBody
from .conveyor import ConveyorBody
from .crate import CrateBody
from .factory import PhysicsSceneFactory, PhysicsSceneTemplate

__all__ = [
    'BasePhysicsBody',
    'ConveyorBody',
    'CrateBody',
    'PhysicsSceneFactory',
    'PhysicsSceneTemplate',
]
