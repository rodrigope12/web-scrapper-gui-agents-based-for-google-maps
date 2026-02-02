import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet'
import { EditControl } from "react-leaflet-draw"
import 'leaflet/dist/leaflet.css'
import 'leaflet-draw/dist/leaflet.draw.css'
import L from 'leaflet'

// Fix for default marker icons in Leaflet with Webpack/Vite
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapProps {
    onPolygonDrawn: (coords: number[][]) => void;
}

const MapComponent = ({ onPolygonDrawn }: MapProps) => {
    const startPosition: [number, number] = [40.7128, -74.0060] // NYC

    const _onCreated = (e: any) => {
        const { layerType, layer } = e;
        if (layerType === 'polygon') {
            const latlngs = layer.getLatLngs()[0]; // Array of LatLng objects
            // Convert to simple array [[lat, lon], ...]
            const coords = latlngs.map((ll: any) => [ll.lat, ll.lng]);
            onPolygonDrawn(coords);
            console.log("Polygon drawn:", coords);
        }
    }

    return (
        // @ts-ignore
        <MapContainer center={startPosition} zoom={13} style={{ height: "100%", width: "100%" }}>
            {/* @ts-ignore */}
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {/* @ts-ignore */}
            <FeatureGroup>
                {/* @ts-ignore */}
                <EditControl
                    position='topright'
                    onCreated={_onCreated}
                    draw={{
                        rectangle: false,
                        circle: false,
                        circlemarker: false,
                        marker: false,
                        polyline: false,
                        polygon: {
                            allowIntersection: false,
                            showArea: true,
                        }
                    }}
                />
            </FeatureGroup>
        </MapContainer>
    )
}

export default MapComponent
