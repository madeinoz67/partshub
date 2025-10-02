"""
AttachmentService for managing component file attachments.
"""

import uuid
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models import Attachment, Component


class AttachmentService:
    """Service layer for attachment operations."""

    def __init__(self, db: Session):
        self.db = db

    def component_exists(self, component_id: str) -> bool:
        """Check if a component exists."""
        return (
            self.db.query(Component).filter(Component.id == component_id).first()
            is not None
        )

    def list_attachments(self, component_id: str) -> list[Attachment]:
        """List all attachments for a component, ordered by display_order."""
        return (
            self.db.query(Attachment)
            .filter(Attachment.component_id == component_id)
            .order_by(Attachment.display_order, Attachment.created_at)
            .all()
        )

    def get_attachment(
        self, attachment_id: str, component_id: str = None
    ) -> Attachment | None:
        """Get a specific attachment, optionally filtered by component."""
        query = self.db.query(Attachment).filter(Attachment.id == attachment_id)

        if component_id:
            query = query.filter(Attachment.component_id == component_id)

        return query.first()

    def create_attachment(self, attachment_data: dict[str, Any]) -> Attachment:
        """Create a new attachment."""
        # Generate ID if not provided
        if "id" not in attachment_data:
            attachment_data["id"] = str(uuid.uuid4())

        attachment = Attachment(**attachment_data)

        # If this is set as primary image, unset other primary images for this component
        if attachment_data.get("is_primary_image"):
            self._clear_primary_images(attachment_data["component_id"])

        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)

        return attachment

    def update_attachment(
        self, attachment_id: str, component_id: str, update_data: dict[str, Any]
    ) -> Attachment | None:
        """Update attachment metadata."""
        attachment = self.get_attachment(attachment_id, component_id)

        if not attachment:
            return None

        # If setting as primary image, clear other primary images first
        if update_data.get("is_primary_image"):
            self._clear_primary_images(component_id)

        for key, value in update_data.items():
            if hasattr(attachment, key):
                setattr(attachment, key, value)

        self.db.commit()
        self.db.refresh(attachment)

        return attachment

    def delete_attachment(self, attachment_id: str, component_id: str) -> bool:
        """Delete an attachment."""
        attachment = self.get_attachment(attachment_id, component_id)

        if not attachment:
            return False

        self.db.delete(attachment)
        self.db.commit()

        return True

    def set_primary_image(
        self, attachment_id: str, component_id: str
    ) -> Attachment | None:
        """Set an attachment as the primary image for a component."""
        attachment = self.get_attachment(attachment_id, component_id)

        if not attachment:
            return None

        # Check if it's an image
        if not attachment.mime_type.startswith("image/"):
            return None

        # Clear other primary images for this component
        self._clear_primary_images(component_id)

        # Set this as primary
        attachment.is_primary_image = True
        self.db.commit()
        self.db.refresh(attachment)

        return attachment

    def get_primary_image(self, component_id: str) -> Attachment | None:
        """Get the primary image attachment for a component."""
        return (
            self.db.query(Attachment)
            .filter(
                and_(
                    Attachment.component_id == component_id,
                    Attachment.is_primary_image is True,
                    Attachment.mime_type.like("image/%"),
                )
            )
            .first()
        )

    def get_images(self, component_id: str) -> list[Attachment]:
        """Get all image attachments for a component, ordered by display_order."""
        return (
            self.db.query(Attachment)
            .filter(
                and_(
                    Attachment.component_id == component_id,
                    Attachment.mime_type.like("image/%"),
                )
            )
            .order_by(Attachment.display_order, Attachment.created_at)
            .all()
        )

    def get_datasheets(self, component_id: str) -> list[Attachment]:
        """Get all datasheet attachments for a component."""
        return (
            self.db.query(Attachment)
            .filter(
                and_(
                    Attachment.component_id == component_id,
                    or_(
                        Attachment.attachment_type == "datasheet",
                        Attachment.mime_type == "application/pdf",
                    ),
                )
            )
            .order_by(Attachment.created_at)
            .all()
        )

    def _clear_primary_images(self, component_id: str) -> None:
        """Clear primary image flag for all images of a component."""
        self.db.query(Attachment).filter(
            and_(
                Attachment.component_id == component_id,
                Attachment.is_primary_image is True,
            )
        ).update({"is_primary_image": False})
