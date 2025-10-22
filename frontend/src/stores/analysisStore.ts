import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface UploadedFile {
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
}

export interface AnalysisResult {
  id: string;
  type: string;
  data: any;
  visualizations?: string[];
  timestamp: Date;
}

export interface Variable {
  name: string;
  description?: string;
  type: 'numeric' | 'categorical';
  selected: boolean;
}

interface AnalysisState {
  // File management
  uploadedFiles: UploadedFile[];
  csvFile: File | null;
  shapeFile: File | null;
  
  // Analysis state
  isAnalyzing: boolean;
  analysisProgress: number;
  currentStep: string;
  analysisResults: AnalysisResult[];
  
  // Variables
  availableVariables: Variable[];
  selectedVariables: string[];
  
  // Data analysis mode
  dataAnalysisMode: boolean;
  tprMode: boolean;
  
  // Actions - File management
  addFile: (file: UploadedFile) => void;
  updateFileStatus: (fileName: string, status: UploadedFile['status'], progress?: number) => void;
  setCsvFile: (file: File | null) => void;
  setShapeFile: (file: File | null) => void;
  clearFiles: () => void;
  
  // Actions - Analysis
  setAnalyzing: (analyzing: boolean) => void;
  setAnalysisProgress: (progress: number) => void;
  setCurrentStep: (step: string) => void;
  addAnalysisResult: (result: AnalysisResult) => void;
  clearAnalysisResults: () => void;
  
  // Actions - Variables
  setAvailableVariables: (variables: Variable[]) => void;
  toggleVariable: (variableName: string) => void;
  setSelectedVariables: (variables: string[]) => void;
  
  // Actions - Modes
  setDataAnalysisMode: (enabled: boolean) => void;
  setTprMode: (enabled: boolean) => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  devtools(
    (set) => ({
      // Initial state
      uploadedFiles: [],
      csvFile: null,
      shapeFile: null,
      isAnalyzing: false,
      analysisProgress: 0,
      currentStep: '',
      analysisResults: [],
      availableVariables: [],
      selectedVariables: [],
      dataAnalysisMode: false,
      tprMode: false,
      
      // File management actions
      addFile: (file) =>
        set((state) => ({
          uploadedFiles: [...state.uploadedFiles, file],
        })),
      
      updateFileStatus: (fileName, status, progress) =>
        set((state) => ({
          uploadedFiles: state.uploadedFiles.map((file) =>
            file.name === fileName
              ? { ...file, status, progress: progress ?? file.progress }
              : file
          ),
        })),
      
      setCsvFile: (file) =>
        set({ csvFile: file }),
      
      setShapeFile: (file) =>
        set({ shapeFile: file }),
      
      clearFiles: () =>
        set({
          uploadedFiles: [],
          csvFile: null,
          shapeFile: null,
        }),
      
      // Analysis actions
      setAnalyzing: (analyzing) =>
        set({ isAnalyzing: analyzing }),
      
      setAnalysisProgress: (progress) =>
        set({ analysisProgress: progress }),
      
      setCurrentStep: (step) =>
        set({ currentStep: step }),
      
      addAnalysisResult: (result) =>
        set((state) => ({
          analysisResults: [...state.analysisResults, result],
        })),
      
      clearAnalysisResults: () =>
        set({ analysisResults: [] }),
      
      // Variable actions
      setAvailableVariables: (variables) =>
        set({
          availableVariables: variables,
          selectedVariables: variables
            .filter((v) => v.selected)
            .map((v) => v.name),
        }),
      
      toggleVariable: (variableName) =>
        set((state) => {
          const variables = state.availableVariables.map((v) =>
            v.name === variableName ? { ...v, selected: !v.selected } : v
          );
          return {
            availableVariables: variables,
            selectedVariables: variables
              .filter((v) => v.selected)
              .map((v) => v.name),
          };
        }),
      
      setSelectedVariables: (variables) =>
        set((state) => ({
          selectedVariables: variables,
          availableVariables: state.availableVariables.map((v) => ({
            ...v,
            selected: variables.includes(v.name),
          })),
        })),
      
      // Mode actions
      setDataAnalysisMode: (enabled) =>
        set({ dataAnalysisMode: enabled }),
      
      setTprMode: (enabled) =>
        set({ tprMode: enabled }),
    }),
    {
      name: 'analysis-store',
    }
  )
);