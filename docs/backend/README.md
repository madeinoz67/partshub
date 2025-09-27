# Backend Documentation

Python FastAPI backend documentation for PartsHub.

## Available Documentation

### Testing
- **[testing.md](testing.md)** - Complete testing guide including:
  - Test environment isolation
  - Running unit, contract, and integration tests
  - Database safety and production isolation
  - Test environment variables and configuration

### KiCad Integration
- **[kicad-field-mappings.md](kicad-field-mappings.md)** - KiCad integration reference:
  - Component data to KiCad field mapping
  - Reference designator mapping by component type
  - Package to footprint mapping
  - API response formats and data models
  - Custom field and template configuration

## Development Setup

For backend development setup, see the main [Getting Started Guide](../user/getting-started.md).

## API Documentation

The backend provides OpenAPI documentation at:
- **Development**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

To run backend tests:
```bash
cd backend
python run_tests.py
```

See [testing.md](testing.md) for detailed testing documentation.