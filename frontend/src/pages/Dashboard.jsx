import Navbar from "../components/Navbar";
import MetricCards from "../components/MetricCards";
import MetricsGraph from "../components/MetricsGraph";
import SystemInfo from "../components/SystemInfo";
import NodeStatus from "../components/NodeStatus";
import TimeSelector from "../components/TimeSelector";

function Dashboard() {

  return (

    <>
      {/* Top Navigation */}
      <Navbar />

      <div className="dashboard-container">

        {/* Metric Cards */}
        <MetricCards />

        {/* Time Range Selector */}
        <TimeSelector />

        {/* Metrics Graph */}
        <div className="graph-container">
          <MetricsGraph />
        </div>

        {/* System Information */}
        <div className="system-info">
          <SystemInfo />
        </div>

        {/* Cluster Node Status */}
        <NodeStatus />

      </div>

    </>

  );

}

export default Dashboard;