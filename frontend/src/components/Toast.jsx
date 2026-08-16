import { useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';

/**
 * Toast notification system provider
 * Wrap your app with this to enable toast notifications
 */
export function ToastProvider({ children }) {
  return (
    <>
      {children}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        toastOptions={{
          duration: 3000,
          style: {
            background: 'var(--bg-card)',
            color: 'var(--text)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-lg)',
            padding: '12px 16px',
            fontSize: 'var(--text-sm)',
          },
        }}
      />
    </>
  );
}

/**
 * Show a success toast notification
 */
export function showSuccess(message, options = {}) {
  return toast.success(message, {
    icon: '✓',
    style: {
      backgroundColor: 'var(--success-light)',
      color: 'var(--success)',
      border: '1px solid rgba(5, 150, 105, 0.2)',
    },
    ...options,
  });
}

/**
 * Show an error toast notification
 */
export function showError(message, options = {}) {
  return toast.error(message, {
    icon: '✕',
    style: {
      backgroundColor: 'var(--danger-light)',
      color: 'var(--danger)',
      border: '1px solid rgba(220, 38, 38, 0.2)',
    },
    ...options,
  });
}

/**
 * Show an info toast notification
 */
export function showInfo(message, options = {}) {
  return toast.promise(
    new Promise(resolve => setTimeout(() => resolve(null), 3000)),
    {
      loading: message,
      success: message,
      error: message,
    },
    {
      style: {
        backgroundColor: 'var(--info-light)',
        color: 'var(--info)',
        border: '1px solid rgba(37, 99, 235, 0.2)',
      },
      ...options,
    }
  );
}

/**
 * Show a loading toast notification
 */
export function showLoading(message) {
  return toast.loading(message, {
    style: {
      backgroundColor: 'var(--bg-card)',
      color: 'var(--text)',
      border: '1px solid var(--border)',
    },
  });
}

// Toast component exports configured above
