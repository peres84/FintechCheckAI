# FinTech Check AI

An AI-powered financial fact-checking application that analyzes video content against official documents to verify claims.

## 🎯 Overview

FinTech Check AI is a frontend shell built with React + TypeScript that provides the complete user interface for a financial fact-checking service. The application allows users to submit YouTube videos containing financial claims, and then displays AI-generated fact-check results with evidence from official documents.

### Key Features

- **YouTube Video Analysis**: Submit any YouTube URL for fact-checking
- **PDF Document Support**: Upload reference documents for additional verification
- **AI-Powered Fact-Checking**: Claims are extracted and verified against official sources
- **Credibility Scoring**: Overall credibility score with detailed claim-by-claim breakdown
- **Follow-up Chat**: Interactive chat to ask questions about the analysis results
- **Dark/Light Mode**: Full theme support with earth-tone color palette

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (This Shell)                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Landing Page → Analyze Page → Loading → Results Page + Chat            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API SERVICE LAYER                               │
│                     (src/services/api.ts)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  extractTranscript() │ extractPdfContent() │ queryRAG() │ factCheck()  │
│                      │       chatWithAgent()                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ YouTube   │   │   Tower   │   │  OpenAI   │
            │ Transcript│   │    RAG    │   │   Agent   │
            │    API    │   │  Instance │   │           │
            └───────────┘   └───────────┘   └───────────┘
                    │
                    ▼ (fallback)
            ┌───────────┐
            │  RunPod   │
            │  Whisper  │
            └───────────┘
```

### Data Flow

1. **User submits content** (YouTube URL + optional PDF)
2. **Transcript extraction**: 
   - Primary: YouTube Transcript API
   - Fallback: Download audio → ImageKit upload → RunPod Whisper → Delete audio
3. **Document retrieval**: Query Tower RAG instance for official documents
4. **AI analysis**: OpenAI agent cross-references claims with retrieved documents
5. **Results display**: Credibility score + claim-by-claim breakdown
6. **Follow-up chat**: User can ask deeper questions about the analysis

## 📁 Project Structure

```
src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   ├── ClaimCard.tsx          # Individual fact-check result display
│   ├── CredibilityScore.tsx   # Visual score indicator (circular)
│   ├── FollowUpChat.tsx       # Chat interface for follow-up questions
│   ├── Footer.tsx             # Site footer
│   ├── LoadingAnalysis.tsx    # Processing state with step indicators
│   ├── Navbar.tsx             # Navigation header with theme toggle
│   ├── PDFUploader.tsx        # Drag-and-drop PDF upload
│   ├── ThemeProvider.tsx      # Dark/light mode context
│   ├── ThemeToggle.tsx        # Theme switcher dropdown
│   └── YouTubeInput.tsx       # URL input with validation
├── pages/
│   ├── Landing.tsx            # Homepage with hero and features
│   ├── Analyze.tsx            # Content input page
│   ├── Results.tsx            # Fact-check results display
│   └── NotFound.tsx           # 404 page
├── services/
│   └── api.ts                 # API integration layer (⚠️ INTEGRATE HERE)
├── hooks/
│   └── use-toast.ts           # Toast notifications
├── lib/
│   └── utils.ts               # Utility functions
└── App.tsx                    # Main app with routing
```

## 🔌 API Integration Guide

The `src/services/api.ts` file contains all placeholder functions that need to be connected to your backend services. Each function includes:

- TypeScript interfaces for request/response types
- Documentation for expected endpoint behavior
- Mock implementation for development

### Functions to Integrate

#### 1. `extractTranscript(youtubeUrl: string): Promise<TranscriptResult>`

**Purpose**: Extract transcript from YouTube video

**Your API should**:
1. First attempt YouTube Transcript API
2. If unavailable, fallback to:
   - Download audio
   - Convert to .wav
   - Upload to ImageKit
   - Send to RunPod Whisper
   - Delete uploaded audio

**Expected endpoint**: `POST /api/extract-transcript`

```typescript
// Request
{ url: string }

// Response
{
  success: boolean;
  transcript: string;
  segments: Array<{ text: string; start: number; duration: number }>;
  source: 'youtube-api' | 'whisper-fallback';
  videoTitle?: string;
  channelName?: string;
  error?: string;
}
```

#### 2. `extractPdfContent(file: File): Promise<PDFExtractionResult>`

**Purpose**: Extract text content from uploaded PDF

**Expected endpoint**: `POST /api/extract-pdf` (FormData)

```typescript
// Response
{
  success: boolean;
  content: string;
  pageCount: number;
  metadata?: { title?: string; author?: string; creationDate?: string };
  error?: string;
}
```

#### 3. `queryRAG(query: string): Promise<RAGQueryResult>`

**Purpose**: Query Tower RAG instance for relevant official documents

**Expected endpoint**: `POST /api/rag/query`

```typescript
// Request
{ query: string, limit?: number }

// Response
{
  success: boolean;
  documents: Array<{
    content: string;
    source: string;
    relevanceScore: number;
    hash: string;  // Immutable document hash
  }>;
  error?: string;
}
```

#### 4. `factCheck(transcript, ragData, pdfContent?): Promise<FactCheckResult>`

**Purpose**: Run AI fact-checking analysis

**Expected endpoint**: `POST /api/fact-check`

```typescript
// Request
{
  transcript: string;
  documents: RAGDocument[];
  pdfContent?: string;
}

// Response
{
  success: boolean;
  overallScore: number;  // 0-100
  claims: Array<{
    id: string;
    text: string;
    verdict: 'true' | 'false' | 'partial' | 'unverifiable';
    confidence: number;
    evidence: Array<{ source: string; excerpt: string; supportLevel: string }>;
    explanation: string;
    timestamp?: string;
  }>;
  summary: string;
  analyzedAt: string;
  error?: string;
}
```

#### 5. `chatWithAgent(message, context): Promise<ChatResponse>`

**Purpose**: Follow-up conversation about results

**Expected endpoint**: `POST /api/chat`

```typescript
// Request
{
  message: string;
  context: {
    analysisId?: string;
    factCheckResult?: FactCheckResult;
    chatHistory: ChatMessage[];
  }
}

// Response
{
  success: boolean;
  message: string;
  error?: string;
}
```

## 🎨 Design System

The application uses a warm earth-tone color palette with full dark mode support.

### Color Tokens (defined in `src/index.css`)

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--primary` | Warm brown | Light brown | Buttons, links |
| `--secondary` | Tan/sand | Muted tan | Secondary elements |
| `--accent` | Olive green | Sage green | Highlights, icons |
| `--muted` | Light cream | Dark earth | Backgrounds |
| `--success` | Forest green | Green | True verdicts |
| `--warning` | Amber | Amber | Partial verdicts |
| `--destructive` | Muted red | Red | False verdicts |

### Verdict Colors

- **True**: `text-success` / `bg-success/10`
- **False**: `text-destructive` / `bg-destructive/10`
- **Partial**: `text-warning` / `bg-warning/10`
- **Unverifiable**: `text-muted-foreground` / `bg-muted`

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Your backend APIs running (or use mock mode)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fintech-check-ai

# Install dependencies
npm install
# or
bun install

# Start development server
npm run dev
# or
bun dev
```

### Environment Variables

Create a `.env` file if needed for your API endpoints:

```env
# Optional: Override API base URL
VITE_API_BASE_URL=https://your-api.com
```

### Development Mode

The application runs in mock mode by default. All API functions in `src/services/api.ts` have mock implementations that return realistic fake data with simulated delays.

To integrate with real APIs, replace the mock implementations with actual `fetch` calls.

## 📝 Customization

### Adding New Verdict Types

1. Update the `VerdictType` in `src/services/api.ts`
2. Add color mappings in `getVerdictColor()`, `getVerdictBgColor()`, `getVerdictLabel()`
3. Add icon in `ClaimCard.tsx` verdictIcons object

### Modifying the Color Scheme

Edit `src/index.css` to change the HSL values for any color token. The design system automatically propagates changes through both light and dark modes.

### Adding New Pages

1. Create a new page component in `src/pages/`
2. Add the route in `src/App.tsx`
3. Update navigation in `src/components/Navbar.tsx`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

[Your License Here]

---

Built with ❤️ using React, TypeScript, Tailwind CSS, and shadcn/ui
