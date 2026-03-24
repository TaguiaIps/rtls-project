# RTLS API

Bootstrap FastAPI service for the RTLS Analytics Platform.

This package provides:

- the initial API application
- the worker entrypoint used by the local Compose stack
- the identity, RBAC, and audit foundation for the first protected web flows
- the backend lint, test, and build baseline for future OpenSpec changes

Bootstrap the first Administrator account with:

```bash
python -m rtls_api.bootstrap_admin --email admin@example.com --password StrongPass123 --display-name "Platform Admin"
```
