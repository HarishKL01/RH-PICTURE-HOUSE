import { useEffect, useState } from "react";
import { listKnownUsers, getUserRatings } from "../api";

export default function UserPicker({ userId, onSelect }) {
  const [users, setUsers] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listKnownUsers(40)
      .then((data) => setUsers(data.users))
      .catch((e) => setError(e.message))
      .finally(() => setLoadingUsers(false));
  }, []);

  useEffect(() => {
    if (userId == null) {
      setRatings([]);
      return;
    }
    getUserRatings(userId, 6)
      .then((data) => setRatings(data.ratings))
      .catch(() => setRatings([]));
  }, [userId]);

  return (
    <div className="bg-surface rounded-xl p-5 border border-white/5">
      <label
        htmlFor="user-select"
        className="block text-xs uppercase tracking-wider text-muted mb-2"
      >
        Choose a patron ID
      </label>
      {error && <p className="text-sm text-danger mb-2">Couldn't load patrons: {error}</p>}
      <select
        id="user-select"
        value={userId ?? ""}
        disabled={loadingUsers}
        onChange={(e) => onSelect(e.target.value ? Number(e.target.value) : null)}
        className="w-full bg-surface-raised border border-white/10 rounded-lg px-3 py-2.5 text-paper font-mono text-sm focus:border-amber outline-none"
      >
        <option value="">
          {loadingUsers ? "Loading patrons…" : "— Select a patron —"}
        </option>
        {users.map((u) => (
          <option key={u.user_id} value={u.user_id}>
            Patron #{u.user_id} · {u.num_ratings} ratings on file
          </option>
        ))}
      </select>

      {ratings.length > 0 && (
        <div className="mt-4">
          <p className="text-xs uppercase tracking-wider text-muted mb-2">
            Recently loved by this patron
          </p>
          <ul className="space-y-1">
            {ratings.map((r) => (
              <li
                key={r.movie_id}
                className="text-sm text-paper/80 flex justify-between gap-2"
              >
                <span className="truncate">{r.title}</span>
                <span className="font-mono text-teal shrink-0">{r.rating}★</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
