import React, { useState } from 'react';
import toast from 'react-hot-toast';

interface VisualizationControlsProps {
  containerRef?: React.RefObject<HTMLDivElement | null>;
  url: string;
  title?: string;
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onExplain?: () => void;
}

const VisualizationControls: React.FC<VisualizationControlsProps> = ({
  containerRef,
  url,
  title = 'visualization',
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  onExplain,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const handleFullscreen = () => {
    const elem = containerRef?.current || document.querySelector('.visualization-container');
    if (!elem) return;
    
    if (!isFullscreen) {
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
      setIsFullscreen(false);
    }
  };
  
  const handleDownload = () => {
    try {
      // Create a temporary anchor element to trigger download
      const link = document.createElement('a');
      link.href = url;

      // Extract filename from URL or use a default name
      const urlParts = url.split('/');
      const filename = urlParts[urlParts.length - 1] || `${title || 'visualization'}.html`;

      // Set download attribute to force download instead of navigation
      link.download = filename;

      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast.success(`Downloading ${filename}`);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback to opening in new tab
      window.open(url, '_blank');
      toast.error('Download failed, opening in new tab instead');
    }
  };
  
  const handleExplain = () => {
    if (onExplain) {
      onExplain();
    } else {
      // Default behavior - could send a message asking for explanation
      toast('Ask in chat for an explanation of this visualization');
    }
  };
  
  const handlePrevPage = () => {
    if (currentPage > 1 && onPageChange) {
      onPageChange(currentPage - 1);
    }
  };
  
  const handleNextPage = () => {
    if (currentPage < totalPages && onPageChange) {
      onPageChange(currentPage + 1);
    }
  };
  
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200 rounded-t-lg">
      <div className="flex items-center space-x-2">
        <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 6a1 1 0 011-1h12a1 1 0 011 1v5a1 1 0 01-1 1H4a1 1 0 01-1-1v-5z" clipRule="evenodd" />
        </svg>
        <h4 className="text-sm font-medium text-gray-900">
          {title.charAt(0).toUpperCase() + title.slice(1)}
        </h4>
      </div>
      
      <div className="flex items-center space-x-2">
        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center space-x-1 mr-2 px-2 py-1 bg-white rounded border border-gray-200">
            <button
              onClick={handlePrevPage}
              disabled={currentPage <= 1}
              className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              title="Previous page"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            <span className="px-2 text-xs text-gray-600">
              {currentPage} / {totalPages}
            </span>
            
            <button
              onClick={handleNextPage}
              disabled={currentPage >= totalPages}
              className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              title="Next page"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
        
        {/* Explain button with purple sparkle style */}
        <button
          onClick={handleExplain}
          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors flex items-center gap-1 text-sm font-medium"
          title="Explain this visualization"
        >
          <span>✨</span>
          <span>Explain</span>
        </button>
        
        <button
          onClick={handleFullscreen}
          className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-white rounded transition-colors"
          title="View fullscreen"
        >
          {isFullscreen ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </button>
        
        <button
          onClick={handleDownload}
          className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-white rounded transition-colors"
          title="Download visualization"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default VisualizationControls;