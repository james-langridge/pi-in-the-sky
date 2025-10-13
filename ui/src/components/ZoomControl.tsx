import React from 'react';
import { formatZoomPercentage } from '../utils/zoomCalculations';

interface ZoomControlProps {
  zoomLevel: number;
  onZoomChange: (newZoom: number) => void;
}

const ZoomControl: React.FC<ZoomControlProps> = ({ zoomLevel, onZoomChange }) => {
  const handleZoomIn = () => {
    const newZoom = Math.min(200, zoomLevel + 10);
    onZoomChange(newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(0, zoomLevel - 10);
    onZoomChange(newZoom);
  };

  const handleReset = () => {
    onZoomChange(0);
  };

  return (
    <div className="flex items-center gap-2 bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-lg px-3 py-2">
      <button
        onClick={handleZoomOut}
        disabled={zoomLevel === 0}
        className="w-10 h-10 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed font-bold text-xl flex items-center justify-center transition-colors"
        aria-label="Zoom out"
      >
        −
      </button>
      <button
        onClick={handleReset}
        className="w-16 h-10 bg-gray-700 text-white rounded-lg hover:bg-gray-600 text-xs font-mono flex items-center justify-center transition-colors"
        aria-label="Reset zoom"
        title="Click to reset zoom"
      >
        {formatZoomPercentage(zoomLevel)}
      </button>
      <button
        onClick={handleZoomIn}
        disabled={zoomLevel === 200}
        className="w-10 h-10 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed font-bold text-xl flex items-center justify-center transition-colors"
        aria-label="Zoom in"
      >
        +
      </button>
    </div>
  );
};

export default ZoomControl;
