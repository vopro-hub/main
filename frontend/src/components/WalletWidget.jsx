import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import {api} from "../api";
import "./WalletWidget.css";

export default function WalletWidget() {
  const {token, user } = useContext(AuthContext);
  const [wallet, setWallet] = useState({ total_credits: 0, reserved_credits: 0, available: 0 });
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [packAmount, setPackAmount] = useState(10); // default $10
  const [isPurchasing, setIsPurchasing] = useState(false);

  // --- Fetch wallet info from backend ---
  async function fetchWallet() {
    
    setLoading(true);
    try {
      const walletRes = await api.get("/wallet/", {
        headers: {Authorization:`Bearer ${token}`}, // ✅ send Django session cookie
      
      });
      setWallet(walletRes.data);
    } catch (err) {
      console.error("Wallet fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }

  // --- Fetch wallet logs ---
  async function fetchLogs() {
    try {
      const logRes = await api.get("/wallet/logs/", {
        headers: {Authorization:`Bearer ${token}`},
      });
      setLogs(logRes.data);
    } catch (err) {
      console.error("Logs fetch failed:", err);
    }
  }

  // --- WebSocket live updates ---
  useEffect(() => {
    if (!user?.id) return;

    fetchWallet();
    fetchLogs();

     const protocol = window.location.protocol === "https:" ? "wss" : "ws";
     const host = window.location.host;
     // If you require auth token via query string:
     const url = `${protocol}://${host}/ws/wallet/${user.id}/?token=${token}`;
   
     const socket = new WebSocket(url);
   
     socket.onopen = () => {
       setConnected(true);
       console.log("WS opened", url);
     };
     socket.onclose = () => {
       setConnected(false);
       console.log("WS closed");
     };
     socket.onerror = (err) => {
       console.error("WS error", err);
     };
     socket.onmessage = (e) => {
       const data = JSON.parse(e.data);
       if (data.type === "wallet.update") setWallet(data.wallet);
       if (data.type === "wallet.log") setLogs(prev => [data.log, ...prev.slice(0, 10)]);
     };
   
     return () => socket.close();
   }, [user?.id, token]);

   async function handlePurchase() {
  if (!packAmount || isNaN(packAmount) || Number(packAmount) <= 0) {
    alert("Enter a valid amount");
    return;
  }

  try {
    const purchaseRes = await api.post(`/wallet/purchase/`, {
      provider: "paystack",
      amount: packAmount,
    });
    if (!purchaseRes.data.reference) throw new Error("Failed to initialize payment");

    // --- ✅ Setup Paystack inline without redirect ---
    const handler = window.PaystackPop && window.PaystackPop.setup({
      key: 'pk_test_280492f7e8feeae35869fb6d23f34476363662b1',
      email: user.email || "abaviawe3@gmail.com",
      amount: Number(packAmount) * 100,
      currency: 'GHS',
      firstname: user.first_name || 'Danny',
      lastname: user.last_name || 'Dan',
      ref: purchaseRes.data.reference,
      metadata: {
        custom_fields: [{
          display_name: `${user.first_name} ${user.last_name}`,
          variable_name: "full_name",
          value: `${user.first_name} ${user.last_name}`,
        }],
      },
      onClose: () => alert("Transaction canceled."),

      // ✅ FIXED CALLBACK — prevents Paystack from redirecting or printing a page
      callback: function (response) {
        (async () => {
           try {
              // Use user.id (avoid sending full object)
              const payload = {
                provider: "paystack",
                reference: response.reference,
              };
        
              // If your backend requires cookies/session auth:
              // ensure api is configured with withCredentials:true or use axios directly:
              const verifyPaymentRes = await api.post("/wallet/verify/", payload, { withCredentials: true });
        
              // debug - inspect full response
              console.log("VERIFY PAYMENT RAW:", verifyPaymentRes);
        
              // most servers return data on verifyPaymentRes.data
              const result = verifyPaymentRes.data;
        
              // If you get unexpected shape, inspect verifyPaymentRes.data to find actual path
              if (result && result.status === "success") {
                alert(`Payment successful! +${result.credits_added} credits`);
                fetchWallet();
                setShowBuyModal(false);
              } else {
                console.warn("Payment verify returned:", result);
                alert("Payment verification failed. Check server response (see console).");
              }
           } catch (err) {
             console.error("Payment verification error:", err);
             alert("Error verifying payment.");
           } finally {
             // 🔒 Close the Paystack iframe manually to avoid extra tab
             if (handler && typeof handler.closeIframe === "function") {
               handler.closeIframe();
             }
           }
        })();
      },
    });

    if (handler) handler.openIframe();
    else alert("Paystack failed to load.");

  } catch (err) {
    console.error("Payment init failed:", err);
    alert("Could not start payment");
  }
}


  if (!user) return null;

  return (
    <div className="wallet-widget">
      <div className="wallet-header">
        <div className="wallet-title">
          <span>Wallet</span>
        </div>
        <div className="wallet-actions">
          <button className="buy-btn" onClick={() => setShowBuyModal(true)}>
            Buy Credits
          </button>
        </div>
        <button className="refresh-btn" onClick={fetchWallet}>
          {loading ? <span className="spin">⟳</span> : "Refresh"}
        </button>
      </div>
      
      <div className="wallet-stats">
        <div><b>Balance:</b> {wallet.total_credits}</div>
        <div><b>Reserved:</b> {wallet.reserved_credits}</div>
        <div><b>Available:</b> {wallet.available}</div>
      </div>

      <hr />

      <div className="wallet-logs">
        <p className="logs-title">Recent Activity</p>
        <ul>
          {logs.length === 0 && <li className="empty">No recent transactions</li>}
          {logs.map((log) => (
            <li key={log.id} className="log-item">
              <span>{log.action}</span>
              <span className={`amount ${log.amount < 0 ? "negative" : "positive"}`}>
                {log.amount > 0 ? "+" : ""}
                {log.amount} cr
              </span>
            </li>
          ))}
        </ul>
      </div>
      {showBuyModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Buy Credits</h3>
            <p>$1 = 100 credits</p>
            <p>Enter amount to purchase:</p>
            <input
              type="number"
              min="1"
              value={packAmount}
              onChange={(e) => setPackAmount(Number(e.target.value))}
              className="input"
            />
            <div className="modal-actions">
              <button onClick={handlePurchase} disabled={isPurchasing}>
                {isPurchasing ? "Processing..." : `Buy $${packAmount}`}
              </button>
              <button className="cancel-btn" onClick={() => setShowBuyModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
