import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth";

const ADMIN_NAV_ITEMS = [
  {
    label: "Spatial",
    path: "/admin/spatial"
  },
  {
    label: "Health",
    path: "/admin/health"
  },
  {
    label: "Audit",
    path: "/admin/audit"
  }
];

export function AdminShell() {
  const { logout, user } = useAuth();

  return (
    <main className="app-shell">
      <aside className="shell-rail">
        <div className="shell-brand">
          <p className="eyebrow">RTLS Analytics Platform</p>
          <h1>Admin</h1>
          <p className="muted-text">
            Spatial setup, infrastructure review, and governance workflows for platform owners.
          </p>
        </div>

        <nav className="shell-nav" aria-label="Admin">
          {ADMIN_NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              className={({ isActive }) =>
                isActive ? "shell-nav__link shell-nav__link--active" : "shell-nav__link"
              }
              to={item.path}
            >
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="shell-status-card">
          <p className="shell-status-card__label">Administrator</p>
          <strong>{user?.display_name || user?.email}</strong>
          <span>{user?.email}</span>
        </div>
      </aside>

      <section className="shell-main">
        <header className="shell-topbar">
          <div className="shell-topbar__meta">
            <div>
              <p className="eyebrow">Admin Console</p>
              <p className="muted-text admin-route-note">
                Spatial setup remains available alongside the delivered Health and Audit views.
              </p>
            </div>
          </div>
          <div className="top-bar-actions">
            <span className="role-badge">{user?.role}</span>
            <button className="secondary-button" onClick={() => void logout()} type="button">
              Sign Out
            </button>
          </div>
        </header>

        <Outlet />
      </section>
    </main>
  );
}
