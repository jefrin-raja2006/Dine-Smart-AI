import { useCallback, useEffect, useState } from "react";
import { addFavorite, getFavorites, removeFavorite } from "../services/api";

// Keeps the set of favourite restaurant ids in sync with the server.
export default function useFavorites() {
  const [favoriteIds, setFavoriteIds] = useState([]);
  const [busy, setBusy] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    getFavorites()
      .then((result) => {
        if (!cancelled) {
          setFavoriteIds((result.favorites || []).map((f) => Number(f.restaurant_id)));
        }
      })
      .catch(() => {
        /* not critical: hearts just start empty */
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const toggle = useCallback(
    async (restaurant) => {
      const id = Number(restaurant.id);
      if (!id) return;

      const isFavorite = favoriteIds.includes(id);
      setBusy((current) => ({ ...current, [id]: true }));
      setError("");

      try {
        if (isFavorite) {
          await removeFavorite(id);
          setFavoriteIds((current) => current.filter((x) => x !== id));
        } else {
          await addFavorite(id);
          setFavoriteIds((current) => [...current, id]);
        }
      } catch (err) {
        setError(err.message || "Unable to update favorite.");
      } finally {
        setBusy((current) => ({ ...current, [id]: false }));
      }
    },
    [favoriteIds]
  );

  return {
    favoriteIds,
    isFavorite: (id) => favoriteIds.includes(Number(id)),
    isBusy: (id) => Boolean(busy[Number(id)]),
    toggle,
    error,
  };
}
