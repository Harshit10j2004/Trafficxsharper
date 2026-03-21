import { useState, useEffect } from "react";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

function MetricsGraph() {

  const [data, setData] = useState([]);

  useEffect(() => {

    // TODO: Backend se data aayega (API / WebSocket)
    // Example future:
    // setData(receivedData);

    setData([]); // abhi empty (no backend)

  }, []);

  return (

    <div style={{
      width: "100%",
      height: 400
    }}>

      <ResponsiveContainer width="100%" height="100%">

        <LineChart data={data}>

          <CartesianGrid stroke="#374151" />

          <XAxis dataKey="time" stroke="#9ca3af" />

          <YAxis stroke="#9ca3af" />

          <Tooltip
            contentStyle={{
              background:"#1f2937",
              border:"none"
            }}
          />

          <Legend />

          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#3b82f6"
            strokeWidth={2}
          />

          <Line
            type="monotone"
            dataKey="memory"
            stroke="#22c55e"
            strokeWidth={2}
          />

          <Line
            type="monotone"
            dataKey="network"
            stroke="#ef4444"
            strokeWidth={2}
          />

        </LineChart>

      </ResponsiveContainer>

    </div>

  );
}

export default MetricsGraph;