import React, { useState, useEffect } from "react";
import "./aireceptionist.css";
import { aiChatApi, publicApi } from "../api";

const ReceptionistWidget = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "ai", text: "👋 Welcome! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [officeId, setOfficeId] = useState(null);

  // Fetch office ID from session when widget opens
  useEffect(() => {
    async function fetchOffice() {
      try {
        if (open) {
          const officeRes = await publicApi.get("/receptionist/office/", {
            withCredentials: true,
          });
          setOfficeId(officeRes.data.id);
        }
      } catch (err) {
        console.error("Error fetching office:", err);
      }
    }
    fetchOffice();
  }, [open]);

  const sendMessage = async () => {
    if (!input.trim() || !officeId) return;

    // show user message immediately
    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await aiChatApi.post(
        "/receptionist/respond/",
        { message: input }, 
        { withCredentials: true }
      );

      const aiMsg = { role: "ai", text: res.data.response };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error("Receptionist error:", err);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "⚠️ Sorry, something went wrong." },
      ]);
    }

    setInput("");
  };

  return (
    <div>
      {/* floating bubble */}
      <button className="chat-bubble" onClick={() => setOpen(!open)}>
       🤖
      </button>

      {open && (
        <div className="chatbox">
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={m.role}>
                {m.text}
              </div>
            ))}
          </div>

          <div className="input">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReceptionistWidget;
