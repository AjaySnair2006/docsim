import React from "react";

export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="error-banner" role="alert">
      <span><strong>Something went wrong</strong>{message}</span>
      {onDismiss && (
        <button className="error-banner__close" onClick={onDismiss}>
          Close
        </button>
      )}
    </div>
  );
}
