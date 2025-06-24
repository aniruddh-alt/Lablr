# Lablr Frontend

A modern Next.js frontend for the Lablr PDF data labeling system.

## Features

- 📄 **PDF Upload**: Drag-and-drop or click to upload multiple PDF documents
- 🧠 **Smart Extraction**: Create custom extraction jobs with AI-powered prompts
- ⚡ **Real-time Monitoring**: Track job progress and status updates
- 📊 **Multiple Formats**: Export results as CSV, JSON, Excel, or Q&A pairs
- 🎨 **Modern UI**: Clean, responsive design built with Tailwind CSS

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons
- **Axios** - HTTP client for API communication

## Getting Started

### Prerequisites

- Node.js 18.17.0 or later
- npm or yarn
- Lablr backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Update environment variables:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

### 1. Upload PDFs
- Navigate to the "Upload PDFs" tab
- Drag and drop PDF files or click to select
- Monitor upload progress
- View uploaded documents and their processing status

### 2. Create Extraction Jobs
- Go to "Create Extraction Job" tab
- Configure job settings:
  - **Job Name**: Descriptive name for your extraction task
  - **Extraction Type**: Choose from structured data, Q&A generation, summarization, etc.
  - **Output Format**: Select CSV, JSON, Excel, or Q&A pairs
  - **Prompt**: Describe what data you want to extract
- Select processed documents
- Submit the job

### 3. Monitor Jobs
- Switch to "View Jobs" tab
- Track job status and progress
- Download completed results
- View job details and error messages

## Configuration

The frontend can be configured through environment variables:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Custom polling intervals, file size limits, etc.
```

## API Integration

The frontend communicates with the Lablr backend API:

- `GET /documents` - List documents
- `POST /documents/upload/bulk` - Upload PDFs
- `GET /extraction/jobs` - List extraction jobs
- `POST /extraction/jobs` - Create new job
- `GET /extraction/jobs/{id}` - Get job details
- `GET /extraction/jobs/{id}/download` - Download results

## Development

### Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

### Project Structure

```
src/
├── app/                 # Next.js App Router pages
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Main dashboard
├── lib/                # Utilities and API layer
│   ├── api.ts         # API service functions
│   └── config.ts      # Configuration
└── components/         # Reusable React components
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Lablr PDF data labeling system.
