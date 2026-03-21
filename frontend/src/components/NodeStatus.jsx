import { useState, useEffect } from "react";

function NodeStatus() {

  const [nodes, setNodes] = useState([]);

  function generateNodeStatus() {

    const nodeList = [];

    for (let i = 1; i <= 5; i++) {

      const usage = Math.floor(Math.random() * 100);

      let status = "Healthy";
      let color = "#16a34a";

      if (usage > 80) {
        status = "Critical";
        color = "#b91c1c";
      } else if (usage > 60) {
        status = "Warning";
        color = "#ca8a04";
      }

      nodeList.push({
        name: "Node " + i,
        usage: usage,
        status: status,
        color: color
      });

    }

    setNodes(nodeList);

  }

  useEffect(() => {

    generateNodeStatus();

    const interval = setInterval(generateNodeStatus, 180000);

    return () => clearInterval(interval);

  }, []);

  return (

    <div style={{
      background:"#1f2937",
      padding:"20px",
      borderRadius:"8px",
      marginTop:"20px"
    }}>

      <h3>Cluster Node Status</h3>

      {nodes.map((node, index) => (

        <div key={index} style={{
          display:"flex",
          justifyContent:"space-between",
          marginTop:"10px",
          padding:"10px",
          background:"#111827",
          borderRadius:"6px"
        }}>

          <span>{node.name}</span>

          <span style={{color:node.color}}>
            {node.status} ({node.usage}%)
          </span>

        </div>

      ))}

    </div>

  );

}

export default NodeStatus;