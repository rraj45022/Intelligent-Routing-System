import React, { useState } from "react";

const EMPTY_FORM = {
  title: "",
  description: "",
  module: "billing",
  priority: "Low",
  customer_segment: "retail",
  channel: "web",
};

export function TicketForm({ onCreate, busy }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await onCreate(form);
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="card">
      <div className="card-head">
        <div>
          <p className="eyebrow">Create</p>
          <h2>New Ticket</h2>
        </div>
      </div>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Title
          <input name="title" value={form.title} onChange={handleChange} required />
        </label>
        <label>
          Description
          <textarea name="description" value={form.description} onChange={handleChange} required />
        </label>
        <div className="grid two">
          <label>
            Module
            <select name="module" value={form.module} onChange={handleChange}>
              <option value="billing">billing</option>
              <option value="auth">auth</option>
              <option value="search">search</option>
              <option value="shipping">shipping</option>
              <option value="catalog">catalog</option>
              <option value="analytics">analytics</option>
            </select>
          </label>
          <label>
            Priority
            <select name="priority" value={form.priority} onChange={handleChange}>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </label>
        </div>
        <div className="grid two">
          <label>
            Segment
            <input name="customer_segment" value={form.customer_segment} onChange={handleChange} />
          </label>
          <label>
            Channel
            <input name="channel" value={form.channel} onChange={handleChange} />
          </label>
        </div>
        <div className="actions-row">
          <button type="submit" disabled={busy}>
            {busy ? "Submitting..." : "Create & Route"}
          </button>
          {error && <span className="error">{error}</span>}
        </div>
      </form>
    </div>
  );
}
