import './States.css';

export function ErrorState({
  title = '요청에 실패했습니다.',
  description = '잠시 후 다시 시도해 주세요.',
  onRetry,
}) {
  return (
    <div className="state state--error" role="alert">
      <strong className="state__title">{title}</strong>
      <p className="state__desc">{description}</p>
      {onRetry ? (
        <button type="button" className="state__retry" onClick={onRetry}>
          다시 시도
        </button>
      ) : null}
    </div>
  );
}
