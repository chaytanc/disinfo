import { useState } from 'react';
import TweetAnalysisDashboard from './TweetAnalysisDashboard';
import SavedDataBrowser from './components/SavedDataBrowser';
import { AuthProvider, useAuth } from './Auth';
import { LoginForm } from './components/LoginForm';
import { Header } from './components/Header';

// Protected Route Component
function ProtectedApp() {
  const [loadedData, setLoadedData] = useState(null);
  const { currentUser, logout } = useAuth();
  
  const handleDataLoad = (data) => {
    console.log("Data loaded in App:", data.length, "records");
    setLoadedData(data);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header user={currentUser} onSignOut={logout} />
      <div className="container mx-auto p-4">
        <SavedDataBrowser onLoadData={handleDataLoad} />
        <TweetAnalysisDashboard loadedData={loadedData} />
      </div>
    </div>
  );
}

// Component that handles showing login or protected app
function AuthenticatedApp() {
  const { currentUser, loading } = useAuth();
  console.log("user", currentUser);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return currentUser ? <ProtectedApp /> : <LoginForm />;
}

export default function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}