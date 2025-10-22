import React, { useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface QuickStartModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const QuickStartModal: React.FC<QuickStartModalProps> = ({ isOpen, onClose }) => {
  const session = useChatStore((s) => s.session);
  const setUploadedFiles = useChatStore((s) => s.setUploadedFiles);
  const [loadingSample, setLoadingSample] = useState(false);

  if (!isOpen) return null;

  const handleLoadSample = async () => {
    try {
      setLoadingSample(true);
      await api.upload.loadSampleData('kano', session.sessionId);
      setUploadedFiles('kano_sample.csv', 'kano_boundaries.zip');
      toast.success('Kano sample data loaded');
    } catch (e: any) {
      console.error('Load sample failed', e);
      toast.error('Failed to load sample data');
    } finally {
      setLoadingSample(false);
    }
  };

  const handleOpenUpload = () => {
    try {
      localStorage.setItem('chatmrpt_open_upload_modal', '1');
      toast('Opening upload…', { icon: '📂' });
      onClose();
    } catch {}
  };

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black bg-opacity-40" onClick={onClose} />
      <div className="relative mx-auto mt-24 w-full max-w-lg bg-white rounded-lg shadow-xl p-6">
        <div className="mb-4 flex items-center">
          <div className="w-10 h-10 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center mr-3">❓</div>
          <h3 className="text-lg font-semibold text-gray-900">Help & Quick Start</h3>
        </div>

        <div className="space-y-4 text-sm text-gray-700">
          <p>Get started in two ways:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li><strong>Load sample data</strong> to explore analyses and maps.</li>
            <li><strong>Upload your own CSV + shapefile</strong> to run a full workflow.</li>
          </ol>
        </div>

        <div className="mt-5 flex items-center justify-between gap-3">
          <button
            onClick={handleLoadSample}
            disabled={loadingSample}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loadingSample ? 'Loading…' : 'Load Kano Sample Data'}
          </button>
          <button
            onClick={handleOpenUpload}
            className="flex-1 px-4 py-2 bg-white text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Open Upload Dialog
          </button>
        </div>

        <div className="mt-3">
          <button
            onClick={() => { try { localStorage.setItem('chatmrpt_start_tour', '1'); } catch {}; onClose(); }}
            className="w-full px-4 py-2 bg-white text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-50"
          >
            Take a 60‑second tour
          </button>
        </div>

        <div className="mt-4 text-xs text-gray-500">
          Tip: You can also ask general questions (e.g., “What is ChatMRPT?”).
        </div>

        <div className="mt-4 flex justify-end">
          <button onClick={onClose} className="text-sm text-gray-600 hover:text-gray-800">Close</button>
        </div>
      </div>
    </div>
  );
};

export default QuickStartModal;
