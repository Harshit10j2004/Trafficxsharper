import { useState, useEffect } from "react";


function SystemInfo() {

  const [nodes, setNodes] = useState(0);
  const [lastScale, setLastScale] = useState("");

  async function fetchSystemInfo() {

    try {

      const info = await getSystemInfo();

      setNodes(info.nodes);
      setLastScale(info.lastScaleTime);

    } catch (error) {

      console.error("Failed to fetch system info");

    }

  }

  useEffect(() => {

    fetchSystemInfo();

    const interval = setInterval(fetchSystemInfo, 180000);

    return () => clearInterval(interval);

  }, []);

  return (

    <div style={{
      background:"#1f2937",
      padding:"20px",
      borderRadius:"8px",
      marginTop:"20px",
      color:"#ffffff"
    }}>

      <h3 style={{marginBottom:"10px"}}>System Information</h3>

      <p>
        <strong>Last Scale Up Time:</strong> {lastScale}
      </p>

      <p>
        <strong>Total Nodes:</strong> {nodes}
      </p>

    </div>

  );

}

export default SystemInfo;