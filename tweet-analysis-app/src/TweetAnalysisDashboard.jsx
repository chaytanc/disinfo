import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiService, validateAndSanitizeInput } from './apiUtils';
import { useAuth } from './Auth';
import CsvUpload from './components/CsvUpload';

export default function TweetAnalysisDashboard({ loadedData }) {
  const { logout } = useAuth();
  
  // Analysis Results State
  const [data, setData] = useState([]); // Final filtered/processed tweets after analysis
  const [selectedTweet, setSelectedTweet] = useState(null); // Currently selected tweet for detail view
  const [narratives, setNarratives] = useState([]); // Generated narrative summaries from clustering
  const [groupedData, setGroupedData] = useState({}); // Data organized by dataset name for chart visualization
  
  // UI Loading States
  const [isLoading, setIsLoading] = useState(false); // True during API calls for filtering
  const [isProcessing, setIsProcessing] = useState(false); // True during narrative generation
  const [isSaving, setIsSaving] = useState(false); // True during save operations
  const [saveMessage, setSaveMessage] = useState(''); // Status message for save operations
  
  // Analysis Parameters
  const [startDate, setStartDate] = useState('2020-11-01');
  const [endDate, setEndDate] = useState('2020-12-01');
  const [targetNarrative, setTargetNarrative] = useState('The 2020 election was stolen');
  const [threshold, setThreshold] = useState(0.5); // Similarity threshold (0-1)
  const [numNarratives, setNumNarratives] = useState(3); // Number of narrative clusters to generate
  
  // Dataset Management
  const [datasets, setDatasets] = useState(["full_tweets.csv"]); // Available dataset names (server + uploaded)
  const [selectedDatasets, setSelectedDatasets] = useState(["full_tweets.csv"]); // Currently selected for analysis
  const [uploadedDatasets, setUploadedDatasets] = useState({}); // Stores actual CSV data: {filename: parsedData[]}
  
  useEffect(() => {
    console.log("Data changed:", data.length);
    console.log("GroupedData:", groupedData);
  }, [data, groupedData]);
  
  useEffect(() => {
    // Initialize datasets on mount
    fetchDatasets();
  }, []);

  // Normalize data types for consistent usage
  const normalizeDataTypes = (data) => {
    return data.map(item => ({
      ...item,
      Similarity: item.Similarity !== null && item.Similarity !== undefined 
        ? (typeof item.Similarity === 'number' ? item.Similarity : parseFloat(item.Similarity) || 0)
        : 0,
      Datetime: typeof item.Datetime === 'string' ? item.Datetime : item.Datetime?.toString() || '',
      Tweet: item.Tweet || '',
      // Add other fields that might need normalization
      LikesCount: item.LikesCount ? parseInt(item.LikesCount) || 0 : 0,
      SharesCount: item.SharesCount ? parseInt(item.SharesCount) || 0 : 0,
      CommentsCount: item.CommentsCount ? parseInt(item.CommentsCount) || 0 : 0,
      ViewsCount: item.ViewsCount ? parseInt(item.ViewsCount) || 0 : 0
    }));
  };

  // Handle loadedData changes
  useEffect(() => {
    if (loadedData && loadedData.length > 0) {
      console.log("Processing loaded data in dashboard:", loadedData.length, "records");
      
      // Normalize data types first
      const normalizedData = normalizeDataTypes(loadedData);
      
      // Group the data by dataset name
      const grouped = {};
      const datasetNames = [...new Set(normalizedData.map(item => item.datasetName || 'unknown'))];
      
      datasetNames.forEach(datasetName => {
        grouped[datasetName] = normalizedData
          .filter(d => (d.datasetName || 'unknown') === datasetName)
          .sort((a, b) => new Date(a.Datetime) - new Date(b.Datetime));
      });
      
      // Update with normalized data
      setData(normalizedData);
      setGroupedData(grouped);
      
      // Extract parameters from the first record if available
      if (loadedData[0].metadata) {
        const metadata = loadedData[0].metadata;
        if (metadata.startDate) setStartDate(metadata.startDate);
        if (metadata.endDate) setEndDate(metadata.endDate);
        if (metadata.targetNarrative) setTargetNarrative(metadata.targetNarrative);
        if (metadata.threshold) setThreshold(metadata.threshold);
        if (metadata.selectedDatasets) setSelectedDatasets(metadata.selectedDatasets);
      }
      
      // Clear any existing narratives when loading new data
      setNarratives([]);
    }
  }, [loadedData]);
  
  // Helper function to handle authentication errors
  const handleAuthError = (error) => {
    if (error.isAuthError) {
      console.log('Authentication error detected, logging out user');
      logout();
    }
  };
  
  // Handle uploaded CSV data - stores data and adds filename to available datasets
  const handleDataUploaded = (uploadData) => {
    const fileName = uploadData.fileName;
    
    // Store the actual parsed CSV data
    setUploadedDatasets(prev => ({
      ...prev,
      [fileName]: uploadData.data
    }));
    
    // Add filename to available datasets list if not already present
    setDatasets(prev => {
      if (!prev.includes(fileName)) {
        return [...prev, fileName];
      }
      return prev;
    });
    
    console.log(`Uploaded ${fileName}: ${uploadData.totalRows} rows stored`);
  };

  // Check if a dataset name refers to uploaded data (vs server file)
  const isUploadedDataset = (datasetName) => {
    return datasetName in uploadedDatasets;
  };

  // Fetch server datasets and combine with uploaded dataset names
  const fetchDatasets = async () => {
    try {
      const result = await apiService.getDatasets({});
      console.log("Fetched server datasets:", result.files);
      
      // Combine server files with uploaded dataset names (but not data)
      const uploadedNames = Object.keys(uploadedDatasets);
      const serverFiles = result.files;
      // Remove duplicates and combine
      const combined = [...new Set([...serverFiles, ...uploadedNames])];
      setDatasets(combined);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      handleAuthError(error);
    }
  };
  
  const fetchFilteredData = async () => {
    setIsLoading(true);
    try {
      // Validate and sanitize target narrative
      const sanitizedNarrative = validateAndSanitizeInput.targetNarrative(targetNarrative);
      
      // Wait for all selected datasets to be processed
      const results = await Promise.all(
        selectedDatasets.map(async (datasetName) => {
          console.log(`Processing dataset: ${datasetName}`);
          
          let result;
          if (isUploadedDataset(datasetName)) {
            // Use upload API for uploaded datasets
            console.log(`Using uploaded data for: ${datasetName}`);
            result = await apiService.traceOverTimeUpload({
              uploadedData: uploadedDatasets[datasetName],
              startDate,
              endDate,
              targetNarrative: sanitizedNarrative,
              threshold
            });
          } else {
            // Use server file API for server datasets
            console.log(`Using server file for: ${datasetName}`);
            result = await apiService.traceOverTime({
              startDate,
              endDate,
              targetNarrative: sanitizedNarrative,
              threshold,
              file1: datasetName
            });
          }
 
          console.log(`Received ${result.filteredData.length} items for ${datasetName}`);
          
          // Add the dataset name to each record
          return result.filteredData.map(d => ({
            ...d,
            datasetName
          }));
        })
      );
  
      // Flatten the results and then sort chronologically by Datetime
      let combinedData = results.flat();
      
      // Normalize data types for consistent usage
      combinedData = normalizeDataTypes(combinedData);
      
      combinedData.sort((a, b) => a.Datetime - b.Datetime);
      
      console.log("Combined and sorted data points:", combinedData.length);
      
      // Create grouped data object based on the sorted combined data
      const grouped = {};
      selectedDatasets.forEach(datasetName => {
        grouped[datasetName] = (combinedData.filter(d => d.datasetName === datasetName)).sort((a, b) => new Date(a.Datetime) - new Date(b.Datetime));
        console.log(`Grouped ${datasetName}:`, grouped[datasetName].length);
      });
      // Set state AFTER processing
      setData(combinedData);
      setGroupedData(grouped);
      
    } catch (error) {
      console.error('Error fetching filtered data:', error);
      handleAuthError(error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Function to generate narratives
  const generateNarratives = async () => {
    setIsProcessing(true);
    try {
      const result = await apiService.generateNarratives({
          filteredData: data,
          numNarratives
        });

      setNarratives(result.narratives);
      
    } catch (error) {
      console.error('Error generating narratives:', error);
      handleAuthError(error);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const saveFilteredData = () => {
    if (data.length === 0) {
      setSaveMessage('No data to save. Please apply filters first.');
      return;
    }
    
    setIsSaving(true);
    setSaveMessage('');
    
    try {
      // Create metadata object
      const metadata = {
        startDate,
        endDate,
        targetNarrative,
        threshold,
        selectedDatasets,
        generatedAt: new Date().toISOString(),
        totalRecords: data.length
      };

      // Add metadata as a comment at the top of CSV
      const metadataComment = `# Analysis Results - Generated ${metadata.generatedAt}\n# Target: ${metadata.targetNarrative}\n# Date Range: ${metadata.startDate} to ${metadata.endDate}\n# Threshold: ${metadata.threshold}\n# Datasets: ${metadata.selectedDatasets.join(', ')}\n# Total Records: ${metadata.totalRecords}\n\n`;

      // Convert data to CSV format
      const headers = Object.keys(data[0]);
      const csvContent = [
        headers.join(','),
        ...data.map(row => 
          headers.map(header => {
            const value = row[header];
            // Handle null/undefined values and escape quotes
            if (value === null || value === undefined) return '';
            const stringValue = String(value);
            // Escape quotes and wrap in quotes if contains comma, quote, or newline
            if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
              return `"${stringValue.replace(/"/g, '""')}"`;
            }
            return stringValue;
          }).join(',')
        )
      ].join('\n');

      const fullContent = metadataComment + csvContent;

      // Create downloadable file
      const blob = new Blob([fullContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const datasetNames = selectedDatasets.join('_').replace(/[^a-zA-Z0-9_]/g, '');
      const filename = `analysis_${datasetNames}_${timestamp}.csv`;
      
      if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        setSaveMessage(`Successfully downloaded ${data.length} records as ${filename}`);
      } else {
        setSaveMessage('Download not supported in this browser');
      }
      
    } catch (error) {
      console.error('Error saving filtered data:', error);
      setSaveMessage(`Error: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleDataPointClick = (data) => {
    console.log("Selected tweet:", data);
    setSelectedTweet(data);
  };

  const addDataset = () => {
    setSelectedDatasets(prev => [...prev, datasets[0] || 'full_tweets.csv']);
  };

  const updateSelectedDatasets = (e, index) => {
    const updated = [...selectedDatasets];
    updated[index] = e.target.value;
    setSelectedDatasets(updated);
  };
  
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white p-4 border border-gray-300 rounded shadow-lg">
          <p className="text-sm text-gray-600">{new Date(data.Datetime).toLocaleString()}</p>
          <p className="font-bold">Similarity: {data.Similarity.toFixed(3)}</p>
          <p className="text-sm mt-2 max-w-xs">{data.Tweet.substring(0, 60)}...</p>
          <p className="text-xs text-blue-500 mt-1 cursor-pointer">Click for details</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-50 p-6 rounded-lg shadow mx-auto max-w-6xl">
      <h2 className="text-2xl font-bold mb-6">Tweet Narrative Analysis Dashboard</h2>
      
      {/* Upload Section */}
      <div className="mb-6">
        <CsvUpload onDataUploaded={handleDataUploaded} />
      </div>
      
      {/* Filter Controls */}
      <div className="bg-white p-4 rounded shadow mb-6">
        <h3 className="font-bold mb-4">Analysis Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <button 
            onClick={addDataset}
            className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
          >
            Add Dataset
          </button>
          {selectedDatasets.map((selectedDataset, index) => (
            <div key={index}>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dataset</label>
              <select
                value={selectedDataset}
                onChange={(e) => updateSelectedDatasets(e, index)}
                className="w-full p-2 border rounded"
              >
                {datasets.map((dataset, datasetIndex) => (
                  <option key={datasetIndex} value={dataset}>
                    {dataset}
                  </option>
                ))}
              </select>
            </div>
          ))}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Narrative</label>
            <input
              type="text"
              value={targetNarrative}
              onChange={(e) => setTargetNarrative(e.target.value)}
              className="w-full p-2 border rounded"
              placeholder="Enter target narrative"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Similarity Threshold</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="text-center">{threshold.toFixed(2)}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full p-2 border rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full p-2 border rounded"
            />
          </div>
        </div>
        <button
          onClick={fetchFilteredData}
          disabled={isLoading}
          className="mt-4 bg-blue-500 hover:bg-blue-600 text-white py-2 px-6 rounded"
        >
          {isLoading ? 'Loading...' : 'Apply Filters'}
        </button>
      </div>
      
      {/* Timeline Chart */}
      {data.length > 0 ? (
        <div className="mb-6">
          <h3 className="font-bold mb-4">Tweet Similarity Timeline</h3>
          <div className="text-sm text-gray-500 mb-2">
            Total data points: {data.length}
          </div>
          <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={data.map(item => ({
              ...item,
              Datetime: new Date(item.Datetime).getTime() // Convert to timestamp for proper scaling
            }))}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            onClick={(e) => e && e.activePayload && handleDataPointClick(e.activePayload[0].payload)}
          >
              <CartesianGrid strokeDasharray="3 3" />
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="Datetime" 
                scale="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(unixTime) => new Date(unixTime).toLocaleDateString()}
                label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                domain={[0, 1]}
                // domain={[-1,1]}
                label={{ value: 'Similarity Score', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {selectedDatasets.map((datasetName, i) => {
                const datasetPoints = (groupedData[datasetName] || []).map(item => ({
                  ...item,
                  Datetime: new Date(item.Datetime).getTime()
                }));
                
                return (
                  <Line
                    key={datasetName}
                    type="monotone"
                    data={datasetPoints}
                    dataKey="Similarity"
                    name={datasetName}
                    stroke={['#8884d8', '#82ca9d', '#ff7300', '#ff69b4'][i % 4]}
                    dot={{ r: 2 }}
                    activeDot={{ r: 6 }}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : !isLoading && (
        <div className="text-center p-12 text-gray-500">
          No data to display. Apply filters to see results.
        </div>
      )}
      
      {/* Selected Tweet Details */}
      {selectedTweet && (
        <div className="bg-white p-4 border-l-4 border-blue-500 mb-6">
          <h3 className="font-bold mb-2">Selected Tweet</h3>
          <p className="text-gray-600 text-sm mb-1">Time: {new Date(selectedTweet.Datetime).toLocaleString()}</p>
          <p className="text-gray-600 text-sm mb-2">Similarity Score: {selectedTweet.Similarity.toFixed(3)}</p>
          <p className="italic">{selectedTweet.Tweet}</p>
        </div>
      )}

      {/* Save Data Section - NEW */}
      {data.length > 0 && (
        <div className="bg-white p-4 rounded shadow mb-6">
          <h3 className="font-bold mb-4">Save Current Data</h3>
          <div className="flex items-center gap-4">
            <button
              onClick={saveFilteredData}
              disabled={isSaving || data.length === 0}
              className="bg-purple-500 hover:bg-purple-600 text-white py-2 px-6 rounded disabled:bg-gray-400"
            >
              {isSaving ? 'Saving...' : 'Save Data for Analysis'}
            </button>
            
            {saveMessage && (
              <div className={`text-sm ${saveMessage.includes('Error') ? 'text-red-500' : 'text-green-600'}`}>
                {saveMessage}
              </div>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Saves the current filtered dataset ({data.length} records) for offline analysis.
          </p>
        </div>
      )}
      
      {/* Narrative Generation Section */}
      <div className="bg-white p-4 rounded shadow mt-6">
        <h3 className="font-bold mb-2">Generated Narratives</h3>
        
        <div className="flex items-center gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Narratives</label>
            <input
              type="number"
              min="1"
              max="10"
              value={numNarratives}
              onChange={(e) => setNumNarratives(parseInt(e.target.value, 10))}
              className="w-20 p-2 border rounded"
            />
          </div>
          
          <button 
            className="mt-4 bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded disabled:bg-gray-400"
            onClick={generateNarratives}
            disabled={isProcessing || data.length === 0}
          >
            {isProcessing ? 'Processing...' : 'Generate Narratives'}
          </button>
        </div>
        
        {narratives.length > 0 ? (
          <ul className="list-disc pl-5">
            {narratives.map((narrative, index) => (
              <li key={index} className="mb-2">
                {narrative.narrative_1} <br />
                {narrative.narrative_2}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 italic">No narratives generated yet.</p>
        )}
      </div>
    </div>
  );
}