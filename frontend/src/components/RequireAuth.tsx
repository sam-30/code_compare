import { Navigate, Outlet } from "react-router-dom";
import { tokenStorage } from "../api/auth";

export default function RequireAuth() {
  const token = tokenStorage.get();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
