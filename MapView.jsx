
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";

export default function MapView({ vehicles }) {
  return (
    <MapContainer center={[8.4844, -13.2344]} zoom={13} style={{ height: 400 }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {vehicles.map(v => (
        <Marker key={v.id} position={[v.latitude, v.longitude]}>
          <Popup>{v.vehicle_code} | {v.battery_percent}%</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
