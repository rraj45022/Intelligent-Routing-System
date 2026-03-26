import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

const navItems = [
  { to: "/agent", label: "Agent Dashboard", roles: ["agent", "admin"] },
  { to: "/admin", label: "Ops Dashboard", roles: ["admin"] },
];

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">SR</div>
        <div>
          <div className="brand-name">Smart Router</div>
          <div className="brand-sub">Ticketing</div>
        </div>
      </div>

      <nav className="nav">
        {navItems
          .filter((item) => (user ? item.roles.includes(user.role) : false))
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
      </nav>

      {user && (
        <div className="user-card">
          <div className="user-meta">
            <div className="user-email">{user.email}</div>
            <div className="user-role">{user.role}</div>
          </div>
          <button className="ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
