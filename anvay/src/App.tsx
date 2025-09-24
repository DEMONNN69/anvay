import React, { useState } from 'react';
import { Scale, AlertTriangle } from 'lucide-react';
import FileUpload from './components/FileUpload';
import ImagePreview from './components/ImagePreview';
import ProgressIndicator from './components/ProgressIndicator';
import ComplianceResults from './components/ComplianceResults';
import { checkCompliance } from './services/api';
import { ComplianceResult } from './types';

type AppState = 'upload' | 'preview' | 'processing' | 'results' | 'error';

function App() {
  const [state, setState] = useState<AppState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [error, setError] = useState<string>('');

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setState('preview');
    setError('');
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setState('upload');
    setResult(null);
    setError('');
  };

  const handleCheckCompliance = async () => {
    if (!selectedFile) return;

    setState('processing');
    setError('');

    const response = await checkCompliance(selectedFile);

    if (response.success && response.data) {
      setResult(response.data);
      setState('results');
    } else {
      setError(response.error || 'Failed to check compliance');
      setState('error');
    }
  };

  const handleCheckAnother = () => {
    setSelectedFile(null);
    setResult(null);
    setError('');
    setState('upload');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-3">
            <Scale className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Legal Metrology Compliance Checker
              </h1>
              <p className="text-sm text-gray-600">
                AI-powered product label compliance verification
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Upload & Preview */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Upload Product Image
              </h2>
              <FileUpload
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
                onClearFile={handleClearFile}
                disabled={state === 'processing'}
              />
              
              {(state === 'preview' || state === 'results') && (
                <div className="mt-6">
                  <button
                    onClick={handleCheckCompliance}
                    disabled={state === 'processing' || !selectedFile}
                    className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {state === 'processing' ? 'Processing...' : 'Check Compliance'}
                  </button>
                </div>
              )}
            </div>

            {selectedFile && state !== 'processing' && (
              <ImagePreview file={selectedFile} />
            )}
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2">
            {state === 'upload' && (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <Scale className="w-16 h-16 text-blue-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Welcome to Compliance Checker
                </h3>
                <p className="text-gray-600 mb-6">
                  Upload a product image to check its compliance with Legal Metrology requirements.
                  Our AI will analyze the label and verify required fields.
                </p>
                <div className="text-left max-w-md mx-auto">
                  <h4 className="font-semibold text-gray-800 mb-3">Required Fields:</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span>Maximum Retail Price (MRP)</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span>Net Quantity</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span>Manufacturer Details</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span>Country of Origin</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span>Manufacturing Date</span>
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {state === 'processing' && <ProgressIndicator />}

            {state === 'results' && result && (
              <ComplianceResults
                result={result}
                onCheckAnother={handleCheckAnother}
              />
            )}

            {state === 'error' && (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <AlertTriangle className="w-16 h-16 text-red-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-red-700 mb-2">
                  Processing Error
                </h3>
                <p className="text-gray-600 mb-6">{error}</p>
                <button
                  onClick={handleCheckAnother}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-500 text-sm">
            AI-Powered Legal Metrology Compliance Checker | 
            Ensuring product label compliance with regulatory standards
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;