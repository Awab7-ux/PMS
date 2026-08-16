/**
 * Page header component
 */
export function PageHeader({ title, description, action, icon }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 'var(--spacing-2xl)',
        gap: 'var(--spacing-lg)',
      }}
    >
      <div>
        {icon && (
          <div
            style={{
              fontSize: '2.5rem',
              marginBottom: 'var(--spacing-sm)',
              opacity: 0.8,
            }}
          >
            {icon}
          </div>
        )}
        <h1 style={{ marginBottom: 'var(--spacing-sm)' }}>{title}</h1>
        {description && <p style={{ color: 'var(--text-muted)' }}>{description}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

/**
 * Card component
 */
export function Card({ children, className = '', header, footer, ...props }) {
  return (
    <div className={`card ${className}`} {...props}>
      {header && <div className="card-header">{header}</div>}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
}

/**
 * Stat card for dashboards
 */
export function StatCard({ icon, label, value, hint, tone = 'blue', onClick }) {
  const toneClass = {
    blue: { bg: 'var(--primary-light)', color: 'var(--primary)' },
    green: { bg: 'var(--success-light)', color: 'var(--success)' },
    red: { bg: 'var(--danger-light)', color: 'var(--danger)' },
    yellow: { bg: 'var(--warning-light)', color: 'var(--warning)' },
  }[tone] || { bg: 'var(--primary-light)', color: 'var(--primary)' };

  const isBootstrapIcon = icon && icon.startsWith('bi-');

  return (
    <Card
      onClick={onClick}
      style={{
        cursor: onClick ? 'pointer' : 'default',
        minHeight: '140px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ marginBottom: 'var(--spacing-md)' }}>
        {icon && (
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-md)',
              background: toneClass.bg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: toneClass.color,
              fontSize: isBootstrapIcon ? '24px' : '1.25rem',
              lineHeight: '1',
            }}
            aria-hidden="true"
          >
            {isBootstrapIcon ? <i className={`bi ${icon}`}></i> : icon}
          </div>
        )}
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)', fontWeight: '600', marginBottom: 'var(--spacing-sm)', textAlign: 'left' }}>
        {label}
      </div>
      <div style={{ fontSize: 'var(--text-2xl)', fontWeight: '700', marginBottom: 'var(--spacing-xs)', textAlign: 'left' }}>
        {value}
      </div>
      {hint && (
        <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)', textAlign: 'left' }}>
          {hint}
        </div>
      )}
    </Card>
  );
}

/**
 * Alert component
 */
export function Alert({ type = 'info', title, message, onClose, icon, action }) {
  const typeConfig = {
    info: { bg: 'var(--info-light)', border: 'var(--info)', text: 'var(--text)', icon: 'bi-info-circle' },
    success: { bg: 'var(--success-light)', border: 'var(--success)', text: 'var(--text)', icon: 'bi-check-circle' },
    warning: { bg: 'var(--warning-light)', border: 'var(--warning)', text: 'var(--text)', icon: 'bi-exclamation-circle' },
    error: { bg: 'var(--danger-light)', border: 'var(--danger)', text: 'var(--text)', icon: 'bi-exclamation-triangle' },
  }[type];

  const iconClass = icon || typeConfig.icon;

  return (
    <div
      className={`alert alert-${type}`}
      style={{
        backgroundColor: typeConfig.bg,
        borderColor: typeConfig.border,
        color: typeConfig.text,
      }}
      role="alert"
    >
      {iconClass && (
        <div className="alert-icon" aria-hidden="true">
          <i className={`bi ${iconClass}`}></i>
        </div>
      )}
      <div style={{ flex: 1 }}>
        {title && <strong>{title}</strong>}
        {message && <div>{message}</div>}
      </div>
      {action && <div style={{ marginLeft: 'var(--spacing-lg)' }}>{action}</div>}
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            fontSize: '1.25rem',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            marginLeft: 'var(--spacing-lg)',
          }}
          aria-label="Close alert"
        >
          <i className="bi bi-x-lg"></i>
        </button>
      )}
    </div>
  );
}

/**
 * Badge component
 */
export function Badge({ children, variant = 'secondary', icon }) {
  return (
    <span className={`badge badge-${variant}`}>
      {icon && <i className={`bi ${icon}`} style={{ marginRight: '4px' }}></i>}
      {children}
    </span>
  );
}

/**
 * Progress bar component
 */
export function ProgressBar({ value = 0, max = 100, showLabel = true, variant = 'primary' }) {
  const percentage = (value / max) * 100;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-md)',
      }}
    >
      <div
        style={{
          flex: 1,
          height: '8px',
          backgroundColor: 'var(--bg-hover)',
          borderRadius: 'var(--radius-full)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${percentage}%`,
            backgroundColor: `var(--${variant})`,
            borderRadius: 'var(--radius-full)',
            transition: 'width var(--transition-base)',
          }}
        />
      </div>
      {showLabel && (
        <span
          style={{
            fontSize: 'var(--text-sm)',
            fontWeight: '600',
            color: 'var(--text-muted)',
            minWidth: '40px',
            textAlign: 'right',
          }}
        >
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
}
