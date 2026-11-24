import React, { useRef, useState } from "react";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function FileUpload({ label, file, onFileSelect, onFileError }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const chooseFile = (selected) => {
    if (!selected) return;
    if (selected.type !== "application/pdf" && !selected.name.toLowerCase().endsWith(".pdf")) {
      onFileError(`${label} must be a PDF file.`);
      return;
    }
    if (selected.size > MAX_FILE_SIZE) {
      onFileError(`${label} is larger than 10 MB. Choose a smaller PDF.`);
      return;
    }
    onFileError("");
    onFileSelect(selected);
  };

  const handleChange = (e) => chooseFile(e.target.files?.[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    chooseFile(e.dataTransfer.files?.[0]);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      inputRef.current?.click();
    }
  };

  return (
    <div
      className={`upload-box ${file ? "upload-box--filled" : ""} ${isDragging ? "upload-box--dragging" : ""}`}
      onClick={() => inputRef.current?.click()}
      onKeyDown={handleKeyDown}
      onDragOver={(e) => e.preventDefault()}
      onDragEnter={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setIsDragging(false); }}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      aria-label={`${label}, ${file ? "file selected" : "choose PDF"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handleChange}
        hidden
      />
      <div className="upload-topline"><span className="doc-index">{label === "Document A" ? "A" : "B"}</span><span className="upload-action">{file ? "Replace file" : "Browse files"}</span></div>
      <div className="upload-icon" aria-hidden="true"><span /></div>
      <p className="upload-label">{file ? "Ready for analysis" : `Add ${label.toLowerCase()}`}</p>
      {file ? (
        <div className="upload-status upload-status--ok">
          <strong>{file.name}</strong><span>{(file.size / 1024).toFixed(0)} KB · PDF</span>
          <button className="file-remove" type="button" onClick={(e) => { e.stopPropagation(); onFileSelect(null); }}>Remove file</button>
        </div>
      ) : (
        <p className="upload-hint">Drag and drop here, or click to browse</p>
      )}
    </div>
  );
}
