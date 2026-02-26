import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import { TicketForm } from "../components/TicketForm.jsx";
import { TicketTable } from "../components/TicketTable.jsx";
import { EventFeed } from "../components/EventFeed.jsx";
import { useTickets } from "../hooks/useTickets.js";

export function AgentDashboard() {
  const { token } = useAuth();
  const { tickets, fetchTickets, createTicket, updateTicket, busyId } = useTickets(token);
  const [events, setEvents] = useState([]);

  const wsUrl = useMemo(() => {
    const { protocol, host } = window.location;
    const wsProto = protocol === "https:" ? "wss:" : "ws:";
    return `${wsProto}//${host}/ws/tickets`;
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchTickets();
  }, [token, fetchTickets]);

  useEffect(() => {
    if (!token) return;
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setEvents((prev) => [data, ...prev].slice(0, 20));
        fetchTickets();
      } catch (err) {
        setEvents((prev) => [{ type: "raw", payload: ev.data }, ...prev].slice(0, 20));
      }
    };
    return () => ws.close(1000, "client navigate");
  }, [token, wsUrl, fetchTickets]);

  return (
    <div className="page-grid">
      <div className="grid two">
        <TicketForm onCreate={createTicket} busy={busyId === "new"} />
        <EventFeed events={events} />
      </div>
      <TicketTable tickets={tickets} onUpdate={updateTicket} busyId={busyId} />
    </div>
  );
}
