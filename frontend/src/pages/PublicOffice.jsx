// pages/PublicOffice.jsx
import React, { useEffect, useState, Suspense} from "react";
import { publicApi, aiChatApi } from "../api";
import { useParams } from "react-router-dom";
import "../App.css";
import "./PublicOffice.css";
import useWebSocket from "../hooks/useWebSocket";

const componentsModules = import.meta.glob("../components/*.jsx");

export default function PublicOffice() {
  const [office, setOffice] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState(null);
  const [scale, setScale] = useState(0.5); // zoom state
  const [mapVisible, setMapVisible] = useState(true); // toggle visibility
  const { slug } = useParams();
  const [workers, setWorkers] = useState([]); 
  const [workerId, setWorkerId] = useState("");
  const [workerPresence, setWorkerPresence] = useState(null);
  const [presenceModalOpen, setPresenceModalOpen] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(true); // toggle between login/logout
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);
  const [accessModal, setAccessModal] = useState(null); // { type, room }
  const [pendingRoom, setPendingRoom] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [accessCode, setAccessCode] = useState("");
  const [loadingAccess, setLoadingAccess] = useState(false);
  const [visitors, setVisitors] = useState([]);
  

  useEffect(() => {
    const fetch = async () => {
      try {
        
        const officeRes = await publicApi.get(`/offices/${slug}/`, {withCredentials:true});
        setOffice(officeRes.data);
        const officRes = await aiChatApi.get("/receptionist/office/") // backend reads session
        
        const roomsRes = await publicApi.get(`/rooms/?office=${officeRes.data.id}`);
        const allRooms = roomsRes.data.map((r) => {
          let cfg = r.access_config;
          try {
            if (typeof cfg === "string") {
              cfg = JSON.parse(cfg); // parse JSON string
            }
          } catch (e) {
            cfg = {};
          }
        
          // normalize form_fields to array
          if (cfg && typeof cfg.form_fields === "string") {
            cfg.form_fields = cfg.form_fields
              .split(",")
              .map((f) => f.trim())
              .filter(Boolean);
          }
        
          return {
            ...r,
            access_config: cfg || {},
          };
        });
        setRooms(allRooms);

         // Use for the mean time switch to websocket later
        const workersRes = await publicApi.get(`/workers/?office=${officeRes.data.id}`);
        setWorkers(workersRes.data);

        // Default landing: Lobby/Reception
        const lobby = allRooms.find(
          (r) =>
            r.name.toLowerCase().includes("office lobby") ||
            r.name.toLowerCase().includes("reception")
        );
        setCurrentRoom(lobby || allRooms[0] || null);
        // 🔑 Restore visitor access from localStorage
        for (let room of allRooms) {
          const token = localStorage.getItem(`access_token_room_${room.id}`);
          if (!token) continue;
          try {
            const res = await publicApi.post(`/rooms/validate_access/`, { token });
            if (res.data.valid) {
              setCurrentRoom(allRooms.find((r) => r.id === res.data.room));
              break; // auto enter first valid room
            }
          } catch (err) {
            console.log("Token invalid/expired for room", room.id);
            localStorage.removeItem(`access_token_room_${room.id}`);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetch();
  }, [slug]);
 
  // Simulate a new visitor checking in every 10 seconds (for demo)
  useEffect(() => {
    const interval = setInterval(() => {
      setVisitors((prev) => [
        ...prev,
        { id: Date.now(), name: `Visitor ${prev.length + 1}` },
      ]);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  // Remove visitor after they reach the desk (10s later)
  useEffect(() => {
    if (visitors.length > 0) {
      const timer = setTimeout(() => {
        setVisitors((prev) => prev.slice(1));
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [visitors]);

  // Public Presence WebSocket
   
  //const publicWS = useWebSocket(
  //  slug ? `ws://localhost:8000/ws/public/offices/${slug}/presence/` : null,
  //  {
  //    shouldReconnect: () => true, // auto reconnect on close/error
  //    reconnectAttempts: 3,       // optional
  //    reconnectInterval: 30000,     // retry every 3s
  //    onOpen: () => {
  //      console.log("✅ Public WS connected");
  //    },
  //    onMessage: (ev) => {
  //      // Initial snapshot
  //      if (ev.type === "worker.presence" && Array.isArray(ev.worker)) {
  //        //setWorkers(ev.worker);
  //      }
  //
  //      // Incremental updates
  //      if (ev.type === "presence_update" && ev.worker) {
  //        setWorkers((prev) => {
  //          if (ev.action === "login") {
  //            // Add/update worker
  //            const others = prev.filter((w) => w.id !== ev.worker.id);
  //            return [...others, ev.worker];
  //          }
  //          if (ev.action === "logout") {
  //            // Remove worker
  //            return prev.filter((w) => w.id !== ev.worker.id);
  //          }
  //          return prev;
  //        });
  //      };
  //      
  //    },
  //  }
  //);


  if (!office) return <div>Loading office...</div>;

  // === SCALE & POSITION ROOMS FOR MINI-MAP ===
  const minX = Math.min(...rooms.map((r) => r.x), 0);
  const minY = Math.min(...rooms.map((r) => r.y), 0);
  const maxX = Math.max(...rooms.map((r) => r.x + r.width), 0);
  const maxY = Math.max(...rooms.map((r) => r.y + r.height), 0);

  const officeWidth = maxX - minX;
  const officeHeight = maxY - minY;
              
  // === Room Widgets ===
  function BookingWidget() {
    return (
      <div className="widget">
        <button>Book a Meeting</button>
      </div>
    );
  }

  function ReceptionChat() {
    return (
      <div className="widget">
        <button>Chat with our receptionist here.</button>
      </div>
    );
  }

  function FAQWidget({ content }) {
    return (
      <div className="widget">
        <h4>FAQ</h4>
        <p>{content || "Ask us anything about our services."}</p>
      </div>
    );
  }

  function InfoBlock({ text }) {
    return (
      <div className="widget">
        <p>{text || "Information about this room."}</p>
      </div>
    );
  }

  // === Room Styling Helper ===
const getRoomStyle = (room) => {
  const style = room?.config?.style || {};
  if (style.bgImage) {
    return {
      position: "relative",
      height: "auto",
      display: "block",
      backgroundImage: `url(${style.bgImage})`,
      backgroundSize: "cover",
      backgroundPosition: "center",
      color: style.textColor || "#0c0c0cff",
      fontSize: style.fontSize ? `${style.fontSize}px` : "14px",
      fontWeight: style.bold ? "bold" : "normal",
      fontStyle: style.italic ? "italic" : "normal",
    };
  } else {
    return {
      backgroundColor: style.bgColor || "#fafafa",
      color: style.textColor || "#333",
      fontSize: style.fontSize ? `${style.fontSize}px` : "14px",
      fontWeight: style.bold ? "bold" : "normal",
      fontStyle: style.italic ? "italic" : "normal",
    };
  }
};

const handleWorkerLogin = async () => {
  try {
    const endpoint = isLoggingIn ? "login" : "logout";

    const res = await publicApi.post(`/worker/${endpoint}/`, {
      work_id: workerId,
    });

    setWorkerPresence(res.data);

    if (endpoint === "logout") {
      // after login, switch to logout mode
      setIsLoggingIn(false);
      setPresenceModalOpen(false);
    } else {
      // after logout, reset for next login
      setIsLoggingIn(true);
      setConfirmLogoutOpen(false);
      setWorkerId("");
    }

  } catch (err) {
    console.error(err);
    alert(`${isLoggingIn ? "Login" : "Logout"} failed. Check Worker ID.`);
  }
};

const handleRoomClick = async (room) => {
  const policy = room.access_policy || "free";
  // 🔑 First check if visitor already has a token
  const tokenKey = `access_token_room_${room.id}`;
  const token = localStorage.getItem(tokenKey);

  if (token) {
    try {
      const res = await publicApi.post(`/rooms/validate_access/`, { token });
      if (res.data.valid) {
        setCurrentRoom(room);
        return; // ✅ Visitor already has access
      } else {
        localStorage.removeItem(tokenKey);
      }
    } catch (err) {
      console.log("Token invalid/expired", err);
      localStorage.removeItem(tokenKey);
    }
  }

  let cfg = room.access_config || {};

  // normalize form_fields if it's a string
  if (typeof cfg.form_fields === "string") {
    cfg.form_fields = cfg.form_fields
      .split(",")
      .map((f) => f.trim())
      .filter(Boolean);
  }

  const normalizedRoom = { ...room, access_config: cfg };

  if (policy === "free") {
    setCurrentRoom(normalizedRoom);
  } else if (policy === "locked") {
    setPendingRoom(normalizedRoom);
    setAccessCode("");
    setAccessModal({ type: "locked", room: normalizedRoom });
  } else if (policy === "form") {
    setPendingRoom(normalizedRoom);
    setFormValues({});
    setAccessModal({ type: "form", room: normalizedRoom });
  } else if (policy === "approval") {
    setPendingRoom(normalizedRoom);
    setFormValues({});
    setAccessModal({ type: "approval", room: normalizedRoom });
  }
};

const handleVisitorAccessSubmit = async (room, extraData = {}) => {
  setLoadingAccess(true);
  try {
    let payload = { room: accessModal.room.id, visitor_id: null };
    if (room.access_policy === "form") {
      const missing = (accessModal.room.access_config?.form_fields || []).filter(
                  (f) => !formValues[f]
                );
                if (missing.length > 0) {
                  alert("Please fill all fields");
                  return;
                }
        payload.data = formValues;
        setCurrentRoom(accessModal.room);
        setAccessModal(null);
      } else if (room.access_policy === "unlock") {
         if (accessModal.room.access_config?.code && accessCode === accessModal.room.access_config.code) {
            payload.data = { code: accessCode };
            setCurrentRoom(accessModal.room);
            setAccessModal(null);
          } else {
            alert("Invalid code");
          }
        
      } else if (room.access_policy === "approval") {
        const missing = (accessModal.room.access_config?.form_fields || []).filter(
                  (f) => !formValues[f]
                );
                if (missing.length > 0) {
                  alert("Please fill all fields");
                  return;
                }
        payload.data = {formValues, request: "pending" };
        setCurrentRoom(accessModal.room);
        setAccessModal(null);
        alert("Request submitted. Please wait for approval.");
        
      }

      const res = await publicApi.post(`/rooms/submit_access/${room.id}/`, payload);
      const { token } = res.data;

      if (token) {
        localStorage.setItem(`access_token_room_${room.id}`, token);
      }
    
    setAccessModal(null);
  } catch (err) {
    console.error(err);
    alert("Access failed. Please try again.");
  } finally {
    setLoadingAccess(false);
  }
};
function renderCurrentRoom (room){
  if(currentRoom.name.toLowerCase().includes("lobby") ||currentRoom.name.toLowerCase().includes("reception")){
    return(
      <div className="lobby-container">
        <div className="reception-lobby">
          <div className="ambient-light"></div>
          <div className="floating-particles">
            {Array.from({length:10}).map((_, i) =>(
              <span key={i} className="particle"></span>
            ))}
          </div>
          {/* Reception Area */}
          <div className="reception-area">
            {/* Waiting Area */}
            <div className="waiting-area">
              <div className="sofa"></div>
              <div className="coffee-table">
                <div className="plant"></div>
              </div>
              <div className="lamp"></div>
            </div>
        
            {/* Reception Desk */}
            <div className="reception-desk">
              <div className="desk-surface">
                <div className="ai-avatar">
                  {currentRoom.config?.components?.map((components, i) => {
                      const WidgetComponent = React.lazy(() => import(`${components.importPath}` /*@vite-ignor*/));
                      return (
                        <Suspense fallback={<div>Loading {components.title}...</div>} key={i}>
                          <WidgetComponent />
                        </Suspense>
                      );
                    })
                  }
                  <span className="ai-label">Receptionist</span>
                </div>
              </div>
              <div className="desk-glow"></div>
              <div className="desk-front"></div>
            </div>
          </div>
          {/* Visitors */}
          <div className="visitors">
            {visitors.map((v) =>(
              <div key={v.id} className="visitor">
                <span className="visitor-avatar">🧍‍♂️</span>
                <span className="visitor-name">{v.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  } else{
    return(
      <div>
        {/* Waiting Area */}
        <div className="waiting-area">
          <div className="sofa"></div>
          <div className="coffee-table">
            <div className="plant"></div>
          </div>
          <div className="lamp"></div>
        </div>
        {currentRoom.config?.components?.map((components, i) => {
            const WidgetComponent = React.lazy(() => import(`${components.importPath}` /*@vite-ignor*/));
            return (
              <Suspense fallback={<div>Loading {components.title}...</div>} key={i}>
                <WidgetComponent />
              </Suspense>
            );
          })
        }

      </div>
    )
  }
}

  return (
    <div className="public-office">
      <div></div>
      <div>
        <div className="office-layout">
        {/* Main content */}
        <main className="office-main">
          {currentRoom && <div className="modern-office-room" style={getRoomStyle(currentRoom)}>
             {currentRoom?.config?.style?.bgImage && (
                <div
                  className="room-overlay"
                  style={{
                    "--overlay-opacity": currentRoom?.config?.style?.overlayOpacity ?? 0.45,
                  }}
                />
              )}
              {/* Room Name */}
              <div className="office-header">
                <h2>Welcome to {office.name} - {currentRoom?.name}</h2>
                <p className ="room-subtitle">{currentRoom?.decription || "Please check in with the receptionist before moving to other rooms."}</p>
              </div>
              {/* Dynamic Layout Based on Room Type */}
              <div className={`office-room-layout ${currentRoom?.name.toLowerCase() || "default-room"}`}>
                {renderCurrentRoom(currentRoom)}
              </div>
              <div className="office-content">
                {currentRoom?.config?.contents?.map((content, idx) =>{
                  switch(content.type){
                    case "text":
                      return (
                        <div
                          key={idx}
                          className="office-block rich-block"
                          dangerouslySetInnerHTML={{ __html: content.value }}
                        />
                      );
                      case "image":
                      return (
                        <div key={idx} className="office-gallery">
                          {(content.contentImg || []).map((img) => (
                            <div key={img.id} className="gallery-thumb">
                              <img src={img.data} alt={`room-content-${img.id}`} />
                            </div>
                          ))}
                        </div>
                      );
                      case "video":
                      return (
                        <div key={idx} className="office-block video-block">
                          <iframe
                            src={content.value}
                            title={`room-video-${idx}`}
                            frameBorder="0"
                            allowFullScreen
                          />
                        </div>
                      );
                    default:
                      return null;
                  }
                })}
              </div>
              <div className="office-decor">
                <div className="window-glow"></div>
              </div>
            </div>
          }
          <br />
          
           {accessModal && (
             <div className="modal-backdrop">
               <div className="modal">
                 <h3>
                   Access Required — {accessModal.room.name}
                 </h3>
           
                 {/* Locked Room */}
                 {accessModal.type === "locked" && (
                   <>
                     <p>This room is locked. Please enter access code:</p>
                     <input
                       type="password"
                       value={accessCode}
                       onChange={(e) => setAccessCode(e.target.value)}
                       placeholder="Enter code"
                     />
                     <div className="modal-actions">
                       <button
                         onClick={() => handleVisitorAccessSubmit(accessModal.room)}
                         disabled={loadingAccess}
                       >
                         Unlock
                       </button>
                       <button onClick={() => setAccessModal(null)}>Cancel</button>
                     </div>
                   </>
                 )}
           
                 {/* Form Required */}
                 {accessModal.type === "form" && (
                   <>
                     <p>Please fill the required form to enter this room:</p>
                     {(accessModal.room.access_config?.form_fields || []).map((field) => (
                       <div key={field}>
                         <label>{field}</label>
                         <input
                           type="text"
                           value={formValues[field] || ""}
                           onChange={(e) =>
                             setFormValues({ ...formValues, [field]: e.target.value })
                           }
                           style={{ width: "100%", padding: 8 }}
                         />
                       </div>
                     ))}
                     <div className="modal-actions">
                       <button
                        onClick={() => handleVisitorAccessSubmit(accessModal.room)}
                        disabled={loadingAccess}
                       >
                         Submit
                       </button>
                       <button onClick={() => setAccessModal(null)}>Cancel</button>
                     </div>
                   </>
                 )}
           
                 {/* Approval Required */}
                 {accessModal.type === "approval" && (
                   <>
                     <p>
                       This room requires staff approval. Please wait for assistance.
                     </p>
                     {(accessModal.room.access_config?.form_fields || []).map((field) => (
                       <div key={field}>
                         <label>{field}</label>
                         <input
                           type="text"
                           value={formValues[field] || ""}
                           onChange={(e) =>
                             setFormValues({ ...formValues, [field]: e.target.value })
                           }
                           style={{ width: "100%", padding: 8 }}
                         />
                       </div>
                     ))}
                     <div className="modal-actions">
                       <button
                        onClick={() => handleVisitorAccessSubmit(accessModal.room)}
                        disabled={loadingAccess}
                       >
                         Submit
                       </button>
                       <button onClick={() => setAccessModal(null)}>Cancel</button>
                     </div>
                   </>
                 )}
               </div>
             </div>
           )}
   
          {confirmLogoutOpen && (
            <div className="modal-backdrop">
              <div className="modal">
                <h3>Confirm Logout</h3>
                <p>Are you sure you want to logout?</p>
                <div className="modal-actions">
                  <button onClick={handleWorkerLogin}>Logout</button>
                  <button onClick={() => {
                    setConfirmLogoutOpen(false)
                    setIsLoggingIn(true);
                  }}>Cancel</button>
                </div>
              </div>
            </div>
          )}
        </main>
         <div className="side-bar-panel">
          <div>
             {/* Mini-map toggle button */}
             <button
               className="map-toggle-btn"
               onClick={() => setMapVisible(!mapVisible)}
             >
               {mapVisible ? "Hide Map ⮝" : "Show office Rooms ⮟"}
             </button>
             
             {/* Sidebar with mini-map */}
             {mapVisible && (
               <aside className="office-sidebar">
                 {/* Zoom controls */}
                 <div className="zoom-controls">
                   <button onClick={() => setScale((s) => Math.min(s + 0.1, 1.5))}>
                     +
                   </button>
                   <button onClick={() => setScale((s) => Math.max(s - 0.1, 0.1))}>
                     –
                   </button>
                 </div>
       
                 <div
                   className="office-map"
                   style={{
                     width: officeWidth * scale,
                     height: officeHeight * scale,
                   }}
                 >
                   {rooms.map((room) => (
                     <div
                       key={room.id}
                       className={`map-room ${currentRoom?.id === room.id ? "map-room-active" : "" }`}
                       onClick={() => handleRoomClick(room)}
                       style={{
                         left: (room.x - minX) * scale,
                         top: (room.y - minY) * scale,
                         width: room.width * scale,
                         height: room.height * scale,
                       }}
                     >
                       {room.name}
                     </div>
                   ))}
                 </div>
               </aside>
             )}
          </div>
          {isLoggingIn ? (
              <button onClick={() => {
              setPresenceModalOpen(true);
              setIsLoggingIn(true); // default to login when opening
            }}>
              Login 
            </button>
            ) :(
             <button onClick={() => {
              setConfirmLogoutOpen(true)
              setPresenceModalOpen(false);
              setIsLoggingIn(false);
              setWorkerId("KO1-0001");
             }}>Logout {workerId}</button>
            )}
            {presenceModalOpen && (
             <div className="modal-backdrop">
               <div className="modal">
                 <h3>{isLoggingIn ? "Worker Login" : "Worker Logout"}</h3>
           
                 <input
                   type="text"
                   placeholder="Enter Worker ID"
                   value={workerId}
                   onChange={(e) => setWorkerId(e.target.value)}
                 />
           
                 <div className="modal-actions">
                   <button onClick={handleWorkerLogin}>
                     Login
                   </button>
                   <button onClick={() => setPresenceModalOpen(false)}>Cancel</button>
                 </div>
               </div>
             </div>
           )}
         </div>
       </div>
      </div>
     
    </div>
  );
}
