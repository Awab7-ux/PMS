import { useEffect } from 'react';

/**
 * Professional Modal component
 */
export function Modal({ isOpen, onClose, title, children, footer, size = 'md', closeOnBackdrop = true }) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClass = {
    sm: 'max-width: 400px',
    md: 'max-width: 500px',
    lg: 'max-width: 700px',
    xl: 'max-width: 900px',
  }[size];

  return (
    <div
      className="modal-overlay"
      onClick={closeOnBackdrop ? onClose : undefined}
      role="presentation"
    >
      <div
        className="modal"
        onClick={e => e.stopPropagation()}
        style={{ width: '90%', ...{ [sizeClass.split(':')[0]]: sizeClass } }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {title && (
          <div className="modal-header">
            <h2 id="modal-title">{title}</h2>
            <button
              type="button"
              className="modal-close"
              onClick={onClose}
              aria-label="Close modal"
            >
              <i className="bi bi-x-lg"></i>
            </button>
          </div>
        )}

        <div className="modal-body">{children}</div>

        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

/**
 * Confirmation dialog component
 */
export function ConfirmDialog({
  isOpen,
  title = 'Confirm',
  message = '',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  isDangerous = false,
  isLoading = false,
}) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title} size="sm">
      <div style={{ marginBottom: 'var(--spacing-xl)' }}>
        <p>{message}</p>
      </div>
      <div className="modal-footer">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onCancel}
          disabled={isLoading}
        >
          {cancelText}
        </button>
        <button
          type="button"
          className={`btn ${isDangerous ? 'btn-danger' : 'btn-primary'}`}
          onClick={onConfirm}
          disabled={isLoading}
        >
          {isLoading ? <i className="bi bi-hourglass-split spinner"></i> : confirmText}
        </button>
      </div>
    </Modal>
  );
}
