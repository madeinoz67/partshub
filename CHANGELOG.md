# Changelog

## [0.1.1](https://github.com/madeinoz67/partshub/compare/v0.1.0...v0.1.1) (2025-10-04)

### Added
- Storage location layout generator with 4 layout types (Single, Row, Grid, 3D Grid)
- Real-time preview for bulk location generation showing first 5 and last names
- Support for up to 500 locations per batch creation with warning at 100+
- Parent-child location hierarchy support for generated locations
- Responsive storage location table view with expandable rows
- Letter range capitalization option (a-z or A-Z)
- Number range zero-padding option (1-9 or 01-09)
- Single-part only designation for generated locations
- Layout configuration audit trail stored as JSONB in database
- Validation for duplicate location names with transaction rollback
- Authentication requirement for bulk location creation (anonymous users can preview only)

### Changed
- Storage locations API endpoints now use `/api/v1/storage-locations` prefix for consistency

### Fixed
- Duplicate API endpoint in storage.py causing validation bypass
- Integration test URLs updated to use correct `/api/v1` prefix
- HTTP status code returns corrected:
  - 409 for duplicate locations
  - 400 for location limit exceeded
  - 404 for invalid parent locations
- API endpoint URL mismatch between frontend and backend location generation services

## [0.1.0] - Initial Release

### Added
- Electronic parts inventory management
- Storage location organization with hierarchical tree structure
- User authentication and authorization
- Component search and filtering
- KiCad library integration
- Project management
- Provider integration (Digi-Key, Mouser, LCSC)
- Barcode scanning support
- Documentation system with MkDocs

