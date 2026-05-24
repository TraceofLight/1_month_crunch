import './Rating.css';

export function Rating({ value = 0, onChange, readOnly = false, max = 5 }) {
  return (
    <div className="rating" role={readOnly ? 'img' : 'radiogroup'} aria-label={`별점 ${value} / ${max}`}>
      {Array.from({ length: max }).map((_, i) => {
        const score = i + 1;
        const active = score <= value;
        if (readOnly) {
          return (
            <span key={score} className={`rating__star ${active ? 'is-active' : ''}`} aria-hidden="true">
              ★
            </span>
          );
        }
        return (
          <button
            key={score}
            type="button"
            className={`rating__star rating__btn ${active ? 'is-active' : ''}`}
            onClick={() => onChange?.(score)}
            aria-label={`${score}점`}
            aria-pressed={active}
          >
            ★
          </button>
        );
      })}
    </div>
  );
}
