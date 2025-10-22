import React, { useMemo, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import VisualizationContainer from '../Visualization/VisualizationContainer';
import DualMethodDisplay from '../Analysis/DualMethodDisplay';
import type { RegularMessage as RegularMessageType } from '@/types';

interface RegularMessageProps {
  message: RegularMessageType;
}

const RegularMessage: React.FC<RegularMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  useEffect(() => {
    if (isUser) {
      return;
    }
    console.groupCollapsed('🛰️ MESSAGE PIPELINE DEBUG');
    console.log('Message ID:', message.id);
    console.log('Workflow metadata:', message.metadata);
    console.log('Visualizations:', message.visualizations?.length ?? 0, message.visualizations);
    console.log('Download links:', message.downloadLinks?.length ?? 0, message.downloadLinks);
    console.log('Content preview:', message.content.substring(0, 200));
    console.groupEnd();
  }, [isUser, message]);
  
  // Detect and extract a top-level warning line (styled in red)
  let topWarning = '';
  let restContent = message.content;
  if (!isUser && typeof message.content === 'string') {
    const firstNewline = message.content.indexOf('\n');
    const firstLine = (firstNewline >= 0 ? message.content.slice(0, firstNewline) : message.content).trim();
    if (firstLine.startsWith('⚠️')) {
      topWarning = firstLine;
      restContent = firstNewline >= 0 ? message.content.slice(firstNewline + 1) : '';
    }
  }
  
  // Check if message contains visualization URLs or has visualizations array
  const hasVisualization = !isUser && (
    message.content.includes('/serve_viz_file/') ||
    (message.visualizations && message.visualizations.length > 0)
  );

  const visualizationEntries = useMemo(() => {
    if (!hasVisualization) {
      return [];
    }

    if (message.visualizations && message.visualizations.length > 0) {
      return message.visualizations.map((viz: any, index: number) => {
        const url = typeof viz === 'string'
          ? viz
          : (viz.url || viz.path || viz.html_path || '');

        return {
          key: `viz_${message.id}_${index}`,
          url,
          title: typeof viz === 'string'
            ? 'Interactive visualization'
            : (viz.title || 'Interactive visualization'),
        };
      }).filter((entry) => !!entry.url);
    }

    return [{
      key: `viz_${message.id}_fallback`,
      url: message.content,
      title: 'Interactive visualization',
    }];
  }, [hasVisualization, message]);
  
  // Check if message contains analysis results
  const analysisData = useMemo(() => {
    if (isUser || !message.metadata?.analysisResults) return null;
    
    // Extract analysis data from metadata
    const { pca, composite, ward, state } = message.metadata.analysisResults;
    
    return {
      data: {
        pca: pca ? {
          score: pca.score,
          ranking: pca.ranking,
          totalRanked: pca.totalRanked,
          indicators: pca.indicators || []
        } : undefined,
        composite: composite ? {
          score: composite.score,
          ranking: composite.ranking,
          totalRanked: composite.totalRanked,
          indicators: composite.indicators || []
        } : undefined,
      },
      wardName: ward,
      stateName: state,
    };
  }, [isUser, message.metadata]);
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-3xl rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        {/* Message Header */}
        <div className="flex items-center mb-1">
          <span className="text-xs font-medium opacity-75">
            {isUser ? 'You' : 'Assistant'}
          </span>
          {message.metadata?.model && (
            <span className="ml-2 text-xs opacity-50">
              ({message.metadata.model})
            </span>
          )}
          {/* Per-message spinner removed for a cleaner UI */}
        </div>
        
        {/* Message Content */}
        <div className={`prose prose-sm max-w-none ${isUser ? 'prose-invert' : ''} [&>p]:mb-4 [&>ul]:mb-4 [&>ol]:mb-4 [&>h2]:mt-6 [&>h2]:mb-3 [&>h3]:mt-4 [&>h3]:mb-2`}>
          {!isUser ? (
            <>
              {topWarning && (
                <div className="text-red-600 font-bold mb-2">{topWarning}</div>
              )}
              {visualizationEntries.length > 0 && (
                <div className="not-prose mb-4">
                  {visualizationEntries.map((viz) => (
                    <div
                      key={viz.key}
                      className="mb-4 rounded-lg border border-blue-200 bg-blue-50/60 p-3"
                    >
                      <div className="mb-2 flex items-center justify-between text-sm font-semibold text-blue-900">
                        <span>{viz.title}</span>
                        <span className="text-xs font-medium uppercase tracking-wide text-blue-600">Interactive</span>
                      </div>
                      <VisualizationContainer
                        content={viz.url}
                        onExplain={(vizUrl) => {
                          console.log('Explain visualization:', vizUrl);
                        }}
                      />
                    </div>
                  ))}
                </div>
              )}
              {/* Check if content starts with our styled HTML */}
              {restContent.startsWith('<span style="color: red') ? (
                <>
                  {/* Extract and render the IMPORTANT message with HTML styling */}
                  {(() => {
                    const htmlEndIndex = restContent.indexOf('</span>\n');
                    if (htmlEndIndex > -1) {
                      const htmlContent = restContent.substring(0, htmlEndIndex + 8);
                      const remainingContent = restContent.substring(htmlEndIndex + 8);
                      return (
                        <>
                          <div dangerouslySetInnerHTML={{ __html: htmlContent }} className="mb-2" />
                          <ReactMarkdown
                            components={{
                              code: ({ className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '');
                                return match ? (
                                  <pre className="bg-gray-800 text-white p-2 rounded overflow-x-auto">
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  </pre>
                                ) : (
                                  <code className="bg-gray-200 px-1 rounded" {...props}>
                                    {children}
                                  </code>
                                );
                              },
                              a: ({ ...props }) => (
                                <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" />
                              ),
                            }}
                          >
                            {remainingContent}
                          </ReactMarkdown>
                        </>
                      );
                    }
                    // Fallback if parsing fails
                    return <div dangerouslySetInnerHTML={{ __html: restContent }} />;
                  })()}
                </>
              ) : (
                <ReactMarkdown
                  components={{
                    code: ({ className, children, ...props }) => {
                      const match = /language-(\w+)/.exec(className || '');
                      return match ? (
                        <pre className="bg-gray-800 text-white p-2 rounded overflow-x-auto">
                          <code className={className} {...props}>
                            {children}
                          </code>
                        </pre>
                      ) : (
                        <code className="bg-gray-200 px-1 rounded" {...props}>
                          {children}
                        </code>
                      );
                    },
                    a: ({ ...props }) => (
                      <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" />
                    ),
                  }}
                >
                  {restContent}
                </ReactMarkdown>
              )}
            </>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>
        
        {/* Message Footer */}
        {message.metadata && (message.metadata.latency || message.metadata.tokens) && (
          <div className="mt-2 text-xs opacity-50">
            {message.metadata.latency && (
              <span>Latency: {message.metadata.latency}ms</span>
            )}
            {message.metadata.tokens && (
              <span className="ml-3">Tokens: {message.metadata.tokens}</span>
            )}
          </div>
        )}
        
        {/* Analysis Results Display */}
        {analysisData && (
          <div className="mt-4">
            <DualMethodDisplay
              data={analysisData.data}
              wardName={analysisData.wardName}
              stateName={analysisData.stateName}
            />
          </div>
        )}
        
        {/* Visualization Container */}
      </div>
    </div>
  );
};

export default RegularMessage;
