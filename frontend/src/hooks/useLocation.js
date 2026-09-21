import { useCallback, useEffect, useState } from "react";

const CACHE_KEY = "lastLocation";

function readCached() {
  try {
    return JSON.parse(sessionStorage.getItem(CACHE_KEY) || "null");
  } catch {
    return null;
  }
}

// Browser GPS with a friendly error and a per-tab cache, so moving between
// pages does not trigger a new permission prompt / GPS fix every time.
export default function useLocation({ auto = true } = {}) {
  const [location, setLocation] = useState(readCached);
  const [loading, setLoading] = useState(auto && !readCached());
  const [error, setError] = useState("");

  const locate = useCallback(() => {
    setError("");
    setLoading(true);

    if (!navigator.geolocation) {
      setError("Your browser does not support location.");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const next = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        sessionStorage.setItem(CACHE_KEY, JSON.stringify(next));
        setLocation(next);
        setLoading(false);
      },
      (geoError) => {
        setError(
          geoError.code === 1
            ? "Location access was denied. Allow location in your browser to see restaurants near you."
            : "Unable to get your location. Please try again."
        );
        setLoading(false);
      },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 }
    );
  }, []);

  useEffect(() => {
    if (auto && !readCached()) {
      locate();
    }
  }, [auto, locate]);

  return { location, loading, error, locate };
}
