import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";



function MetricDetail() {

  const { name } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function fetchMetrics() {

    try {

      const metrics = await getMetrics();
      setData(metrics);
      setLoading(false);

    } catch (err) {

      console.error(err);
      setError("Failed to load metrics");
      setLoading(false);

    }

  }

  useEffect(() => {

    fetchMetrics();

    const interval = setInterval(fetchMetrics, 180000);

    return () => clearInterval(interval);

  }, []);

  const colors = {
    cpu: "#3b82f6",
    memory: "#22c55e",
    network: "#ef4444"
  };

  if (loading) {
    return <p style={{ padding: "30px" }}>Loading metrics...</p>;
  }

  if (error) {
    return <p style={{ padding: "30px" }}>{error}</p>;
  }

  return (

    <div className="dashboard-container">

      <button
        onClick={() => navigate("/")}
        style={{
          marginBottom: "20px",
          padding: "10px 15px",
          cursor: "pointer"
        }}
      >
        ← Back to Dashboard
      </button>

      <h2 style={{ marginBottom: "20px" }}>
        {name.toUpperCase()} Metric Details
      </h2>

      <div className="graph-container">

        <ResponsiveContainer width="100%" height={400}>

          <LineChart data={data}>

            <CartesianGrid stroke="#374151" />

            <XAxis dataKey="time" stroke="#9ca3af" />

            <YAxis stroke="#9ca3af" />

            <Tooltip />

            <Line
              type="monotone"
              dataKey={name}
              stroke={colors[name]}
              strokeWidth={3}
            />

          </LineChart>

        </ResponsiveContainer>

      </div>

    </div>

  );

}

export default MetricDetail;