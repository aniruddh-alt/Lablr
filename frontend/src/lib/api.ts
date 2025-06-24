import axios from 'axios';
import config from './config';

const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 30000,
});

// Types
export interface Document {
  id: string;
  filename: string;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
  upload_timestamp: string;
  job_id?: string;
}

export interface ExtractionJob {
  id: string;
  name: string;
  status: string;
  created_at: string;
  document_ids: string[];
  extraction_type: string;
  output_format: string;
  description?: string;
  prompt?: string;
  result_file_path?: string;
  error_message?: string;
}

export interface CreateJobRequest {
  name: string;
  description: string;
  document_ids: string[];
  extraction_type: string;
  output_format: string;
  prompt: string;
  batch_size?: number;
}

// API functions
export const apiService = {
  // Document operations
  getDocuments: async (): Promise<Document[]> => {
    const response = await api.get('/documents');
    return response.data;
  },

  uploadDocuments: async (
    files: FileList, 
    onProgress?: (progress: number) => void
  ): Promise<Document[]> => {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post('/documents/upload/bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },

  // Job operations
  getJobs: async (): Promise<ExtractionJob[]> => {
    const response = await api.get('/extraction/jobs');
    return response.data;
  },

  getJob: async (jobId: string): Promise<ExtractionJob> => {
    const response = await api.get(`/extraction/jobs/${jobId}`);
    return response.data;
  },

  createJob: async (jobConfig: CreateJobRequest): Promise<ExtractionJob> => {
    const response = await api.post('/extraction/jobs', jobConfig);
    return response.data;
  },

  deleteJob: async (jobId: string): Promise<void> => {
    await api.delete(`/extraction/jobs/${jobId}`);
  },

  downloadJobResults: async (jobId: string): Promise<Blob> => {
    const response = await api.get(`/extraction/jobs/${jobId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Single document extraction
  extractFromDocument: async (
    documentId: string,
    extractionType: string,
    outputFormat: string,
    prompt: string
  ): Promise<any> => {
    const response = await api.post('/extraction/single', {
      document_id: documentId,
      extraction_type: extractionType,
      output_format: outputFormat,
      prompt: prompt,
    });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default apiService; 