import React from 'react';
import { formatZoomPercentage } from '../utils/zoomCalculations';

interface ZoomControlProps {
  zoomLevel: number;
  onZoomChange: (newZoom: number) => void;
}

const ZoomControl: React.FC<ZoomControlProps> = ({ zoomLevel, onZoomChange }) => {
  const handleZoomIn = () => {
    const newZoom = Math.min(100, zoomLevel + 10);
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
    <div className="flex flex-col items-center gap-1 bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-lg p-2">
      <button
        onClick={handleZoomIn}
        disabled={zoomLevel === 100}
        className="w-10 h-10 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed font-bold text-xl flex items-center justify-center transition-colors"
        aria-label="Zoom in"
      >
        +
      </button>
      <button
        onClick={handleReset}
        className="w-10 h-10 bg-gray-700 text-white rounded-lg hover:bg-gray-600 text-xs font-mono flex items-center justify-center transition-colors"
        aria-label="Reset zoom"
        title="Click to reset zoom"
      >
        {formatZoomPercentage(zoomLevel)}
      </button>
      <button
        onClick={handleZoomOut}
        disabled={zoomLevel === 0}
        className="w-10 h-10 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed font-bold text-xl flex items-center justify-center transition-colors"
        aria-label="Zoom out"
      >
        −
      </button>
    </div>
  );
};

export default ZoomControl;
