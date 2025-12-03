import React, { useState, useRef, useEffect, useContext } from "react";
import { myOffices } from "../api";
import { AuthContext } from "../context/AuthContext";
import useWebSocket from "../hooks/useWebSocket";
import "./ChatWedge.css";



const ChatWedge = () => {
    const { user, token } = useContext(AuthContext);
    const [offices, setOffices] = useState([]);
    const [selected, setSelected] = useState(null);
    const [messages, setMessages] = useState([]);
    const [chatInput, setChatInput] = useState("");
    const [presence, setPresence] = useState([]);
    const [chatMode, setChatMode] = useState("office"); // "office" | "city"
  
  const [open, setOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const chatRef = useRef(null);

  const [position, setPosition] = useState({ 
    x: window.innerWidth - 320, 
    y: window.innerHeight - 400 
  });

  const toggleWidget = () => setOpen(!open);


  // Start dragging
  const handleMouseDown = e => {
    if (!chatRef.current) return;
    setIsDragging(true);
    const rect = chatRef.current.getBoundingClientRect();
    setOffset({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  // Move while dragging
  const handleMouseMove = e => {
    if (!isDragging || !chatRef.current) return;
    setPosition({
      x: e.clientX - offset.x,
      y: e.clientY - offset.y
    });
  };

  // Stop dragging
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Attach/remove listeners properly
  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, offset]);

  useEffect(() => {
      if (!user) return;
      (async () => {
        const list = await myOffices();
        setSelected(list[0]);
      })();
    }, [user]);
  // Presence socket (switches between office & city)
const presenceWS = useWebSocket(
  selected && token
    ? chatMode === "office"
      ? `ws://localhost:8000/ws/presence/office/${selected.id}/?token=${token}`
      : `ws://localhost:8000/ws/presence/city/${selected.city}/?token=${token}`
    : null,
  {
    onMessage: (ev) => {
      if (ev.type === "presence.list") {
        setPresence(ev.users.map((u) => ({ user: u, status: "online" })));
      }
      if (ev.type === "presence.update") {
        setPresence((prev) => {
          const filtered = prev.filter((p) => p.user !== ev.user);
          return [...filtered, ev];
        });
      }
    },
    onOpen: () => presenceWS.send({ status: "online" }),
  }
);
  // Office Room Chat (Lobby = first room)
  const lobby = selected?.rooms?.[0];
  const chatWSOffice = useWebSocket(
    chatMode === "office" && lobby && token
      ? `ws://localhost:8000/ws/chat/office/${lobby.id}/?token=${token}`
      : null,
    { onMessage: (msg) => setMessages((m) => [...m, msg]) }
  );

  // City Lobby Chat
  const chatWSCity = useWebSocket(
    chatMode === "city" && selected?.city && token
      ? `ws://localhost:8000/ws/chat/city/${selected.city}/?token=${token}`
      : null,
    { onMessage: (msg) => setMessages((m) => [...m, msg]) }
  );

  function sendChat() {
    if (!chatInput.trim()) return;
    const socket = chatMode === "office" ? chatWSOffice : chatWSCity;
    socket.send({ content: chatInput.trim() });
    setChatInput("");
  }

  // Small status dot component
  function StatusDot({ isConnected }) {
    return (
      <span
        style={{
          display: "inline-block",
          width: 10,
          height: 10,
          borderRadius: "50%",
          marginLeft: 8,
          backgroundColor: isConnected ? "green" : "red",
        }}
      />
    );
  }

  return (
    <>
      {!open && (
        <div className="assistant-bubble" onClick={toggleWidget}>
          🤖
        </div>
      )}

      {open && (
        <div
          className="assistant-chat"
          ref={chatRef}
          style={{
            position: "fixed",
            left: `${position.x}px`,
            top: `${position.y}px`
          }}
        >
          <div className="assistant-header" onMouseDown={handleMouseDown}>
           
            {/* Toggle Chat Mode */}
            <div style={{ margin: "10px 0" }}>
                    <button
                      onClick={() => {
                        setMessages([]); // clear previous
                        setChatMode("office");
                      }}
                       style={{
                      backgroundColor: chatMode === "office" ? "white" : "grey",
                     
                    }}
                    >
                      Office Chat
                    </button>
                    <button
                      onClick={() => {
                        setMessages([]);
                        setChatMode("city");
                      }}
                      style={{
                      backgroundColor: chatMode === "city" ? "white" : "grey",
                     
                    }}
                    >
                      City Lobby Chat
                    </button>
                  </div>
            <button className="close-btn" onClick={toggleWidget}>✕</button>
          </div>

          <div className="chat-body"> 
            {messages.map((m, i) => (
                <div key={i} className={`message ${m.user}`}>
                  <strong>{m.user}:</strong> {m.content}
                </div>
              ))}
          </div>

          <div className="chat-input">
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Type message..."
            />
           <button
              className="send-btn"
              onClick={sendChat}
              disabled={
                chatMode === "office"
                  ? !chatWSOffice.isConnected
                  : !chatWSCity.isConnected
              }
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWedge;
