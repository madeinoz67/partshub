"""
Nested attachments API endpoints for component file management.
Implements nested routes under /api/v1/components/{component_id}/attachments
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from ..database import get_db
from ..services.attachment_service import AttachmentService
from ..services.file_storage import file_storage

# Pydantic schemas
class AttachmentResponse(BaseModel):
    id: str
    component_id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    attachment_type: Optional[str] = None
    is_primary_image: bool = False
    thumbnail_path: Optional[str] = None
    display_order: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class AttachmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    attachment_type: Optional[str] = None
    is_primary_image: Optional[bool] = None
    display_order: Optional[int] = None

class AttachmentListResponse(BaseModel):
    attachments: List[AttachmentResponse]
    total: int

router = APIRouter()

# Mock authentication dependency
def require_auth():
    """Mock authentication requirement - allows mock tokens for testing."""
    return {"user_id": "test_user", "username": "test"}

@router.get("/api/v1/components/{component_id}/attachments", response_model=AttachmentListResponse, tags=["attachments"])
def list_component_attachments(
    component_id: str,
    db: Session = Depends(get_db)
):
    """List all attachments for a specific component."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = AttachmentService(db)
    attachments = service.list_attachments(component_id)

    attachment_list = []
    for attachment in attachments:
        attachment_dict = {
            "id": attachment.id,
            "component_id": attachment.component_id,
            "filename": attachment.filename,
            "original_filename": attachment.original_filename,
            "file_size": attachment.file_size,
            "mime_type": attachment.mime_type,
            "title": attachment.title,
            "description": attachment.description,
            "attachment_type": attachment.attachment_type,
            "is_primary_image": attachment.is_primary_image,
            "thumbnail_path": attachment.thumbnail_path,
            "display_order": attachment.display_order,
            "created_at": attachment.created_at.isoformat(),
            "updated_at": attachment.updated_at.isoformat()
        }
        attachment_list.append(attachment_dict)

    return AttachmentListResponse(
        attachments=attachment_list,
        total=len(attachment_list)
    )

@router.post("/api/v1/components/{component_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED, tags=["attachments"])
async def upload_attachment(
    component_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    attachment_type: Optional[str] = Form(None),
    is_primary_image: bool = Form(False),
    display_order: int = Form(0),
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Upload a new attachment for a component."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = AttachmentService(db)

    # Verify component exists
    if not service.component_exists(component_id):
        raise HTTPException(status_code=404, detail="Component not found")

    try:
        # Read file content
        file_content = await file.read()

        # Store file using FileStorageService
        file_path, thumbnail_path, file_size, mime_type, safe_filename = file_storage.store_file(
            component_id=component_id,
            file_content=file_content,
            filename=file.filename or "unknown",
            attachment_type=attachment_type
        )

        # Create attachment record
        attachment_data = {
            "component_id": component_id,
            "filename": safe_filename,
            "original_filename": file.filename or "unknown",
            "file_size": file_size,
            "mime_type": mime_type,
            "file_path": file_path,
            "thumbnail_path": thumbnail_path,
            "title": title,
            "description": description,
            "attachment_type": attachment_type,
            "is_primary_image": is_primary_image,
            "display_order": display_order
        }

        attachment = service.create_attachment(attachment_data)

        return {
            "id": attachment.id,
            "component_id": attachment.component_id,
            "filename": attachment.filename,
            "original_filename": attachment.original_filename,
            "file_size": attachment.file_size,
            "mime_type": attachment.mime_type,
            "title": attachment.title,
            "description": attachment.description,
            "attachment_type": attachment.attachment_type,
            "is_primary_image": attachment.is_primary_image,
            "thumbnail_path": attachment.thumbnail_path,
            "display_order": attachment.display_order,
            "created_at": attachment.created_at.isoformat(),
            "updated_at": attachment.updated_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.get("/api/v1/components/{component_id}/attachments/{attachment_id}", response_model=AttachmentResponse, tags=["attachments"])
def get_attachment(
    component_id: str,
    attachment_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific attachment."""
    try:
        uuid.UUID(component_id)
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID format")

    service = AttachmentService(db)
    attachment = service.get_attachment(attachment_id, component_id)

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return {
        "id": attachment.id,
        "component_id": attachment.component_id,
        "filename": attachment.filename,
        "original_filename": attachment.original_filename,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "title": attachment.title,
        "description": attachment.description,
        "attachment_type": attachment.attachment_type,
        "is_primary_image": attachment.is_primary_image,
        "thumbnail_path": attachment.thumbnail_path,
        "display_order": attachment.display_order,
        "created_at": attachment.created_at.isoformat(),
        "updated_at": attachment.updated_at.isoformat()
    }

@router.put("/api/v1/components/{component_id}/attachments/{attachment_id}", response_model=AttachmentResponse, tags=["attachments"])
def update_attachment(
    component_id: str,
    attachment_id: str,
    attachment_update: AttachmentUpdate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update attachment metadata."""
    try:
        uuid.UUID(component_id)
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID format")

    service = AttachmentService(db)

    # Filter out None values
    update_data = {k: v for k, v in attachment_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=422, detail="No data provided for update")

    attachment = service.update_attachment(attachment_id, component_id, update_data)

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return {
        "id": attachment.id,
        "component_id": attachment.component_id,
        "filename": attachment.filename,
        "original_filename": attachment.original_filename,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "title": attachment.title,
        "description": attachment.description,
        "attachment_type": attachment.attachment_type,
        "is_primary_image": attachment.is_primary_image,
        "thumbnail_path": attachment.thumbnail_path,
        "display_order": attachment.display_order,
        "created_at": attachment.created_at.isoformat(),
        "updated_at": attachment.updated_at.isoformat()
    }

@router.delete("/api/v1/components/{component_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["attachments"])
def delete_attachment(
    component_id: str,
    attachment_id: str,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete an attachment and its associated files."""
    try:
        uuid.UUID(component_id)
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID format")

    service = AttachmentService(db)

    # Get attachment details before deletion
    attachment = service.get_attachment(attachment_id, component_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete files from storage
    file_storage.delete_file(attachment.file_path, attachment.thumbnail_path)

    # Delete database record
    success = service.delete_attachment(attachment_id, component_id)

    if not success:
        raise HTTPException(status_code=404, detail="Attachment not found")

@router.get("/api/v1/components/{component_id}/attachments/{attachment_id}/download", tags=["attachments"])
def download_attachment(
    component_id: str,
    attachment_id: str,
    db: Session = Depends(get_db)
):
    """Download the attachment file."""
    try:
        uuid.UUID(component_id)
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID format")

    service = AttachmentService(db)
    attachment = service.get_attachment(attachment_id, component_id)

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = file_storage.get_file_path(attachment.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=attachment.original_filename,
        media_type=attachment.mime_type
    )

@router.get("/api/v1/components/{component_id}/attachments/{attachment_id}/thumbnail", tags=["attachments"])
def get_attachment_thumbnail(
    component_id: str,
    attachment_id: str,
    db: Session = Depends(get_db)
):
    """Get thumbnail for an image attachment."""
    try:
        uuid.UUID(component_id)
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID format")

    service = AttachmentService(db)
    attachment = service.get_attachment(attachment_id, component_id)

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not attachment.thumbnail_path:
        raise HTTPException(status_code=404, detail="No thumbnail available for this attachment")

    thumbnail_path = file_storage.get_file_path(attachment.thumbnail_path)

    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/jpeg"
    )

@router.post("/api/v1/components/{component_id}/attachments/{attachment_id}/set-primary", response_model=AttachmentResponse, tags=["attachments"])
def set_primary_image(
    component_id: str,
    attachment_id: str,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Set an image attachment as the primary image for the component."""
    try:
        uuid.UUID(component_id)
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID format")

    service = AttachmentService(db)
    attachment = service.set_primary_image(attachment_id, component_id)

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found or not an image")

    return {
        "id": attachment.id,
        "component_id": attachment.component_id,
        "filename": attachment.filename,
        "original_filename": attachment.original_filename,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "title": attachment.title,
        "description": attachment.description,
        "attachment_type": attachment.attachment_type,
        "is_primary_image": attachment.is_primary_image,
        "thumbnail_path": attachment.thumbnail_path,
        "display_order": attachment.display_order,
        "created_at": attachment.created_at.isoformat(),
        "updated_at": attachment.updated_at.isoformat()
    }