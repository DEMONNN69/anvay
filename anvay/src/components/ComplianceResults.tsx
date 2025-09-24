import React from 'react';
import { 
  IndianRupee, 
  Package, 
  Building, 
  Globe, 
  Calendar,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { ComplianceResult } from '../types';

interface ComplianceResultsProps {
  result: ComplianceResult;
  onCheckAnother: () => void;
}

const ComplianceResults: React.FC<ComplianceResultsProps> = ({
  result,
  onCheckAnother
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 60) return 'text-green-600 bg-green-100';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreBorderColor = (score: number) => {
    if (score >= 60) return 'border-green-200';
    if (score >= 40) return 'border-yellow-200';
    return 'border-red-200';
  };

  const getStatusIcon = (score: number) => {
    if (score >= 60) return <CheckCircle className="w-6 h-6 text-green-500" />;
    if (score >= 40) return <AlertCircle className="w-6 h-6 text-yellow-500" />;
    return <XCircle className="w-6 h-6 text-red-500" />;
  };

  const getFieldIcon = (iconName: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'rupee': <IndianRupee className="w-5 h-5" />,
      'package': <Package className="w-5 h-5" />,
      'building': <Building className="w-5 h-5" />,
      'globe': <Globe className="w-5 h-5" />,
      'calendar': <Calendar className="w-5 h-5" />
    };
    return iconMap[iconName] || <Package className="w-5 h-5" />;
  };

  const detectedFields = result.fields.filter(field => field.detected);
  const missingFields = result.fields.filter(field => !field.detected);

  return (
    <div className="space-y-6">
      {/* Compliance Score */}
      <div className={`bg-white rounded-lg shadow-md border-l-4 ${getScoreBorderColor(result.score)}`}>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {getStatusIcon(result.score)}
              <div>
                <h3 className="text-xl font-bold text-gray-800">
                  Compliance Score
                </h3>
                <p className="text-gray-600">
                  {result.status === 'pass' && 'Compliant'}
                  {result.status === 'partial' && 'Partially Compliant'}
                  {result.status === 'fail' && 'Non-Compliant'}
                </p>
              </div>
            </div>
            <div className={`px-4 py-2 rounded-lg ${getScoreColor(result.score)}`}>
              <span className="text-2xl font-bold">{result.score}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Detected Fields */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-lg font-semibold text-green-700 flex items-center">
              <CheckCircle className="w-5 h-5 mr-2" />
              Detected Fields ({detectedFields.length})
            </h4>
          </div>
          <div className="p-4">
            {detectedFields.length > 0 ? (
              <div className="space-y-3">
                {detectedFields.map((field, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg"
                  >
                    <div className="text-green-600">
                      {getFieldIcon(field.icon)}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-800">{field.name}</p>
                      {field.value && (
                        <p className="text-sm text-gray-600">{field.value}</p>
                      )}
                    </div>
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">
                No fields detected
              </p>
            )}
          </div>
        </div>

        {/* Missing Fields */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-lg font-semibold text-red-700 flex items-center">
              <XCircle className="w-5 h-5 mr-2" />
              Missing Fields ({missingFields.length})
            </h4>
          </div>
          <div className="p-4">
            {missingFields.length > 0 ? (
              <div className="space-y-3">
                {missingFields.map((field, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-3 p-3 bg-red-50 rounded-lg"
                  >
                    <div className="text-red-600">
                      {getFieldIcon(field.icon)}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-800">{field.name}</p>
                      <p className="text-sm text-red-600">Required for compliance</p>
                    </div>
                    <XCircle className="w-4 h-4 text-red-500" />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">
                All required fields detected
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Extracted Text */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-4 border-b border-gray-200">
          <h4 className="text-lg font-semibold text-gray-800">Extracted Text</h4>
        </div>
        <div className="p-4">
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
              {result.extractedText || 'No text extracted'}
            </pre>
          </div>
        </div>
      </div>

      {/* Check Another Button */}
      <div className="text-center">
        <button
          onClick={onCheckAnother}
          className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Check Another Product
        </button>
      </div>
    </div>
  );
};

export default ComplianceResults;