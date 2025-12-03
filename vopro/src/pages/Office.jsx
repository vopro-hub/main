import React, { useEffect, useState, useContext, useRef } from "react";
import {api, myOffices } from "../api";
import { AuthContext } from "../context/AuthContext";
import ChatWedge from "./ChatWedge";
import AIAssistantWidget from "../AIStaff/AISecretary";
import AISalesAgentWidget from "../AIStaff/AISalesAgent";
import useWebSocket from "../hooks/useWebSocket";
import { Stage, Layer, Rect, Text, Circle, Transformer } from "react-konva";
import WalletWidget from "../components/WalletWidget";
import '../App.css';
import "./Office.css";
import RichTextEditor from "../components/RichTextEditor";
import { ReactSortable } from "react-sortablejs";
// Animated avatar for users
function AnimatedUserCircle({ x, y, user }) {
  const circleRef = useRef();

  useEffect(() => {
    if (circleRef.current) {
      circleRef.current.scale({ x: 0, y: 0 });
      circleRef.current.to({
        scaleX: 1,
        scaleY: 1,
        duration: 0.25,
        easing: Konva.Easings.EaseOutBack,
      });
    }
  }, [user.id]);

  return (
    <>
      <Circle
        ref={circleRef}
        x={x}
        y={y}
        radius={12}
        fill={user.color || "skyblue"}
        stroke="white"
        strokeWidth={2}
      />
      <Text
        text={user.name}
        x={x + 16}
        y={y - 6}
        fontSize={12}
        fill="#444"
      />
    </>
  );
}

// Room shape with resize support
function RoomShape({ room, isSelected, onSelect, onChange, draggable }) {
  const shapeRef = useRef();
  const trRef = useRef();

  useEffect(() => {
    if (isSelected && trRef.current && shapeRef.current) {
      trRef.current.nodes([shapeRef.current]);
      trRef.current.getLayer().batchDraw();
    }
  }, [isSelected]);

  const style = room.config?.style || {};
  const bgColor = style.bgColor || "#fafafa";
  const textColor = style.textColor || "#333";
  const fontSize = style.fontSize || 14;
  const fontStyle = `${style.bold ? "bold" : ""} ${style.italic ? "italic" : ""}`.trim();

  return (
    <>
      <Rect
        ref={shapeRef}
        x={room.x}
        y={room.y}
        width={room.width}
        height={room.height}
        fill={bgColor}
        stroke="#ccc"
        strokeWidth={2}
        cornerRadius={6}
        shadowBlur={4}
        draggable={draggable}
        onClick={onSelect}
        onTap={onSelect}
        onDragEnd={(e) => {
          onChange({
            ...room,
            x: e.target.x(),
            y: e.target.y(),
          });
        }}
        onTransformEnd={() => {
          const node = shapeRef.current;
          const scaleX = node.scaleX();
          const scaleY = node.scaleY();
          node.scaleX(1);
          node.scaleY(1);
          onChange({
            ...room,
            x: node.x(),
            y: node.y(),
            width: Math.max(50, node.width() * scaleX),
            height: Math.max(50, node.height() * scaleY),
          });
        }}
      />
      <Text
        text={room.name}
        x={room.x + 10}
        y={room.y + 10}
        fontSize={fontSize}
        fill={textColor}
        fontStyle={fontStyle}
      />
      {isSelected && draggable && (
        <Transformer
          ref={trRef}
          boundBoxFunc={(oldBox, newBox) => {
            if (newBox.width < 50 || newBox.height < 50) {
              return oldBox;
            }
            return newBox;
          }}
        />
      )}
    </>
  );
}


export default function Office() {
  const { user, token } = useContext(AuthContext);
  const [offices, setOffices] = useState([]);
  const [presence, setPresence] = useState([]);
  const [selected, setSelected] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [stageScale, setStageScale] = useState(1);
  const [stagePos, setStagePos] = useState({ x: 0, y: 0 });
  const stageRef = useRef();
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [layoutDirty, setLayoutDirty] = useState(false);
  const [roomUsers, setRoomUsers] = useState({}); // mapping: roomId -> [users]
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);
  const [workers, setWorkers] = useState([]);
  const [showWorkerForm, setShowWorkerForm] = useState(false);
  const [newWorkerName, setNewWorkerName] = useState("");
  const [newWorkerRooms, setNewWorkerRooms] = useState("");
  const [editingWorker, setEditingWorker] = useState(null); // holds worker being edited
  const [workerPresence, setWorkerPresence] = useState([]);
  const [to, setTo] = useState("");
  const [body, setBody] = useState("");
  const [logs, setLogs] = useState([]);
  const [activeTool, setActiveTool] = useState(null);
   
  const [accessTab, setAccessTab] = useState("workers"); // "workers" | "visitors"
  const [visitorRooms, setVisitorRooms] = useState([]);

  // Fetch offices
  useEffect(() => {
    if (!user) return;
    (async () => {
      const list = await myOffices();
      setOffices(list);
      if (list.length > 0) {
        loadRooms(list[0].id);
        setSelected(list[0]);
      }

    })();
  }, [user]);

  // Helper to center rooms
  const centerRooms = (roomsData, resetScale = false) => {
    if (!roomsData.length || !stageRef.current) return;

    const stage = stageRef.current;
    const stageWidth = stage.width();
    const stageHeight = stage.height();

    const minX = Math.min(...roomsData.map((r) => r.x));
    const minY = Math.min(...roomsData.map((r) => r.y));
    const maxX = Math.max(...roomsData.map((r) => r.x + r.width));
    const maxY = Math.max(...roomsData.map((r) => r.y + r.height));

    const roomsWidth = maxX - minX || 1;
    const roomsHeight = maxY - minY || 1;

    let newScale = stageScale;

    if (resetScale) {
      const scaleX = stageWidth / roomsWidth;
      const scaleY = stageHeight / roomsHeight;
      newScale = Math.min(scaleX, scaleY, 1);
      setStageScale(newScale);
    }

    const scaleToUse = resetScale ? newScale : stageScale;
    const offsetX =
      (stageWidth - roomsWidth * scaleToUse) / 2 - minX * scaleToUse;
    const offsetY =
      (stageHeight - roomsHeight * scaleToUse) / 2 - minY * scaleToUse;

    setStagePos({ x: offsetX, y: offsetY });
  };

  useEffect(() => {
    if (rooms.length) {
      centerRooms(rooms, true);
    }
  }, [rooms]);

// helper for unique ids
const genId = () =>
  (window.crypto && crypto.randomUUID && crypto.randomUUID()) ||
  `img_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;

// normalize old rooms so contentImg always has {id,data}
const normalizeRooms = (rooms) =>
  rooms.map((r) => {
    const cfg = r.config || {};
    if (Array.isArray(cfg.contents)) {
      cfg.contents = cfg.contents.map((c) => {
        if (c.type === "image") {
          c.contentImg = (c.contentImg || []).map((v) =>
            typeof v === "string" ? { id: genId(), data: v } : v
          );
        }
        return c;
      });
    }
    return { ...r, config: cfg };
  });

  // Load rooms
const loadRooms = async (officeId) => {
  try {
    const roomsRes = await api.get(`/workspace/rooms/?office=${officeId}`);
    
    let allRooms = roomsRes.data.map((r) => {
      let cfg = r.access_config;
      try {
        if (typeof cfg === "string") {
          cfg = JSON.parse(cfg);
        }
      } catch (e) {
        cfg = {};
      }
      if (cfg && typeof cfg.form_fields === "string") {
        cfg.form_fields = cfg.form_fields
          .split(",")
          .map((f) => f.trim())
          .filter(Boolean);
      }
      return { ...r, access_config: cfg || {}, config: r.config || {} };
    });

    allRooms = normalizeRooms(allRooms); // ✅ normalize images
    setRooms(allRooms);

    const resWorkers = await api.get(`/workspace/workers/?office=${officeId}`);
    setWorkers(resWorkers.data);
    const res = await api.get(`/comms/logs/?office=${officeId}`);
    setLogs(res.data);
  } catch (err) {
    console.error("Failed to load rooms or workers:", err);
  }
};


  // Presence WebSocket
  const presenceWS = useWebSocket(
    selected && token
      ? `ws://localhost:8000/ws/presence/office/${selected.id}/?token=${token}`
      : null,
    {
      onMessage: (ev) => {
        if (ev.type === "presence.list" && Array.isArray(ev.users)) {
          const mapping = {};
          ev.users.forEach((u) => {
            const rid = String(u.room || "none");
            if (!mapping[rid]) mapping[rid] = [];
            mapping[rid].push(u);
          });
          setRoomUsers(mapping);
          // also set flat presence list
          setPresence(ev.users.map((u) => ({ user: u, status: "online" })));
        }

        if (ev.type === "presence.update" && ev.user) {
          setRoomUsers((prev) => {
            const newState = {};
            Object.keys(prev).forEach((rid) => {
              newState[rid] = prev[rid].filter((x) => x.id !== ev.user.id);
            });
            const newRoomId = String(ev.user.room || "none");
            if (!newState[newRoomId]) newState[newRoomId] = [];
            newState[newRoomId].push(ev.user);
            return newState;
          });
          // update presence list
           setPresence((prev) => {
             const others = prev.filter((p) => p.id !== ev.user.id);
             return [...others, ev.user];
           });
        }

        if (ev.type === "worker.presence" && Array.isArray(ev.workers)) {
          setWorkerPresence(ev.workers);
        }
      },
      onOpen: () => {
        try {
          presenceWS.send({ status: "online" });
        } catch {}
      },
    }
  );

  // Zoom helpers
  const zoomBy = (factor) => {
    const oldScale = stageScale;
    const newScale = oldScale * factor;
    const stage = stageRef.current;
    if (!stage) return;

    const center = { x: stage.width() / 2, y: stage.height() / 2 };
    const mousePointTo = {
      x: (center.x - stagePos.x) / oldScale,
      y: (center.y - stagePos.y) / oldScale,
    };

    setStageScale(newScale);
    setStagePos({
      x: center.x - mousePointTo.x * newScale,
      y: center.y - mousePointTo.y * newScale,
    });
  };

  const handleZoomIn = () => zoomBy(1.1);
  const handleZoomOut = () => zoomBy(0.9);

  const handleImageUpload = (e, contentIdx) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
  
    Promise.all(
      files.map(
        (file) =>
          new Promise((resolve) => {
            if (file.size > 2 * 1024 * 1024) {
              alert(`${file.name} too large (max 2MB). Skipped.`);
              return resolve(null);
            }
            const reader = new FileReader();
            reader.onloadend = () =>
              resolve({ id: genId(), data: reader.result });
            reader.onerror = () => resolve(null);
            reader.readAsDataURL(file);
          })
      )
    ).then((newImgs) => {
      const valid = newImgs.filter(Boolean);
      if (!valid.length) return;
      setRooms((prev) =>
        prev.map((r) => {
          if (r.id !== selectedRoomId) return r;
          const cfg = { ...r.config };
          cfg.contents = Array.isArray(cfg.contents) ? [...cfg.contents] : [];
          if (!cfg.contents[contentIdx]) {
            cfg.contents[contentIdx] = { type: "image", contentImg: [] };
          }
          const slot = { ...cfg.contents[contentIdx] };
          slot.contentImg = [
            ...(slot.contentImg || []).map((v) =>
              typeof v === "string" ? { id: genId(), data: v } : v
            ),
            ...valid,
          ];
          cfg.contents = cfg.contents.map((c, i) =>
            i === contentIdx ? slot : c
          );
          return { ...r, config: cfg };
        })
      );
      setLayoutDirty(true);
    });
  };
  
  const handleRemoveImage = (imgId, contentIdx) => {
    setRooms((prev) =>
      prev.map((r) => {
        if (r.id !== selectedRoomId) return r;
        const cfg = { ...r.config };
        cfg.contents = (cfg.contents || []).map((c, i) =>
          i === contentIdx
            ? {
                ...c,
                contentImg: (c.contentImg || []).filter((img) => img.id !== imgId),
              }
            : c
        );
        return { ...r, config: cfg };
      })
    );
    setLayoutDirty(true);
  };

  
  // Save layout
  const saveLayout = async () => {
    try {
      const normalizedRooms = rooms.map((r) => {
        let access_config = r.access_config || {};
  
        // Normalize form_fields if present
        if (access_config.form_fields) {
          let fields = [];
  
          if (Array.isArray(access_config.form_fields)) {
            fields = access_config.form_fields;
          } else if (typeof access_config.form_fields === "string") {
            fields = access_config.form_fields.split(",");
          }
  
          fields = fields
            .map((f) => f.trim())
            .filter(Boolean);
  
          access_config = {
            ...access_config,
            form_fields: fields,
          };
        }
  
        return {
          id: r.id,
          x: r.x,
          y: r.y,
          width: r.width,
          height: r.height,
          config: r.config,
          access_policy: r.access_policy || "free",
          access_config,
        };
      });
  
      await api.post("/workspace/rooms/save_layout/", {
        rooms: normalizedRooms,
      });
      alert("Layout saved!");
      setLayoutDirty(false);
      setEditMode(false);
      setSelectedRoomId(null);
    } catch (err) {
      console.error("Error saving layout:", err);
      alert("Failed to save layout.");
    }
  };

  // Add room
  const addRoom = async () => {
    const name = prompt("Enter new room name:");
    if (!name || !selected) return;
    try {
      const res = await api.post("/workspace/rooms/", {
        office: selected.id,
        name,
        x: 100,
        y: 100,
        width: 150,
        height: 100,
      });
      setRooms((prev) => [...prev, res.data]);
    } catch (err) {
      console.error("Error adding room:", err);
    }
  };

  // dropdown for room funtionalities
  //useEffect(() => {
  //  function handleClickOutside(e) {
  //    if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
  //      setShowDropdown(false);
  //    }
  //  }
  //  document.addEventListener("mousedown", handleClickOutside);
  //  return () => {
  //    document.removeEventListener("mousedown", handleClickOutside);
  //  };
  //}, []);

  const addWorker = () => {
    setNewWorkerName("");
    setNewWorkerRooms([]);
    setShowWorkerForm(true);
  };
  
  const saveWorker = async () => {
    if (!selected || !newWorkerName || newWorkerRooms.length === 0) return;
  
    try {
      if (editingWorker) {
        // Update existing worker
        const res = await api.put(`/workspace/workers/${editingWorker.id}/`, {
          office: selected.id,
          name: newWorkerName,
          rooms: newWorkerRooms,
          
        });
        console.log(res.data);
        setWorkers((prev) =>
          prev.map((w) => (w.id === editingWorker.id ? res.data : w))
        );
      } else {
        // Create new worker
        const res = await api.post("/workspace/workers/", {
          office: selected.id,
          name: newWorkerName,
          rooms: newWorkerRooms,
        });
        setWorkers((prev) => [...prev, res.data]);
      }
  
      // Reset form
      setShowWorkerForm(false);
      setEditingWorker(null);
      setNewWorkerName("");
      setNewWorkerRooms([]);
    } catch (err) {
      console.error("Error saving worker:", err);
      alert("Failed to save worker");
    }
  };

  const sendSMS = async (officeId) => {
    await api.post("/comms/sms/send/", { office_id: officeId, to, body });
    setTo(""); setBody("");
  };

   const updateContent = (idx, key, value) => {
  const updated = rooms.map(r =>
    r.id === selectedRoomId
      ? {
          ...r,
          config: {
            ...r.config,
            contents: r.config.contents.map((c, i) =>
              i === idx ? { ...c, [key]: value } : c
            ),
          },
        }
      : r
  );

  setRooms(updated);
  setLayoutDirty(true);
};

  return (
    <div className="office-container">
      <div></div>
      <div>
        <header className="office-header">
        <h2>
          {selected?.name} {selected?.city && `(${selected.city})`}
        </h2>
      </header>
      <div className="sidebar">
        <WalletWidget/>
      </div>
      <div>
        < AIAssistantWidget/>
        < AISalesAgentWidget/>
      </div>
      <div className="chat-panel">
        <ChatWedge />
      </div>
      <div className="office-layout">
        {/* Rooms Grid */}
        <div className="rooms-grid">
          <div className="canvas-wrapper">
            <Stage
              ref={stageRef}
              width={window.innerWidth < 768 ? window.innerWidth - 40 : 800}
              height={window.innerWidth < 768 ? 300 : 400}
              scaleX={stageScale}
              scaleY={stageScale}
              x={stagePos.x}
              y={stagePos.y}
              draggable
              style={{ border: "1px solid #e0e0e0", borderRadius: "8px" }}
              onMouseDown={(e) => {
                if (e.target === e.target.getStage()) {
                  setSelectedRoomId(null);
                }
              }}
            >
              <Layer>
                {rooms.map((room) => {
                  const usersInRoom = roomUsers[String(room.id)] || [];

                  // clamp users inside room width
                  const avatarSpacing = 30;
                  const maxPerRow = Math.floor((room.width - 20) / avatarSpacing);
                  const displayUsers = usersInRoom.slice(0, maxPerRow);
                  const startX = room.x + 20;
                  const baseY =
                    room.y +
                    Math.min(room.height - 24, Math.max(24, room.height / 2));

                  return (
                    <React.Fragment key={room.id}>
                      <RoomShape
                        room={room}
                        isSelected={editMode && room.id === selectedRoomId}
                        draggable={editMode}
                        onSelect={() =>
                          editMode && setSelectedRoomId(room.id) 
                          
                        }
                        onChange={(newAttrs) => {
                          const updated = rooms.map((r) =>
                            r.id === room.id ? newAttrs : r
                          );
                          setRooms(updated);
                          setLayoutDirty(true);
                        }}
                      />

                      {/* Render occupants */}
                      {displayUsers.map((u, i) => (
                        <AnimatedUserCircle
                          key={u.id}
                          x={startX + i * avatarSpacing}
                          y={baseY}
                          user={u}
                        />
                      ))}
                      {/* Render workers */}
                      {workers.filter(w => (w.rooms || []).includes(room.id)).map((w, i) => {
                        const cx = room.x + 20 + (i * 28);
                        const cy = room.y + room.height - 20;
                        return (
                          <React.Fragment key={`worker-${w.id}-${room.id}`}>
                            <Circle
                              x={cx}
                              y={cy}
                              radius={10}
                              fill="orange"
                              stroke="white"
                              strokeWidth={2}
                            />
                            <Text
                              text={w.name}
                              x={cx + 14}
                              y={cy - 6}
                              fontSize={11}
                              fill="#222"
                            />
                          </React.Fragment>
                        );
                      })}


                    </React.Fragment>
                  );
                })}
              </Layer>
            </Stage>
            {editMode && selectedRoomId && (
              <div className="room-settings">
                {/* Bottom Toolbar */}
                <div className="design-toolbar">
                  {["Functionalities", "Content", "Appearance", "Text", "Access"].map((tool) => (
                    <button
                      key={tool}
                      className={`tool-btn ${activeTool === tool ? "active" : ""}`}
                      onClick={() => setActiveTool(tool)}
                    >
                      {tool}
                    </button>
                  ))}
                </div>
                {activeTool && (
                  <>
                    <div className="design-panel">
                     {activeTool === "Functionalities" && (
                     <div className="panel-section">
                       <h4>🧩 Functionalities</h4>
                       <p>Manage meeting rooms, chatbots, and integrations here.</p>
                   
                       {/* Dropdown with checkboxes */}
                       <div className="dropdown" ref={dropdownRef}>
                         <button
                           className="dropdown-toggle"
                           onClick={() => setShowDropdown(!showDropdown)}
                         >
                           Add Functionalities ⮟
                         </button>
                   
                         {showDropdown && (
                           <div className="dropdown-menu">
                             {["assistant", "receptionist", "sales","wallet",  "faq", "info"].map((type) => {
                               const room = rooms.find((r) => r.id === selectedRoomId);
                               const components = room?.config?.components || [];
                               const checked = components.some((w) => w.type === type);
                   
                               const labels = {
                                 assistant: "AI Office Assistant",
                                 receptionist: "AI Receptionist",
                                 sales: "AI Sales Exacutive",
                                 wallet: "Wallet",
                                 faq: "Inquiries / FAQ",
                                 info: "Static Info",
                               };
                   
                               const importPaths = {
                                 assistant: "../AIStaff/AISecretary",
                                 receptionist: "../AIStaff/aireceptionist",
                                 sales: "../AIStaff/AISalesAgent",
                                 wallet: "../components/WalletWidget",
                                 faq: "../components/FaqWidget",
                                 info: "../components/InfoWidget",
                               };
                   
                               return (
                                 <div key={type} className="dropdown-item">
                                   <input
                                     type="checkbox"
                                     id={`${selectedRoomId}-${type}`}
                                     checked={checked}
                                     onChange={(e) => {
                                       const updated = rooms.map((r) =>
                                         r.id === selectedRoomId
                                           ? {
                                               ...r,
                                               config: {
                                                 ...r.config,
                                                 components: e.target.checked
                                                   ? [
                                                       ...components,
                                                       {
                                                         type,
                                                         title: labels[type],
                                                         importPath: importPaths[type],
                                                       },
                                                     ]
                                                   : components.filter((c) => c.type !== type),
                                               },
                                             }
                                           : r
                                       );
                                       setRooms(updated);
                                       setLayoutDirty(true);
                                     }}
                                   />
                                   <label htmlFor={`${selectedRoomId}-${type}`}>
                                     {labels[type]}
                                   </label>
                                 </div>
                               );
                             })}
                           </div>
                         )}
                       </div>
                   
                       {/* Assigned widgets list with remove buttons */}
                       <ul>
                         {rooms.find((r) => r.id === selectedRoomId)?.config?.components?.map(
                           (c, i) => (
                             <li
                               key={i}
                               style={{ display: "flex", alignItems: "center", gap: "8px" }}
                             >
                               <span>{c.title}</span>
                               <button
                                 className="del-room-func-btn"
                                 onClick={() => {
                                   const updated = rooms.map((r) =>
                                     r.id === selectedRoomId
                                       ? {
                                           ...r,
                                           config: {
                                             ...r.config,
                                             components: r.config.components.filter(
                                               (_, idx) => idx !== i
                                             ),
                                           },
                                         }
                                       : r
                                   );
                                   setRooms(updated);
                                   setLayoutDirty(true);
                                 }}
                               >
                                 ✖
                               </button>
                             </li>
                           )
                         )}
                       </ul>
                     </div>
                   )}
                      {activeTool === "Content" && (
                        <div className="panel-section">
                          <h4>📝 Content</h4>
                          <p>Edit room descriptions, images, and resources.</p>
                          {selectedRoomId && (
                            <div className="room-content-editor">
                              <div className="content-add">
                                <label>Add Content:</label>
                                <select
                                  onChange={(e) => {
                                    const type = e.target.value;
                                    if (!type) return;
                                    const room = rooms.find((r) => r.id === selectedRoomId);
                                    const updated = rooms.map((r) =>
                                      r.id === selectedRoomId
                                        ? {
                                            ...r,
                                            config: {
                                              ...r.config,
                                              contents: [
                                                ...(r.config?.contents || []),
                                                { type, value: "" },
                                              ],
                                            },
                                          }
                                        : r
                                    );
                                    setRooms(updated);
                                    setLayoutDirty(true);
                                  }}
                                >
                                  <option value="">Select type...</option>
                                  <option value="text">Text Block</option>
                                  <option value="image">Image</option>
                                  <option value="video">Video</option>
                                  <option value="rich">Rich Content Editor</option>
                                </select>
                              </div>
                              <ReactSortable
                                list={rooms.find(r => r.id === selectedRoomId)?.config?.contents || []}
                                setList={(newList) => {
                                  const updated = rooms.map(r =>
                                    r.id === selectedRoomId
                                      ? {
                                          ...r,
                                          config: { ...r.config, contents: newList },
                                        }
                                      : r
                                  );
                                  setRooms(updated);
                                  setLayoutDirty(true);
                                }}
                                animation={200}
                                handle=".drag-handle"
                              >
                                {(rooms.find(r => r.id === selectedRoomId)?.config?.contents || []).map((content, idx) => (
                                  <div className="content-block" key={idx}>
                                    {content.type === "text" && (
                                     <RichTextEditor
                                        value={content.value || ""}
                                        onChange={(v) => updateContent(idx, "value", v)}
                                      />
                                    )}
                                    {content.type === "image" && (
                                      <div key={idx} className="content-editor">
                                        <label>Upload File (max 2MB)</label>
                                        <label>
                                          <span className="upload-file">📁</span> File
                                          <input
                                            style={{ display: "none" }}
                                            type="file"
                                            accept="image/*"
                                            multiple
                                            onChange={(e) => handleImageUpload(e, idx)}
                                          />
                                        </label>
                                        
                                    
                                        {/* Preview Gallery */}
                                        <div className="image-gallery">
                                          {(content.contentImg || []).map((img) => (
                                            <div key={img.id} className="image-thumb" >
                                              <img
                                                src={img.data}
                                                alt={`room-content-${img.id}`}
                                              />
                                              {/* 🗑️ Remove Button */}
                                              <button className="remove-content-img-btn"
                                                onClick={() => handleRemoveImage(img.id, idx)}
                                                title="Remove image"
                                              >
                                                 ✖
                                              </button>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    {content.type === "video" && (
                                      <>
                                        <label>Video (YouTube/Vimeo URL)</label>
                                        <input
                                          type="text"
                                          value={content.contentVideo || ""}
                                          onChange={(e) => {
                                            const updated = rooms.map((r) =>
                                              r.id === selectedRoomId
                                                ? {
                                                    ...r,
                                                    config: {
                                                      ...r.config,
                                                      contents: r.config.contents.map((c, i) =>
                                                        i === idx ? { ...c, contentVideo: e.target.value } : c
                                                      ),
                                                    },
                                                  }
                                                : r
                                            );
                                            setRooms(updated);
                                            setLayoutDirty(true);
                                          }}
                                        />
                                      </>
                                    )}
                                  </div>
                                ))}
                              </ReactSortable>
                            </div>
                          )}
                        </div>
                      )}
                      {activeTool === "Appearance" && (
                        <div className="panel-section">
                          <h4>🎨 Appearance</h4>
                          <p>Adjust colors, furniture, and room layout style.</p>
                          <div className="background">
                           <p>Background Color or Image</p>
                           <div className="bg-color">
                             <label>Color:</label>
                              <input
                                type="color"
                                value={rooms.find(r => r.id === selectedRoomId)?.config?.style?.bgColor || "#fafafa"}
                                onChange={(e) => {
                                  const updated = rooms.map(r =>
                                    r.id === selectedRoomId
                                      ? {
                                          ...r,
                                          config: {
                                            ...r.config,
                                            style: {
                                              ...r.config?.style,
                                              bgColor: e.target.value,
                                              bgImage: null, // clear image if color chosen
                                            },
                                          },
                                        }
                                      : r
                                  );
                                  setRooms(updated);
                                  setLayoutDirty(true);
                                }}
                              />
                           </div>
                           <div className="bg-img-file">
                             <label htmlFor="upload image file">Upload image:</label>
                             <input
                               type="file"
                               accept="image/*"
                               onChange={(e) => {
                                 const file = e.target.files[0];
                                 if (!file) return;
                                 const reader = new FileReader();
                                 reader.onloadend = () => {
                                   const updated = rooms.map((r) =>
                                     r.id === selectedRoomId
                                       ? {
                                           ...r,
                                           config: {
                                             ...r.config,
                                             style: {
                                               ...r.config?.style,
                                               bgImage: reader.result, // Base64 string
                                             },
                                           },
                                         }
                                       : r
                                   );
                                   setRooms(updated);
                                   setLayoutDirty(true);
                                 };
                                 reader.readAsDataURL(file);
                               }}
                             />
                           </div>
                           <div className="bg-img-url">
                             <label>Or image URL:</label>
                             <input
                               type="text"
                               placeholder="https://example.com/bg.jpg"
                               onBlur={(e) => {
                                 const url = e.target.value;
                                 if (!url) return;
                                 const updated = rooms.map((r) =>
                                   r.id === selectedRoomId
                                     ? {
                                         ...r,
                                         config: {
                                           ...r.config,
                                           style: {
                                             ...r.config?.style,
                                             bgImage: url,
                                           },
                                         },
                                       }
                                     : r
                                 );
                                 setRooms(updated);
                                 setLayoutDirty(true);
                               }}
                             />
                           </div>
                           <button className="clear-bg-btn"
                             onClick={() => {
                               const updated = rooms.map((r) =>
                                 r.id === selectedRoomId
                                   ? {
                                       ...r,
                                       config: {
                                         ...r.config,
                                         style: {
                                           ...r.config?.style,
                                           bgImage: null,
                                         },
                                       },
                                     }
                                   : r
                               );
                               setRooms(updated);
                               setLayoutDirty(true);
                             }}
                             style={{ marginTop: "5px", color: "red" }}
                           >
                             ✖ Clear Background
                           </button>
                          </div>
                           {/* Overlay opacity slider */}
                          {rooms.find((r) => r.id === selectedRoomId)?.config?.style?.bgImage && (
                            <>
                            <div className="overlay">
                              <label>Overlay Opacity:</label>
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.05"
                                value={
                                  rooms.find((r) => r.id === selectedRoomId)?.config?.style
                                    ?.overlayOpacity ?? 0.45
                                }
                                onChange={(e) => {
                                  const opacity = parseFloat(e.target.value);
                                  const updated = rooms.map((r) =>
                                    r.id === selectedRoomId
                                      ? {
                                          ...r,
                                          config: {
                                            ...r.config,
                                            style: {
                                              ...r.config?.style,
                                              overlayOpacity: opacity,
                                            },
                                          },
                                        }
                                      : r
                                  );
                                  setRooms(updated);
                                  setLayoutDirty(true);
                                }}
                              />
                              <span>
                                {(
                                  rooms.find((r) => r.id === selectedRoomId)?.config?.style
                                    ?.overlayOpacity ?? 0.45
                                ).toFixed(2)}
                              </span>
                            </div>
                            </>
                          )}
                        </div>
                      )}
                      {activeTool === "Text" && (
                        <div className="panel-section">
                          <h4> Text</h4>
                          <p>Set the text colour and font style.</p>
                          <div>
                           {/* Text color */}
                           <span className="text-color">
                            <label>Text Color:</label>
                            <input
                             type="color"
                             value={rooms.find(r => r.id === selectedRoomId)?.config?.style?.textColor || "#333"}
                             onChange={(e) => {
                               const updated = rooms.map(r =>
                                 r.id === selectedRoomId
                                   ? {
                                       ...r,
                                       config: {
                                         ...r.config,
                                         style: {
                                           ...r.config?.style,
                                           textColor: e.target.value,
                                         },
                                       },
                                     }
                                   : r
                               );
                               setRooms(updated);
                               setLayoutDirty(true);
                             }}
                           />
                           </span>
                           <span className="font-size">
                            <label>Font Size:</label>
                            <input
                             type="number"
                             min="10"
                             max="36"
                             value={rooms.find(r => r.id === selectedRoomId)?.config?.style?.fontSize || 14}
                             onChange={(e) => {
                               const updated = rooms.map(r =>
                                 r.id === selectedRoomId
                                   ? {
                                       ...r,
                                       config: {
                                         ...r.config,
                                         style: {
                                           ...r.config?.style,
                                           fontSize: parseInt(e.target.value, 10),
                                         },
                                       },
                                     }
                                   : r
                               );
                               setRooms(updated);
                               setLayoutDirty(true);
                             }}
                           />
                           </span>
                          </div>
                          <div className="text-styles">
                            <label>
                              <input
                                type="checkbox"
                                checked={rooms.find(r => r.id === selectedRoomId)?.config?.style?.bold || false}
                                onChange={(e) => {
                                  const updated = rooms.map(r =>
                                    r.id === selectedRoomId
                                      ? {
                                          ...r,
                                          config: {
                                            ...r.config,
                                            style: {
                                              ...r.config?.style,
                                              bold: e.target.checked,
                                            },
                                          },
                                        }
                                      : r
                                  );
                                  setRooms(updated);
                                  setLayoutDirty(true);
                                }}
                              />
                              Bold
                            </label>
                            <label>
                              <input
                                type="checkbox"
                                checked={rooms.find(r => r.id === selectedRoomId)?.config?.style?.italic || false}
                                onChange={(e) => {
                                  const updated = rooms.map(r =>
                                    r.id === selectedRoomId
                                      ? {
                                          ...r,
                                          config: {
                                            ...r.config,
                                            style: {
                                              ...r.config?.style,
                                              italic: e.target.checked,
                                            },
                                          },
                                        }
                                      : r
                                  );
                                  setRooms(updated);
                                  setLayoutDirty(true);
                                }}
                              />
                              Italic
                            </label>
                          </div>
                        </div>
                      )}
                      {activeTool === "Access" && (
                        <div className="panel-section">
                          <h4>🔐 Access</h4>
                          <p>Set who can view or edit this office area.</p>
                          {(() => {
                            const room = rooms.find(r => r.id === selectedRoomId);
                            const policy = room?.access_policy || "free";
                            const config = room?.access_config || {};
                      
                            return (
                              <div className="access-tabs">
                                <label>Policy:</label>
                                <select
                                  value={policy}
                                  onChange={(e) => {
                                    const updated = rooms.map(r =>
                                      r.id === selectedRoomId
                                        ? {
                                            ...r,
                                            access_policy: e.target.value,
                                            access_config: {}, // reset config when switching
                                          }
                                        : r
                                    );
                                    setRooms(updated);
                                    setLayoutDirty(true);
                                  }}
                                >
                                  <option value="free">Free Access</option>
                                  <option value="form">Form Required</option>
                                  <option value="approval">Staff Approval</option>
                                  <option value="locked">Access Code</option>
                                </select>
                      
                                {policy === "locked" && (
                                  <div>
                                    <label>Access Code:</label>
                                    <input
                                      type="text"
                                      value={config.code || ""}
                                      onChange={(e) => {
                                        const updated = rooms.map(r =>
                                          r.id === selectedRoomId
                                            ? {
                                                ...r,
                                                access_policy: policy,
                                                access_config: { ...config, code: e.target.value },
                                              }
                                            : r
                                        );
                                        setRooms(updated);
                                        setLayoutDirty(true);
                                      }}
                                    />
                                  </div>
                                )}
                      
                                {policy === "form" && (
                                  <div>
                                    <label>Required Fields (comma separated):</label>
                                    <input
                                      type="text"
                                      value={config.form_fields}
                                      onChange={(e) => {
                                        const fields = e.target.value
                                        const updated = rooms.map(r =>
                                          r.id === selectedRoomId
                                            ? {
                                                ...r,
                                                access_policy: policy,
                                                access_config: { ...config, form_fields: fields },
                                              }
                                            : r
                                        );
                                        setRooms(updated);
                                        setLayoutDirty(true);
                                      }}
                                    />
                                  </div>
                                )}
                      
                               {policy === "approval" && (
                                 <>
                                   <p style={{ fontSize: "13px", color: "#666" }}>
                                     Visitors must wait for staff approval before entering this room.
                                   </p>
                                   <div>
                                     <label>Required Fields (comma separated):</label>
                                     <input
                                       type="text"
                                       value={config.form_fields}
                                       onChange={(e) => {
                                         const fields = e.target.value
                                         const updated = rooms.map((r) =>
                                           r.id === selectedRoomId
                                             ? {
                                                 ...r,
                                                 access_policy: policy,
                                                 access_config: { ...config, form_fields: fields },
                                               }
                                             : r
                                         );
                               
                                         setRooms(updated);
                                         setLayoutDirty(true);
                                       }}
                                     />
                                   </div>
                                 </>
                               )}
          
                              </div>
                            );
                          })()}
                        </div>
                      )}
                      <div className="content-btns">
                        {editMode && (
                          <>
                            <button className="save-layout-btn"
                              onClick={saveLayout}
                            >
                              Save
                            </button>
          
                            <button className="cancel-changes-btn"
                              onClick={() => {
                                if (layoutDirty) {
                                  const ok = window.confirm("Discard unsaved changes?");
                                  if (!ok) return;
                                }
                                if (selected) {
                                  loadRooms(selected.id);
                                }
                                setEditMode(false);
                                setLayoutDirty(false);
                                setSelectedRoomId(null);
                              }}
                            >
                              Cancel
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Controls */}
            <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
              <button onClick={handleZoomIn}>+</button>
              <button onClick={handleZoomOut}>−</button>
              <button onClick={() => centerRooms(rooms, true)}>Reset</button>

              <button className="layout-mode-btn"
                onClick={() => {
                  if (layoutDirty) {
                    const ok = window.confirm(
                      "You have unsaved changes. Discard and exit edit mode?"
                    );
                    if (!ok) return;
                  }
                  setEditMode(!editMode);
                  setSelectedRoomId(null);
                  if (!editMode) setLayoutDirty(false);
                }}
                style={{background: editMode ? "#f39c12" : "#2d89ef",}}
              >
                {editMode ? "Exit Layout Mode" : "Change Office Layout"}
              </button>

              {editMode && layoutDirty && (
                <>
                  <button className="save-layout-btn"
                    onClick={saveLayout}
                  >
                    Save Layout
                  </button>

                  <button className="cancel-changes-btn"
                    onClick={() => {
                      if (layoutDirty) {
                        const ok = window.confirm("Discard unsaved changes?");
                        if (!ok) return;
                      }
                      if (selected) {
                        loadRooms(selected.id);
                      }
                      setEditMode(false);
                      setLayoutDirty(false);
                      setSelectedRoomId(null);
                    }}
                  >
                    Cancel Changes
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Add Room Button */}
          <div className="room-card add-room" onClick={addRoom}>
            + Add Room
          </div>
        </div>

        {/* Side Panel */}
        <div className="side-panel">
          <div className="card">
            <h3>My Offices</h3>
            <ul>
              {offices.map((o) => (
                <li key={o.id}>
                  <button
                    onClick={() => {
                      setSelected(o);
                      loadRooms(o.id);
                    }}
                  >
                    {o.name} ({o.city})
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const res = await api.post(`/workspace/offices/${selected.id}/toggle_public/`);
                        setSelected(res.data);
                      } catch (err) {
                        console.error("Failed to toggle office:", err);
                      }
                    }}
                  >
                    {selected?.public ? "Make Private" : "Make Public"}
                  </button>
                  {selected?.preview_url && (
                    <a
                      href={selected.preview_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ display: "block", marginTop: "10px", color: "blue" }}
                    >
                      Preview Public Office
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h3>Workers</h3>
            <button onClick={addWorker}>+ Add Worker</button>

            {showWorkerForm && (
              <div className="worker-form">
                <h4>{editingWorker ? "Edit Worker" : "Add Worker"}</h4>
                 
                <input
                  type="text"
                  placeholder="Worker name"
                  value={newWorkerName}
                  onChange={(e) => setNewWorkerName(e.target.value)}
                />
                <select
                  multiple
                  value={newWorkerRooms}
                  onChange={(e) =>
                    setNewWorkerRooms(Array.from(e.target.selectedOptions, (opt) => opt.value))
                  }
                  style={{ minHeight: "80px" }}
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>

                <div className="form-actions">
                  <button onClick={saveWorker}>Save</button>
                  <button
                    onClick={() => {
                      setShowWorkerForm(false);
                      setEditingWorker(null);
                      setNewWorkerName("");
                      setNewWorkerRooms([]);
                    }}
                    style={{ marginLeft: "8px", background: "#f0f0f0" }}
                  >
                    Cancel
                  </button>

                </div>
              </div>
            )}

            <ul>
              {workers.map((w) => (
                <li
                  key={w.id}
                  className="workers-list"
                >
                  <span>
                    {w.name} →{" "}
                    {(w.rooms || [])
                      .map((rid) => rooms.find((r) => r.id === rid)?.name || `Room ${rid}`)
                      .join(", ")}
                  </span>
                  <div className="worker-action-btn">
                    {/* Edit button */}
                    <button className="worker-edit-btn"
                      onClick={() => {
                        setEditingWorker(w);
                        setNewWorkerName(w.name);
                        setNewWorkerRooms(w.rooms || []);
                        setShowWorkerForm(true);
                      }}
                    >
                      ✏ Edit
                    </button>
            
                    {/* Delete button */}
                    <button className="worker-del-btn"
                      onClick={async () => {
                        const ok = window.confirm(
                          `Are you sure you want to delete ${w.name}?`
                        );
                        if (!ok) return;
                        try {
                          await api.delete(`/workspace/workers/${w.id}/`);
                          setWorkers((prev) => prev.filter((x) => x.id !== w.id));
                        } catch (err) {
                          console.error("Error deleting worker:", err);
                          alert("Failed to delete worker.");
                        }
                      }}
                    >
                      🗑 Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>



          </div>
          <div className="card">
            <h3>Workers Online</h3>
            {workerPresence.map((w) => (
              <div key={w.id} className="presence-item">
                <span
                  className="status-dot"
                  style={{ backgroundColor: w.status === "online" ? "green" : "red" }}
                />
                {w.name}
                {w.worker_id}
              </div>
            ))}
          </div>

          <div className="card">
            <h3>All Online</h3>
            {presence.map((p, i) => (
              <div key={i} className="presence-item">
                <span
                  className="status-dot"
                  style={{
                    backgroundColor: p.status === "online" ? "green" : "red",
                  }}
                />
                {p.user}
              </div>
            ))}
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}

   {/* Render editors for existing contents 
                              {(rooms.find((r) => r.id === selectedRoomId)?.config?.contents || []).map(
                                (content, idx) => (
                                  <div key={idx} className="content-editor">
                                    {content.type === "text" && (
                                      <>
                                        <label>Text Block</label>
                                        <textarea
                                          value={content.value || ""}
                                          onChange={(e) => {
                                            const updated = rooms.map((r) =>
                                              r.id === selectedRoomId
                                                ? {
                                                    ...r,
                                                    config: {
                                                      ...r.config,
                                                      contents: r.config.contents.map((c, i) =>
                                                        i === idx ? { ...c, value: e.target.value } : c
                                                      ),
                                                    },
                                                  }
                                                : r
                                            );
                                            setRooms(updated);
                                            setLayoutDirty(true);
                                          }}
                                        />
                                      </>
                                    )}
                                    
                                    {content.type === "video" && (
                                      <>
                                        <label>Video (YouTube/Vimeo URL)</label>
                                        <input
                                          type="text"
                                          value={content.contentVideo || ""}
                                          onChange={(e) => {
                                            const updated = rooms.map((r) =>
                                              r.id === selectedRoomId
                                                ? {
                                                    ...r,
                                                    config: {
                                                      ...r.config,
                                                      contents: r.config.contents.map((c, i) =>
                                                        i === idx ? { ...c, contentVideo: e.target.value } : c
                                                      ),
                                                    },
                                                  }
                                                : r
                                            );
                                            setRooms(updated);
                                            setLayoutDirty(true);
                                          }}
                                        />
                                      </>
                                    )}
                          
                                    
                          
                                    {/* Remove button *
                                    <button className="remove-content"
                                      onClick={() => {
                                        const updated = rooms.map((r) =>
                                          r.id === selectedRoomId
                                            ? {
                                                ...r,
                                                config: {
                                                  ...r.config,
                                                  contents: r.config.contents.filter((_, i) => i !== idx),
                                                },
                                              }
                                            : r
                                        );
                                        setRooms(updated);
                                        setLayoutDirty(true);
                                      }}
                                    >
                                      Remove
                                    </button>
                                  </div>
                                )
                              )}
   */}