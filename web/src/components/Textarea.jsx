import './Field.css';

export function Textarea({ label, name, value, onChange, error, help, placeholder, rows = 5, required }) {
  const id = `f-${name}`;
  return (
    <div className="field">
      {label ? (
        <label htmlFor={id}>
          {label}
          {required ? <span aria-hidden="true" className="req">*</span> : null}
        </label>
      ) : null}
      <textarea
        id={id}
        name={name}
        value={value ?? ''}
        onChange={onChange}
        placeholder={placeholder}
        rows={rows}
        aria-invalid={Boolean(error)}
        className={['input', 'input--textarea', error && 'input--error'].filter(Boolean).join(' ')}
      />
      {help && !error ? <span className="help">{help}</span> : null}
      {error ? <span className="error">{error}</span> : null}
    </div>
  );
}
