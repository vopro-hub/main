import React, { useState, useEffect } from "react";
import { api } from "../api";
import "./salesAgentWidget.css";

export default function SalesAgentWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [logs, setLogs] = useState([]);
  const [lead, setLead] = useState({ name: "", email: "", phone: "" });
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("all");
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch logs
  useEffect(() => {
    let url = "/sales/agent/logs/";
    if (filter !== "all") url += `?status=${filter}`;
    api
      .get(url)
      .then((res) => res.json())
      .then((data) => setLogs(data.results || data || []))
      .catch((err) => console.error("Fetch logs error:", err));
  }, [filter, refreshKey]);

  // Send AI instruction
  const handleSend = async () => {
    if (!message.trim()) return;
    setLoading(true);
    try {
      const sentRes = await api.post("/sales/agent/instruct/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = sentRes.data || {};
      setLogs((prev) => [
        { text: data.reply || "✅ Instruction sent", type: "ai" },
        ...prev,
      ]);
      setMessage("");
    } catch (err) {
      setLogs((prev) => [
        { text: "⚠️ Failed to send instruction", type: "error" },
        ...prev,
      ]);
    } finally {
      setLoading(false);
      setRefreshKey((k) => k + 1);
    }
  };

  // Add manual lead
  const handleAddLead = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post("/sales/agent/add-lead/", lead, { withCredentials: true });
      setLogs((prev) => [
        { text: `✅ Lead added: ${lead.name}`, type: "system" },
        ...prev,
      ]);
      alert("lead data:" + res.data);
      setLead({ name: "", email: "", phone: "" });
    } catch  (err) {
      alert("lead data:" + err.response?.data.name || err.message);
      setLogs((prev) => [
        { text: "⚠️ Failed to add lead", lead, type: "error" },
        ...prev,
      ]);
    } finally {
      setLoading(false);
      setRefreshKey((k) => k + 1);
    }
  };

  return (
    <>
      <div
        className="sales-agent-floating-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="AI Sales Agent"
      >
        💼
      </div>

      {isOpen && (
        <div className="sales-agent-widget">
          <div className="widget-header">
            <h4>AI Sales Agent</h4>
            <button onClick={() => setIsOpen(false)}>✖</button>
          </div>

          <div className="widget-controls">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="scheduled">Scheduled</option>
              <option value="won">Won</option>
              <option value="lost">Lost</option>
            </select>
            <button onClick={() => setRefreshKey((k) => k + 1)}>🔄 Refresh</button>
          </div>

          <div className="widget-body">
            <div className="activity-feed">
              {logs.length === 0 && <p>No activity yet</p>}
              {logs.map((log, i) => (
                <div key={i} className={`log-item ${log.type || "system"}`}>
                  <strong>{log.status ? `[${log.status}] ` : ""}</strong>
                  {log.text || log.message}
                  {log.timestamp && (
                    <div className="timestamp">
                      {new Date(log.timestamp).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="chat-input">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Give AI an instruction..."
              />
              <button disabled={loading} onClick={handleSend}>
                {loading ? "..." : "Send"}
              </button>
            </div>

            <form className="lead-form" onSubmit={handleAddLead}>
              <h5>➕ Add Lead</h5>
              <input
                type="text"
                value={lead.name}
                onChange={(e) => setLead({ ...lead, name: e.target.value })}
                placeholder="Lead Name"
                required
              />
              <input
                type="email"
                value={lead.email}
                onChange={(e) => setLead({ ...lead, email: e.target.value })}
                placeholder="Lead Email"
              />
              <input
                type="text"
                value={lead.phone}
                onChange={(e) => setLead({ ...lead, phone: e.target.value })}
                placeholder="Phone Number"
              />
              <button type="submit" disabled={loading}>
                {loading ? "Adding..." : "Add Lead"}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
