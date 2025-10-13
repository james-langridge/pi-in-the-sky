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
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-semibold mb-3">Zoom</h3>
      <div className="flex items-center gap-2">
        <button
          onClick={handleZoomOut}
          disabled={zoomLevel === 0}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-bold"
          aria-label="Zoom out"
        >
          −
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
          aria-label="Reset zoom"
        >
          {formatZoomPercentage(zoomLevel)}
        </button>
        <button
          onClick={handleZoomIn}
          disabled={zoomLevel === 100}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-bold"
          aria-label="Zoom in"
        >
          +
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Click buttons to zoom, tap percentage to reset
      </p>
    </div>
  );
};

export default ZoomControl;
