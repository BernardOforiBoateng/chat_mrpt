import { useEffect, useState } from 'react';

interface Visualization {
  id: string;
  url: string;
  title?: string;
  type?: string;
  metadata?: Record<string, any>;
}

const useVisualization = (content: string) => {
  const [visualizations, setVisualizations] = useState<Visualization[]>([]);
  
  useEffect(() => {
    // Support two patterns:
    // 1) Legacy inline URLs in message content: /serve_viz_file/....
    // 2) Direct URL strings (e.g., /static/visualizations/....html) passed as content

    const isDirectUrl = typeof content === 'string' && (
      content.startsWith('/static/visualizations/') ||
      content.startsWith('/images/plotly_figures/pickle/') ||
      content.startsWith('http://') ||
      content.startsWith('https://') ||
      content.endsWith('.html') ||
      content.endsWith('.pickle')
    );

    if (isDirectUrl) {
      const filename = content.split('/').pop() || 'visualization';
      let type = 'general';
      if (filename.includes('map')) type = 'map';
      else if (filename.includes('chart')) type = 'chart';
      else if (filename.includes('plot')) type = 'plot';
      else if (filename.includes('distribution')) type = 'distribution';

      setVisualizations([
        {
          id: `viz_${Date.now()}_0`,
          url: content,
          title: filename.replace(/\.[^/.]+$/, '').replace(/_/g, ' '),
          type,
        }
      ]);
      return;
    }

    // Pattern to detect embedded visualization URLs
    const vizUrlPattern = /\/serve_viz_file\/[a-zA-Z0-9\-_\/]+\.[a-zA-Z]+/g;
    const matches = content.match(vizUrlPattern);
    if (matches && matches.length > 0) {
      const vizList: Visualization[] = matches.map((url, index) => {
        const filename = url.split('/').pop() || 'visualization';
        let type = 'general';
        if (filename.includes('map')) type = 'map';
        else if (filename.includes('chart')) type = 'chart';
        else if (filename.includes('plot')) type = 'plot';
        else if (filename.includes('distribution')) type = 'distribution';
        return {
          id: `viz_${Date.now()}_${index}`,
          url,
          title: filename.replace(/\.[^/.]+$/, '').replace(/_/g, ' '),
          type,
        };
      });
      setVisualizations(vizList);
    } else {
      setVisualizations([]);
    }
  }, [content]);
  
  return visualizations;
};

export default useVisualization;
