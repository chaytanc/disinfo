import { useState, useRef } from 'react';
import Papa from 'papaparse';
import DataFormatHelp from './DataFormatHelp';

export default function CsvUpload({ onDataUploaded }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  const validateCsvData = (data, fileName) => {
    if (!data || data.length === 0) {
      throw new Error('CSV file is empty');
    }

    const headers = Object.keys(data[0]);
    
    // Check for required columns
    const requiredColumns = ['Tweet', 'Datetime'];
    const missingColumns = requiredColumns.filter(col => !headers.includes(col));
    
    if (missingColumns.length > 0) {
      throw new Error(`Missing required columns: ${missingColumns.join(', ')}`);
    }

    // Validate that we have actual data rows (not just headers)
    const validRows = data.filter(row => row.Tweet && row.Tweet.trim() !== '');
    if (validRows.length === 0) {
      throw new Error('No valid tweet data found. Make sure the Tweet column contains text.');
    }

    // Validate datetime format in first few rows
    const sampleRows = validRows.slice(0, 5);
    for (const row of sampleRows) {
      const dateStr = row.Datetime;
      if (!dateStr) {
        throw new Error('Datetime column contains empty values');
      }
      
      // Try to parse the date
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        throw new Error(`Invalid date format: "${dateStr}". Please use YYYY-MM-DD HH:MM:SS or YYYY-MM-DD format.`);
      }
    }

    return {
      data: validRows,
      totalRows: validRows.length,
      columns: headers,
      fileName: fileName
    };
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadError('Please select a CSV file (.csv extension)');
      return;
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
      setUploadError('File size exceeds 50MB limit. Please upload a smaller file.');
      return;
    }

    setIsUploading(true);
    setUploadError('');
    setUploadStatus('Reading file...');

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      encoding: 'UTF-8',
      complete: (results) => {
        try {
          setUploadStatus('Validating data format...');
          
          if (results.errors && results.errors.length > 0) {
            const criticalErrors = results.errors.filter(error => error.type === 'Delimiter');
            if (criticalErrors.length > 0) {
              throw new Error('CSV parsing error: Invalid file format or delimiter');
            }
          }

          const validatedData = validateCsvData(results.data, file.name);
          
          setUploadStatus(`Successfully loaded ${validatedData.totalRows} tweets from ${validatedData.fileName}`);
          
          // Call the parent component's callback with the parsed data
          onDataUploaded({
            data: validatedData.data,
            fileName: validatedData.fileName,
            totalRows: validatedData.totalRows,
            columns: validatedData.columns
          });

          // Clear the file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }

        } catch (error) {
          setUploadError(error.message);
          setUploadStatus('');
        } finally {
          setIsUploading(false);
        }
      },
      error: (error) => {
        setUploadError(`Failed to parse CSV file: ${error.message}`);
        setUploadStatus('');
        setIsUploading(false);
      }
    });
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Upload Your Data</h3>
        <DataFormatHelp />
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
            id="csv-upload"
          />
          
          <button
            onClick={triggerFileInput}
            disabled={isUploading}
            className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white 
              ${isUploading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              }`}
          >
            {isUploading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload CSV File
              </>
            )}
          </button>
          
          <div className="text-sm text-gray-500">
            Maximum file size: 50MB
          </div>
        </div>

        {uploadStatus && (
          <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-md">
            <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-green-800">{uploadStatus}</span>
          </div>
        )}

        {uploadError && (
          <div className="flex items-start p-3 bg-red-50 border border-red-200 rounded-md">
            <svg className="w-5 h-5 text-red-400 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h4 className="text-sm font-medium text-red-800">Upload Error</h4>
              <p className="text-sm text-red-700 mt-1">{uploadError}</p>
            </div>
          </div>
        )}

        <div className="text-xs text-gray-500 space-y-1">
          <p>• Supported format: CSV files with Tweet and Datetime columns</p>
          <p>• Files are processed locally in your browser for security</p>
          <p>• Click the Help button above for detailed format requirements</p>
        </div>
      </div>
    </div>
  );
}