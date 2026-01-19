// Message Types
export type MessageType = 'regular' | 'arena' | 'system' | 'clarification';

export interface BaseMessage {
  id: string;
  timestamp: Date;
  sessionId: string;
}

export interface DownloadLink {
  url: string;
  filename: string;
  description: string;
  type: 'csv' | 'html' | 'pdf' | 'zip';
}

export interface RegularMessage extends BaseMessage {
  type: 'regular';
  sender: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  visualizations?: any[]; // For data analysis visualizations
  downloadLinks?: DownloadLink[]; // For downloadable documents
  metadata?: {
    model?: string;
    latency?: number;
    tokens?: number;
    analysisResults?: {
      pca?: {
        score: number;
        ranking: number;
        totalRanked: number;
        indicators?: string[];
      };
      composite?: {
        score: number;
        ranking: number;
        totalRanked: number;
        indicators?: string[];
      };
      ward?: string;
      state?: string;
    };
  };
}

export interface ArenaMessage extends BaseMessage {
  type: 'arena';
  battleId: string;
  userMessage: string;
  round: number;
  currentMatchup: {
    modelA: ModelName;
    modelB: ModelName;
    responseA: string;
    responseB: string;
  };
  eliminatedModels: ModelName[];
  winnerChain: ModelName[];
  remainingModels: ModelName[];
  currentVote?: Vote;
  modelsRevealed: boolean;
  isComplete: boolean;
}

export interface SystemMessage extends BaseMessage {
  type: 'system';
  content: string;
  severity?: 'info' | 'warning' | 'error';
}

export interface ClarificationOption {
  id: string;
  label: string;
  icon: string;
  value: string;
}

export interface ClarificationMessage extends BaseMessage {
  type: 'clarification';
  sender: 'assistant';
  content: string;
  options: ClarificationOption[];
  originalMessage?: string;
}

export type Message = RegularMessage | ArenaMessage | SystemMessage | ClarificationMessage;

// Arena Types - Updated to match backend models
export type ModelName = 
  | 'mistral:7b'
  | 'llama3.1:8b'
  | 'qwen3:8b'
  | 'gpt-4o';

export type ModelResponses = {
  [K in ModelName]: string;
};

export type Vote = 'a' | 'b' | 'tie' | 'bad';

// Arena uses progressive elimination tournament system

// Model display names
export const MODEL_DISPLAY_NAMES: Record<ModelName, string> = {
  'mistral:7b': 'Mistral 7B',
  'llama3.1:8b': 'Llama 3.1 8B',
  'qwen3:8b': 'Qwen 3 8B',
  'gpt-4o': 'GPT-4o',
};

// Session Types
export interface SessionData {
  sessionId: string;
  startTime: Date;
  messageCount: number;
  hasUploadedFiles: boolean;
  conversationId?: string;
  uploadedFiles?: {
    csv?: string;
    shapefile?: string;
  };
}

// API Response Types
export interface StreamChunk {
  type: 'start' | 'content' | 'arena_response' | 'complete' | 'error';
  content?: string;
  arenaData?: {
    battleId: string;
    responses: ModelResponses;
  };
  error?: string;
}

// File Upload Types
export interface UploadedFile {
  name: string;
  size: number;
  type: string;
  uploadTime: Date;
}
