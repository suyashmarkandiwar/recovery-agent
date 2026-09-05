const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = async (endpoint, options = {}) => {
  const url = `${BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    credentials: 'include', // Crucial: This ensures our HttpOnly auth cookie is sent to the backend
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Merge options and headers
  const finalOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  // If the body is an object and not FormData, stringify it
  if (finalOptions.body && typeof finalOptions.body === 'object') {
    finalOptions.body = JSON.stringify(finalOptions.body);
  }

  const response = await fetch(url, finalOptions);
  
  // Basic error handling
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || errorDetail;
    } catch (e) {
        // If JSON parsing fails, just use status text
        errorDetail = response.statusText;
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }
  
  return response.json();
};
