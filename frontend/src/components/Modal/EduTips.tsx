import React, { useEffect, useState } from 'react';

type Tip = { target: string; text: string; key: string };

const TIPS: Tip[] = [
  {
    target: '[data-edu-tip-chat] ',
    text: 'Ask about TPR, risk analysis, vulnerability maps, or ITN planning. ChatMRPT can guide you end‑to‑end.',
    key: 'tip_chat',
  },
  {
    target: '[data-edu-tip-upload] ',
    text: 'Upload CSV + shapefile to enable analyses and maps.',
    key: 'tip_upload',
  },
  {
    target: '[data-edu-tip-arena] ',
    text: 'Arena compares models for the same prompt. Winner stays left; labels A → C → D.',
    key: 'tip_arena',
  },
  {
    target: '[data-edu-tip-export] ',
    text: 'Export analysis outputs and reports for sharing with stakeholders.',
    key: 'tip_export',
  },
];

const EduTips: React.FC = () => {
  const [visible, setVisible] = useState<{ text: string; x: number; y: number } | null>(null);

  useEffect(() => {
    const handlers: Array<{ el: Element; enter: any; leave: any }> = [];
    TIPS.forEach((tip) => {
      const els = document.querySelectorAll(tip.target);
      els.forEach((el) => {
        const onEnter = (e: Event) => {
          const rect = (el as HTMLElement).getBoundingClientRect();
          setVisible({ text: tip.text, x: rect.left + window.scrollX, y: rect.bottom + window.scrollY + 8 });
        };
        const onLeave = () => setVisible(null);
        el.addEventListener('mouseenter', onEnter);
        el.addEventListener('mouseleave', onLeave);
        handlers.push({ el, enter: onEnter, leave: onLeave });
      });
    });
    return () => {
      handlers.forEach(({ el, enter, leave }) => {
        el.removeEventListener('mouseenter', enter);
        el.removeEventListener('mouseleave', leave);
      });
    };
  }, []);

  if (!visible) return null;
  return (
    <div
      className="absolute z-[9998] px-3 py-2 bg-gray-900 text-white text-xs rounded shadow"
      style={{ top: visible.y, left: visible.x, maxWidth: 280 }}
    >
      {visible.text}
    </div>
  );
};

export default EduTips;

