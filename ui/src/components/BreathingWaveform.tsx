/**
 * Live breathing waveform visualization.
 * Shows motion intensity over time as a line chart.
 */

import { useMemo } from 'react';
import type { BreathingWaveformPoint } from '../types';

interface BreathingWaveformProps {
  points: BreathingWaveformPoint[];
  width?: number;
  height?: number;
  className?: string;
}

export function BreathingWaveform({
  points,
  width = 300,
  height = 80,
  className = '',
}: BreathingWaveformProps) {
  const pathData = useMemo(() => {
    if (points.length < 2) return '';

    // Normalize timestamps to fit in the width
    const minTime = points[0].timestamp;
    const maxTime = points[points.length - 1].timestamp;
    const timeRange = maxTime - minTime || 1;

    // Build SVG path
    const pathPoints = points.map((point, index) => {
      const x = ((point.timestamp - minTime) / timeRange) * (width - 10) + 5;
      // Invert y so higher values are at the top, with padding
      const y = height - 10 - point.intensity * (height - 20);
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    });

    return pathPoints.join(' ');
  }, [points, width, height]);

  // Calculate average intensity for display
  const avgIntensity = useMemo(() => {
    if (points.length === 0) return 0;
    const sum = points.reduce((acc, p) => acc + p.intensity, 0);
    return sum / points.length;
  }, [points]);

  if (points.length < 2) {
    return (
      <div
        className={`flex items-center justify-center bg-gray-800 rounded-lg ${className}`}
        style={{ width, height }}
      >
        <span className="text-gray-500 text-sm">Collecting data...</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <svg
        width={width}
        height={height}
        className="bg-gray-800 rounded-lg overflow-hidden"
      >
        {/* Grid lines */}
        <defs>
          <pattern
            id="grid"
            width="20"
            height="20"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 20 0 L 0 0 0 20"
              fill="none"
              stroke="rgba(75, 85, 99, 0.3)"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect width={width} height={height} fill="url(#grid)" />

        {/* Waveform line */}
        <path
          d={pathData}
          fill="none"
          stroke="#22c55e"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Gradient fill under the line */}
        <defs>
          <linearGradient id="waveformGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
          </linearGradient>
        </defs>
        {pathData && (
          <path
            d={`${pathData} L ${width - 5} ${height - 5} L 5 ${height - 5} Z`}
            fill="url(#waveformGradient)"
          />
        )}

        {/* Labels */}
        <text
          x="5"
          y="12"
          className="text-[10px] fill-gray-400"
        >
          Motion
        </text>
        <text
          x={width - 5}
          y={height - 5}
          textAnchor="end"
          className="text-[10px] fill-gray-400"
        >
          Time
        </text>
      </svg>

      {/* Intensity indicator */}
      <div className="absolute top-1 right-2 text-xs text-gray-400">
        Avg: {(avgIntensity * 100).toFixed(0)}%
      </div>
    </div>
  );
}
