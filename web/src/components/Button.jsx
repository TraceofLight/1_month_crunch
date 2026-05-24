import './Button.css';

export function Button({
  type = 'button',
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  children,
  ...rest
}) {
  const cls = ['btn', `btn--${variant}`, `btn--${size}`, loading && 'btn--loading']
    .filter(Boolean)
    .join(' ');
  return (
    <button
      type={type}
      className={cls}
      disabled={disabled || loading}
      onClick={onClick}
      {...rest}
    >
      {loading ? <span className="btn__spinner" aria-hidden="true" /> : null}
      <span className="btn__label">{children}</span>
    </button>
  );
}
