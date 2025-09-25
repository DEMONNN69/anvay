import { APIResponse, ComplianceResult } from '../types';

// Hardcoded for Codespaces presentation
const API_BASE_URL = 'https://musical-acorn-v6vw59v9vjv3rpx-8000.app.github.dev/api';

export const checkCompliance = async (file: File): Promise<APIResponse> => {
  try {
    console.log('Making API request to:', `${API_BASE_URL}/check-compliance/`);
    
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE_URL}/check-compliance/`, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type header, let browser set it for FormData
      },
    });

    console.log('Response status:', response.status);
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response error:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
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
    
    // More detailed error logging
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('Network error - check if backend is running and CORS is configured');
    }
    
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An error occurred'
    };
  }
};