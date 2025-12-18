/**
 * Breathing zone overlay that shows the detection zone on the video.
 * Renders a semi-transparent rectangle over the configured zone area.
 */

import type { BreathingZone } from '../types';

interface BreathingZoneOverlayProps {
  zone: BreathingZone | null;
  videoWidth: number;
  videoHeight: number;
  isDetecting?: boolean;
}

export function BreathingZoneOverlay({
  zone,
  videoWidth,
  videoHeight,
  isDetecting = false,
}: BreathingZoneOverlayProps) {
  if (!zone || !zone.enabled) return null;

  // Calculate percentage-based positioning for responsive display
  const left = `${(zone.x / videoWidth) * 100}%`;
  const top = `${(zone.y / videoHeight) * 100}%`;
  const width = `${(zone.width / videoWidth) * 100}%`;
  const height = `${(zone.height / videoHeight) * 100}%`;

  return (
    <div
      className={`absolute pointer-events-none border-2 transition-colors duration-300 ${
        isDetecting
          ? 'border-green-400 bg-green-400/10'
          : 'border-blue-400 bg-blue-400/10'
      }`}
      style={{ left, top, width, height }}
    >
      {/* Corner markers */}
      <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-current" />
      <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-current" />
      <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-current" />
      <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-current" />

      {/* Label */}
      <div
        className={`absolute -top-6 left-0 text-xs px-1.5 py-0.5 rounded ${
          isDetecting ? 'bg-green-600 text-white' : 'bg-blue-600 text-white'
        }`}
      >
        {isDetecting ? 'Detecting' : 'Breathing Zone'}
      </div>
    </div>
  );
}
