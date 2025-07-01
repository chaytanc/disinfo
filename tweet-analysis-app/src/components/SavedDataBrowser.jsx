import { useState, useEffect } from 'react';
import { apiService } from '../apiUtils';

const API_BASE_URL = 'http://localhost:5000/api';

export default function SavedDataBrowser({ onLoadData }) {
  const [savedDatasets, setSavedDatasets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSavedDatasets();
  }, []);

  const fetchSavedDatasets = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.listSavedData();
      
      if (!response.ok) {
        throw new Error('Failed to fetch saved datasets');
      }
      
      const result = await response.json();
      setSavedDatasets(result.datasets || []);
      
      if (result.datasets.length === 0) {
        setMessage('No saved datasets found');
      } else {
        setMessage('');
      }
      
    } catch (error) {
      console.error('Error fetching saved datasets:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadDataset = async (filename) => {
    setIsLoading(true);
    setMessage('');
    
    try {
      const response = await apiService.loadSavedData({
          filename
      });
      
      if (!response.ok) {
        throw new Error('Failed to load dataset');
      }
      
      const result = await response.json();
      
      // Pass loaded data back to parent component
      if (onLoadData && typeof onLoadData === 'function') {
        onLoadData(result.data);
        setMessage(`Successfully loaded ${result.data.length} records`);
      }
      
    } catch (error) {
      console.error('Error loading dataset:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold">Saved Datasets</h3>
        <button 
          onClick={fetchSavedDatasets}
          className="text-blue-500 hover:text-blue-700 text-sm flex items-center"
          disabled={isLoading}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>
      
      {isLoading ? (
        <div className="text-center py-4">
          <p className="text-gray-500">Loading...</p>
        </div>
      ) : message ? (
        <div className="text-center py-4">
          <p className={`text-sm ${message.includes('Error') ? 'text-red-500' : 'text-gray-500'}`}>
            {message}
          </p>
        </div>
      ) : (
        <div className="max-h-60 overflow-y-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Filename
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date Saved
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {savedDatasets.map((dataset, index) => {
                // Extract timestamp from filename
                const timestampMatch = dataset.match(/filtered_data_(\d{8}_\d{6})\.pkl/);
                const timestamp = timestampMatch ? 
                  timestampMatch[1].replace(/_/, ' ').replace(/(\d{4})(\d{2})(\d{2}) (\d{2})(\d{2})(\d{2})/, '$1-$2-$3 $4:$5:$6') :
                  'Unknown';
                
                return (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dataset}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {timestamp}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => loadDataset(dataset)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        Load
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}