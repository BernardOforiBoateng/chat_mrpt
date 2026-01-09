import { useChatStore } from '@/stores/chatStore';
import toast from 'react-hot-toast';
import storage from '@/utils/storage';

interface ExportOptions {
  format: 'pdf' | 'html' | 'csv' | 'json';
  includeMetadata?: boolean;
  includeTimestamps?: boolean;
}

class ExportService {
  /**
   * Export chat history
   */
  async exportChatHistory(options: ExportOptions = { format: 'html' }) {
    try {
      const messages = useChatStore.getState().messages;
      const sessionId = useChatStore.getState().session.sessionId;
      
      if (messages.length === 0) {
        toast.error('No messages to export');
        return;
      }
      
      // Format messages for export
      const exportData = messages.map(msg => {
        if (msg.type === 'regular') {
          return {
            sender: msg.sender,
            content: msg.content,
            timestamp: msg.timestamp,
            metadata: options.includeMetadata ? msg.metadata : undefined,
          };
        }
        return null;
      }).filter(Boolean);
      
      // Generate export based on format
      switch (options.format) {
        case 'html':
          this.exportAsHTML(exportData, sessionId);
          break;
        case 'json':
          this.exportAsJSON(exportData, sessionId);
          break;
        case 'csv':
          this.exportAsCSV(exportData, sessionId);
          break;
        case 'pdf':
          // For PDF, we'd need to call a backend endpoint
          await this.exportAsPDF(sessionId);
          break;
        default:
          throw new Error(`Unsupported format: ${options.format}`);
      }
      
      toast.success(`Chat history exported as ${options.format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export chat history');
    }
  }
  
  /**
   * Export analysis results
   */
  async exportAnalysisResults(sessionId: string) {
    try {
      // Call backend endpoint to get analysis results
      const response = await fetch(`/api/export_analysis/${sessionId}`, {
      headers: {
        'X-Conversation-ID': storage.ensureConversationId(),
      },
    });
      
      if (!response.ok) {
        throw new Error('Failed to export analysis results');
      }
      
      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis_results_${sessionId}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success('Analysis results exported');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export analysis results');
    }
  }
  
  /**
   * Download a specific visualization
   */
  async downloadVisualization(vizUrl: string, filename?: string) {
    try {
      const response = await fetch(vizUrl, {
      headers: {
        'X-Conversation-ID': storage.ensureConversationId(),
      },
    });
      
      if (!response.ok) {
        throw new Error('Failed to download visualization');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || vizUrl.split('/').pop() || 'visualization.html';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success('Visualization downloaded');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download visualization');
    }
  }
  
  /**
   * Generate comprehensive report
   */
  async generateReport(sessionId: string, format: 'pdf' | 'html' = 'pdf') {
    try {
      const response = await fetch(`/api/generate_report/${sessionId}?format=${format}`, {
      headers: {
        'X-Conversation-ID': storage.ensureConversationId(),
      },
    });
      
      if (!response.ok) {
        throw new Error('Failed to generate report');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${sessionId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success(`Report generated as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Report generation error:', error);
      toast.error('Failed to generate report');
    }
  }
  
  // Private helper methods
  
  private exportAsHTML(data: any[], sessionId: string) {
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>Chat History - ${sessionId}</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          .message { margin-bottom: 15px; padding: 10px; border-radius: 5px; }
          .user { background: #e3f2fd; text-align: right; }
          .assistant { background: #f5f5f5; }
          .timestamp { font-size: 0.8em; color: #666; }
        </style>
      </head>
      <body>
        <h1>Chat History</h1>
        <p>Session: ${sessionId}</p>
        <p>Exported: ${new Date().toLocaleString()}</p>
        <hr>
        ${data.map(msg => `
          <div class="message ${msg.sender}">
            <strong>${msg.sender === 'user' ? 'You' : 'Assistant'}:</strong>
            <p>${msg.content}</p>
            <span class="timestamp">${new Date(msg.timestamp).toLocaleString()}</span>
          </div>
        `).join('')}
      </body>
      </html>
    `;
    
    const blob = new Blob([html], { type: 'text/html' });
    this.downloadBlob(blob, `chat_history_${sessionId}.html`);
  }
  
  private exportAsJSON(data: any[], sessionId: string) {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    this.downloadBlob(blob, `chat_history_${sessionId}.json`);
  }
  
  private exportAsCSV(data: any[], sessionId: string) {
    const headers = ['Timestamp', 'Sender', 'Content'];
    const rows = data.map(msg => [
      new Date(msg.timestamp).toISOString(),
      msg.sender,
      `"${msg.content.replace(/"/g, '""')}"`, // Escape quotes
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    this.downloadBlob(blob, `chat_history_${sessionId}.csv`);
  }
  
  private async exportAsPDF(sessionId: string) {
    // This would call a backend endpoint that generates a PDF
    const response = await fetch(`/api/export_chat_pdf/${sessionId}`, {
      headers: {
        'X-Conversation-ID': storage.ensureConversationId(),
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to generate PDF');
    }
    
    const blob = await response.blob();
    this.downloadBlob(blob, `chat_history_${sessionId}.pdf`);
  }
  
  private downloadBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

export default new ExportService();