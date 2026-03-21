import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

function MetricCards() {

  const navigate = useNavigate();

  const [cpu, setCpu] = useState(0);
  const [memory, setMemory] = useState(0);
  const [network, setNetwork] = useState(0);

  // determine alert color
  function getStatusColor(value) {

    if (value > 80) return "#b91c1c";   // red (critical)

    if (value > 60) return "#ca8a04";   // yellow (warning)

    return "#166534";                   // green (healthy)

  }

  async function fetchMetrics() {

    try {

      const metrics = await getMetrics();

      const latest = metrics[metrics.length - 1];

      setCpu(latest.cpu);
      setMemory(latest.memory);
      setNetwork(latest.network);

    } catch (error) {

      console.error("Failed to fetch metrics", error);

    }

  }

  useEffect(() => {

    fetchMetrics();

    const interval = setInterval(fetchMetrics, 180000); // refresh every 3 minutes

    return () => clearInterval(interval);

  }, []);

  return (

    <div className="cards-container">

      {/* CPU CARD */}
      <div
        onClick={() => navigate("/metric/cpu")}
        className="card"
        style={{ background: getStatusColor(cpu) }}
      >
        <h3>CPU Usage</h3>

        <p style={{fontSize:"24px", fontWeight:"bold"}}>{cpu}%</p>

        {cpu > 80 && <span>⚠ High Usage</span>}
      </div>


      {/* MEMORY CARD */}
      <div
        onClick={() => navigate("/metric/memory")}
        className="card"
        style={{ background: getStatusColor(memory) }}
      >
        <h3>Memory Usage</h3>

        <p style={{fontSize:"24px", fontWeight:"bold"}}>{cpu}%</p>

        {memory > 80 && <span>⚠ High Usage</span>}
      </div>


      {/* NETWORK CARD */}
      <div
        onClick={() => navigate("/metric/network")}
        className="card"
        style={{ background: getStatusColor(network) }}
      >
        <h3>Network Usage</h3>

        <p style={{fontSize:"24px", fontWeight:"bold"}}>{cpu}%</p>

        {network > 80 && <span>⚠ High Usage</span>}
      </div>

    </div>

  );
}

export default MetricCards;