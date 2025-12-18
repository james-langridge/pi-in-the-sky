/**
 * Breathing zone selector overlay for video stream.
 * Allows users to draw a rectangle over the baby's chest area.
 */

import { useState, useRef, useCallback } from 'react';

interface BreathingZoneSelectorProps {
  onSave: (zone: { x: number; y: number; width: number; height: number }) => void;
  onCancel: () => void;
  videoWidth: number;
  videoHeight: number;
  initialZone?: { x: number; y: number; width: number; height: number } | null;
}

export function BreathingZoneSelector({
  onSave,
  onCancel,
  videoWidth,
  videoHeight,
  initialZone,
}: BreathingZoneSelectorProps) {
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [currentRect, setCurrentRect] = useState<{
    x: number;
    y: number;
    width: number;
    height: number;
  } | null>(initialZone || null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Convert screen coordinates to video coordinates
  const screenToVideo = useCallback(
    (screenX: number, screenY: number) => {
      if (!containerRef.current) return { x: 0, y: 0 };
      const rect = containerRef.current.getBoundingClientRect();
      const scaleX = videoWidth / rect.width;
      const scaleY = videoHeight / rect.height;
      return {
        x: Math.round((screenX - rect.left) * scaleX),
        y: Math.round((screenY - rect.top) * scaleY),
      };
    },
    [videoWidth, videoHeight]
  );

  // Convert video coordinates to screen coordinates for display
  const videoToScreen = useCallback(
    (videoX: number, videoY: number, videoW: number, videoH: number) => {
      if (!containerRef.current) return { x: 0, y: 0, width: 0, height: 0 };
      const rect = containerRef.current.getBoundingClientRect();
      const scaleX = rect.width / videoWidth;
      const scaleY = rect.height / videoHeight;
      return {
        x: videoX * scaleX,
        y: videoY * scaleY,
        width: videoW * scaleX,
        height: videoH * scaleY,
      };
    },
    [videoWidth, videoHeight]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      const point = screenToVideo(e.clientX, e.clientY);
      setStartPoint(point);
      setIsDrawing(true);
      setCurrentRect(null);
    },
    [screenToVideo]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDrawing || !startPoint) return;
      const point = screenToVideo(e.clientX, e.clientY);
      const x = Math.min(startPoint.x, point.x);
      const y = Math.min(startPoint.y, point.y);
      const width = Math.abs(point.x - startPoint.x);
      const height = Math.abs(point.y - startPoint.y);
      setCurrentRect({ x, y, width, height });
    },
    [isDrawing, startPoint, screenToVideo]
  );

  const handleMouseUp = useCallback(() => {
    setIsDrawing(false);
    setStartPoint(null);
  }, []);

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      const point = screenToVideo(touch.clientX, touch.clientY);
      setStartPoint(point);
      setIsDrawing(true);
      setCurrentRect(null);
    },
    [screenToVideo]
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!isDrawing || !startPoint) return;
      const touch = e.touches[0];
      const point = screenToVideo(touch.clientX, touch.clientY);
      const x = Math.min(startPoint.x, point.x);
      const y = Math.min(startPoint.y, point.y);
      const width = Math.abs(point.x - startPoint.x);
      const height = Math.abs(point.y - startPoint.y);
      setCurrentRect({ x, y, width, height });
    },
    [isDrawing, startPoint, screenToVideo]
  );

  const handleTouchEnd = useCallback(() => {
    setIsDrawing(false);
    setStartPoint(null);
  }, []);

  const handleSave = useCallback(() => {
    if (currentRect && currentRect.width > 10 && currentRect.height > 10) {
      onSave(currentRect);
    }
  }, [currentRect, onSave]);

  // Get screen coordinates for the rectangle display
  const displayRect = currentRect ? videoToScreen(currentRect.x, currentRect.y, currentRect.width, currentRect.height) : null;

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-30 cursor-crosshair"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Semi-transparent overlay */}
      <div className="absolute inset-0 bg-black/30" />

      {/* Instructions */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-lg text-sm">
        Draw a rectangle over the baby's chest area
      </div>

      {/* Selected zone rectangle */}
      {displayRect && (
        <div
          className="absolute border-2 border-green-400 bg-green-400/20"
          style={{
            left: displayRect.x,
            top: displayRect.y,
            width: displayRect.width,
            height: displayRect.height,
          }}
        >
          <div className="absolute -top-6 left-0 text-xs text-green-400 bg-black/70 px-1 rounded">
            {currentRect?.width}x{currentRect?.height}px
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div
        className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3"
        onMouseDown={(e) => e.stopPropagation()}
        onTouchStart={(e) => e.stopPropagation()}
      >
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg font-medium transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={!currentRect || currentRect.width < 10 || currentRect.height < 10}
          className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-500 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors cursor-pointer"
        >
          Save Zone
        </button>
      </div>
    </div>
  );
}
