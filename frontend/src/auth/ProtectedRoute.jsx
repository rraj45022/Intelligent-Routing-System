import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";

export function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="page loading">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (role && user.role !== role) {
    // If the user lacks permissions, push them to their default dashboard.
    const fallback = user.role === "admin" ? "/admin" : "/agent";
    return <Navigate to={fallback} replace />;
  }

  return children;
}
