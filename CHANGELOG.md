# Brew-Web Changelog

## [1.2.0] - 2025-05-07

### Added
- Stats page displaying batch ABVs and frequency over time.
- Flash message when trying to create a batch without any recipes.
- Custom error pages: 403, 404, and 500 with friendly styling.
- Custom `utils.py` with `@role_required` decorator for per-role route control.
- Automatic admin role assignment on first user setup with fallback detection.
- Conditional display of top menu and navigation items based on user role.
- Flash messaging block added to `new_recipe.html` to show redirect notices.
- Brew Web logo added to top-left of UI with proper scaling and transparency.
- Admin settings page scaffolded and integrated into settings sidebar.
- User management via Administration page:
  - List current users with username, role, and admin status.
  - Create new users with selected role (`admin`, `editor`, `user`).
  - Reset user passwords.
  - Delete user accounts (with protection against deleting self).
- Role-based access control (RBAC) system:
  - New `role` field added to `User` model.
  - Decorator `@role_required(*roles)` added to enforce per-route role access.
  - Viewer access restricted from editing or creating recipes, batches, and measurements.
- First user created during `/setup` is automatically promoted to admin.
- User role shown in admin table for clarity.
- Dynamic sidebar hides "Administration" link from non-admin users.

### Fixed
- Removed hardcoded duplicate warning from `new_batch.html`.
- Improved flash message styling and visibility.
- Fixed improper route fallback causing setup logic to fail silently.
- Corrected error handling to catch batch creation issues and log them clearly.
- Brew Web logo size corrected and now responsive.
- Sidebar layout restored on `admin.html` to match other settings pages.
- CSS properly loaded by fixing static path to `/static/...`
- 403 errors correctly raised for restricted pages using `@role_required`.

### Changed
- `new_batch.html` now redirects instead of displaying a fallback block when no recipes exist.
- Sidebar logic refined to hide Administration unless role is explicitly `admin`.
- Consolidated flash message handling into layout base to avoid redundancy.
- `/recipes/new`, `/edit`, and `/delete` routes now limited to `admin` and `editor`.
- `/batches` and `/measurements` edit/delete routes restricted similarly.
- Deprecated `is_admin` use in favor of `role`, but preserved for backward compatibility.

---

## [1.1.0] - 2025-05-06

- Initial deployment of Dockerized Brew-Web app using GitHub ZIP release
- Added customizable theme (light/dark) and font size settings
- Integrated brewing calculators (ABV, sweetness, dilution, TOSNA, etc.)
- Fixed favicon appearance and reverse proxy path resolution for static assets
