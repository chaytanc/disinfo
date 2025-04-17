import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE_URL = 'http://localhost:5000';

export default function TweetAnalysisDashboard() {
  // State variables
  const [data, setData] = useState([]);
  const [selectedTweet, setSelectedTweet] = useState(null);
  const [narratives, setNarratives] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Filter parameters
  const [startDate, setStartDate] = useState('2020-11-01');
  const [endDate, setEndDate] = useState('2020-12-01');
  const [targetNarrative, setTargetNarrative] = useState('The 2020 election was a hoax');
  const [threshold, setThreshold] = useState(0.5);
  const [numNarratives, setNumNarratives] = useState(3);
  const [groupedData, setGroupedData] = useState({});
  const [datasets, setDatasets] = useState(["full_tweets.csv"]);
  const [selectedDatasets, setSelectedDatasets] = useState(["full_tweets.csv"]);
  
  // Debug useEffect to track state changes
  useEffect(() => {
    console.log("Data changed:", data.length);
    console.log("GroupedData:", groupedData);
  }, [data, groupedData]);
  
  // Add useEffect to fetch datasets when component mounts
  useEffect(() => {
    fetchDatasets();
  }, []);
  
  // Fetch datasets function
  const fetchDatasets = async () => {
    try {
      debugger;
      const response = await fetch(`${API_BASE_URL}/post-datasets`, 
      {        
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const result = await response.json();
      console.log("Fetched datasets:", result.files);
      setDatasets(result.files);
    } catch (error) {
      console.error('Error fetching datasets:', error);
    }
  };
  
  const fetchFilteredData = async () => {
    setIsLoading(true);
    try {
      // Wait for all selected datasets to be processed
      const results = await Promise.all(
        selectedDatasets.map(async (datasetName) => {
          console.log(`Fetching data for dataset: ${datasetName}`);
          const response = await fetch(`${API_BASE_URL}/trace-over-time`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              startDate,
              endDate,
              targetNarrative,
              threshold,
              file1: datasetName
            }),
          });
  
          if (!response.ok) {
            throw new Error(`Failed to fetch data for ${datasetName}`);
          }
          // // Log the raw text response to see what's coming back
          // const rawText = await response.text();
          // console.log('Raw response:', rawText);
  
          const result = await response.json();
          console.log(`Received ${result.filteredData.length} items for ${datasetName}`);
          
          // Make sure each data point has a valid Date object for Datetime
          return result.filteredData.map(d => ({
            ...d,
            // Datetime: d.Datetime ? new Date(d.Datetime).getTime() : new Date().getTime(),
            datasetName, // tag each point with its dataset name
          }));
        })
      );
  
      const combinedData = results.flat(); // combine results into a single array
      console.log("Combined data points:", combinedData.length);
      
      // Create new grouped data object based on the combined data
      const grouped = {};
      selectedDatasets.forEach(datasetName => {
        grouped[datasetName] = combinedData.filter(d => d.datasetName === datasetName);
        console.log(`Grouped ${datasetName}:`, grouped[datasetName].length);
      });
      
      // Set state AFTER processing
      setData(combinedData);
      setGroupedData(grouped);
      
    } catch (error) {
      debugger;
      console.error('Error fetching filtered data:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Function to generate narratives
  const generateNarratives = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/generate-narratives`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filteredData: data,
          numNarratives
        }),
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const result = await response.json();
      setNarratives(result.narratives);
      
    } catch (error) {
      console.error('Error generating narratives:', error);
    } finally {
      setIsProcessing(false);
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
              data={data} // Provide all data as a baseline
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              onClick={(e) => e && e.activePayload && handleDataPointClick(e.activePayload[0].payload)}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="Datetime" 
                tickFormatter={(datetime) => new Date(datetime).toLocaleDateString()}
                label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                domain={[0, 1]}
                label={{ value: 'Similarity Score', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {selectedDatasets.map((datasetName, i) => {
                const datasetPoints = groupedData[datasetName] || [];
                console.log(`Rendering line for ${datasetName}: ${datasetPoints.length} points`);
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