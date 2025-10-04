# Getting Started with PartsHub

PartsHub is an electronic parts inventory management system with a Vue.js frontend and FastAPI backend.

## Docker Deployment (Recommended for Quick Start)

**[📦 Docker Quick Start Guide](docker-quickstart.md){ .md-button .md-button--primary }**

**Easiest Way to Get Started!**
- Single command deployment
- No local dependencies required
- Consistent environment across all systems
- Instant setup in under 5 minutes

```bash
docker run -p 3000:3000 ghcr.io/your-org/partshub:latest
```

## Local Development Setup

### Prerequisites

- **Docker** (recommended) or:
  - **Node.js** (v16 or higher)
  - **Python** (3.10 or higher)
  - **uv** (Python package manager)

### Manual Setup: 1. Clone and Setup

```bash
git clone <repository-url>
cd partshub
```

### 2. Backend Setup

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will start on `http://localhost:8000`

### 3. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:3000`

## Initial Admin Access

### Finding the Admin Password

When the backend starts for the first time, it automatically creates a default admin user and displays the credentials in the console output:

```
🔑 DEFAULT ADMIN CREATED:
   Username: admin
   Password: <randomly-generated-password>
   ⚠️  Please change this password after first login!
```

**Important:** Look for this output in your backend server console when you first run the application.

### First Login

1. Navigate to `http://localhost:3000`
2. Click the "Login" button
3. Enter:
   - **Username:** `admin`
   - **Password:** `<the password from console output>`
4. You will be prompted to change your password on first login

### What to Expect After Login

After successful login and password change, you should see:
- **Navigation tabs:** Components, Storage Locations, Dashboard, API Tokens (admin only)
- **User menu:** Shows your username with options to:
  - Change Password (anytime)
  - API Tokens (admin only)
  - Logout

## Authentication System

PartsHub uses a tiered access control system:

### Anonymous Users (No Login Required)
- **Read access:** Browse all components, storage locations, and inventory data
- **Search and filter:** Use all search and filtering features
- **View details:** See complete component specifications and stock history

### Authenticated Users (Login Required)
- **All anonymous permissions** plus:
- **Create, Edit, Delete:** Full CRUD operations on components
- **Stock management:** Update stock quantities and track changes
- **Location management:** Manage storage locations and organization

### Admin Users
- **All authenticated permissions** plus:
- **API token management:** Create and manage API access tokens
- **User administration:** (future feature)

## Troubleshooting

### Backend Won't Start
- Ensure Python 3.10+ is installed
- Run `uv sync` to install dependencies
- Check if port 8000 is already in use

### Frontend Won't Start
- Ensure Node.js v16+ is installed
- Run `npm install` to install dependencies
- Check if port 3000 is already in use

### Can't Find Admin Password
- Look in the backend console output when the server starts
- The password is displayed only once during first startup
- If you missed it, you can restart the backend server to see it again

### Authentication Issues
- Clear your browser's local storage if you have login issues
- Ensure the backend is running and accessible
- Check browser console for any JavaScript errors

## Database

PartsHub uses SQLite by default with the database file located at `backend/partshub.db`. No additional database setup is required.

## API Documentation

Once the backend is running, you can access the interactive API documentation at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Next Steps

After getting the application running:

1. **Change the admin password** (required on first login)
2. **Create storage locations** to organize your parts
3. **Add component categories** for better organization
4. **Import or manually add components** to your inventory
5. **Set up API tokens** if you need programmatic access

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the API documentation at `/docs`
- Check the application logs for error details