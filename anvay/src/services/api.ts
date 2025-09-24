import { APIResponse, ComplianceResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_REACT_APP_API_URL || 'http://localhost:8000/api';

export const checkCompliance = async (file: File): Promise<APIResponse> => {
  try {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE_URL}/check-compliance/`, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type header, let browser set it for FormData
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Transform the API response to match our frontend types
    const complianceResult: ComplianceResult = {
      score: data.score || 0,
      extractedText: data.extracted_text || '',
      fields: data.fields || [
        { name: 'MRP', detected: false, icon: 'rupee' },
        { name: 'Net Quantity', detected: false, icon: 'package' },
        { name: 'Manufacturer', detected: false, icon: 'building' },
        { name: 'Country of Origin', detected: false, icon: 'globe' },
        { name: 'Manufacturing Date', detected: false, icon: 'calendar' },
      ],
      status: data.status || (data.score >= 60 ? 'pass' : data.score >= 40 ? 'partial' : 'fail')
    };

    return {
      success: true,
      data: complianceResult
    };
  } catch (error) {
    console.error('API Error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An error occurred'
    };
  }
};