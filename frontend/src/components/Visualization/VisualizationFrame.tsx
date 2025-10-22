import React, {
  useState,
  useRef,
  useEffect,
  forwardRef,
  useImperativeHandle,
} from 'react';

export interface VisualizationFrameHandle {
  captureImage: () => Promise<string>;
}

interface VisualizationFrameProps {
  url: string;
  title?: string;
  className?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

const VisualizationFrame = forwardRef<VisualizationFrameHandle, VisualizationFrameProps>(({
  url,
  title,
  className = '',
  onLoad,
  onError,
}, ref) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [currentUrl, setCurrentUrl] = useState(url);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const handleLoad = () => {
    setIsLoading(false);
    setHasError(false);
    onLoad?.();
    
    // Auto-adjust iframe height if possible
    try {
      if (iframeRef.current?.contentWindow) {
        const body = iframeRef.current.contentWindow.document.body;
        const height = body.scrollHeight;
        if (height > 0) {
          iframeRef.current.style.height = `${Math.min(height + 20, 800)}px`;
        }
      }
    } catch (e) {
      // Cross-origin restriction, use default height
      console.log('Cannot access iframe content (cross-origin)');
    }
  };
  
  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
    onError?.(new Error(`Failed to load visualization: ${url}`));
  };
  
  useEffect(() => {
    setCurrentUrl(url);
    setIsLoading(true);
    setHasError(false);
  }, [url]);
  
  // Listen for ITN map update messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Only handle ITN map updates
      if (event.data?.type === 'updateITNMap' && event.data?.mapPath) {
        console.log('Received ITN map update:', event.data.mapPath);
        // Update the iframe URL
        setCurrentUrl(event.data.mapPath);
        setIsLoading(true);
        setHasError(false);
      }
    };
    
    window.addEventListener('message', handleMessage);

    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, []);

  useImperativeHandle(ref, () => ({
    async captureImage() {
      const iframe = iframeRef.current;
      if (!iframe) {
        throw new Error('Visualization not loaded yet');
      }

      const iframeWindow = iframe.contentWindow as (Window & { Plotly?: any });
      if (!iframeWindow) {
        throw new Error('Unable to access visualization content');
      }

      const plotly = iframeWindow.Plotly;
      if (!plotly || typeof plotly.toImage !== 'function') {
        throw new Error('Plotly renderer not available for this visualization');
      }

      const doc = iframeWindow.document;
      const graphDiv = doc?.querySelector('.plotly-graph-div') as HTMLElement | null;
      if (!graphDiv) {
        throw new Error('Plot element not found in visualization');
      }

      try {
        const dataUrl: string = await plotly.toImage(graphDiv, {
          format: 'png',
          height: 720,
          width: 1024,
          scale: 2,
        });

        if (!dataUrl.startsWith('data:image')) {
          throw new Error('Unexpected capture output from Plotly');
        }

        return dataUrl;
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        throw new Error(`Failed to capture visualization: ${message}`);
      }
    },
  }));

  return (
    <div className={`visualization-frame relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 rounded-lg">
          <div className="flex flex-col items-center">
            <svg className="animate-spin h-8 w-8 text-blue-600 mb-2" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-sm text-gray-600">Loading visualization...</p>
          </div>
        </div>
      )}
      
      {hasError && (
        <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-gray-600">Failed to load visualization</p>
            <p className="text-xs text-gray-500 mt-1">{title || 'Unknown visualization'}</p>
          </div>
        </div>
      )}
      
      <iframe
        ref={iframeRef}
        src={currentUrl}
        title={title || 'Visualization'}
        className={`w-full border-0 rounded-lg ${hasError ? 'hidden' : ''}`}
        style={{ minHeight: '400px', height: '600px' }}
        sandbox="allow-scripts allow-same-origin allow-popups"
        loading="lazy"
        onLoad={handleLoad}
        onError={handleError}
      />
    </div>
  );
});

VisualizationFrame.displayName = 'VisualizationFrame';

export default VisualizationFrame;
