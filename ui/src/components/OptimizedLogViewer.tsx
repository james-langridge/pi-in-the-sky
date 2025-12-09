import { useEffect, useRef, useState } from 'react';
import { useConditionalLogs } from '../api/optimized-hooks';
import { RefreshCw, Download, Trash2, Copy } from 'lucide-react';

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: 'text-gray-400',
  INFO: 'text-blue-400',
  WARNING: 'text-yellow-400',
  ERROR: 'text-red-400',
  CRITICAL: 'text-red-600 font-bold'
};

interface OptimizedLogViewerProps {
  isVisible?: boolean;
}

export function OptimizedLogViewer({ isVisible = true }: OptimizedLogViewerProps) {
  const [source, setSource] = useState<'memory' | 'file'>('file');
  const [autoScroll, setAutoScroll] = useState(true);
  
  // Only fetch logs when component is visible
  const { entries, loading, error, refetch, clear } = useConditionalLogs(
    isVisible,
    200,
    source
  );
  
  const containerRef = useRef<HTMLDivElement>(null);
  const lastScrollPosRef = useRef(0);

  // Auto-scroll to bottom when new entries arrive (if enabled)
  useEffect(() => {
    if (autoScroll && containerRef.current && entries.length > 0) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [entries, autoScroll]);

  // Detect if user has scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    // Only update if state actually changes
    if (isAtBottom && !autoScroll) {
      setAutoScroll(true);
    } else if (!isAtBottom && autoScroll && scrollTop < lastScrollPosRef.current) {
      // User scrolled up
      setAutoScroll(false);
    }
    
    lastScrollPosRef.current = scrollTop;
  };

  // Format logs as text
  const formatLogs = () => entries.map(entry =>
    `${entry.timestamp} [${entry.level}] ${entry.name}: ${entry.message}`
  ).join('\n');

  // Export logs to file
  const exportLogs = () => {
    const blob = new Blob([formatLogs()], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Copy logs to clipboard
  const copyLogs = async () => {
    await navigator.clipboard.writeText(formatLogs());
  };

  if (!isVisible) {
    return null;
  }

  if (loading && entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-gray-400">Loading logs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/30 rounded-lg border border-red-700">
        <p className="text-red-400">Failed to load logs: {error.message}</p>
        <button
          onClick={refetch}
          className="mt-2 px-3 py-1 bg-red-700 hover:bg-red-600 text-white rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col gap-3">
      {/* Header with controls - two rows for better layout */}
      <div className="flex-shrink-0 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Source selector */}
            <div className="flex rounded-lg overflow-hidden border border-gray-600">
              <button
                onClick={() => setSource('memory')}
                className={`px-3 py-1 text-xs font-medium transition-colors ${
                  source === 'memory'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Memory
              </button>
              <button
                onClick={() => setSource('file')}
                className={`px-3 py-1 text-xs font-medium transition-colors ${
                  source === 'file'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                File
              </button>
            </div>
            <span className="text-sm text-gray-500">{entries.length} entries</span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={refetch}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Refresh logs"
            >
              <RefreshCw className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={copyLogs}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Copy logs to clipboard"
              disabled={entries.length === 0}
            >
              <Copy className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={exportLogs}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Download logs"
              disabled={entries.length === 0}
            >
              <Download className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={clear}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Clear displayed logs"
              disabled={entries.length === 0}
            >
              <Trash2 className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Auto-scroll indicator */}
        <div className={`text-xs px-2 py-1 rounded inline-block ${
          autoScroll ? 'bg-green-600/20 text-green-400' : 'bg-gray-600/20 text-gray-400'
        }`}>
          {autoScroll ? 'Auto-scroll ON' : 'Scroll up to pause'}
        </div>
      </div>

      {/* Log entries - fills remaining space */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 bg-gray-900 rounded-lg p-3 overflow-y-auto font-mono text-xs space-y-1"
      >
        {entries.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No log entries available
          </div>
        ) : (
          entries.map((entry, index) => (
            <div key={index} className="flex gap-2 hover:bg-gray-800/50 px-1 rounded">
              <span className="text-gray-500 flex-shrink-0">
                {entry.timestamp}
              </span>
              <span className={`${LEVEL_COLORS[entry.level] || 'text-gray-400'} w-16 flex-shrink-0`}>
                [{entry.level}]
              </span>
              <span className="text-gray-400 flex-shrink-0">
                {entry.name}:
              </span>
              <span className="text-gray-300 break-all">
                {entry.message}
              </span>
            </div>
          ))
        )}
        
        {/* Auto-scroll anchor */}
        {autoScroll && <div className="h-0" />}
      </div>
    </div>
  );
}