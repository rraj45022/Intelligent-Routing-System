import React from "react";
import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="eyebrow">404</p>
        <h1>Page not found</h1>
        <p className="muted">The page you are looking for does not exist.</p>
        <Link to="/">Go home</Link>
      </div>
    </div>
  );
}
