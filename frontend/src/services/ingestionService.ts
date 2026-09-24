import { apiClient } from './apiClient';
import { StandardResponse } from '../types/api';

export interface IngestionResult {
  status: 'SUCCESS' | 'DUPLICATE' | 'FAILED';
  message: string;
  report_id?: string;
  filename?: string;
  detected_report_type?: string;
  final_report_type?: string;
  confidence_score?: number;
  report_date?: string;
  inserted_counts?: Record<string, number>;
  validation_warnings?: string[];
  existing_report?: {
    id: string;
    filename: string;
    report_type: string;
    report_date?: string;
    upload_timestamp: string;
  };
}

export interface FileStatusEntry {
  filename: string;
  status: 'PROCESSING' | 'SUCCESS' | 'DUPLICATE' | 'FAILED';
  message: string;
  report_type?: string;
  report_date?: string;
}

export interface JobStatusResult {
  job_id: string;
  status: 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_files: number;
  processed_count: number;
  success_count: number;
  failed_count: number;
  duplicate_count: number;
  progress_pct: number;
  created_at: string;
  file_statuses: FileStatusEntry[];
}

export interface ReportHistoryItem {
  id: string;
  filename: string;
  report_type: string;
  confidence_score: number;
  status: string;
  report_date?: string;
  upload_timestamp: string;
}

export const ingestionService = {
  async createIngestionJob(
    files: File[],
    reportTypeOverride?: string,
    dateOverride?: string,
    forceReplace: boolean = false
  ): Promise<{ job_id: string; total_files: number }> {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));

    if (reportTypeOverride) {
      formData.append('report_type_override', reportTypeOverride);
    }
    if (dateOverride) {
      formData.append('date_override', dateOverride);
    }
    if (forceReplace) {
      formData.append('force_replace', 'true');
    }

    const response = await apiClient.post<StandardResponse<{ job_id: string; total_files: number }>>(
      '/ingestion/upload-job',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    if (response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Job creation failed.');
  },

  async getJobStatus(jobId: string): Promise<JobStatusResult> {
    const response = await apiClient.get<StandardResponse<JobStatusResult>>(`/ingestion/job/${jobId}`);
    if (response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Failed to fetch job status.');
  },

  async uploadReport(
    file: File,
    reportTypeOverride?: string,
    dateOverride?: string,
    forceReplace: boolean = false
  ): Promise<IngestionResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (reportTypeOverride) {
      formData.append('report_type_override', reportTypeOverride);
    }
    if (dateOverride) {
      formData.append('date_override', dateOverride);
    }
    if (forceReplace) {
      formData.append('force_replace', 'true');
    }

    const response = await apiClient.post<StandardResponse<IngestionResult>>('/ingestion/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Upload failed.');
  },

  async getUploadHistory(): Promise<ReportHistoryItem[]> {
    try {
      const response = await apiClient.get<StandardResponse<ReportHistoryItem[]>>('/ingestion/history');
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      return [];
    } catch (err) {
      console.warn('Failed to load upload history:', err);
      return [];
    }
  },
};
