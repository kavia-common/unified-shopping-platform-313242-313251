# unified-shopping-platform-313242-313251

## Environment variables (local defaults)

### Backend (`shopping_app_backend/.env`)
- `DATABASE_URL=postgresql://appuser:dbuser123@localhost:5000/myapp`
- `JWT_SECRET=dev_jwt_secret_change_me`
- `BACKEND_BASE_URL=http://localhost:3001`
- `FRONTEND_URL=http://localhost:3000`
- `CORS_ORIGINS=http://localhost:3000`

Notes:
- Backend also supports legacy/alternate names: `JWT_SECRET_KEY` and `CORS_ALLOW_ORIGINS`.
- A non-secret config snapshot is available at `GET /health/config`.

### Frontend (`shopping_app_frontend/.env`)
- `REACT_APP_API_BASE_URL=http://localhost:3001`