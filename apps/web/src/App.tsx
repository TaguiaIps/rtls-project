import { PRODUCT_NAME } from "@rtls/config";
import { useState, type FormEvent, type PropsWithChildren } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate
} from "react-router-dom";

import { AdminSpatialWorkspace } from "./admin/AdminSpatialWorkspace";
import { AuthProvider, roleHomeRoute, useAuth } from "./auth";
import {
  LiveMapPage,
  OperationsOverviewPage,
  OperationsShellLayout
} from "./operations/OperationsShell";

function LoadingScreen() {
  return (
    <main className="centered-screen">
      <div className="panel panel--compact">
        <p className="eyebrow">Authorizing</p>
        <h1>Loading session</h1>
        <p className="muted-text">Checking the current RTLS Analytics Platform session.</p>
      </div>
    </main>
  );
}

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, status } = useAuth();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("StrongPass123");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  const nextPath = (location.state as { from?: string } | null)?.from;

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const role = await login(email, password);
      navigate(nextPath || roleHomeRoute(role), { replace: true });
    } catch {
      setError("Sign-in failed. Check the credentials and Administrator bootstrap state.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="centered-screen">
      <section className="panel login-panel">
        <div>
          <p className="eyebrow">Secure Sign-In</p>
          <h1>{PRODUCT_NAME}</h1>
          <p className="panel-copy">
            High-trust access for operations monitoring and system administration. The first
            Administrator is bootstrapped outside the UI.
          </p>
        </div>

        <form className="login-form" onSubmit={onSubmit}>
          <label>
            <span>Email</span>
            <input
              autoComplete="email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            <span>Password</span>
            <input
              autoComplete="current-password"
              name="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? "Signing In..." : "Sign In"}
          </button>
        </form>

        <div className="status-strip">
          <span>JWT access and refresh flow</span>
          <span>Role-aware routing</span>
          <span>Audit event recording enabled</span>
        </div>
      </section>
    </main>
  );
}

function ShellLayout({
  title,
  subtitle,
  children
}: PropsWithChildren<{ title: string; subtitle: string }>) {
  const { logout, user } = useAuth();

  return (
    <main className="dashboard-shell">
      <aside className="nav-rail">
        <p className="eyebrow">RTLS</p>
        <h2>{title}</h2>
        <p className="muted-text">{subtitle}</p>
      </aside>
      <section className="dashboard-main">
        <header className="top-bar">
          <div>
            <p className="muted-text">Signed in as</p>
            <strong>{user?.display_name || user?.email}</strong>
          </div>
          <div className="top-bar-actions">
            <span className="role-badge">{user?.role}</span>
            <button className="secondary-button" onClick={() => void logout()} type="button">
              Sign Out
            </button>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}

function AdminHome() {
  return (
    <ShellLayout
      title="Admin Console"
      subtitle="Spatial hierarchy, floor plans, scale confirmation, and operational zone setup."
    >
      <AdminSpatialWorkspace />
    </ShellLayout>
  );
}

function ProtectedRoute({
  allowedRoles,
  children
}: PropsWithChildren<{ allowedRoles?: string[] }>) {
  const { status, user } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <LoadingScreen />;
  }

  if (status === "unauthenticated" || !user) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate replace to={roleHomeRoute(user.role)} />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  const { status, user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Navigate replace to={user ? roleHomeRoute(user.role) : "/login"} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={["Administrator"]}>
            <AdminHome />
          </ProtectedRoute>
        }
      />
      <Route
        path="/operations"
        element={
          <ProtectedRoute allowedRoles={["Administrator", "General User"]}>
            <OperationsShellLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<OperationsOverviewPage />} />
        <Route path="live-map" element={<LiveMapPage />} />
      </Route>
      <Route
        path="*"
        element={
          <Navigate
            replace
            to={
              status === "authenticated" && user ? roleHomeRoute(user.role) : "/login"
            }
          />
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
