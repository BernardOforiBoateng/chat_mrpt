import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';

interface AnalysisResult {
  id: string;
  type: string;
  data: any;
  timestamp: Date;
}

interface AnalysisState {
  csvFile: File | null;
  shapeFile: File | null;
  dataAnalysisMode: boolean;
  analysisResults: AnalysisResult[];
  setCsvFile: (file: File | null) => void;
  setShapeFile: (file: File | null) => void;
  setDataAnalysisMode: (mode: boolean) => void;
  addAnalysisResult: (result: AnalysisResult) => void;
  clearAnalysisResults: () => void;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  devtools(
    persist(
      (set) => ({
        csvFile: null,
        shapeFile: null,
        dataAnalysisMode: false,
        analysisResults: [],

        setCsvFile: (file) => set({ csvFile: file }),
        setShapeFile: (file) => set({ shapeFile: file }),
        setDataAnalysisMode: (mode) => set({ dataAnalysisMode: mode }),
        addAnalysisResult: (result) =>
          set((state) => ({ analysisResults: [...state.analysisResults, result] })),
        clearAnalysisResults: () => set({ analysisResults: [] }),
        reset: () =>
          set({
            csvFile: null,
            shapeFile: null,
            dataAnalysisMode: false,
            analysisResults: [],
          }),
      }),
      {
        name: 'analysis-storage',
        storage: createJSONStorage(() => sessionStorage),
        partialize: (state) => ({
          dataAnalysisMode: state.dataAnalysisMode,
          analysisResults: state.analysisResults.slice(-10),
        }),
      }
    )
  )
);

