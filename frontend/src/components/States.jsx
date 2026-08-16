/**
 * Loading state component for pages and sections
 */
export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="empty-state">
      <div className="spinner" aria-hidden="true"></div>
      <p className="empty-state-text">{message}</p>
    </div>
  );
}

/**
 * Empty state component
 */
export function EmptyState({ icon = 'bi-inbox', title = 'No data', message = '', action = null }) {
  const isIcon = icon && icon.startsWith('bi-');
  
  return (
    <div className="empty-state">
      {isIcon ? (
        <div className="empty-state-icon" aria-hidden="true">
          <i className={`bi ${icon}`}></i>
        </div>
      ) : (
        <div className="empty-state-icon" aria-hidden="true">{icon}</div>
      )}
      <h3 className="empty-state-title">{title}</h3>
      {message && <p className="empty-state-text">{message}</p>}
      {action && <div className="mt-lg">{action}</div>}
    </div>
  );
}

/**
 * Error state component
 */
export function ErrorState({ title = 'Something went wrong', message = '', onRetry = null }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon error-icon" aria-hidden="true">
        <i className="bi bi-exclamation-circle"></i>
      </div>
      <h3 className="empty-state-title">{title}</h3>
      {message && <p className="empty-state-text">{message}</p>}
      {onRetry && (
        <div className="mt-lg">
          <button className="btn btn-primary btn-sm" onClick={onRetry}>
            <i className="bi bi-arrow-clockwise"></i>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Skeleton loader component
 */
export function SkeletonLoader({ count = 3, height = 200 }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="skeleton skeleton-card"
          style={{ height: `${height}px` }}
          role="status"
          aria-label="Loading content"
        />
      ))}
    </div>
  );
}

/**
 * Table skeleton loader
 */
export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i}>
                <div className="skeleton skeleton-line" style={{ width: '80px' }} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIdx) => (
            <tr key={rowIdx}>
              {Array.from({ length: columns }).map((_, colIdx) => (
                <td key={colIdx}>
                  <div className="skeleton skeleton-line" style={{ width: '100%' }} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
