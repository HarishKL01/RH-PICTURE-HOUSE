const MODES = [
  { id: "genre", label: "By Genre", hint: "Browse a category" },
  { id: "ratings", label: "Top Rated", hint: "Highest rated overall" },
  { id: "cold", label: "Search By Favourite Movie", hint: "Tell us what you like" },
];

export default function ModeTabs({ mode, onChange }) {
  return (
    <div
      role="tablist"
      aria-label="Recommendation mode"
      className="flex flex-col sm:flex-row gap-2 sm:gap-0 sm:divide-x divide-white/10 bg-surface rounded-xl overflow-hidden border border-white/5"
    >
      {MODES.map((m) => {
        const active = mode === m.id;
        return (
          <button
            key={m.id}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(m.id)}
            className={`flex-1 text-left px-5 py-3 transition-colors cursor-pointer ${
              active ? "bg-surface-raised" : "hover:bg-white/5"
            }`}
          >
            <span
              className={`block font-display text-lg tracking-wide ${
                active ? "text-amber" : "text-paper/80"
              }`}
            >
              {m.label}
            </span>
            <span className="block text-xs text-muted">{m.hint}</span>
          </button>
        );
      })}
    </div>
  );
}
