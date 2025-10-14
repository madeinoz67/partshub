"""
Models package for PartsHub backend.

Imports all models to ensure proper SQLAlchemy relationship initialization.
"""

# Import Base first
from ..database import Base
from .api_token import APIToken
from .attachment import Attachment
from .category import Category

# Import all models to ensure they are registered with SQLAlchemy
from .component import Component
from .component_location import ComponentLocation
from .custom_field import CustomField, CustomFieldValue, FieldType
from .kicad_data import KiCadLibraryData
from .meta_part import MetaPart, MetaPartComponent
from .project import Project, ProjectComponent, ProjectStatus
from .provider import ComponentDataProvider
from .provider_data import ComponentProviderData
from .provider_link import ProviderLink
from .purchase import Purchase, PurchaseItem
from .resource import Resource
from .saved_search import SavedSearch
from .stock_transaction import StockTransaction, TransactionType
from .storage_location import StorageLocation
from .substitute import Substitute
from .supplier import Supplier
from .tag import Tag, component_tags
from .user import User
from .wizard_provider import Provider

# Export all models
__all__ = [
    "Base",
    "Component",
    "ComponentLocation",
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
    "Provider",
    "ProviderLink",
    "Resource",
    "SavedSearch",
]
