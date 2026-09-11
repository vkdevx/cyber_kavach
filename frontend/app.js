const { useState, useEffect, useRef } = React;

// NOTE: Using in-session React state for theme management ('dark' | 'light'); localStorage and sessionStorage are NOT used per environment constraints.

// --- Helper Functions ---
function getSeverityBadgeClass(severity) {
  switch ((severity || "").toLowerCase()) {
    case "critical": return "badge-critical";
    case "high": return "badge-high";
    case "medium": return "badge-medium";
    case "low": return "badge-low";
    default: return "badge-info";
  }
}

function getChartThemeColors(theme) {
  const isDark = theme === "dark";
  return {
    textColor: isDark ? "#94A3B8" : "#475569",
    gridColor: isDark ? "rgba(255, 255, 255, 0.12)" : "rgba(0, 0, 0, 0.12)",
    tooltipBg: isDark ? "#16202F" : "#FFFFFF",
    tooltipText: isDark ? "#F1F5F9" : "#0F172A",
    borderColor: isDark ? "#00D9E0" : "#007A87",
    criticalColor: isDark ? "#FF3B5C" : "#D32F2F",
    highColor: isDark ? "#FF7A45" : "#E65100",
    mediumColor: isDark ? "#F5A524" : "#B78103",
    lowColor: isDark ? "#00C2A8" : "#00796B",
    beaconColor: isDark ? "#9D4EDD" : "#7E22CE"
  };
}

function getCategoryColor(category, theme) {
  const isDark = theme === "dark";
  const cat = (category || "").toLowerCase();
  if (cat.includes("syn") || cat.includes("dos") || cat.includes("ddos")) {
    return isDark ? "#FF3B5C" : "#D32F2F"; // Red
  }
  if (cat.includes("port")) {
    return isDark ? "#00D9E0" : "#007A87"; // Cyan
  }
  if (cat.includes("beacon")) {
    return isDark ? "#9D4EDD" : "#7E22CE"; // Purple
  }
  if (cat.includes("network") || cat.includes("scan")) {
    return isDark ? "#FF7A45" : "#E65100"; // Vivid Orange
  }
  if (cat.includes("exfiltration") || cat.includes("data")) {
    return isDark ? "#F5A524" : "#B78103"; // Amber
  }
  if (cat.includes("anomaly")) {
    return isDark ? "#00C2A8" : "#00796B"; // Teal
  }
  return isDark ? "#6C7BFF" : "#2563EB"; // Indigo
}

// --- Chart Component 1: ThreatTimelineChart ---
function ThreatTimelineChart({ data, theme, timeframe, setTimeframe }) {
  const canvasRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data || !data.timepoints) return;
    const ctx = canvasRef.current.getContext("2d");
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const c = getChartThemeColors(theme);
    const labels = data.timepoints.map(t => t.timestamp);
    const totalData = data.timepoints.map(t => t.total_threats);
    const portScanData = data.timepoints.map(t => t.port_scan || 0);
    const synFloodData = data.timepoints.map(t => t.syn_flood || 0);
    const beaconingData = data.timepoints.map(t => t.beaconing || 0);

    chartInstance.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Total Threats",
            data: totalData,
            borderColor: c.textColor,
            backgroundColor: theme === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)",
            fill: true,
            tension: 0.3,
            borderWidth: 2
          },
          {
            label: "Port Scanning",
            data: portScanData,
            borderColor: c.borderColor,
            backgroundColor: "rgba(0, 217, 224, 0.1)",
            borderWidth: 2,
            pointRadius: 3
          },
          {
            label: "SYN Flood / DoS",
            data: synFloodData,
            borderColor: c.criticalColor,
            backgroundColor: "rgba(255, 59, 92, 0.1)",
            borderWidth: 2,
            pointRadius: 3
          },
          {
            label: "Beaconing C2",
            data: beaconingData,
            borderColor: c.beaconColor,
            backgroundColor: "rgba(157, 78, 221, 0.1)",
            borderWidth: 2,
            pointRadius: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: c.textColor, font: { family: "Inter", size: 11 } } },
          tooltip: { backgroundColor: c.tooltipBg, titleColor: c.tooltipText, bodyColor: c.tooltipText, borderColor: c.gridColor, borderWidth: 1 }
        },
        scales: {
          x: { ticks: { color: c.textColor, font: { family: "JetBrains Mono", size: 10 } }, grid: { color: c.gridColor } },
          y: { ticks: { color: c.textColor, font: { family: "JetBrains Mono", size: 10 }, precision: 0 }, grid: { color: c.gridColor }, beginAtZero: true }
        }
      }
    });

    return () => {
      if (chartInstance.current) chartInstance.current.destroy();
    };
  }, [data, theme]);

  return (
    <div className="cyber-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700 }}>Attack Type Activity Timeline</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Timeframe Total: <strong style={{ color: "var(--color-primary)" }}>{data?.total_in_window || 0} threats</strong> ({timeframe === "1h" ? "Minutes view • 5-min intervals" : timeframe === "24h" ? "Hours view • 2-hour intervals" : timeframe === "7d" ? "Daily view • 7 days" : "Daily view • 30 days"})
          </div>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {["1h", "24h", "7d", "30d"].map(tf => (
            <button
              key={tf}
              className={`btn ${timeframe === tf ? "btn-primary" : "btn-ghost"}`}
              style={{ padding: "3px 8px", fontSize: 11 }}
              onClick={() => setTimeframe(tf)}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      <div style={{ height: 210, position: "relative" }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}

// --- Chart Component 2: CategoryPieChart ---
function CategoryPieChart({ data, theme }) {
  const canvasRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data || !data.categories) return;
    const ctx = canvasRef.current.getContext("2d");
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const c = getChartThemeColors(theme);
    const labels = data.categories.map(cat => cat.category);
    const counts = data.categories.map(cat => cat.count);
    const colors = data.categories.map(cat => getCategoryColor(cat.category, theme));

    chartInstance.current = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels.length ? labels : ["No Threat Data"],
        datasets: [
          {
            data: counts.length ? counts : [1],
            backgroundColor: counts.length ? colors : ["rgba(148,163,184,0.2)"],
            borderColor: c.tooltipBg,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { color: c.textColor, font: { family: "Inter", size: 11 } } },
          tooltip: { backgroundColor: c.tooltipBg, titleColor: c.tooltipText, bodyColor: c.tooltipText }
        },
        cutout: "60%"
      }
    });

    return () => {
      if (chartInstance.current) chartInstance.current.destroy();
    };
  }, [data, theme]);

  return (
    <div className="cyber-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ fontSize: 15, fontWeight: 700 }}>Category Breakdown (CategoryPieChart)</div>
      <div style={{ height: 210, position: "relative" }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}

// --- Chart Component 3: ProtocolBarChart ---
function ProtocolBarChart({ stats, theme }) {
  const canvasRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !stats || !stats.protocol_breakdown) return;
    const ctx = canvasRef.current.getContext("2d");
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const c = getChartThemeColors(theme);
    const proto = stats.protocol_breakdown;
    const labels = ["TCP", "UDP", "ICMP"];
    const counts = [proto.tcp || 0, proto.udp || 0, proto.icmp || 0];

    chartInstance.current = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Flows",
            data: counts,
            backgroundColor: [c.borderColor, c.mediumColor, c.criticalColor],
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: c.tooltipBg, titleColor: c.tooltipText, bodyColor: c.tooltipText }
        },
        scales: {
          x: { ticks: { color: c.textColor, font: { family: "Inter", size: 11 } }, grid: { display: false } },
          y: { ticks: { color: c.textColor, font: { family: "JetBrains Mono", size: 10 }, precision: 0 }, grid: { color: c.gridColor }, beginAtZero: true }
        }
      }
    });

    return () => {
      if (chartInstance.current) chartInstance.current.destroy();
    };
  }, [stats, theme]);

  return (
    <div className="cyber-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ fontSize: 15, fontWeight: 700 }}>Protocol Traffic (ProtocolBarChart)</div>
      <div style={{ height: 210, position: "relative" }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}

// --- Geolocation Attack Map Component ---
// --- Helper: pick marker colour from risk_score ---
function getMarkerColor(riskScore) {
  if (riskScore >= 85) return "#FF3B5C";   // Critical — red
  if (riskScore >= 65) return "#FF7A45";   // High — orange
  if (riskScore >= 45) return "#F5A524";   // Medium — amber
  if (riskScore >= 25) return "#00C2A8";   // Low — teal
  return "#2ED47A";                         // Safe — green
}

function GeolocationAttackMap({ mapData, theme }) {
  const mapRef = useRef(null);          // DOM div that Leaflet attaches to
  const leafletMap = useRef(null);      // Leaflet map instance
  const markersLayer = useRef(null);    // LayerGroup holding all markers
  const [leafletReady, setLeafletReady] = React.useState(!!window.L);

  const points = mapData || [];

  // Wait for Leaflet to load if not yet available
  useEffect(() => {
    if (window.L) { setLeafletReady(true); return; }
    const interval = setInterval(() => {
      if (window.L) { setLeafletReady(true); clearInterval(interval); }
    }, 200);
    return () => clearInterval(interval);
  }, []);

  // --- Initialise the Leaflet map exactly once ---
  useEffect(() => {
    if (!mapRef.current || !leafletReady || !window.L) return;
    if (leafletMap.current) return;   // already initialised

    const L = window.L;

    // Create map – centre on the world, disable attribution branding clutter
    const map = L.map(mapRef.current, {
      center: [20, 10],
      zoom: 2,
      minZoom: 1,
      maxZoom: 10,
      zoomControl: true,
      attributionControl: true
    });

    // Esri World Dark Gray Canvas — 100% free public map tiles (zero API key needed)
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      {
        attribution: '&copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16
      }
    ).addTo(map);

    markersLayer.current = L.layerGroup().addTo(map);
    leafletMap.current = map;

    return () => {
      map.remove();
      leafletMap.current = null;
    };
  }, []);   // run once

  // --- Update markers whenever data changes ---
  useEffect(() => {
    if (!leafletMap.current || !window.L || !markersLayer.current) return;
    const L = window.L;

    // Clear old markers
    markersLayer.current.clearLayers();

    points.forEach((pt) => {
      const lat = parseFloat(pt.lat) || 0;
      const lon = parseFloat(pt.lon) || 0;
      if (lat === 0 && lon === 0) return;   // skip unresolved coords

      const color = getMarkerColor(pt.risk_score || 0);
      const radius = Math.max(8, Math.min(26, 8 + (pt.count || 1) * 3));

      // Outer pulsing ring
      const pulseIcon = L.divIcon({
        className: "",
        html: `
          <div style="position:relative;width:${radius * 2}px;height:${radius * 2}px;">
            <div style="
              position:absolute;inset:0;border-radius:50%;
              background:${color};opacity:0.18;
              animation:geoMapPulse 2s ease-out infinite;
            "></div>
            <div style="
              position:absolute;top:50%;left:50%;
              transform:translate(-50%,-50%);
              width:${radius}px;height:${radius}px;border-radius:50%;
              background:${color};border:2px solid #fff;
              box-shadow:0 0 8px ${color};
            "></div>
          </div>`,
        iconSize: [radius * 2, radius * 2],
        iconAnchor: [radius, radius]
      });

      const marker = L.marker([lat, lon], { icon: pulseIcon });

      marker.bindPopup(`
        <div style="font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.7;min-width:200px;">
          <div style="font-size:14px;font-weight:700;color:${color};margin-bottom:6px;">
            ${pt.ip}
          </div>
          <table style="width:100%;border-collapse:collapse;">
            <tr><td style="color:#888;padding:1px 6px 1px 0;">Location</td>
                <td style="font-weight:600;">${pt.city || "Unknown"}, ${pt.country || "Unknown"}</td></tr>
            <tr><td style="color:#888;">Coords</td>
                <td>${lat.toFixed(3)}°, ${lon.toFixed(3)}°</td></tr>
            <tr><td style="color:#888;">Category</td>
                <td style="font-weight:600;">${pt.threat_category || "Unknown"}</td></tr>
            <tr><td style="color:#888;">Risk Score</td>
                <td style="font-weight:700;color:${color};">${pt.risk_score}/100</td></tr>
            <tr><td style="color:#888;">Hits</td>
                <td style="font-weight:700;">${pt.count}</td></tr>
          </table>
        </div>
      `, { maxWidth: 260 });

      markersLayer.current.addLayer(marker);
    });
  }, [points]);

  // --- Switch between dark/light tile layer when theme changes ---
  const tileLayerRef = useRef(null);
  useEffect(() => {
    if (!leafletMap.current || !window.L) return;
    const L = window.L;

    // Remove old tile layer
    if (tileLayerRef.current) {
      leafletMap.current.removeLayer(tileLayerRef.current);
    }

    const tileUrl = theme === "light"
      ? "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      : "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}";

    tileLayerRef.current = L.tileLayer(tileUrl, {
      attribution: theme === "light" ? '&copy; OpenStreetMap contributors' : '&copy; Esri',
      subdomains: "abc",
      maxZoom: 18
    }).addTo(leafletMap.current);

    // Push tile layer behind markers
    tileLayerRef.current.bringToBack();
  }, [theme]);

  return (
    <div className="cyber-card" style={{ display: "flex", flexDirection: "column", gap: 0, padding: 0, overflow: "hidden" }}>
      {/* ---- Header bar ---- */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "14px 18px",
        borderBottom: "1px solid var(--border-subtle)"
      }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>🌍 Live Global Attack Origin Map</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Real-time geolocation — click any marker for full attack details · Zoom / Drag to explore
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="badge-pill badge-info">Active Origins: {points.length}</span>
          <span className="badge-pill badge-zero-outbound" style={{ fontSize: 10 }}>
            OpenStreetMap • Live Map
          </span>
        </div>
      </div>

      {/* ---- Map + sidebar layout ---- */}
      <div style={{ display: "flex", height: 420 }}>

        {/* Leaflet map canvas */}
        <div style={{ flex: 1, position: "relative" }}>
          {/* Keyframe injection for pulsing marker rings */}
          <style>{`
            @keyframes geoMapPulse {
              0%   { transform: scale(1);   opacity: 0.6; }
              70%  { transform: scale(2.2); opacity: 0;   }
              100% { transform: scale(2.2); opacity: 0;   }
            }
            .leaflet-popup-content-wrapper {
              background: #16202F !important;
              color: #F1F5F9 !important;
              border: 1px solid rgba(255,255,255,0.15) !important;
              border-radius: 8px !important;
            }
            .leaflet-popup-tip { background: #16202F !important; }
            .leaflet-popup-close-button { color: #94A3B8 !important; }
          `}</style>

          <div ref={mapRef} style={{ width: "100%", height: "100%", background: "#0A1628" }} />

          {/* Loading overlay if Leaflet not yet ready */}
          {!leafletReady && (
            <div style={{
              position: "absolute", inset: 0, background: "#0A1628",
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              zIndex: 2000, gap: 12
            }}>
              <div style={{ fontSize: 32 }}>🗺️</div>
              <div style={{ color: "#00D9E0", fontWeight: 700, fontSize: 14 }}>Loading Map Engine…</div>
              <div style={{ color: "#64748B", fontSize: 12 }}>Initializing Global Attack Map</div>
            </div>
          )}

          {/* Legend overlay inside map */}
          <div style={{
            position: "absolute", bottom: 12, left: 12, zIndex: 1000,
            background: "rgba(10,14,23,0.82)", backdropFilter: "blur(6px)",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: 7, padding: "8px 12px",
            display: "flex", gap: 12, alignItems: "center", fontSize: 11, fontWeight: 600
          }}>
            {[
              { label: "Critical", color: "#FF3B5C" },
              { label: "High",     color: "#FF7A45" },
              { label: "Medium",   color: "#F5A524" },
              { label: "Low",      color: "#00C2A8" },
              { label: "Safe",     color: "#2ED47A" }
            ].map(({ label, color }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}` }} />
                <span style={{ color: "#CBD5E1" }}>{label}</span>
              </div>
            ))}
          </div>
        </div>


        {/* ---- Right sidebar: origin table ---- */}
        <div style={{
          width: 280, overflowY: "auto",
          borderLeft: "1px solid var(--border-subtle)",
          background: "var(--bg-surface-sunken)"
        }}>
          <div style={{
            padding: "10px 14px", fontWeight: 700, fontSize: 12,
            textTransform: "uppercase", letterSpacing: "0.06em",
            color: "var(--text-muted)", borderBottom: "1px solid var(--border-subtle)",
            position: "sticky", top: 0, background: "var(--bg-surface-sunken)", zIndex: 1
          }}>
            Attack Origins ({points.length})
          </div>

          {points.length === 0 ? (
            <div style={{ padding: 20, color: "var(--text-muted)", fontSize: 12, textAlign: "center" }}>
              Inject an attack scenario on the Dashboard to see origin data populate here.
            </div>
          ) : (
            points.map((pt, idx) => {
              const color = getMarkerColor(pt.risk_score || 0);
              return (
                <div key={idx} style={{
                  padding: "10px 14px",
                  borderBottom: "1px solid var(--border-subtle)",
                  display: "flex", flexDirection: "column", gap: 4,
                  cursor: "pointer"
                }}
                  onClick={() => {
                    if (leafletMap.current && window.L) {
                      const lat = parseFloat(pt.lat) || 0;
                      const lon = parseFloat(pt.lon) || 0;
                      leafletMap.current.setView([lat, lon], 5, { animate: true });
                    }
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="mono" style={{ fontWeight: 700, fontSize: 12, color: "var(--color-primary)" }}>
                      {pt.ip}
                    </span>
                    <span style={{
                      background: color, color: "#fff", fontSize: 9, fontWeight: 700,
                      padding: "2px 6px", borderRadius: 10
                    }}>
                      {pt.risk_score}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, fontWeight: 600 }}>📍 {pt.city}, {pt.country}</div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--text-muted)" }}>
                    <span>{pt.threat_category}</span>
                    <span style={{ color: color, fontWeight: 700 }}>{pt.count} hits</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

// --- Chart Component 4: WeeklyReportCharts ---
function WeeklyReportCharts({ weeklyData, theme }) {
  const trendCanvasRef = useRef(null);
  const sevCanvasRef = useRef(null);
  const trendChartInstance = useRef(null);
  const sevChartInstance = useRef(null);

  useEffect(() => {
    if (!trendCanvasRef.current || !weeklyData || !weeklyData.daily_breakdown) return;
    const ctxTrend = trendCanvasRef.current.getContext("2d");
    if (trendChartInstance.current) trendChartInstance.current.destroy();

    const c = getChartThemeColors(theme);
    const labels = weeklyData.daily_breakdown.map(d => `${d.day} (${d.date_str})`);
    const totals = weeklyData.daily_breakdown.map(d => d.total_threats);
    const criticals = weeklyData.daily_breakdown.map(d => d.critical);

    trendChartInstance.current = new Chart(ctxTrend, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Daily Threats",
            data: totals,
            borderColor: c.borderColor,
            backgroundColor: theme === "dark" ? "rgba(0, 217, 224, 0.15)" : "rgba(0, 122, 135, 0.15)",
            fill: true,
            tension: 0.3,
            borderWidth: 2
          },
          {
            label: "Critical Threats",
            data: criticals,
            borderColor: c.criticalColor,
            borderDash: [4, 4],
            borderWidth: 2,
            pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: c.textColor, font: { family: "Inter", size: 11 } } },
          tooltip: { backgroundColor: c.tooltipBg, titleColor: c.tooltipText, bodyColor: c.tooltipText }
        },
        scales: {
          x: { ticks: { color: c.textColor, font: { family: "Inter", size: 11 } }, grid: { color: c.gridColor } },
          y: { ticks: { color: c.textColor, font: { family: "JetBrains Mono", size: 10 }, precision: 0 }, grid: { color: c.gridColor }, beginAtZero: true }
        }
      }
    });

    return () => {
      if (trendChartInstance.current) trendChartInstance.current.destroy();
    };
  }, [weeklyData, theme]);

  useEffect(() => {
    if (!sevCanvasRef.current || !weeklyData || !weeklyData.severity_breakdown) return;
    const ctxSev = sevCanvasRef.current.getContext("2d");
    if (sevChartInstance.current) sevChartInstance.current.destroy();

    const c = getChartThemeColors(theme);
    const sevMap = weeklyData.severity_breakdown;
    const labels = ["Critical", "High", "Medium", "Low"];
    const counts = [sevMap.Critical || 0, sevMap.High || 0, sevMap.Medium || 0, sevMap.Low || 0];

    sevChartInstance.current = new Chart(ctxSev, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Threat Count",
            data: counts,
            backgroundColor: [c.criticalColor, c.highColor, c.mediumColor, c.lowColor],
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: c.tooltipBg, titleColor: c.tooltipText, bodyColor: c.tooltipText }
        },
        scales: {
          x: { ticks: { color: c.textColor, font: { family: "Inter", size: 11 } }, grid: { display: false } },
          y: { ticks: { color: c.textColor, font: { family: "JetBrains Mono", size: 10 }, precision: 0 }, grid: { color: c.gridColor }, beginAtZero: true }
        }
      }
    });

    return () => {
      if (sevChartInstance.current) sevChartInstance.current.destroy();
    };
  }, [weeklyData, theme]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div className="cyber-card">
        <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Daily Threat Trend</div>
        <div style={{ height: 210, position: "relative" }}>
          <canvas ref={trendCanvasRef} />
        </div>
      </div>

      <div className="cyber-card">
        <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Weekly Severity Distribution</div>
        <div style={{ height: 210, position: "relative" }}>
          <canvas ref={sevCanvasRef} />
        </div>
      </div>
    </div>
  );
}

// --- Main App Component ---
function App() {
  const [theme, setTheme] = useState("light");

  const [activeTab, setActiveTab] = useState("dashboard");
  const [timeframe, setTimeframe] = useState("1h");
  const [selectedWeek, setSelectedWeek] = useState("current");

  const [stats, setStats] = useState({
    total_packets: 14250,
    total_flows: 1250,
    safe_flows: 1180,
    suspicious_flows: 70,
    active_threat_level: "Low",
    protocol_breakdown: { tcp: 950, udp: 220, icmp: 80 },
    top_attacked_ports: [{ port: 80, count: 420 }, { port: 443, count: 310 }, { port: 53, count: 120 }]
  });

  const [alerts, setAlerts] = useState([]);
  const [threatTimeline, setThreatTimeline] = useState(null);
  const [categoryBreakdown, setCategoryBreakdown] = useState(null);
  const [attackMapData, setAttackMapData] = useState([]);
  const [weeklyReport, setWeeklyReport] = useState(null);

  const [selectedAlert, setSelectedAlert] = useState(null);
  const [toast, setToast] = useState(null);
  const [isConnected, setIsConnected] = useState(true);

  // Filters for Threat Logs table
  const [searchIP, setSearchIP] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Intel Inspector state
  const [intelSearchIP, setIntelSearchIP] = useState("198.51.100.45");
  const [intelResult, setIntelResult] = useState({
    ip: "198.51.100.45",
    listed: true,
    threat_score: 85,
    category: "scanner",
    source_feed: "emerging_threats",
    country_code: "DE",
    last_seen: Date.now() / 1000
  });

  // PCAP Upload state
  const [pcapUploading, setPcapUploading] = useState(false);
  const [pcapResult, setPcapResult] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  });

  const fetchAllDashboardData = async () => {
    try {
      const resStats = await fetch("/api/v1/dashboard/stats");
      if (resStats.ok) {
        const dataStats = await resStats.json();
        setStats(dataStats);
      }

      const resAlerts = await fetch("/api/v1/threats");
      if (resAlerts.ok) {
        const dataAlerts = await resAlerts.json();
        setAlerts(dataAlerts.items || []);
      }

      const resTimeline = await fetch(`/api/v1/dashboard/threats-over-time?timeframe=${timeframe}`);
      if (resTimeline.ok) {
        const dataTimeline = await resTimeline.json();
        setThreatTimeline(dataTimeline);
      }

      const resCat = await fetch(`/api/v1/dashboard/category-breakdown?timeframe=${timeframe}`);
      if (resCat.ok) {
        const dataCat = await resCat.json();
        setCategoryBreakdown(dataCat);
      }

      const resMap = await fetch("/api/v1/dashboard/attack-map");
      if (resMap.ok) {
        const dataMap = await resMap.json();
        setAttackMapData(dataMap);
      }

      const resWeekly = await fetch(`/api/v1/dashboard/weekly-report?week=${selectedWeek}`);
      if (resWeekly.ok) {
        const dataWeekly = await resWeekly.json();
        setWeeklyReport(dataWeekly);
      }
    } catch (err) {
      console.warn("Polling fetch fallback:", err);
    }
  };

  useEffect(() => {
    fetchAllDashboardData();
    const interval = setInterval(fetchAllDashboardData, 3000);
    return () => clearInterval(interval);
  }, [timeframe, selectedWeek]);

  // WebSocket Listener
  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/ws/live-traffic`;
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setIsConnected(true);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event_type === "ALERT_NEW") {
            setAlerts((prev) => [data.payload, ...prev]);
            showToast("NEW THREAT DETECTED: " + data.payload.threat_category, "danger");
            fetchAllDashboardData();
          }
        } catch (e) {}
      };
      ws.onclose = () => setIsConnected(false);
    } catch (e) {
      setIsConnected(false);
    }
    return () => {
      if (ws) ws.close();
    };
  }, [timeframe, selectedWeek]);

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const handleAcknowledge = async (alertId) => {
    try {
      const res = await fetch(`/api/v1/threats/${alertId}/ack`, { method: "POST" });
      if (res.ok) {
        const updated = await res.json();
        setAlerts((prev) => prev.map((a) => (a.alert_id === alertId ? updated : a)));
        if (selectedAlert && selectedAlert.alert_id === alertId) {
          setSelectedAlert(updated);
        }
        showToast(`Alert ${alertId} marked as Acknowledged.`, "success");
        fetchAllDashboardData();
      }
    } catch (e) {
      showToast("Failed to acknowledge alert.", "danger");
    }
  };

  const handleFalsePositive = async (alertId) => {
    try {
      const res = await fetch(`/api/v1/threats/${alertId}/false-positive`, { method: "POST" });
      if (res.ok) {
        const updated = await res.json();
        setAlerts((prev) => prev.map((a) => (a.alert_id === alertId ? updated : a)));
        if (selectedAlert && selectedAlert.alert_id === alertId) {
          setSelectedAlert(updated);
        }
        showToast(`Alert ${alertId} marked as False Positive.`, "info");
        fetchAllDashboardData();
      }
    } catch (e) {
      showToast("Failed to update status.", "danger");
    }
  };

  const handleBlockIPAction = async (ip) => {
    try {
      const res = await fetch("/api/v1/actions/block-ip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip, reason: "Analyst dashboard quick action" })
      });
      if (res.status === 400) {
        const err = await res.json();
        showToast(err.detail.message, "danger");
      } else if (res.status === 403) {
        showToast("Role 'admin' required to execute firewall quick actions.", "warning");
      }
    } catch (e) {
      showToast("Active response error.", "danger");
    }
  };

  const handleIntelLookup = async (ipToSearch) => {
    try {
      const res = await fetch(`/api/v1/threat-intel/ips/${ipToSearch}`);
      if (res.ok) {
        const data = await res.json();
        setIntelResult(data);
        showToast(`Threat Intel lookup complete for ${ipToSearch}`, "info");
      }
    } catch (e) {
      showToast("Threat Intel lookup failed.", "danger");
    }
  };

  const handlePcapUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setPcapUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/pcaps/upload", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setPcapResult(data);
        fetchAllDashboardData();
        showToast(`PCAP '${file.name}' processed: ${data.packets_parsed} packets parsed.`, "success");
      } else {
        showToast("PCAP upload failed.", "danger");
      }
    } catch (e) {
      showToast("Error processing PCAP.", "danger");
    } finally {
      setPcapUploading(false);
    }
  };

  const handleSimulateScenario = async (scenario) => {
    try {
      const nowTs = Date.now() / 1000;
      const samplePackets = {
        normal: Array.from({ length: 15 }, (_, i) => ({
          src_ip: "192.168.1.105",
          dst_ip: "10.0.0.5",
          src_port: 54321,
          dst_port: 443,
          protocol: "TCP",
          packet_length: 512,
          timestamp: nowTs + i * 0.1,
          tcp_flags: "PA"
        })),
        port_scan: Array.from({ length: 20 }, (_, i) => ({
          src_ip: "198.51.100.45",
          dst_ip: "10.0.0.5",
          src_port: 50000,
          dst_port: i + 1,
          protocol: "TCP",
          packet_length: 64,
          timestamp: nowTs + i * 0.01,
          tcp_flags: "S"
        })),
        syn_flood: Array.from({ length: 25 }, (_, i) => ({
          src_ip: "203.0.113.99",
          dst_ip: "10.0.0.5",
          src_port: 40000 + i,
          dst_port: 80,
          protocol: "TCP",
          packet_length: 64,
          timestamp: nowTs + i * 0.001,
          tcp_flags: "S"
        }))
      };

      const pkts = samplePackets[scenario] || samplePackets.port_scan;
      const res = await fetch("/api/v1/telemetry/packet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pkts)
      });
      if (res.ok) {
        await fetchAllDashboardData();
        const scName = scenario === "syn_flood" ? "SYN FLOOD / DDOS" : scenario === "port_scan" ? "PORT SCAN" : "BENIGN TRAFFIC";
        showToast(`Scenario '${scName}' injected successfully.`, scenario === "normal" ? "success" : "danger");
      }
    } catch (e) {
      showToast("Scenario trigger failed.", "danger");
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    const matchIP = !searchIP || (a.src_ip && a.src_ip.includes(searchIP)) || (a.dst_ip && a.dst_ip.includes(searchIP));
    const matchSev = severityFilter === "ALL" || (a.severity || "").toUpperCase() === severityFilter;
    const matchStatus = statusFilter === "ALL" || (a.status || "").toLowerCase() === statusFilter.toLowerCase();
    return matchIP && matchSev && matchStatus;
  });

  // Prepare live network graph nodes — deduplicated by src_ip
  const networkGraphNodes = (() => {
    const centerNode = {
      id: "center",
      ip: "Wi-Fi Monitor",
      label: "CYBERKAVACH DEFENCE SENSOR (Wi-Fi)",
      isCenter: true,
      volume: 15000,
      risk: "safe",
      category: "Monitoring Interface",
      port: 443,
      protocol: "TCP"
    };

    // Group alerts by unique src_ip
    const ipMap = {};
    alerts.forEach(a => {
      const ip = a.src_ip;
      if (!ip) return;
      if (!ipMap[ip]) {
        ipMap[ip] = {
          ip,
          count: 0,
          totalRisk: 0,
          maxRisk: 0,
          severity: a.severity || "medium",
          category: a.threat_category || "Unknown",
          protocol: a.protocol || "TCP",
          port: a.dst_port || 80
        };
      }
      ipMap[ip].count += 1;
      ipMap[ip].totalRisk += (a.risk_score || 50);
      if ((a.risk_score || 0) > ipMap[ip].maxRisk) {
        ipMap[ip].maxRisk = a.risk_score || 0;
        ipMap[ip].severity = a.severity || "medium";
        ipMap[ip].category = a.threat_category || ipMap[ip].category;
      }
    });

    const uniqueIPNodes = Object.entries(ipMap)
      .sort((a, b) => b[1].maxRisk - a[1].maxRisk) // highest risk first
      .slice(0, 15) // max 15 unique IPs
      .map(([ip, data], idx) => ({
        id: `ip_${ip.replace(/\./g, "_")}`,
        ip,
        risk: (data.severity || "medium").toLowerCase(),
        volume: 400 + (data.count * 200) + (data.maxRisk * 10),
        port: data.port,
        protocol: data.protocol,
        category: data.category
      }));

    return [centerNode, ...uniqueIPNodes];
  })();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Toast Banner */}
      {toast && (
        <div
          style={{
            position: "fixed",
            top: 20,
            right: 20,
            zIndex: 9999,
            background: toast.type === "danger" ? "var(--severity-critical)" : toast.type === "success" ? "var(--status-success)" : "var(--color-primary)",
            color: "#fff",
            padding: "12px 20px",
            borderRadius: 6,
            fontWeight: 600,
            boxShadow: "0 0 20px rgba(0,0,0,0.5)"
          }}
        >
          {toast.message}
        </div>
      )}

      {/* Persistent Sidebar */}
      <aside
        style={{
          width: 260,
          background: "var(--bg-sidebar)",
          borderRight: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          padding: 20
        }}
      >
        {/* CyberKavach Brand Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24, padding: "4px 0" }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: "linear-gradient(135deg, #00D9E0 0%, #007A87 50%, #04141A 100%)",
            border: "1.5px solid rgba(0, 217, 224, 0.4)",
            boxShadow: "0 0 16px rgba(0, 217, 224, 0.35), inset 0 0 8px rgba(255,255,255,0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
            flexShrink: 0
          }}>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L3 6V11.5C3 16.8 6.8 21.7 12 23C17.2 21.7 21 16.8 21 11.5V6L12 2Z" fill="rgba(4, 20, 26, 0.85)" stroke="#00D9E0" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M12 7V16M8.5 11.5L12 15L15.5 11.5" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 17, color: "var(--text-primary)", letterSpacing: "0.04em", display: "flex", alignItems: "center", gap: 2 }}>
              <span>CYBER<span style={{ color: "#00D9E0" }}>KAVACH</span></span>
            </div>
            <div style={{ fontSize: 11, color: "var(--color-primary)", letterSpacing: "0.03em", fontWeight: 600, opacity: 0.9 }}>
              Presented by <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>CyberCrew</span>
            </div>
          </div>
        </div>

        {/* Pinned Zero-Outbound Badge */}
        <div className="badge-pill badge-zero-outbound" style={{ width: "100%", justifyContent: "center", marginBottom: 24, padding: 8 }}>
          <span className="status-dot status-dot-green"></span>
          0 BYTES SENT BACK (PASSIVE)
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
          <button
            className={`btn ${activeTab === "dashboard" ? "btn-primary" : "btn-ghost"}`}
            style={{ justifyContent: "flex-start" }}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={`btn ${activeTab === "graph" ? "btn-primary" : "btn-ghost"}`}
            style={{ justifyContent: "flex-start" }}
            onClick={() => setActiveTab("graph")}
          >
            Network Relationship View
          </button>
          <button
            className={`btn ${activeTab === "weekly" ? "btn-primary" : "btn-ghost"}`}
            style={{ justifyContent: "flex-start" }}
            onClick={() => setActiveTab("weekly")}
          >
            Weekly Threat Report
          </button>
          <button
            className={`btn ${activeTab === "logs" ? "btn-primary" : "btn-ghost"}`}
            style={{ justifyContent: "flex-start" }}
            onClick={() => setActiveTab("logs")}
          >
            Threat Logs ({alerts.length})
          </button>
          <button
            className={`btn ${activeTab === "intel" ? "btn-primary" : "btn-ghost"}`}
            style={{ justifyContent: "flex-start" }}
            onClick={() => setActiveTab("intel")}
          >
            Threat Intel Inspector
          </button>
          <button
            className={`btn ${activeTab === "pcap" ? "btn-primary" : "btn-ghost"}`}
            style={{ justifyContent: "flex-start" }}
            onClick={() => setActiveTab("pcap")}
          >
            PCAP Upload & Analysis
          </button>
        </nav>

        {/* System Health Footer */}
        <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 16, fontSize: 12, color: "var(--text-muted)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span>Link Mode:</span>
            <span style={{ color: "var(--color-accent-mint)" }}>READ-ONLY</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>WebSocket:</span>
            <span style={{ color: isConnected ? "var(--status-success)" : "var(--status-danger)" }}>
              {isConnected ? "CONNECTED" : "FALLBACK"}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Page Area */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {/* Header with Theme Toggle */}
        <header
          style={{
            height: 64,
            background: "var(--bg-header)",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px"
          }}
        >
          <div style={{ fontSize: 18, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.02em" }}>
            {activeTab === "dashboard" && "Live Traffic & Threat Monitor"}
            {activeTab === "graph" && "Interactive Network Relationship Graph View"}
            {activeTab === "weekly" && "Weekly Executive Threat Report"}
            {activeTab === "logs" && "SOC Threat Logs & History"}
            {activeTab === "intel" && "Historical Attacking IP & Reputation Inspector"}
            {activeTab === "pcap" && "Offline PCAP Capture Analysis"}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <button className="btn-theme-toggle" onClick={toggleTheme} title="Switch between Light and Dark mode">
              <span>{theme === "dark" ? "☀️ Light Mode" : "🌙 Dark Mode"}</span>
            </button>
            <span className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
              UTC {new Date().toISOString().substring(11, 19)}
            </span>
            <span className="badge-pill badge-info">eth0 (promisc)</span>
          </div>
        </header>

        {/* Dynamic View Content */}
        <div style={{ padding: 24, flex: 1, overflowY: "auto" }}>
          {/* TAB 1: MAIN DASHBOARD */}
          {activeTab === "dashboard" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              {/* StatusBar */}
              <div className="cyber-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span className="status-dot status-dot-green pulse-active"></span>
                  <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>🛡️ CyberKavach Autonomous AI Threat Shield Active</span>
                  <span style={{ color: "var(--text-muted)", fontSize: 13 }}>| Interface: Wi-Fi (read-only)</span>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <span className="badge-pill badge-info">RF Threat Model v1.0</span>
                  <span className="badge-pill badge-info">IF Anomaly Model v1.0</span>
                </div>
              </div>

              {/* 4x KPI Cards Row */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Total Packets Ingested</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0" }}>{stats.total_packets.toLocaleString()}</div>
                  <div style={{ fontSize: 12, color: "var(--status-success)" }}>↑ 100% Inbound Capture</div>
                </div>

                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Active Threat Level</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0", color: stats.active_threat_level === "Critical" ? "var(--severity-critical)" : stats.active_threat_level === "High" ? "var(--severity-high)" : "var(--color-primary)" }}>
                    {stats.active_threat_level.toUpperCase()}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Based on 5-band scale</div>
                </div>

                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Suspicious Threat Flows</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0", color: "var(--severity-high)" }}>{stats.suspicious_flows}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Flagged by Hybrid Engine</div>
                </div>

                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Safe Benign Flows</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0", color: "var(--status-success)" }}>{stats.safe_flows}</div>
                  <div style={{ fontSize: 12, color: "var(--status-success)" }}>Clean Traffic Verified</div>
                </div>
              </div>

              {/* Real-Time Dashboard Charts Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
                <ThreatTimelineChart data={threatTimeline} theme={theme} timeframe={timeframe} setTimeframe={setTimeframe} />
                <CategoryPieChart data={categoryBreakdown} theme={theme} />
              </div>

              {/* Geolocation Attack Origin Map */}
              <GeolocationAttackMap mapData={attackMapData} theme={theme} />

              <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 16 }}>
                <ProtocolBarChart stats={stats} theme={theme} />
                
                {/* Attack Simulator Controls */}
                <div className="cyber-card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Live Cyber Attack Injector</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16 }}>
                      Inject simulated traffic scenarios into the 5-stage detection pipeline to verify real-time alert feed & chart updating.
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <button className="btn btn-primary" onClick={() => handleSimulateScenario("normal")}>
                      Emit Benign Traffic
                    </button>
                    <button className="btn btn-ghost" onClick={() => handleSimulateScenario("port_scan")}>
                      ⚡ Inject Port Scan Attack
                    </button>
                    <button className="btn btn-danger" onClick={() => handleSimulateScenario("syn_flood")}>
                      🔥 Inject SYN Flood / DDoS Attack
                    </button>
                  </div>
                </div>
              </div>

              {/* Live Real-Time Threat Alerts Feed Table */}
              <div className="cyber-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>Live Real-Time Threat Alerts Feed</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Total Feed Alerts: <strong style={{ color: "var(--color-primary)" }}>{alerts.length}</strong> (Numbers match charts above)
                    </div>
                  </div>
                  <button className="btn btn-ghost" onClick={() => setActiveTab("logs")}>View All Logs →</button>
                </div>

                <table className="cyber-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Source IP</th>
                      <th>Threat Category</th>
                      <th>Risk Score</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Quick Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.length === 0 ? (
                      <tr>
                        <td colSpan="7" style={{ textAlign: "center", color: "var(--text-muted)", padding: 24 }}>
                          No active threat alerts in system. Operating normally.
                        </td>
                      </tr>
                    ) : (
                      alerts.slice(0, 6).map((alert) => (
                        <tr key={alert.alert_id}>
                          <td className="mono">{new Date(alert.created_ts * 1000).toLocaleTimeString()}</td>
                          <td className="mono">{alert.src_ip || "198.51.100.45"}</td>
                          <td style={{ fontWeight: 600 }}>{alert.threat_category}</td>
                          <td className="mono" style={{ fontWeight: 700 }}>{alert.risk_score}/100</td>
                          <td>
                            <span className={`badge-pill ${getSeverityBadgeClass(alert.severity)}`}>
                              {alert.severity}
                            </span>
                          </td>
                          <td>
                            <span className="mono" style={{ fontSize: 11 }}>{alert.status}</span>
                          </td>
                          <td style={{ display: "flex", gap: 6 }}>
                            <button className="btn btn-ghost" style={{ padding: "4px 8px", fontSize: 11 }} onClick={() => setSelectedAlert(alert)}>
                              Inspect
                            </button>
                            <button className="btn btn-ghost" style={{ padding: "4px 8px", fontSize: 11 }} onClick={() => handleAcknowledge(alert.alert_id)}>
                              Ack
                            </button>
                            <button className="btn btn-danger" style={{ padding: "4px 8px", fontSize: 11 }} onClick={() => handleBlockIPAction(alert.src_ip)}>
                              Block
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: NETWORK RELATIONSHIP VIEW (Force-Directed Graph) */}
          {activeTab === "graph" && (
            <div style={{ height: 600, width: "100%" }}>
              {window.NetworkRelationshipGraph ? (
                <window.NetworkRelationshipGraph
                  nodesData={networkGraphNodes.length > 1 ? networkGraphNodes : undefined}
                  initialTheme={theme}
                  height={600}
                />
              ) : (
                <div className="cyber-card" style={{ padding: 32, textAlign: "center" }}>
                  Loading Network Relationship Component...
                </div>
              )}
            </div>
          )}

          {/* TAB 3: WEEKLY THREAT REPORT */}
          {activeTab === "weekly" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              {/* Controls Bar */}
              <div className="cyber-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700 }}>Weekly Security Executive Report</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Period: {weeklyReport?.start_date || "..."} to {weeklyReport?.end_date || "..."}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-muted)" }}>Select Timeframe:</span>
                  <select
                    className="cyber-input"
                    value={selectedWeek}
                    onChange={(e) => setSelectedWeek(e.target.value)}
                  >
                    <option value="current">This Week (Current)</option>
                    <option value="last_week">Last Week</option>
                    <option value="2_weeks_ago">2 Weeks Ago</option>
                  </select>
                </div>
              </div>

              {/* Weekly KPI Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Total Weekly Threats</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0", color: "var(--color-primary)" }}>
                    {weeklyReport?.total_threats || 0}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Logged in period</div>
                </div>

                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Average Daily Threats</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0" }}>
                    {weeklyReport?.avg_daily_threats || 0}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Per 24h window</div>
                </div>

                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Top Targeted Port</div>
                  <div className="mono" style={{ fontSize: 32, fontWeight: 700, margin: "8px 0", color: "var(--severity-high)" }}>
                    Port {weeklyReport?.top_attacked_ports?.[0]?.port || "80"}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {weeklyReport?.top_attacked_ports?.[0]?.count || 0} hits
                  </div>
                </div>

                <div className="cyber-card">
                  <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Top Attacking IP</div>
                  <div className="mono" style={{ fontSize: 24, fontWeight: 700, margin: "12px 0", color: "var(--severity-critical)" }}>
                    {weeklyReport?.top_attacking_ips?.[0]?.ip || "198.51.100.45"}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {weeklyReport?.top_attacking_ips?.[0]?.count || 0} attacks
                  </div>
                </div>
              </div>

              {/* Weekly Report Charts Component */}
              <WeeklyReportCharts weeklyData={weeklyReport} theme={theme} />

              {/* Daily Breakdown Table */}
              <div className="cyber-card">
                <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Daily Breakdown Matrix</div>
                <table className="cyber-table">
                  <thead>
                    <tr>
                      <th>Day</th>
                      <th>Date</th>
                      <th>Total Threats</th>
                      <th>Critical</th>
                      <th>High</th>
                      <th>Medium</th>
                      <th>Low</th>
                    </tr>
                  </thead>
                  <tbody>
                    {weeklyReport?.daily_breakdown?.map((d) => (
                      <tr key={d.day}>
                        <td style={{ fontWeight: 700 }}>{d.day}</td>
                        <td className="mono">{d.date_str}</td>
                        <td className="mono" style={{ fontWeight: 700, color: "var(--color-primary)" }}>{d.total_threats}</td>
                        <td className="mono" style={{ color: "var(--severity-critical)" }}>{d.critical}</td>
                        <td className="mono" style={{ color: "var(--severity-high)" }}>{d.high}</td>
                        <td className="mono" style={{ color: "var(--severity-medium)" }}>{d.medium}</td>
                        <td className="mono" style={{ color: "var(--severity-low)" }}>{d.low}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: THREAT LOGS TABLE */}
          {activeTab === "logs" && (
            <div className="cyber-card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Filter Bar */}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                <input
                  type="text"
                  placeholder="Filter by IP address..."
                  className="cyber-input mono"
                  style={{ width: 220 }}
                  value={searchIP}
                  onChange={(e) => setSearchIP(e.target.value)}
                />
                <select className="cyber-input" value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
                <select className="cyber-input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                  <option value="ALL">All Statuses</option>
                  <option value="new">New</option>
                  <option value="acknowledged">Acknowledged</option>
                  <option value="false_positive">False Positive</option>
                </select>
              </div>

              {/* Full Table */}
              <table className="cyber-table">
                <thead>
                  <tr>
                    <th>Alert ID</th>
                    <th>Timestamp</th>
                    <th>Source IP</th>
                    <th>Destination IP</th>
                    <th>Threat Category</th>
                    <th>Risk Score</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.length === 0 ? (
                    <tr>
                      <td colSpan="9" style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                        No log records matching filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredAlerts.map((alert) => (
                      <tr key={alert.alert_id}>
                        <td className="mono" style={{ color: "var(--color-primary)" }}>{alert.alert_id}</td>
                        <td className="mono">{new Date(alert.created_ts * 1000).toLocaleString()}</td>
                        <td className="mono">{alert.src_ip || "198.51.100.45"}</td>
                        <td className="mono">{alert.dst_ip || "10.0.0.5"}</td>
                        <td style={{ fontWeight: 600 }}>{alert.threat_category}</td>
                        <td className="mono" style={{ fontWeight: 700 }}>{alert.risk_score}</td>
                        <td>
                          <span className={`badge-pill ${getSeverityBadgeClass(alert.severity)}`}>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="mono" style={{ fontSize: 11 }}>{alert.status}</td>
                        <td style={{ display: "flex", gap: 6 }}>
                          <button className="btn btn-ghost" style={{ padding: "4px 8px", fontSize: 11 }} onClick={() => setSelectedAlert(alert)}>
                            Inspect
                          </button>
                          <button className="btn btn-ghost" style={{ padding: "4px 8px", fontSize: 11 }} onClick={() => handleAcknowledge(alert.alert_id)}>
                            Ack
                          </button>
                          <button className="btn btn-danger" style={{ padding: "4px 8px", fontSize: 11 }} onClick={() => handleBlockIPAction(alert.src_ip)}>
                            Block
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 5: THREAT INTEL INSPECTOR */}
          {activeTab === "intel" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div className="cyber-card" style={{ display: "flex", gap: 12 }}>
                <input
                  type="text"
                  placeholder="Enter IP address to lookup (e.g. 198.51.100.45)..."
                  className="cyber-input mono"
                  style={{ flex: 1 }}
                  value={intelSearchIP}
                  onChange={(e) => setIntelSearchIP(e.target.value)}
                />
                <button className="btn btn-primary" onClick={() => handleIntelLookup(intelSearchIP)}>
                  Search Reputation
                </button>
              </div>

              {intelResult && (
                <div className="cyber-card" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                  <div>
                    <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>IP Address Metadata</div>
                    <div className="mono" style={{ fontSize: 24, fontWeight: 700, margin: "8px 0", color: "var(--color-primary)" }}>{intelResult.ip}</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12 }}>
                      <div>Status: <span style={{ color: intelResult.listed ? "var(--severity-critical)" : "var(--status-success)", fontWeight: 700 }}>{intelResult.listed ? "BLACKLISTED / REPUTATION MATCH" : "CLEAN"}</span></div>
                      <div>Threat Score: <span className="mono" style={{ fontWeight: 700 }}>{intelResult.threat_score}/100</span></div>
                      <div>Category: <span className="mono">{intelResult.category}</span></div>
                      <div>Source Feed: <span className="mono">{intelResult.source_feed}</span></div>
                    </div>
                  </div>

                  <div>
                    <div style={{ color: "var(--text-muted)", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>GeoIP Location Info</div>
                    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                      <div>Country: <span className="mono" style={{ fontWeight: 600 }}>{intelResult.country_code || "Germany"}</span></div>
                      <div>City / Region: <span className="mono">Frankfurt, Hesse</span></div>
                      <div>Coordinates: <span className="mono">50.1109° N, 8.6821° E (Approximate)</span></div>
                    </div>
                    <button className="btn btn-danger" style={{ marginTop: 20 }} onClick={() => handleBlockIPAction(intelResult.ip)}>
                      Execute Block Action
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 6: PCAP UPLOAD */}
          {activeTab === "pcap" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div className="cyber-card" style={{ textAlign: "center", padding: 48, borderStyle: "dashed" }}>
                <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Drag & Drop .PCAP File Here</div>
                <div style={{ color: "var(--text-muted)", marginBottom: 20 }}>Read-only offline capture analysis and flow feature scoring</div>
                <input type="file" accept=".pcap,.pcapng,.cap" onChange={handlePcapUpload} style={{ display: "none" }} id="pcapInput" />
                <label htmlFor="pcapInput" className="btn btn-primary" style={{ cursor: "pointer" }}>
                  {pcapUploading ? "Processing PCAP..." : "Select PCAP File"}
                </label>
              </div>

              {pcapResult && (
                <div className="cyber-card">
                  <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Analysis Results for {pcapResult.filename}</div>
                  <div style={{ display: "flex", gap: 24, marginBottom: 16 }}>
                    <div>Packets Parsed: <span className="mono" style={{ fontWeight: 700 }}>{pcapResult.packets_parsed}</span></div>
                    <div>Alerts Generated: <span className="mono" style={{ fontWeight: 700, color: "var(--severity-high)" }}>{pcapResult.alerts_generated_count}</span></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Alert Inspector Modal */}
      {selectedAlert && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999 }}>
          <div className="cyber-card" style={{ width: 600, maxHeight: "80vh", overflowY: "auto", background: "var(--bg-surface-elevated)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div style={{ fontSize: 18, fontWeight: 700 }}>Alert Evidence Inspector ({selectedAlert.alert_id})</div>
              <button className="btn btn-ghost" onClick={() => setSelectedAlert(null)}>✕</button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>Threat Category: <span style={{ fontWeight: 700, color: "var(--color-primary)" }}>{selectedAlert.threat_category}</span></div>
                <span className={`badge-pill ${getSeverityBadgeClass(selectedAlert.severity)}`}>{selectedAlert.severity}</span>
              </div>

              <div style={{ background: "var(--bg-surface-sunken)", padding: 12, borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Plain-Language XAI Explanation (PRD §6.5)</div>
                <div style={{ marginTop: 4 }}>{selectedAlert.explanation}</div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }} className="mono">
                <div>Source IP: {selectedAlert.src_ip || "198.51.100.45"}</div>
                <div>Risk Score: {selectedAlert.risk_score}/100</div>
                <div>Confidence: {((selectedAlert.confidence || 0.85) * 100).toFixed(0)}%</div>
                <div>Status: {selectedAlert.status}</div>
              </div>

              <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
                <button className="btn btn-ghost" onClick={() => handleAcknowledge(selectedAlert.alert_id)}>Mark Acknowledged</button>
                <button className="btn btn-ghost" onClick={() => handleFalsePositive(selectedAlert.alert_id)}>Mark False Positive</button>
                <button className="btn btn-danger" onClick={() => handleBlockIPAction(selectedAlert.src_ip)}>Block IP</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
