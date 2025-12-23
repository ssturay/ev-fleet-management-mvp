
import { useEffect, useState } from "react";
import axios from "axios";
import MapView from "./MapView";

function App() {
  const [vehicles, setVehicles] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:4000/api/vehicles")
      .then(res => setVehicles(res.data));
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>EV Fleet Management MVP</h1>
      <MapView vehicles={vehicles} />
    </div>
  );
}

export default App;
