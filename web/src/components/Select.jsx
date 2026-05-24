import './Field.css';

export function Select({ label, name, value, onChange, options, error, help, required }) {
  const id = `f-${name}`;
  return (
    <div className="field">
      {label ? (
        <label htmlFor={id}>
          {label}
          {required ? <span aria-hidden="true" className="req">*</span> : null}
        </label>
      ) : null}
      <select
        id={id}
        name={name}
        value={value ?? ''}
        onChange={onChange}
        aria-invalid={Boolean(error)}
        className={['input', error && 'input--error'].filter(Boolean).join(' ')}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {help && !error ? <span className="help">{help}</span> : null}
      {error ? <span className="error">{error}</span> : null}
    </div>
  );
}
