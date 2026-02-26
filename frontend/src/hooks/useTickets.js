import { useCallback, useState } from "react";
import { authedJson } from "../lib/api.js";

export function useTickets(token) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const fetchTickets = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await authedJson(token, "/tickets/");
      setTickets(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const createTicket = useCallback(async (payload) => {
    setBusyId("new");
    setError(null);
    try {
      await authedJson(token, "/tickets/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      await fetchTickets();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setBusyId(null);
    }
  }, [token, fetchTickets]);

  const updateTicket = useCallback(async (ticketId, payload) => {
    setBusyId(ticketId);
    setError(null);
    try {
      await authedJson(token, `/tickets/${ticketId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      await fetchTickets();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setBusyId(null);
    }
  }, [token, fetchTickets]);

  return {
    tickets,
    loading,
    error,
    busyId,
    fetchTickets,
    createTicket,
    updateTicket,
  };
}
