"""Concrete physics body implementations.

This module provides specific physics body types that can be used in simulations,
such as conveyor belts, crates, platforms, UI panels, proximity sensors, and other
interactive objects.

These are concrete implementations built on top of the PhysicsBody2D protocol
implementation from pyrox.models.protocols.physics.
"""
from .base import BasePhysicsBody
from .conveyor import ConveyorBody
from .crate import CrateBody
from .ui_panel import UIPanelBody, UIButtonBody
from .sensor import ProximitySensorBody
from .factory import PhysicsSceneFactory, PhysicsSceneTemplate

__all__ = [
    'BasePhysicsBody',
    'ConveyorBody',
    'CrateBody',
    'UIPanelBody',
    'UIButtonBody',
    'ProximitySensorBody',
    'PhysicsSceneFactory',
    'PhysicsSceneTemplate',
]
