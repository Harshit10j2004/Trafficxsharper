import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import MetricDetail from "./pages/MetricDetail";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/metric/:name" element={<MetricDetail />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;