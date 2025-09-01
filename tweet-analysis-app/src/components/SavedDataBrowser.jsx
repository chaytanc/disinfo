import { useState, useRef } from 'react';
import Papa from 'papaparse';

export default function SavedDataBrowser({ onLoadData }) {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const fileInputRef = useRef(null);

  const parseAnalysisCSV = (csvContent, fileName) => {
    // Check if this is an analysis results file (has metadata comments)
    const lines = csvContent.split('\n');
    let metadata = {};
    let csvStart = 0;
    
    // Parse metadata from comments
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('#')) {
        if (line.includes('Target:')) {
          metadata.targetNarrative = line.split('Target:')[1].trim();
        } else if (line.includes('Date Range:')) {
          const range = line.split('Date Range:')[1].trim();
          const [start, end] = range.split(' to ');
          metadata.startDate = start;
          metadata.endDate = end;
        } else if (line.includes('Threshold:')) {
          metadata.threshold = parseFloat(line.split('Threshold:')[1].trim());
        } else if (line.includes('Datasets:')) {
          metadata.selectedDatasets = line.split('Datasets:')[1].trim().split(', ');
        } else if (line.includes('Total Records:')) {
          metadata.totalRecords = parseInt(line.split('Total Records:')[1].trim());
        }
      } else if (line && !line.startsWith('#')) {
        csvStart = i;
        break;
      }
    }
    
    // Get CSV content without metadata comments
    const csvData = lines.slice(csvStart).join('\n');
    
    return new Promise((resolve, reject) => {
      Papa.parse(csvData, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.errors && results.errors.length > 0) {
            reject(new Error(`Failed to parse CSV data in ${fileName}: ${results.errors[0].message}`));
            return;
          }
          
          // Add metadata to each record
          const dataWithMetadata = results.data.map(item => ({
            ...item,
            metadata
          }));
          
          resolve(dataWithMetadata);
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  };

  const handleFileLoad = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setMessage('Please select a CSV file');
      return;
    }

    setIsLoading(true);
    setMessage('');

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const csvContent = e.target.result;
        const parsedData = await parseAnalysisCSV(csvContent, file.name);
        
        // Pass loaded data back to parent component
        if (onLoadData && typeof onLoadData === 'function') {
          onLoadData(parsedData);
          setMessage(`Successfully loaded ${parsedData.length} records from ${file.name}`);
        }
        
        // Clear the file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        
      } catch (error) {
        console.error('Error loading dataset:', error);
        setMessage(`Error: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    reader.onerror = () => {
      setMessage('Error reading file');
      setIsLoading(false);
    };

    reader.readAsText(file);
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="bg-white p-4 rounded shadow mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold">Load Saved Analysis</h3>
        <div className="text-sm text-gray-500">
          Load previously saved analysis results from your Downloads folder
        </div>
      </div>
      
      <div className="space-y-4">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileLoad}
          className="hidden"
          id="analysis-file-load"
        />
        
        <button
          onClick={triggerFileInput}
          disabled={isLoading}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white 
            ${isLoading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2'
            }`}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 12l2 2 4-4" />
              </svg>
              Load Analysis File
            </>
          )}
        </button>

        {message && (
          <div className={`flex items-start p-3 rounded-md ${
            message.includes('Error') 
              ? 'bg-red-50 border border-red-200' 
              : 'bg-green-50 border border-green-200'
          }`}>
            <svg className={`w-5 h-5 mr-2 mt-0.5 flex-shrink-0 ${
              message.includes('Error') ? 'text-red-400' : 'text-green-400'
            }`} fill="currentColor" viewBox="0 0 20 20">
              {message.includes('Error') ? (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              ) : (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              )}
            </svg>
            <div>
              <p className={`text-sm ${
                message.includes('Error') ? 'text-red-800' : 'text-green-800'
              }`}>
                {message}
              </p>
            </div>
          </div>
        )}

        <div className="text-xs text-gray-500 space-y-1">
          <p>• Select analysis CSV files saved from this dashboard</p>
          <p>• Files contain metadata and will restore analysis parameters</p>
          <p>• Look for files starting with "analysis_" in your Downloads folder</p>
        </div>
      </div>
    </div>
  );
}