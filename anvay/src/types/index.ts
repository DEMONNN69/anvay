export interface ComplianceField {
  name: string;
  detected: boolean;
  value?: string;
  icon: string;
}

export interface ComplianceResult {
  score: number;
  extractedText: string;
  fields: ComplianceField[];
  status: 'pass' | 'partial' | 'fail';
}

export interface APIResponse {
  success: boolean;
  data?: ComplianceResult;
  error?: string;
}