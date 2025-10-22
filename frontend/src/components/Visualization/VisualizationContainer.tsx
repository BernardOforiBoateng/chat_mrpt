import React, { useState, useEffect, useRef } from 'react';
import VisualizationFrame, { type VisualizationFrameHandle } from './VisualizationFrame';
import VisualizationControls from './VisualizationControls';
import useVisualization from '@/hooks/useVisualization';
import { useChatStore } from '@/stores/chatStore';
import toast from 'react-hot-toast';
import { api } from '@/services/api';

interface VisualizationContainerProps {
  content: string;
  className?: string;
  onExplain?: (vizUrl: string) => void;
}

const VisualizationContainer: React.FC<VisualizationContainerProps> = ({
  content,
  className = '',
  onExplain,
}) => {
  const visualizations = useVisualization(content);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef<VisualizationFrameHandle>(null);
  const session = useChatStore((state) => state.session);
  const explanationCacheRef = useRef<Record<string, string>>({});

  useEffect(() => {
    // Reset to first visualization when content changes
    setCurrentIndex(0);
    setShowExplanation(false);
    setExplanation('');
  }, [visualizations]);

  if (visualizations.length === 0) {
    return null;
  }

  const currentViz = visualizations[currentIndex];
  const hasMultiple = visualizations.length > 1;

  const handlePageChange = (page: number) => {
    // Page is 1-indexed, array is 0-indexed
    setCurrentIndex(page - 1);
  };

  const handleExplain = async () => {
    if (!currentViz) return;

    const cacheKey = currentViz.url || currentViz.title || `viz_${currentIndex}`;

    if (showExplanation && explanation) {
      setShowExplanation(false);
      return;
    }

    const cached = explanationCacheRef.current[cacheKey];
    if (cached) {
      setExplanation(cached);
      setShowExplanation(true);
      return;
    }

    setShowExplanation(true);
    setIsLoadingExplanation(true);
    setExplanation('');

    // Extract visualization path from URL
    let vizPath = '';
    let vizType = 'visualization';

    // Handle different URL patterns
    if (currentViz.url.includes('/serve_viz_file/')) {
      const pathMatch = currentViz.url.match(/\/serve_viz_file\/(.*)/);
      vizPath = pathMatch ? pathMatch[1] : '';
    } else if (currentViz.url.includes('/images/plotly_figures/pickle/')) {
      // Handle Data Analysis V3 pickle URLs
      vizPath = currentViz.url; // Use full URL as path
      vizType = 'data_analysis'; // Mark as data analysis visualization
    } else if (currentViz.url.includes('/static/visualizations/')) {
      // Handle static HTML visualizations
      vizPath = currentViz.url;
      vizType = 'data_analysis';
    } else {
      // Fallback to using the full URL
      vizPath = currentViz.url;
    }

    // Determine specific visualization type if not data_analysis
    if (vizType !== 'data_analysis') {
      if (vizPath.includes('vulnerability_map')) vizType = 'vulnerability_map';
      else if (vizPath.includes('box_plot')) vizType = 'box_plot';
      else if (vizPath.includes('pca_map')) vizType = 'pca_map';
      else if (vizPath.includes('composite_score')) vizType = 'composite_score_maps';
      else if (vizPath.includes('variable_distribution')) vizType = 'variable_distribution';
      else if (vizPath.includes('settlement')) vizType = 'settlement_map';
      else if (vizPath.includes('itn')) vizType = 'itn_map';
      else if (vizPath.includes('tpr')) vizType = 'tpr_map';
    }

    try {
      let imageBase64: string | undefined;

      try {
        const dataUrl = await frameRef.current?.captureImage();
        if (dataUrl?.startsWith('data:image')) {
          imageBase64 = dataUrl.split(',')[1];
        }
      } catch (captureError) {
        console.warn('Visualization capture failed', captureError);
      }

      const payload = {
        session_id: session.sessionId,
        viz_url: currentViz.url,
        viz_path: vizPath,
        viz_type: vizType,
        title: currentViz.title,
        image_base64: imageBase64,
        cache_key: cacheKey,
        metadata: {
          ...(currentViz.metadata || {}),
          type: currentViz.type,
          title: currentViz.title,
        },
      };

      const response = await api.visualization.explainVisualization(payload);
      const data = response.data;

      if (data.status === 'success' && data.explanation) {
        setExplanation(data.explanation);
        explanationCacheRef.current[data.cache_key || cacheKey] = data.explanation;
      } else {
        throw new Error(data.message || 'Failed to get explanation');
      }
    } catch (error) {
      console.error('❌ Error explaining visualization:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      setExplanation(`ERROR: ${errorMessage}`);
      toast.error(`Failed: ${errorMessage}`);
    } finally {
      setIsLoadingExplanation(false);
    }
  };

  return (
    <div ref={containerRef} className={`visualization-container bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden ${className}`}>
      {currentViz && (
        <>
          <VisualizationControls
            containerRef={containerRef}
            url={currentViz.url}
            title={currentViz.title}
            currentPage={currentIndex + 1}
            totalPages={visualizations.length}
            onPageChange={hasMultiple ? handlePageChange : undefined}
            onExplain={handleExplain}
          />

          <div className="p-4 bg-white">
            <VisualizationFrame
              ref={frameRef}
              url={currentViz.url}
              title={currentViz.title}
            />
          </div>

          {/* Explanation Area - NO FALLBACK TEXT */}
          {showExplanation && (
            <div className="border-t border-gray-200 bg-gray-50 p-4">
              <div className="flex items-start gap-3">
                <div className="text-2xl">💡</div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    AI Explanation
                    {isLoadingExplanation && (
                      <span className="inline-flex items-center gap-1 text-xs text-purple-600">
                        <div className="w-3 h-3 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                        <span>Processing...</span>
                      </span>
                    )}
                  </h4>
                  <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {explanation || (isLoadingExplanation ? '' : 'No explanation available')}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Visualization carousel dots */}
          {hasMultiple && (
            <div className="flex justify-center p-3 bg-gray-50 border-t border-gray-200">
              <div className="flex space-x-2">
                {visualizations.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentIndex(index)}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      index === currentIndex
                        ? 'bg-blue-600'
                        : 'bg-gray-300 hover:bg-gray-400'
                    }`}
                    title={`View visualization ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default VisualizationContainer;
