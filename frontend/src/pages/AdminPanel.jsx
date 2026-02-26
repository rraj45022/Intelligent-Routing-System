import React, { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import { authedJson } from "../lib/api.js";

const DEFAULT_FORM = { email: "", full_name: "", password: "", role: "agent" };

export function AdminPanel() {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const fetchUsers = async () => {
    try {
      const data = await authedJson(token, "/auth/users");
      setUsers(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (token) fetchUsers();
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await authedJson(token, "/auth/users", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setForm(DEFAULT_FORM);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-grid">
      <div className="card">
        <div className="card-head">
          <div>
            <p className="eyebrow">Team</p>
            <h2>Users</h2>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="table-scroll">
          <div className="table admin-table">
            <div className="table-head">
              <div>Email</div>
              <div>Name</div>
              <div>Role</div>
              <div>Status</div>
            </div>
            {users.map((u) => (
              <div className="table-row" key={u.id}>
                <div>{u.email}</div>
                <div>{u.full_name ?? "-"}</div>
                <div>
                  <span className="pill">{u.role}</span>
                </div>
                <div>{u.is_active ? "Active" : "Inactive"}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <div>
            <p className="eyebrow">Create</p>
            <h2>Invite user</h2>
          </div>
        </div>
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input name="full_name" value={form.full_name} onChange={handleChange} />
          </label>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Password
            <input type="password" name="password" value={form.password} onChange={handleChange} required />
          </label>
          <label>
            Role
            <select name="role" value={form.role} onChange={handleChange}>
              <option value="agent">Agent</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button type="submit" disabled={busy}>{busy ? "Saving..." : "Create user"}</button>
        </form>
      </div>
    </div>
  );
}
