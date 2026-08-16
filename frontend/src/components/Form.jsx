/**
 * Form group with label and error handling
 */
export function FormGroup({
  label,
  error,
  hint,
  children,
  required = false,
  className = '',
}) {
  return (
    <div className={`form-group ${error ? 'error' : ''} ${className}`}>
      {label && (
        <label className="label">
          {label}
          {required && <span style={{ color: 'var(--danger)', marginLeft: '2px' }}>*</span>}
        </label>
      )}
      {children}
      {hint && <div className="form-hint">{hint}</div>}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
}

/**
 * Input field component
 */
export function Input({
  label,
  error,
  hint,
  required = false,
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  ...props
}) {
  return (
    <FormGroup label={label} error={error} hint={hint} required={required}>
      <input
        type={type}
        className="input"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        {...props}
      />
    </FormGroup>
  );
}

/**
 * Select field component
 */
export function Select({
  label,
  error,
  hint,
  required = false,
  placeholder,
  value,
  onChange,
  options = [],
  disabled = false,
  ...props
}) {
  return (
    <FormGroup label={label} error={error} hint={hint} required={required}>
      <select
        className="select"
        value={value}
        onChange={onChange}
        disabled={disabled}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </FormGroup>
  );
}

/**
 * Textarea component
 */
export function Textarea({
  label,
  error,
  hint,
  required = false,
  placeholder,
  value,
  onChange,
  disabled = false,
  rows = 4,
  ...props
}) {
  return (
    <FormGroup label={label} error={error} hint={hint} required={required}>
      <textarea
        className="textarea"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        rows={rows}
        {...props}
      />
    </FormGroup>
  );
}

/**
 * Checkbox component
 */
export function Checkbox({ label, checked, onChange, disabled = false, id, ...props }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        {...props}
        style={{
          width: '18px',
          height: '18px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          accentColor: 'var(--primary)',
        }}
      />
      {label && (
        <label htmlFor={id} style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}>
          {label}
        </label>
      )}
    </div>
  );
}

/**
 * Form section with heading
 */
export function FormSection({ title, description, children }) {
  return (
    <div style={{ marginBottom: 'var(--spacing-2xl)' }}>
      {title && <h3 style={{ marginTop: 0, marginBottom: 'var(--spacing-sm)' }}>{title}</h3>}
      {description && <p style={{ color: 'var(--text-muted)', marginBottom: 'var(--spacing-lg)' }}>{description}</p>}
      {children}
    </div>
  );
}
