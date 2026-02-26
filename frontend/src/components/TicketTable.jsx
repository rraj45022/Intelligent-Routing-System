import React from "react";

export function TicketTable({ tickets, onUpdate, busyId }) {
  if (!tickets?.length) {
    return (
      <div className="card">
        <h2>Tickets</h2>
        <p className="muted">No tickets yet. Create one to see routing.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-head">
        <div>
          <p className="eyebrow">Live</p>
          <h2>Tickets</h2>
        </div>
      </div>
      <div className="table-scroll">
        <div className="table">
          <div className="table-head">
            <div>ID</div>
            <div>Title</div>
            <div>Status</div>
            <div>Assigned</div>
            <div>Priority</div>
            <div>Actions</div>
          </div>
          {tickets.map((t) => (
            <div className="table-row" key={t.id}>
              <div>#{t.id}</div>
              <div>
                <div className="title">{t.title}</div>
                <div className="muted small">{t.module}</div>
              </div>
              <div>
                <span className={`pill status ${t.status.replace(/\s+/g, "-").toLowerCase()}`}>{t.status}</span>
              </div>
              <div>{t.assigned_associate_id ?? "-"}</div>
              <div>
                <span className={`pill priority ${t.priority.toLowerCase()}`}>{t.priority}</span>
              </div>
              <div className="actions">
                <select
                  onChange={(e) => onUpdate(t.id, { status: e.target.value })}
                  defaultValue=""
                  disabled={!!busyId}
                >
                  <option value="" disabled>
                    Update status
                  </option>
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Closed">Closed</option>
                </select>
                <input
                  type="number"
                  placeholder="Reassign id"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      const val = Number(e.currentTarget.value);
                      if (!Number.isNaN(val)) {
                        onUpdate(t.id, { assigned_associate_id: val });
                        e.currentTarget.value = "";
                      }
                    }
                  }}
                  disabled={!!busyId}
                />
                {busyId === t.id && <span className="muted small">Saving…</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
