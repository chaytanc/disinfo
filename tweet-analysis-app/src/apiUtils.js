import { auth } from './firebase';

// const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_BASE_URL = 'http://localhost:5000/api';

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
      throw new Error('Authentication failed. Please log in again.');
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

  // Trace over time
  traceOverTime: async (params) => {
    return await makeAuthenticatedRequest('/trace-over-time', {
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