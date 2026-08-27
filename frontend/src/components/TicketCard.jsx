const STRATEGY_LABELS = {
  collaborative_filtering: { label: "Patron Match", color: "var(--color-teal)" },
  content_based: { label: "Same Reel", color: "var(--color-amber)" },
  popularity: { label: "Box Office", color: "var(--color-muted)" },
  genre_popularity: { label: "Genre Pick", color: "var(--color-teal)" },
};

export default function TicketCard({ rec, rank }) {
  const strategy = STRATEGY_LABELS[rec.strategy] || {
    label: rec.strategy,
    color: "var(--color-muted)",
  };

  return (
    <div className="ticket px-5 pt-6 pb-5 mx-1 shadow-lg shadow-black/30">
      <span className="ticket-notch-top ticket-notch-top" aria-hidden="true" />

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-mono text-xs text-muted tracking-wide">
            SEAT {String(rank).padStart(2, "0")}
          </p>
          <h3 className="font-display text-2xl leading-none mt-1 text-paper truncate">
            {rec.title}
          </h3>
          <p className="text-xs text-muted mt-1">
            {rec.year ?? "Year unknown"} &middot;{" "}
            {rec.genres?.length ? rec.genres.join(", ") : "Unclassified"}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="font-mono text-lg text-amber leading-none">
            {rec.score?.toFixed(2)}
          </p>
          <p className="text-[10px] text-muted uppercase tracking-wider">score</p>
        </div>
      </div>

      <div className="tear-line my-4" />

      <div className="flex items-start gap-2">
        <span
          className="mt-0.5 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide shrink-0"
          style={{
            color: strategy.color,
            border: `1px solid ${strategy.color}`,
          }}
        >
          {strategy.label}
        </span>
        <p className="text-sm text-paper/85 leading-snug">{rec.reason}</p>
      </div>

      <span className="ticket-notch-bottom" aria-hidden="true" />
    </div>
  );
}
