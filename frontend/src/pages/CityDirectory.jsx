// pages/CityDirectory.jsx
import React, { useEffect, useState } from "react";
import api from "../api"; // your axios wrapper

export default function CityDirectory({ slug }) {
  const [city, setCity] = useState(null);
  const [offices, setOffices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        // endpoint: /public/city/:slug/
        const res = await api.get(`/public/city/${slug}/`);
        setCity(res.data.city);
        setOffices(res.data.offices || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [slug]);

  if (loading) return <div>Loading...</div>;
  if (!city) return <div>City not found</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Public Offices in {city}</h2>
      <div style={{ display: "grid", gap: 12 }}>
        {offices.map((o) => (
          <div key={o.id} style={{ border: "1px solid #eee", padding: 12, borderRadius: 8 }}>
            <h3>{o.name}</h3>
            <div>Services: {o.services ? Object.keys(o.services).join(", ") : "—"}</div>
            <div style={{ marginTop: 8 }}>
              <a href={`/public-office/${o.public_slug}`}>Enter Office</a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
