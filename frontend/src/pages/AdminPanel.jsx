import React, { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import { authedJson } from "../lib/api.js";

const DEFAULT_FORM = { email: "", full_name: "", password: "", role: "agent" };

function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function when(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export function AdminPanel() {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [ops, setOps] = useState(null);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const [userData, opsData] = await Promise.all([
        authedJson(token, "/auth/users"),
        authedJson(token, "/routing/ops/dashboard"),
      ]);
      setUsers(userData);
      setOps(opsData);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (token) fetchData();
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
      fetchData();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const runCommands = [
    "/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.generate_ticket_batch massive_tickets.json --count 10000",
    "/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.train_routing_models",
    "/Users/rahulraj/python/agent-recommender-system/venv/bin/python -m backend.scripts.route_ticket_batch massive_tickets.json --chunk-size 25 --persist --job-name morning-load-10k",
  ].join("\n");

  return (
    <div className="page-grid ops-page-grid">
      <section className="ops-hero card">
        <div>
          <p className="eyebrow">Routing operations</p>
          <h1>Control tower</h1>
          <p className="muted ops-subtitle">
            Embedding retrieval, workload balancing, batch orchestration, and routing audit visibility in one place.
          </p>
        </div>
        <div className="ops-actions">
          <button onClick={fetchData}>Refresh dashboard</button>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="metric-grid">
        {(ops?.metrics || []).map((metric) => (
          <article className="metric-card card" key={metric.label}>
            <p className="eyebrow">{metric.label}</p>
            <div className="metric-value">{metric.value}</div>
            <p className="muted small">{metric.detail}</p>
          </article>
        ))}
      </section>

      <div className="ops-layout-grid">
        <section className="card ops-panel">
          <div className="card-head">
            <div>
              <p className="eyebrow">Model</p>
              <h2>Retrieval stack</h2>
            </div>
          </div>
          <div className="stacked-list">
            <div className="stacked-item">
              <span className="muted">Embedding model</span>
              <strong>{ops?.embedding_model_name || "Loading..."}</strong>
            </div>
            <div className="stacked-item">
              <span className="muted">Artifact path</span>
              <strong className="path-chip">{ops?.artifact_path || "Loading..."}</strong>
            </div>
          </div>
        </section>

        <section className="card ops-panel">
          <div className="card-head">
            <div>
              <p className="eyebrow">10k runbook</p>
              <h2>Morning load commands</h2>
            </div>
          </div>
          <pre className="command-block">{runCommands}</pre>
          <p className="muted small">
            Use chunk size 25 to match the batch router defaults and persist the routed tickets plus audits into Postgres.
          </p>
        </section>
      </div>

      <div className="ops-layout-grid three-up">
        <section className="card ops-panel">
          <div className="card-head">
            <div>
              <p className="eyebrow">Strategy mix</p>
              <h2>Decision breakdown</h2>
            </div>
          </div>
          <div className="stacked-list">
            {(ops?.strategy_breakdown || []).map((stat) => (
              <div className="strategy-row" key={stat.strategy}>
                <div>
                  <strong>{stat.strategy.replaceAll("_", " ")}</strong>
                  <div className="muted small">{stat.count} decisions</div>
                </div>
                <div className="strategy-bar-shell">
                  <div className="strategy-bar-fill" style={{ width: pct(stat.share) }} />
                </div>
                <div className="small strategy-share">{pct(stat.share)}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="card ops-panel span-two">
          <div className="card-head">
            <div>
              <p className="eyebrow">Agent load</p>
              <h2>Capacity snapshot</h2>
            </div>
          </div>
          <div className="associate-load-grid">
            {(ops?.associate_load || []).map((associate) => (
              <article className="load-card" key={associate.associate_id}>
                <div className="load-card-head">
                  <div>
                    <strong>{associate.associate_name}</strong>
                    <div className="muted small">{associate.availability_status}</div>
                  </div>
                  <span className={`pill status ${associate.availability_status}`}>{associate.open_tickets} open</span>
                </div>
                <div className="load-metrics">
                  <span>Today: {associate.daily_assigned}/{associate.daily_capacity}</span>
                  <span>Concurrent cap: {associate.max_concurrent_tickets}</span>
                </div>
                <div className="tag-row">
                  {associate.top_skills.map((skill) => (
                    <span className="pill" key={skill}>{skill}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="ops-layout-grid">
        <section className="card ops-panel">
          <div className="card-head">
            <div>
              <p className="eyebrow">Batch jobs</p>
              <h2>Recent ingestion runs</h2>
            </div>
          </div>
          <div className="table-scroll">
            <div className="table jobs-table compact-table">
              <div className="table-head">
                <div>Job</div>
                <div>Status</div>
                <div>Counts</div>
                <div>Chunk</div>
                <div>Completed</div>
              </div>
              {(ops?.recent_jobs || []).map((job) => (
                <div className="table-row" key={job.id}>
                  <div>
                    <div className="title">{job.job_name}</div>
                    <div className="muted small">{job.source_name}</div>
                  </div>
                  <div><span className="pill">{job.status}</span></div>
                  <div>{job.succeeded_tickets}/{job.total_tickets}</div>
                  <div>{job.chunk_size}</div>
                  <div>{when(job.completed_at)}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="card ops-panel">
          <div className="card-head">
            <div>
              <p className="eyebrow">Audit trail</p>
              <h2>Recent routing decisions</h2>
            </div>
          </div>
          <div className="audit-list">
            {(ops?.recent_audits || []).map((audit) => (
              <article className="audit-card" key={audit.id}>
                <div className="audit-head">
                  <strong>{audit.chosen_associate_name}</strong>
                  <span className="pill">{audit.strategy.replaceAll("_", " ")}</span>
                </div>
                <div className="muted small">Confidence {Math.round(audit.confidence * 100)}%</div>
                <p className="audit-reason">{audit.reason}</p>
                <div className="audit-meta small muted">
                  <span>{when(audit.created_at)}</span>
                  <span>{audit.llm_used ? "LLM reviewed" : "Rules only"}</span>
                  <span>{audit.ticket_id ? `Ticket #${audit.ticket_id}` : "Batch preview"}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="ops-layout-grid">
        <div className="card">
          <div className="card-head">
            <div>
              <p className="eyebrow">Team</p>
              <h2>Users</h2>
            </div>
          </div>
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
    </div>
  );
}
