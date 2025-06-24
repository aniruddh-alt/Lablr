'use client';

import { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Brain, 
  Settings, 
  Download, 
  Play, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  Plus,
  Eye
} from 'lucide-react';
import apiService, { Document, ExtractionJob } from '@/lib/api';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'upload' | 'extract' | 'jobs'>('upload');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [jobs, setJobs] = useState<ExtractionJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // File upload state
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Extraction job state
  const [jobName, setJobName] = useState('');
  const [extractionType, setExtractionType] = useState('structured_data');
  const [outputFormat, setOutputFormat] = useState('csv');
  const [prompt, setPrompt] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);

  // Load data on component mount
  useEffect(() => {
    loadDocuments();
    loadJobs();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await apiService.getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadJobs = async () => {
    try {
      const jobsData = await apiService.getJobs();
      setJobs(jobsData);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    setLoading(true);
    setUploadProgress(0);

    try {
      await apiService.uploadDocuments(files, (progress) => {
        setUploadProgress(progress);
      });

      console.log('Upload successful');
      await loadDocuments();
      setSelectedFiles(null);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files);
    }
  };

  const createExtractionJob = async () => {
    if (!jobName || !prompt || selectedDocuments.length === 0) {
      alert('Please fill in all required fields and select documents');
      return;
    }

    setLoading(true);
    try {
      const jobConfig = {
        name: jobName,
        description: `Extraction job: ${extractionType}`,
        document_ids: selectedDocuments,
        extraction_type: extractionType,
        output_format: outputFormat,
        prompt: prompt,
        batch_size: 5,
      };

      const job = await apiService.createJob(jobConfig);
      console.log('Job created:', job);
      
      // Reset form
      setJobName('');
      setPrompt('');
      setSelectedDocuments([]);
      
      await loadJobs();
    } catch (error) {
      console.error('Failed to create job:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
      case 'started':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-blue-600" />
              <h1 className="ml-3 text-2xl font-bold text-gray-900">Lablr</h1>
              <span className="ml-2 text-sm text-gray-500">PDF Data Labeling</span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="p-2 text-gray-400 hover:text-gray-500">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'upload', label: 'Upload PDFs', icon: Upload },
              { id: 'extract', label: 'Create Extraction Job', icon: Brain },
              { id: 'jobs', label: 'View Jobs', icon: Eye },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                                 onClick={() => setActiveTab(id as 'upload' | 'extract' | 'jobs')}
                className={`${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload PDF Documents</h2>
              
              {/* File Drop Zone */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center ${
                  dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                }`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg text-gray-600 mb-2">
                  Drop PDF files here or click to select
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Supports multiple files up to 50MB each
                </p>
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Select Files
                </label>
              </div>

              {/* Selected Files */}
              {selectedFiles && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Selected Files:</h3>
                  <div className="space-y-2">
                    {Array.from(selectedFiles).map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm text-gray-600">{file.name}</span>
                        <span className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => handleFileUpload(selectedFiles)}
                    disabled={loading}
                    className="mt-4 w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Uploading... {uploadProgress}%
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Files
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>

            {/* Documents List */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Uploaded Documents</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {documents.map((doc) => (
                  <div key={doc.id} className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(doc.status)}
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                        <p className="text-sm text-gray-500">
                          Uploaded {new Date(doc.upload_timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      doc.status === 'processed' ? 'bg-green-100 text-green-800' :
                      doc.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                      doc.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                ))}
                {documents.length === 0 && (
                  <div className="px-6 py-8 text-center text-gray-500">
                    No documents uploaded yet
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'extract' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Create Extraction Job</h2>
            
            <div className="space-y-6">
              {/* Job Configuration */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job Name
                  </label>
                  <input
                    type="text"
                    value={jobName}
                    onChange={(e) => setJobName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Invoice Data Extraction"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Extraction Type
                  </label>
                  <select
                    value={extractionType}
                    onChange={(e) => setExtractionType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="structured_data">Structured Data</option>
                    <option value="qa_generation">Q&A Generation</option>
                    <option value="summarization">Summarization</option>
                    <option value="classification">Classification</option>
                    <option value="entity_extraction">Entity Extraction</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Output Format
                  </label>
                  <select
                    value={outputFormat}
                    onChange={(e) => setOutputFormat(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="csv">CSV</option>
                    <option value="json">JSON</option>
                    <option value="xlsx">Excel</option>
                    <option value="qa_pairs">Q&A Pairs</option>
                  </select>
                </div>
              </div>

              {/* Extraction Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Extraction Prompt
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Describe what data you want to extract from the documents..."
                />
              </div>

              {/* Document Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Documents
                </label>
                <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-md">
                  {documents.filter(doc => doc.status === 'processed').map((doc) => (
                    <label key={doc.id} className="flex items-center px-3 py-2 hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={selectedDocuments.includes(doc.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDocuments([...selectedDocuments, doc.id]);
                          } else {
                            setSelectedDocuments(selectedDocuments.filter(id => id !== doc.id));
                          }
                        }}
                        className="mr-3"
                      />
                      <span className="text-sm text-gray-900">{doc.filename}</span>
                    </label>
                  ))}
                  {documents.filter(doc => doc.status === 'processed').length === 0 && (
                    <div className="px-3 py-4 text-center text-gray-500 text-sm">
                      No processed documents available
                    </div>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={createExtractionJob}
                disabled={loading || !jobName || !prompt || selectedDocuments.length === 0}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating Job...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Create Extraction Job
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Extraction Jobs</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {jobs.map((job) => (
                <div key={job.id} className="px-6 py-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{job.name}</h4>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        job.status === 'completed' ? 'bg-green-100 text-green-800' :
                        job.status === 'started' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {job.status}
                      </span>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>Type: {job.extraction_type} | Format: {job.output_format}</p>
                    <p>Documents: {job.document_ids.length} | Created: {new Date(job.created_at).toLocaleString()}</p>
                  </div>
                  {job.status === 'completed' && (
                    <button className="mt-2 inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-xs font-medium text-gray-700 bg-white hover:bg-gray-50">
                      <Download className="h-3 w-3 mr-1" />
                      Download Results
                    </button>
                  )}
                </div>
              ))}
              {jobs.length === 0 && (
                <div className="px-6 py-8 text-center text-gray-500">
                  No extraction jobs created yet
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
