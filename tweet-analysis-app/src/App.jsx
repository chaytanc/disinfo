import { useState } from 'react';
import TweetAnalysisDashboard from './TweetAnalysisDashboard';
import SavedDataBrowser from './SavedDataBrowser';

export default function App() {
  const [loadedData, setLoadedData] = useState(null);
  
  // This function is called when a dataset is loaded from SavedDataBrowser
  const handleDataLoad = (data) => {
    console.log("Data loaded in App:", data.length, "records");
    setLoadedData(data);
  };

  return (
    <div className="container mx-auto p-4">
      {/* SavedDataBrowser passes data through onLoadData */}
      <SavedDataBrowser onLoadData={handleDataLoad} />
      
      {/* Pass the loaded data as a prop instead of using refs */}
      <TweetAnalysisDashboard loadedData={loadedData} />
    </div>
  );
}