import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { tokenStorage } from "../api/auth";

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const nav = [
    { to: "/", label: "New Comparison" },
    { to: "/history", label: "History" },
  ];

  function handleLogout() {
    tokenStorage.clear();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-8">
        <span className="font-bold text-lg text-gray-900">Code Comparison</span>
        <nav className="flex gap-4 flex-1">
          {nav.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`text-sm font-medium ${
                location.pathname === to
                  ? "text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-gray-900"
          data-testid="logout-button"
        >
          Sign out
        </button>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
