import './Field.css';

export function Input({ label, name, value, onChange, error, help, type = 'text', placeholder, required }) {
  const id = `f-${name}`;
  return (
    <div className="field">
      {label ? (
        <label htmlFor={id}>
          {label}
          {required ? <span aria-hidden="true" className="req">*</span> : null}
        </label>
      ) : null}
      <input
        id={id}
        name={name}
        type={type}
        value={value ?? ''}
        onChange={onChange}
        placeholder={placeholder}
        aria-invalid={Boolean(error)}
        className={['input', error && 'input--error'].filter(Boolean).join(' ')}
      />
      {help && !error ? <span className="help">{help}</span> : null}
      {error ? <span className="error">{error}</span> : null}
    </div>
  );
}
