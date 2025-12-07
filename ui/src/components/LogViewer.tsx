import { useEffect, useRef, useState } from 'react';
import { useLogs } from '../api/hooks';

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: 'text-gray-400',
  INFO: 'text-blue-400',
  WARNING: 'text-yellow-400',
  ERROR: 'text-red-400',
  CRITICAL: 'text-red-600 font-bold'
};

export function LogViewer() {
  const [source, setSource] = useState<'memory' | 'file'>('memory');
  const { entries, loading, error } = useLogs(5000, 200, source);
  const containerRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (autoScrollRef.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [entries]);

  // Detect if user has scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    autoScrollRef.current = scrollHeight - scrollTop - clientHeight < 50;
  };

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
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-200">Server Logs</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">{entries.length} entries</span>
          <div className="flex rounded-lg overflow-hidden border border-gray-600">
            <button
              onClick={() => setSource('memory')}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                source === 'memory'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Live
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
        </div>
      </div>

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="bg-gray-900 rounded-lg border border-gray-700 p-3 h-64 overflow-y-auto font-mono text-xs"
      >
        {entries.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No log entries</p>
        ) : (
          entries.map((entry, idx) => (
            <div key={idx} className="py-0.5 hover:bg-gray-800/50">
              <span className="text-gray-500">{entry.timestamp}</span>
              <span className={`ml-2 ${LEVEL_COLORS[entry.level] || 'text-gray-300'}`}>
                [{entry.level}]
              </span>
              <span className="text-gray-400 ml-2">{entry.name}:</span>
              <span className="text-gray-200 ml-2">{entry.message}</span>
            </div>
          ))
        )}
      </div>

      <p className="text-xs text-gray-500">
        {source === 'memory' ? 'Live logs from memory' : 'Persistent logs from file'} - refreshes every 5s
      </p>
    </div>
  );
}
