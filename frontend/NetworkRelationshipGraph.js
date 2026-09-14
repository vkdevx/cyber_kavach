// NetworkRelationshipGraph.js — Self-Contained Force-Directed Network Relationship Graph Component

const THEME_TOKENS = {
  dark: {
    bg: "#0A0E17",
    surface: "rgba(16, 24, 40, 0.85)",
    panelBg: "rgba(22, 32, 47, 0.95)",
    border: "rgba(255, 255, 255, 0.12)",
    borderStrong: "rgba(255, 255, 255, 0.22)",
    textPrimary: "#F1F5F9",
    textSecondary: "#CBD5E1",
    textMuted: "#94A3B8",
    textOnAccent: "#04141A",
    centerNodeFill: "#00D9E0",
    centerNodeStroke: "#00FFC2",
    edgeStroke: "rgba(0, 217, 224, 0.35)",
    edgeHover: "#00D9E0",
    risk: {
      safe: "#2ED47A",
      low: "#00C2A8",
      medium: "#F5A524",
      high: "#FF7A45",
      critical: "#FF3B5C"
    }
  },
  light: {
    bg: "#F8FAFC",
    surface: "rgba(255, 255, 255, 0.95)",
    panelBg: "rgba(255, 255, 255, 0.98)",
    border: "rgba(0, 0, 0, 0.12)",
    borderStrong: "rgba(0, 0, 0, 0.22)",
    textPrimary: "#0F172A",
    textSecondary: "#334155",
    textMuted: "#64748B",
    textOnAccent: "#FFFFFF",
    centerNodeFill: "#007A87",
    centerNodeStroke: "#005662",
    edgeStroke: "rgba(0, 122, 135, 0.35)",
    edgeHover: "#007A87",
    risk: {
      safe: "#16A34A",
      low: "#00796B",
      medium: "#B78103",
      high: "#E65100",
      critical: "#D32F2F"
    }
  }
};

const DEFAULT_MOCK_NODES = [
  { id: "center", ip: "10.0.0.5", label: "CYBERKAVACH DEFENCE SENSOR", isCenter: true, volume: 15000, risk: "safe", category: "Monitoring Interface", port: 80, protocol: "TCP" },
  { id: "n1", ip: "198.51.100.45", risk: "high", volume: 1420, port: 80, protocol: "TCP", category: "Port Scanning" },
  { id: "n2", ip: "203.0.113.99", risk: "critical", volume: 2850, port: 80, protocol: "TCP", category: "SYN Flood / DoS" },
  { id: "n3", ip: "192.168.1.105", risk: "safe", volume: 5120, port: 443, protocol: "TCP", category: "Benign HTTP Browse" },
  { id: "n4", ip: "198.51.100.88", risk: "medium", volume: 980, port: 22, protocol: "TCP", category: "SSH Brute-Force" },
  { id: "n5", ip: "45.33.32.156", risk: "low", volume: 450, port: 53, protocol: "UDP", category: "DNS Query" },
  { id: "n6", ip: "185.220.101.5", risk: "critical", volume: 3100, port: 8080, protocol: "TCP", category: "Malware / C2 Beacon" },
  { id: "n7", ip: "192.168.1.200", risk: "safe", volume: 2300, port: 443, protocol: "TCP", category: "Benign Stream" }
];

function NetworkRelationshipGraph({
  nodesData = DEFAULT_MOCK_NODES,
  initialTheme = "dark",
  width = 900,
  height = 550,
  onNodeClick = null
}) {
  const [themeMode, setThemeMode] = React.useState(initialTheme);
  const [selectedNode, setSelectedNode] = React.useState(null);
  const [nodes, setNodes] = React.useState([]);
  const [links, setLinks] = React.useState([]);
  const [zoomScale, setZoomScale] = React.useState(1);
  const [panOffset, setPanOffset] = React.useState({ x: 0, y: 0 });
  const [isDraggingPan, setIsDraggingPan] = React.useState(false);
  const [dragStart, setDragStart] = React.useState({ x: 0, y: 0 });

  const svgRef = React.useRef(null);
  const simulationRef = React.useRef(null);
  const theme = THEME_TOKENS[themeMode] || THEME_TOKENS.dark;

  // Serialize nodesData for stable dependency checking
  const nodesDataStr = React.useMemo(() => JSON.stringify(nodesData), [nodesData]);

  // Initialize and run d3 force-directed simulation
  React.useEffect(() => {
    const rawNodes = JSON.parse(nodesDataStr || "[]");
    if (!rawNodes.length) return;

    const centerNode = rawNodes.find(n => n.isCenter) || rawNodes[0];

    // Seed initial coordinates to prevent layout flicker or NaN values
    rawNodes.forEach((n, i) => {
      if (n.isCenter) {
        n.x = width / 2;
        n.y = height / 2;
      } else {
        const angle = (i / (rawNodes.length || 1)) * 2 * Math.PI;
        n.x = width / 2 + 130 * Math.cos(angle);
        n.y = height / 2 + 130 * Math.sin(angle);
      }
    });

    const generatedLinks = rawNodes
      .filter(n => !n.isCenter)
      .map(n => ({
        source: n.id,
        target: centerNode.id,
        volume: n.volume
      }));

    if (window.d3) {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }

      const simulation = window.d3.forceSimulation(rawNodes)
        .force("link", window.d3.forceLink(generatedLinks).id(d => d.id).distance(140))
        .force("charge", window.d3.forceManyBody().strength(-350))
        .force("center", window.d3.forceCenter(width / 2, height / 2))
        .force("collide", window.d3.forceCollide().radius(d => (d.isCenter ? 45 : 30)));

      simulationRef.current = simulation;

      simulation.on("tick", () => {
        setNodes([...rawNodes]);
        setLinks([...generatedLinks]);
      });

      // Run initial ticks immediately so graph appears instantly
      for (let i = 0; i < 30; ++i) simulation.tick();
      setNodes([...rawNodes]);
      setLinks([...generatedLinks]);
    } else {
      // Fallback radial layout if D3 is loading
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = 180;
      const sources = rawNodes.filter(n => !n.isCenter);

      sources.forEach((n, i) => {
        const angle = (i / (sources.length || 1)) * 2 * Math.PI;
        n.x = centerX + radius * Math.cos(angle);
        n.y = centerY + radius * Math.sin(angle);
      });
      centerNode.x = centerX;
      centerNode.y = centerY;

      setNodes(rawNodes);
      setLinks(generatedLinks);
    }

    return () => {
      if (simulationRef.current) simulationRef.current.stop();
    };
  }, [nodesDataStr, width, height]);

  // Zoom & Pan Handlers
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoomScale(prev => Math.max(0.4, Math.min(3.0, prev * zoomFactor)));
  };

  const handleMouseDown = (e) => {
    if (e.target.tagName === "svg" || e.target.tagName === "rect" && e.target.id === "bg-rect") {
      setIsDraggingPan(true);
      setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDraggingPan) {
      setPanOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDraggingPan(false);
  };

  const resetView = () => {
    setZoomScale(1);
    setPanOffset({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  const toggleTheme = () => {
    setThemeMode(prev => (prev === "dark" ? "light" : "dark"));
  };

  const getNodeColor = (node) => {
    if (node.isCenter) return theme.centerNodeFill;
    return theme.risk[node.risk] || theme.risk.safe;
  };

  const getEdgeWidth = (volume) => {
    if (!volume) return 1.5;
    return Math.max(1.5, Math.min(7.0, volume / 600));
  };

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        minHeight: height,
        backgroundColor: theme.bg,
        borderRadius: 10,
        border: `1px solid ${theme.border}`,
        position: "relative",
        overflow: "hidden",
        fontFamily: "'Inter', sans-serif",
        color: theme.textPrimary,
        userSelect: "none"
      }}
    >
      {/* Top Header & Control Toolbar */}
      <div
        style={{
          position: "absolute",
          top: 16,
          left: 16,
          right: 16,
          zIndex: 10,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, letterSpacing: "0.02em" }}>
            Network Relationship Graph (Interactive Topology)
          </div>
          <div style={{ fontSize: 12, color: theme.textMuted }}>
            Visualizing force-directed traffic flows connected to Central Monitoring Node
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button
            onClick={resetView}
            style={{
              backgroundColor: theme.surface,
              color: theme.textPrimary,
              border: `1px solid ${theme.borderStrong}`,
              borderRadius: 6,
              padding: "6px 12px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease"
            }}
          >
            Reset View
          </button>
          <button
            onClick={toggleTheme}
            style={{
              backgroundColor: theme.surface,
              color: theme.textPrimary,
              border: `1px solid ${theme.borderStrong}`,
              borderRadius: 20,
              padding: "6px 14px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6
            }}
          >
            {themeMode === "dark" ? "☀️ Light Theme" : "🌙 Dark Theme"}
          </button>
        </div>
      </div>

      {/* SVG Canvas for Graph Visualization */}
      <svg
        ref={svgRef}
        width="100%"
        height={height}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        style={{ cursor: isDraggingPan ? "grabbing" : "grab" }}
      >
        <rect id="bg-rect" width="100%" height="100%" fill={theme.bg} />

        <g transform={`translate(${panOffset.x}, ${panOffset.y}) scale(${zoomScale})`}>
          {/* Link Edges */}
          {links.map((link, idx) => {
            const sourceNode = typeof link.source === "object" ? link.source : nodes.find(n => n.id === link.source);
            const targetNode = typeof link.target === "object" ? link.target : nodes.find(n => n.id === link.target);

            if (!sourceNode || !targetNode || sourceNode.x == null || targetNode.x == null) return null;

            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={theme.edgeStroke}
                strokeWidth={getEdgeWidth(link.volume)}
                strokeLinecap="round"
              />
            );
          })}

          {/* Node Elements */}
          {nodes.map(node => {
            if (node.x == null || node.y == null) return null;
            const isSelected = selectedNode && selectedNode.id === node.id;
            const nodeColor = getNodeColor(node);

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => {
                  setSelectedNode(node);
                  if (onNodeClick) onNodeClick(node);
                }}
                style={{ cursor: "pointer" }}
              >
                {/* Central Monitoring Node (Rounded Square) */}
                {node.isCenter ? (
                  <g>
                    <rect
                      x={-28}
                      y={-28}
                      width={56}
                      height={56}
                      rx={10}
                      ry={10}
                      fill={nodeColor}
                      stroke={theme.centerNodeStroke}
                      strokeWidth={3}
                      style={{ filter: "drop-shadow(0 0 10px rgba(0,217,224,0.4))" }}
                    />
                    <text
                      y={42}
                      textAnchor="middle"
                      fill={theme.textPrimary}
                      fontSize={11}
                      fontWeight={700}
                      fontFamily="'JetBrains Mono', monospace"
                    >
                      {node.label || node.ip}
                    </text>
                  </g>
                ) : (
                  /* Source IP Nodes (Circle) */
                  <g>
                    <circle
                      r={isSelected ? 18 : 14}
                      fill={nodeColor}
                      stroke={isSelected ? theme.textPrimary : theme.surface}
                      strokeWidth={isSelected ? 3 : 2}
                      style={{ transition: "r 0.15s ease", filter: isSelected ? "drop-shadow(0 0 8px currentColor)" : "none" }}
                    />
                    <text
                      y={26}
                      textAnchor="middle"
                      fill={theme.textSecondary}
                      fontSize={10}
                      fontWeight={600}
                      fontFamily="'JetBrains Mono', monospace"
                    >
                      {node.ip}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* Risk Level Legend */}
      <div
        style={{
          position: "absolute",
          bottom: 16,
          left: 16,
          backgroundColor: theme.panelBg,
          backdropFilter: "blur(8px)",
          border: `1px solid ${theme.border}`,
          borderRadius: 8,
          padding: "10px 14px",
          display: "flex",
          gap: 14,
          alignItems: "center",
          fontSize: 11,
          fontWeight: 600
        }}
      >
        <div style={{ color: theme.textMuted, textTransform: "uppercase", fontSize: 10, fontWeight: 700 }}>
          Risk Levels:
        </div>
        {Object.entries(theme.risk).map(([key, color]) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: color }} />
            <span style={{ textTransform: "capitalize", color: theme.textPrimary }}>{key}</span>
          </div>
        ))}
      </div>

      {/* Selected Node Details Side Panel */}
      {selectedNode && (
        <div
          style={{
            position: "absolute",
            bottom: 16,
            right: 16,
            width: 280,
            backgroundColor: theme.panelBg,
            backdropFilter: "blur(12px)",
            border: `1px solid ${theme.border}`,
            borderRadius: 8,
            padding: 16,
            boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            display: "flex",
            flexDirection: "column",
            gap: 10,
            animation: "fadeIn 0.2s ease"
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", color: theme.textMuted }}>
              Node Details
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              style={{
                background: "transparent",
                border: "none",
                color: theme.textMuted,
                fontSize: 14,
                cursor: "pointer"
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 16, fontWeight: 700, color: theme.centerNodeFill }}>
            {selectedNode.ip}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: theme.textMuted }}>Risk Level:</span>
            <span
              style={{
                textTransform: "uppercase",
                fontWeight: 700,
                color: selectedNode.isCenter ? theme.centerNodeFill : theme.risk[selectedNode.risk]
              }}
            >
              {selectedNode.risk}
            </span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: theme.textMuted }}>Category:</span>
            <span style={{ fontWeight: 600, color: theme.textPrimary }}>{selectedNode.category || "N/A"}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, fontFamily: "'JetBrains Mono', monospace" }}>
            <span style={{ color: theme.textMuted }}>Port / Protocol:</span>
            <span>{selectedNode.port} / {selectedNode.protocol}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, fontFamily: "'JetBrains Mono', monospace" }}>
            <span style={{ color: theme.textMuted }}>Traffic Volume:</span>
            <span>{selectedNode.volume ? selectedNode.volume.toLocaleString() + " B" : "N/A"}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Make globally accessible in browser React context
if (typeof window !== "undefined") {
  window.NetworkRelationshipGraph = NetworkRelationshipGraph;
}
