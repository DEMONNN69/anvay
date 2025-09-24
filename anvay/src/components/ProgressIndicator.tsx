import React from 'react';
import { Loader2 } from 'lucide-react';

interface ProgressIndicatorProps {
  message?: string;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  message = 'Processing image...'
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <div className="flex flex-col items-center space-y-4">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        <p className="text-lg font-medium text-gray-700">{message}</p>
        <div className="w-64 bg-gray-200 rounded-full h-2">
          <div className="bg-blue-500 h-2 rounded-full animate-pulse w-1/2"></div>
        </div>
        <p className="text-sm text-gray-500">
          Analyzing product compliance requirements...
        </p>
      </div>
    </div>
  );
};

export default ProgressIndicator;