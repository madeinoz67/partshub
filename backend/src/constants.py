"""
Shared constants and enums for the application.
"""

from enum import Enum


class StorageLocationType(str, Enum):
    """Valid storage location types matching database constraints."""

    CONTAINER = "container"
    ROOM = "room"
    BUILDING = "building"
    CABINET = "cabinet"
    DRAWER = "drawer"
    SHELF = "shelf"
    BIN = "bin"
    BOX = "box"
    BAG = "bag"
