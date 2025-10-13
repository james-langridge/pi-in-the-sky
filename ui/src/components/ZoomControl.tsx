import React from 'react';
import { formatZoomPercentage } from '../utils/zoomCalculations';

interface ZoomControlProps {
  zoomLevel: number;
  onZoomChange: (newZoom: number) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const ZoomControl: React.FC<ZoomControlProps> = ({ zoomLevel, onZoomChange, isOpen, onToggle }) => {
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
    <>
      {/* Collapsed icon button */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="w-12 h-12 bg-gray-700 hover:bg-gray-600 text-white rounded-full shadow-lg transition-all duration-200 flex items-center justify-center"
          aria-label="Open zoom controls"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
          </svg>
        </button>
      )}

      {/* Expanded vertical controls */}
      {isOpen && (
        <div className="relative flex flex-col items-center gap-1 bg-gray-900/90 backdrop-blur-sm rounded-lg shadow-lg p-2 z-[21]">
          <button
            onClick={handleZoomIn}
            disabled={zoomLevel === 200}
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
          <button
            onClick={onToggle}
            className="w-10 h-10 bg-gray-600 text-white rounded-lg hover:bg-gray-500 flex items-center justify-center transition-colors mt-1"
            aria-label="Close zoom controls"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </>
  );
};

export default ZoomControl;
