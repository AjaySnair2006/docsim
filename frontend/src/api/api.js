import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * Uploads two PDFs and returns the structured comparison result.
 * @param {File} fileA
 * @param {File} fileB
 * @param {(progress: number) => void} onProgress optional upload progress callback (0-100)
 */
export async function compareDocuments(fileA, fileB, onProgress) {
  const formData = new FormData();
  formData.append("document_a", fileA);
  formData.append("document_b", fileB);

  const response = await client.post("/compare", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded * 100) / evt.total));
      }
    },
  });

  return response.data;
}

/** Builds the absolute download URL for a report path returned by /compare */
export function getReportDownloadUrl(reportDownloadUrl) {
  return `${API_BASE_URL}${reportDownloadUrl}`;
}

export async function checkHealth() {
  const response = await client.get("/health");
  return response.data;
}

/** Normalizes backend/network errors into a readable message string. */
export function extractErrorMessage(error) {
  if (error.response?.data?.detail?.message) {
    return error.response.data.detail.message;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return "An unexpected error occurred. Please try again.";
}
