import './States.css';

export function Loading({ label = '불러오는 중…' }) {
  return (
    <div className="state state--loading" role="status" aria-live="polite">
      <span className="state__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
