import React from 'react';

interface EducationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const Card: React.FC<{ icon: string; title: string; lines: string[] }> = ({ icon, title, lines }) => (
  <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
    <div className="flex items-start">
      <div className="mr-3 text-xl" aria-hidden>
        {icon}
      </div>
      <div>
        <div className="text-sm font-semibold text-gray-900 mb-1">{title}</div>
        <ul className="text-xs text-gray-600 space-y-1 list-disc list-inside">
          {lines.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      </div>
    </div>
  </div>
);

const EducationPanel: React.FC<EducationPanelProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[9998]">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative max-w-4xl mx-auto mt-16 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-gray-50">
          <div>
            <h3 className="text-base font-semibold text-gray-900">Learn about ChatMRPT</h3>
            <p className="text-xs text-gray-500">A concise overview of workflows and capabilities</p>
          </div>
          <button onClick={onClose} className="p-2 rounded hover:bg-gray-200" aria-label="Close">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-5 bg-white">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card
              icon="🧠"
              title="What is ChatMRPT?"
              lines={[
                'AI assistant for malaria & public health.',
                'Answers questions and runs analyses.',
              ]}
            />
            <Card
              icon="🧪"
              title="TPR Workflow"
              lines={[
                'Analyzes facility testing outcomes (age groups & levels).',
                'Prepares inputs for risk analysis.',
              ]}
            />
            <Card
              icon="📈"
              title="Risk Analysis"
              lines={[
                'Composite & PCA rank wards by vulnerability.',
                'Generates ranked outputs for decisions.',
              ]}
            />
            <Card
              icon="🗺️"
              title="Vulnerability Maps"
              lines={[
                'Interactive maps highlight high‑risk areas.',
                'Support communication & resource targeting.',
              ]}
            />
            <Card
              icon="🛏️"
              title="ITN Planning"
              lines={[
                'Allocates bed nets based on risk rankings & parameters.',
                'Produces an ITN map & exportable results.',
              ]}
            />
            <Card
              icon="⚖️"
              title="Arena"
              lines={[
                'Compares model responses side‑by‑side.',
                'Winner stays left; labels A → C → D (GPT‑4o final).',
              ]}
            />
            <Card
              icon="📦"
              title="Exports & Reports"
              lines={[
                'Export chat, analysis outputs, and reports.',
                'Share results with stakeholders easily.',
              ]}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EducationPanel;

