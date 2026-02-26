import React from "react";

export function EventFeed({ events }) {
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <p className="eyebrow">WebSocket</p>
          <h2>Recent Events</h2>
        </div>
      </div>
      {events.length === 0 ? (
        <p className="muted">No events yet. Create a ticket or wait for the feeder.</p>
      ) : (
        <ul className="event-list">
          {events.map((evt, idx) => (
            <li key={idx}>
              <div className="event-type">{evt.type}</div>
              <pre>{JSON.stringify(evt.payload ?? evt, null, 2)}</pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
