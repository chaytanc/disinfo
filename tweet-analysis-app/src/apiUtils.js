import { auth } from './firebase';
import DOMPurify from 'dompurify';

// const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_BASE_URL = 'http://localhost:5000/api';

// Input validation and sanitization
export const validateAndSanitizeInput = {
  targetNarrative: (input) => {
    if (!input || typeof input !== 'string') {
      throw new Error('Target narrative must be a non-empty string');
    }
    
    // Length validation
    if (input.length > 500) {
      throw new Error('Target narrative must be less than 500 characters');
    }
    
    if (input.length < 3) {
      throw new Error('Target narrative must be at least 3 characters');
    }
    
    // Use DOMPurify to sanitize the input
    const sanitized = DOMPurify.sanitize(input, {
      ALLOWED_TAGS: [], // No HTML tags allowed
      ALLOWED_ATTR: [], // No attributes allowed
      KEEP_CONTENT: true // Keep text content
    }).trim();
    
    // Additional validation after sanitization
    if (sanitized.length < 3) {
      throw new Error('Target narrative must be at least 3 characters after sanitization');
    }
    
    return sanitized;
  }
};

// Helper function to get the current user's ID token
const getAuthToken = async () => {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }
  return await user.getIdToken();
};

// Generic function for making authenticated API requests
const makeAuthenticatedRequest = async (url, options = {}) => {
  const token = await getAuthToken();
  
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Create a special error type for 401s that components can catch
      const authError = new Error('Authentication failed. Please log in again.');
      authError.isAuthError = true;
      throw authError;
    }
    const errorData = await response.json();
    throw new Error(errorData.error || `${url} HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

// API functions
export const apiService = {
  // Get available datasets
  getDatasets: async () => {
    return await makeAuthenticatedRequest('/post-datasets', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },

  // Trace over time (for server files)
  traceOverTime: async (params) => {
    return await makeAuthenticatedRequest('/trace-over-time', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
  },

  // Trace over time (for uploaded CSV data)
  traceOverTimeUpload: async (params) => {
    return await makeAuthenticatedRequest('/trace-over-time-upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
  },

  // Generate narratives
  generateNarratives: async (data) => {
    return await makeAuthenticatedRequest('/generate-narratives', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  },

  // Save filtered data
  saveFilteredData: async (data) => {
    return await makeAuthenticatedRequest('/save-filtered-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  },

  // List saved data
  listSavedData: async () => {
    return await makeAuthenticatedRequest('/list-saved-data', {
      method: 'GET',
    });
  },

  // Load saved data
  loadSavedData: async (filename) => {
    return await makeAuthenticatedRequest('/load-saved-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ filename }),
    });
  },
};