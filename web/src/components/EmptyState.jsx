import './States.css';

export function EmptyState({ title = '표시할 데이터가 없습니다.', description, action }) {
  return (
    <div className="state state--empty">
      <strong className="state__title">{title}</strong>
      {description ? <p className="state__desc">{description}</p> : null}
      {action ? <div className="state__action">{action}</div> : null}
    </div>
  );
}
