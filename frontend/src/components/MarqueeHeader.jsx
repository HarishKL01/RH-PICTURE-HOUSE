function BulbStrip() {
  return (
    <div className="bulb-strip" aria-hidden="true">
      {Array.from({ length: 24 }).map((_, i) => (
        <span key={i} />
      ))}
    </div>
  );
}

export default function MarqueeHeader() {
  return (
    <header className="pt-8 pb-6">
      <BulbStrip />
      <div className="py-4">
        <p className="font-mono text-4xl text-teal tracking-[0.3em] uppercase mb-1 tracking-wide ">
           RH Picture House
        </p>
        <h1 className="font-display text-xl sm:text-2xl text-amber marquee-flicker tracking-wide">
          NOW RECOMMENDING
        </h1>
        <p className="text-muted text-sm mt-2 max-w-lg">
          Alone and don't know what to do? 'OR' Have Company at home and don't know what to do? Watch a Movie.
        </p>
      </div>
      <BulbStrip />
    </header>
  );
}
