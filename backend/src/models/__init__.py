"""
Models package for PartsHub backend.

Imports all models to ensure proper SQLAlchemy relationship initialization.
"""

# Import Base first
from ..database import Base

# Import all models to ensure they are registered with SQLAlchemy
from .component import Component
from .storage_location import StorageLocation
from .category import Category
from .project import Project, ProjectComponent, ProjectStatus
from .stock_transaction import StockTransaction, TransactionType
from .tag import Tag, component_tags
from .attachment import Attachment
from .custom_field import CustomField, CustomFieldValue, FieldType
from .substitute import Substitute
from .user import User
from .api_token import APIToken
from .supplier import Supplier
from .purchase import Purchase, PurchaseItem
from .provider import ComponentDataProvider
from .provider_data import ComponentProviderData
from .kicad_data import KiCadLibraryData
from .meta_part import MetaPart, MetaPartComponent

# Export all models
__all__ = [
    "Base",
    "Component",
    "StorageLocation",
    "Category",
    "Project",
    "ProjectComponent",
    "ProjectStatus",
    "StockTransaction",
    "TransactionType",
    "Tag",
    "component_tags",
    "Attachment",
    "CustomField",
    "CustomFieldValue",
    "FieldType",
    "Substitute",
    "User",
    "APIToken",
    "Supplier",
    "Purchase",
    "PurchaseItem",
    "ComponentDataProvider",
    "ComponentProviderData",
    "KiCadLibraryData",
    "MetaPart",
    "MetaPartComponent",
]