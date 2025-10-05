# Changelog

## [0.3.0](https://github.com/madeinoz67/partshub/compare/v0.2.1...v0.3.0) (2025-10-05)


### Features

* **stock-ops:** add inline stock management operations ([#16](https://github.com/madeinoz67/partshub/issues/16)) ([dc33f9d](https://github.com/madeinoz67/partshub/commit/dc33f9d4ebdd7ec0d6c7dbfa8e83a99910be0639))


### Bug Fixes

* remove --no-build-isolation flag from release workflow ([10ed529](https://github.com/madeinoz67/partshub/commit/10ed52975524edd5caee2f430e7a62476fa04d32))


### Documentation

* add v0.3.0 release notes and update documentation ([12e1fb6](https://github.com/madeinoz67/partshub/commit/12e1fb67a5600d126aa61742d291939d27ae5c29))

## [0.2.1](https://github.com/madeinoz67/partshub/compare/v0.2.0...v0.2.1) (2025-10-04)


### Bug Fixes

* correct release workflow tag extraction for workflow_call ([54840fb](https://github.com/madeinoz67/partshub/commit/54840fb4cdad0f9f1d040c67a57ed8cd239b480c))
* resolve documentation build and deployment issues ([ec256c5](https://github.com/madeinoz67/partshub/commit/ec256c58b97ee5d015dc16f0ae0fda21a0ba94fb))

## [0.2.0](https://github.com/madeinoz67/partshub/compare/v0.1.2...v0.2.0) (2025-10-04)


### Features

* add bulk operations for component management ([#12](https://github.com/madeinoz67/partshub/issues/12)) ([fe6af3e](https://github.com/madeinoz67/partshub/commit/fe6af3e75ee63a289290ade0947d93d66fd34b16))


### Bug Fixes

* configure release workflow to trigger from release-please ([b5ba0ce](https://github.com/madeinoz67/partshub/commit/b5ba0ce6bba64978c7aa3dc437ab839f89bf5040))

## [0.1.2](https://github.com/madeinoz67/partshub/compare/v0.1.1...v0.1.2) (2025-10-04)


### Documentation

* Add comprehensive Docker deployment and user documentation ([#10](https://github.com/madeinoz67/partshub/issues/10)) ([b8f04a2](https://github.com/madeinoz67/partshub/commit/b8f04a26b0516914b7346ead7af6de774752d95d))

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
