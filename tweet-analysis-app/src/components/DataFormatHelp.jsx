import { useState } from 'react';

export default function DataFormatHelp() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        title="Data Format Requirements"
      >
        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
        Help
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 bg-gray-50 rounded-t-lg border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Data Format Requirements</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="px-6 py-4 space-y-6">
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">Required CSV Format</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Your CSV file must contain these essential columns for the disinformation analysis pipeline:
                </p>
                
                <div className="bg-red-50 p-4 rounded-md border border-red-200">
                  <h5 className="font-semibold text-sm text-red-700 mb-2">Required Columns:</h5>
                  <ul className="text-sm text-red-600 space-y-1">
                    <li><strong>Tweet</strong> - The main text content to analyze (used for similarity scoring)</li>
                    <li><strong>Datetime</strong> - Timestamp for time-based filtering and visualization</li>
                  </ul>
                </div>

                <div className="bg-blue-50 p-4 rounded-md mt-4 border border-blue-200">
                  <h5 className="font-semibold text-sm text-blue-700 mb-2">Highly Recommended:</h5>
                  <ul className="text-sm text-blue-600 space-y-1">
                    <li><strong>ChannelName</strong> - Account/user name (creates "Author: [name]" prefix for better analysis)</li>
                  </ul>
                </div>

                <div className="bg-green-50 p-4 rounded-md mt-4 border border-green-200">
                  <h5 className="font-semibold text-sm text-green-700 mb-2">Optional Columns (enhance analysis):</h5>
                  <ul className="text-sm text-green-600 space-y-1">
                    <li><strong>PostId</strong> - Unique identifier</li>
                    <li><strong>PostUrl</strong> - Link to original post</li>
                    <li><strong>LikesCount</strong> - Engagement metrics</li>
                    <li><strong>SharesCount</strong> - Retweet/share counts</li>
                    <li><strong>CommentsCount</strong> - Reply counts</li>
                    <li><strong>ViewsCount</strong> - View metrics</li>
                    <li><strong>Platform</strong> - Social media platform (Twitter, Facebook, etc.)</li>
                  </ul>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">Example CSV Structure</h4>
                <div className="bg-gray-900 text-green-400 p-4 rounded-md text-xs font-mono overflow-x-auto">
                  <pre>{`Tweet,Datetime,ChannelName,PostId,Platform
"The 2020 election results were questionable","2020-11-15 14:30:00","ExampleUser",12345,"Twitter"
"Voting machines had serious irregularities","2020-11-16 09:15:00","NewsSource",12346,"Twitter"
"Mail-in ballots were not properly verified","2020-11-17 16:45:00","PoliticalAccount",12347,"Twitter"`}</pre>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  This example shows content that would be analyzed for narrative similarity to targets like "The 2020 election was stolen"
                </p>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">Date Format Requirements</h4>
                <div className="bg-yellow-50 p-4 rounded-md border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    <strong>Critical:</strong> The Datetime column must use one of these formats:
                  </p>
                  <ul className="text-sm text-yellow-700 mt-2 space-y-1">
                    <li>• <strong>YYYY-MM-DD HH:MM:SS</strong> (e.g., "2020-11-15 14:30:00")</li>
                    <li>• <strong>YYYY-MM-DD</strong> (e.g., "2020-11-15")</li>
                    <li>• <strong>ISO format</strong> (e.g., "2020-11-15T14:30:00.000Z")</li>
                  </ul>
                  <p className="text-sm text-yellow-800 mt-2">
                    Time-based filtering depends on proper date parsing.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">How the Analysis Works</h4>
                <div className="bg-gray-50 p-4 rounded-md space-y-3">
                  <div>
                    <h5 className="font-semibold text-sm text-gray-700">1. Text Processing</h5>
                    <p className="text-sm text-gray-600">
                      If <code>ChannelName</code> is present: creates "Author: [ChannelName]\nTweet: [Tweet]" format for better context analysis
                    </p>
                  </div>
                  <div>
                    <h5 className="font-semibold text-sm text-gray-700">2. Similarity Scoring</h5>
                    <p className="text-sm text-gray-600">
                      Uses sentence transformers to calculate cosine similarity between your tweets and target narratives
                    </p>
                  </div>
                  <div>
                    <h5 className="font-semibold text-sm text-gray-700">3. Time Filtering</h5>
                    <p className="text-sm text-gray-600">
                      Filters results by date range and similarity threshold for trend analysis
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">File Requirements</h4>
                <ul className="text-sm text-gray-600 space-y-2">
                  <li>• <strong>Format:</strong> CSV files only (.csv extension)</li>
                  <li>• <strong>Encoding:</strong> UTF-8 (handles international characters)</li>
                  <li>• <strong>Size Limit:</strong> Maximum 50MB per file</li>
                  <li>• <strong>Headers:</strong> First row must contain column names</li>
                  <li>• <strong>Text Content:</strong> Enclose text with quotes if it contains commas or newlines</li>
                  <li>• <strong>Empty Values:</strong> Empty cells in optional columns are fine, but required columns should not be empty</li>
                </ul>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">Common Issues & Solutions</h4>
                <div className="space-y-3">
                  <div className="bg-red-50 p-3 rounded-md border border-red-200">
                    <h5 className="font-semibold text-sm text-red-700 mb-1">Missing Required Columns</h5>
                    <p className="text-xs text-red-600">Ensure your CSV has both "Tweet" and "Datetime" columns with exact spelling</p>
                  </div>
                  <div className="bg-orange-50 p-3 rounded-md border border-orange-200">
                    <h5 className="font-semibold text-sm text-orange-700 mb-1">Invalid Date Formats</h5>
                    <p className="text-xs text-orange-600">Convert dates to YYYY-MM-DD format. Excel date formats may need conversion</p>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-md border border-purple-200">
                    <h5 className="font-semibold text-sm text-purple-700 mb-1">Text Encoding Issues</h5>
                    <p className="text-xs text-purple-600">Save as UTF-8 CSV to preserve emojis and special characters</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 bg-gray-50 rounded-b-lg border-t">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Got it!
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}