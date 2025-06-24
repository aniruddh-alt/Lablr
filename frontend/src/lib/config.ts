export const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  
  // Upload settings
  maxFileSize: 50 * 1024 * 1024, // 50MB
  allowedFileTypes: ['.pdf'],
  
  // Polling settings
  pollInterval: 2000, // 2 seconds
  
  // UI settings
  itemsPerPage: 10,
};

export default config; 