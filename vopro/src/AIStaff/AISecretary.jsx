import React, { useState, useEffect } from "react";
import { api } from "../api";
import "./assistantWidget.css"; 
export default function AIAssistantWidget() {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("chat"); // "chat" | "history"
 
  // Chat state
  const [msgs, setMsgs] = useState([
    { role: "assistant", text: "Hi — I can help with tasks, meetings, notes, files and more." }
  ]);
  const [input, setInput] = useState("");

  // History state
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [typeMap, setTypeMap] = useState({});
  const [filterType, setFilterType] = useState("all");
  const [filterSubtype, setFilterSubtype] = useState("");
  const [filterDays, setFilterDays] = useState("all");
  const [search, setSearch] = useState("");
  
  // Load type/subtype map once
  useEffect(() => {
    async function fetchTypes() {
      try {
        const res = await api.get("/assistant/types/");
        setTypeMap(res.data);
      } catch (err) {
        console.error("Failed to load assistant types:", err);
      }
    }
    fetchTypes();
  }, []);

   // Filters
   const SUBTYPE_MAP = {
     task: ["created", "updated", "deleted", "completed"],
     meeting: ["scheduled", "rescheduled", "cancelled"],
     note: ["created", "updated", "deleted"],
     email: ["sent", "drafted"],
     resource: [],
     file: [],
     general: [],
   };

  const send = async () => {
    if (!input.trim()) return;
    setMsgs((m) => [...m, { role: "user", text: input }]);
    try {
      const res = await api.post("/assistant/respond/", { message: input }, { withCredentials: true });
      const data = res.data;
      const text = data.text || (data.response || JSON.stringify(data));
     
      setMsgs((m) => [...m, { role: "assistant", text }]);
      setInput("");
    } catch (err) {
      setMsgs((m) => [...m, { role: "assistant", text: "Error: failed to call assistant." }]);
    }
  };

  const loadLogs = async () => {
    setLoadingLogs(true);
    try {
      let params = {};
      if (filterType !== "all") params.type = filterType;
      if (filterSubtype) params.subtype = filterSubtype;
      if (filterDays !== "all") params.days = filterDays;
      if (search.trim()) params.q = search.trim();


      const res = await api.get("/assistant/logs/", {
        params,
        withCredentials: true
      });
      setLogs(res.data);
    } catch (err) {
      console.error("Failed to load logs", err);
    } finally {
      setLoadingLogs(false);
    }
  };

  // load whenever filters change
  useEffect(() => {
    if (activeTab === "history" && open) {
      loadLogs();
      setFilterSubtype("");
    }
  }, [activeTab, open, filterType, filterDays, search]);
  

  return (
    <div className="ai-assistant-container">
      {/* toggle button */}
      <button onClick={() => setOpen(!open)} className="ai-assistant-toggle">🤖</button>
      {open && (
        <div className="ai-assistant-box">
          
          {/* Header + Tabs */}
          <div className="ai-assistant-header">
            <strong>Office Assistant</strong>
            <div className="ai-assistant-tabs">
              <button 
                onClick={() => setActiveTab("chat")} 
                 className={activeTab === "chat" ? "active" : ""}
              >
                Chat
              </button>
              <button 
                onClick={() => setActiveTab("history")} 
                 className={activeTab === "history" ? "active" : ""}
              >
                History
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="ai-assistant-body">
            {activeTab === "chat" && (
              <>
                {msgs.map((m, i) => (
                  <div key={i} className={`ai-message ${m.role}`}>
                    <div className="ai-bubble" style={{ background: m.role === "user" ? "#2d89ef" : "#f1f1f1", color: m.role === "user" ? "#fff" : "#222" }}>
                      {m.text}
                    </div>
                  </div>
                ))}
              </>
            )}

            {activeTab === "history" && (
              <>
                {/* Filters */}
                <div style={{ marginBottom: 10, display: "flex", gap: 6 }}>
                  <select value={filterType} onChange={e => setFilterType(e.target.value)}>
                    <option value="all">All Types</option>
                    {Object.keys(typeMap).map((t) => (
                      <option key={t} value={t}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </option>
                    ))}
                  </select>
                  
                  <select 
                    value={filterSubtype} 
                    onChange={e => setFilterSubtype(e.target.value)}
                    disabled={filterType === "all" || !typeMap[filterType] || typeMap[filterType].length === 0}
                  >
                    <option value="">All Subtypes</option>
                    {filterType !== "all" && typeMap[filterType]?.map((st) => (
                      <option key={st} value={st.id}>{st.charAt(0).toUpperCase() + st.slice(1)}</option>
                    ))}
                  </select>

                  <select value={filterDays} onChange={e => setFilterDays(e.target.value)}>
                    <option value="all">All Time</option>
                    <option value="7">Last 7 days</option>
                    <option value="30">Last 30 days</option>
                  </select>

                  <input 
                    type="text" 
                    placeholder="Search…" 
                    value={search} 
                    onChange={e => setSearch(e.target.value)} 
                    style={{ flex: 1 }}
                  />
                </div>

                {loadingLogs && <p>Loading history…</p>}
                {!loadingLogs && logs.length === 0 && <p>No matching history.</p>}
                {!loadingLogs && logs.map((log) => (
                  <div key={log.id} className="ai-log-card">
                    <div><strong>You:</strong> {log.input_text}</div>
                    <div><strong>Assistant:</strong> {log.response_text}</div>
                    {log.action_data && Object.keys(log.action_data).length > 0 && (
                      <pre style={{ background: "#f8f8f8", padding: 8, marginTop: 5 }}>
                        {JSON.stringify(log.action_data, null, 2)}
                      </pre>
                    )}
                    <div style={{ fontSize: 12, color: "#777" }}>{new Date(log.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Footer for chat only */}
          {activeTab === "chat" && (
            <div className="ai-assistant-footer">
              <input 
                value={input} 
                onChange={(e) => setInput(e.target.value)} 
                style={{ flex: 1 }} 
                onKeyDown={(e) => { if (e.key === "Enter") send(); }}
                placeholder="Type a message..." 
              />
              <button onClick={send}>Send</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

