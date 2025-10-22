import React, { useEffect, useMemo, useState } from 'react';

type Step = {
  id: string;
  title: string;
  text: string;
  target: string; // CSS selector for [data-tour-id]
  cta?: string;
};

interface TourOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onCompleted?: () => void;
}

const DEFAULT_STEPS: Step[] = [
  {
    id: 'about',
    title: 'What is ChatMRPT?',
    text: 'ChatMRPT is an AI assistant for malaria and public health. It answers questions and runs analyses like TPR, risk profiling, vulnerability maps, and ITN (bed net) planning.',
    target: '[data-tour-id="chat-input"]',
    cta: 'Next',
  },
  {
    id: 'tpr',
    title: 'TPR Workflow',
    text: 'Test Positivity Rate (TPR) analysis examines facility testing outcomes by age groups and levels, preparing inputs for risk analysis.',
    target: '[data-tour-id="chat-input"]',
    cta: 'Next',
  },
  {
    id: 'risk',
    title: 'Risk Analysis',
    text: 'Risk analysis (composite and PCA) ranks wards by vulnerability using uploaded indicators and TPR, producing ranked tables and downloadable outputs.',
    target: '[data-tour-id="chat-input"]',
    cta: 'Next',
  },
  {
    id: 'maps',
    title: 'Vulnerability Maps',
    text: 'Interactive vulnerability maps visualize high‑risk areas, supporting communication and decision‑making.',
    target: '[data-tour-id="chat-input"]',
    cta: 'Next',
  },
  {
    id: 'itn',
    title: 'ITN Planning',
    text: 'ITN (bed net) planning allocates nets optimally based on risk rankings and parameters, producing an ITN map and exportable results.',
    target: '[data-tour-id="chat-input"]',
    cta: 'Next',
  },
  {
    id: 'arena',
    title: 'Arena Comparisons',
    text: 'Arena compares models side‑by‑side for the same question. Winner stays left; labels progress A → C → D (GPT‑4o appears in the final round).',
    target: '[data-tour-id="arena-panel"]',
    cta: 'Next',
  },
  {
    id: 'export',
    title: 'Exports & Reports',
    text: 'You can export chat history, analysis outputs, and comprehensive reports for sharing with stakeholders.',
    target: '[data-tour-id="export"]',
    cta: 'Finish',
  },
];

const TourOverlay: React.FC<TourOverlayProps> = ({ isOpen, onClose, onCompleted }) => {
  const [index, setIndex] = useState(0);
  const steps = useMemo(() => DEFAULT_STEPS, []);
  const step = steps[index];

  useEffect(() => {
    if (!isOpen) return;
    const el = document.querySelector(step?.target || '') as HTMLElement | null;
    if (el && 'scrollIntoView' in el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    }
  }, [isOpen, index, step]);

  if (!isOpen || !step) return null;

  const targetEl = document.querySelector(step.target) as HTMLElement | null;
  const rect = targetEl?.getBoundingClientRect();

  const next = () => {
    if (index < steps.length - 1) setIndex(index + 1);
    else {
      try { localStorage.setItem('chatmrpt_tour_completed', '1'); } catch {}
      onCompleted?.();
      onClose();
    }
  };
  const prev = () => setIndex(Math.max(0, index - 1));

  const spotlightStyle: React.CSSProperties | undefined = rect
    ? {
        position: 'absolute',
        top: rect.top + window.scrollY - 8,
        left: rect.left + window.scrollX - 8,
        width: rect.width + 16,
        height: rect.height + 16,
        border: '2px solid #3B82F6',
        borderRadius: 8,
        boxShadow: '0 0 0 20000px rgba(0,0,0,0.3)',
        pointerEvents: 'none',
        transition: 'all 0.2s ease',
      }
    : undefined;

  const popoverStyle: React.CSSProperties = rect
    ? {
        position: 'absolute',
        top: rect.bottom + window.scrollY + 12,
        left: rect.left + window.scrollX,
        maxWidth: 360,
      }
    : { position: 'absolute', top: window.scrollY + 100, left: window.scrollX + 100 };

  return (
    <div className="fixed inset-0 z-[9999]">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-40" onClick={onClose} />

      {/* Spotlight */}
      {spotlightStyle && <div style={spotlightStyle} />}

      {/* Popover */}
      <div className="bg-white rounded-lg shadow-xl p-4 border border-gray-200" style={popoverStyle}>
        <div className="text-sm font-semibold text-gray-900 mb-1">{step.title}</div>
        <div className="text-sm text-gray-700 mb-3">{step.text}</div>
        <div className="flex items-center justify-between">
          <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-700">Skip tour</button>
          <div className="space-x-2">
            <button onClick={prev} disabled={index === 0} className="px-3 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50">Back</button>
            <button onClick={next} className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">{step.cta || 'Next'}</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TourOverlay;
