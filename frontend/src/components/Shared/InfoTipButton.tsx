import React, { useEffect, useRef, useState } from 'react';

interface InfoTipButtonProps {
  text: string;
  position?: 'auto' | 'above' | 'below';
  label?: string;
}

const InfoTipButton: React.FC<InfoTipButtonProps> = ({ text, position = 'auto', label = 'Learn' }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!ref.current) return;
      if (!ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  return (
    <div ref={ref} className="inline-block relative align-middle">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="ml-2 inline-flex items-center justify-center px-2.5 py-1 rounded border border-blue-500 text-blue-700 bg-white hover:bg-blue-50 text-xs font-medium"
        aria-label="Learn"
        title="Learn"
      >
        {label}
      </button>
      {open && (
        <div
          className="absolute z-50 mt-2 p-3 bg-gray-900 text-white text-xs rounded shadow max-w-xs"
          style={{
            top: position === 'above' ? -8 : undefined,
          }}
        >
          {text}
        </div>
      )}
    </div>
  );
};

export default InfoTipButton;
