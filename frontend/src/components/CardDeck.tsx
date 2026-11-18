import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

export interface DeckTab {
  id: string;
  label: string;
  count: number;
}

interface CardDeckProps {
  title: string;
  subtitle?: string;
  cards: ReactNode[];
  tabs?: DeckTab[];
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  emptyNote?: string;
  icon?: string;
}

/**
 * One card at a time, with prev/next controls, dot progress, keyboard
 * arrows and touch swipe. Replaces endless vertical card lists — the
 * reader swipes through insight instead of scrolling past it.
 */
export default function CardDeck({
  title,
  subtitle,
  cards,
  tabs,
  activeTab,
  onTabChange,
  emptyNote = "Nothing in this bucket.",
  icon,
}: CardDeckProps) {
  const [index, setIndex] = useState(0);
  const touchX = useRef<number | null>(null);
  const deckRef = useRef<HTMLDivElement>(null);

  const count = cards.length;
  const clamped = count === 0 ? 0 : Math.min(index, count - 1);

  useEffect(() => {
    setIndex(0);
  }, [activeTab, count]);

  const go = useCallback(
    (delta: number) => {
      setIndex((i) => {
        if (count === 0) return 0;
        return (i + delta + count) % count; // wraps around — feels like a deck
      });
    },
    [count]
  );

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "ArrowLeft") { event.preventDefault(); go(-1); }
      if (event.key === "ArrowRight") { event.preventDefault(); go(1); }
    },
    [go]
  );

  return (
    <section className="deck" ref={deckRef}>
      <div className="deck-head">
        <div className="deck-title-group">
          {icon && <span className="deck-icon" aria-hidden="true">{icon}</span>}
          <div>
            <h3 className="deck-title">{title}</h3>
            {subtitle && <p className="deck-subtitle">{subtitle}</p>}
          </div>
        </div>
        {count > 0 && (
          <div className="deck-pager" aria-label="Card navigation">
            <button type="button" className="deck-arrow" onClick={() => go(-1)} aria-label="Previous card">←</button>
            <span className="deck-counter"><b>{clamped + 1}</b> / {count}</span>
            <button type="button" className="deck-arrow" onClick={() => go(1)} aria-label="Next card">→</button>
          </div>
        )}
      </div>

      {tabs && tabs.length > 1 && (
        <div className="deck-tabs" role="tablist" aria-label={`${title} filters`}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`deck-tab${activeTab === tab.id ? " active" : ""}`}
              onClick={() => onTabChange?.(tab.id)}
            >
              {tab.label} <span className="deck-tab-count">{tab.count}</span>
            </button>
          ))}
        </div>
      )}

      {count === 0 ? (
        <p className="deck-empty">{emptyNote}</p>
      ) : (
        <>
          <div
            className="deck-stage"
            tabIndex={0}
            role="region"
            aria-label={`${title}: card ${clamped + 1} of ${count}`}
            onKeyDown={onKeyDown}
            onTouchStart={(e) => { touchX.current = e.touches[0].clientX; }}
            onTouchEnd={(e) => {
              if (touchX.current === null) return;
              const delta = e.changedTouches[0].clientX - touchX.current;
              if (Math.abs(delta) > 40) go(delta < 0 ? 1 : -1);
              touchX.current = null;
            }}
          >
            <div className="deck-card" key={clamped}>
              {cards[clamped]}
            </div>
          </div>

          <div className="deck-dots" aria-hidden="true">
            {cards.map((_, i) => (
              <button
                key={i}
                type="button"
                className={`deck-dot${i === clamped ? " active" : ""}`}
                onClick={() => setIndex(i)}
                aria-label={`Go to card ${i + 1}`}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
