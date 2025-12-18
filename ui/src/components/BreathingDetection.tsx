/**
 * Breathing detection settings panel.
 * Allows users to configure breathing detection zone and view status.
 */

import { useState } from 'react';
import { useOptimizedBreathingDetection } from '../api/optimized-hooks';
import { BreathingStatusBadge } from './BreathingStatusBadge';
import { BreathingWaveform } from './BreathingWaveform';

interface BreathingDetectionProps {
  onStartZoneSelection: () => void;
  showZoneOverlay?: boolean;
  onZoneOverlayToggle?: (enabled: boolean) => void;
}

export function BreathingDetection({
  onStartZoneSelection,
  showZoneOverlay,
  onZoneOverlayToggle,
}: BreathingDetectionProps) {
  const { status, waveform, loading, clearZone, updateConfig } = useOptimizedBreathingDetection();
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (loading) {
    return (
      <div className="p-4 text-gray-400 text-center">
        Loading breathing detection...
      </div>
    );
  }

  const hasZone = status?.zone !== null;
  const isEnabled = status?.status !== 'disabled';

  return (
    <div className="p-4 space-y-4">
      {/* Disclaimer */}
      <div className="bg-yellow-900/30 border border-yellow-600/50 rounded-lg p-3 text-xs text-yellow-200">
        This is a convenience indicator only, not a medical device.
        Always follow safe sleep guidelines.
      </div>

      {/* Status Section */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-white">Breathing Detection</h3>
        <BreathingStatusBadge status={status} />
      </div>

      {/* Zone Setup */}
      <div className="space-y-3">
        {hasZone ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Detection zone active</span>
              <button
                onClick={clearZone}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                Clear Zone
              </button>
            </div>
            {status?.zone && (
              <div className="text-xs text-gray-500">
                Position: {status.zone.x}, {status.zone.y} |
                Size: {status.zone.width}x{status.zone.height}px
              </div>
            )}
            {/* Show zone overlay toggle */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Show zone on video</span>
              <button
                onClick={() => onZoneOverlayToggle?.(!showZoneOverlay)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  showZoneOverlay ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                    showZoneOverlay ? 'translate-x-5' : ''
                  }`}
                />
              </button>
            </div>
            {/* Redraw zone button */}
            <button
              onClick={onStartZoneSelection}
              className="w-full py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              Redraw Zone
            </button>
          </div>
        ) : (
          <button
            onClick={onStartZoneSelection}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
          >
            Set Detection Zone
          </button>
        )}
      </div>

      {/* Waveform Display (when enabled) */}
      {isEnabled && hasZone && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Motion Intensity</h4>
          <BreathingWaveform points={waveform} width={320} height={100} />
        </div>
      )}

      {/* Status Details */}
      {isEnabled && status && (
        <div className="bg-gray-800 rounded-lg p-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Status</span>
            <span className="text-white capitalize">{status.status}</span>
          </div>
          {status.rate_bpm && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Breathing Rate</span>
              <span className="text-green-400">{Math.round(status.rate_bpm)} BPM</span>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Confidence</span>
            <span className="text-white">{Math.round((status.confidence || 0) * 100)}%</span>
          </div>
          {status.last_detected_time && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Last detected</span>
              <span className="text-white">{status.last_detected_time}</span>
            </div>
          )}
        </div>
      )}

      {/* Advanced Settings */}
      {hasZone && (
        <div className="border-t border-gray-700 pt-3">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full text-sm text-gray-400 hover:text-white"
          >
            <span>Advanced Settings</span>
            <svg
              className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showAdvanced && (
            <div className="mt-3 space-y-4">
              {/* Alert Timeout */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <label className="text-gray-400">Alert after no breathing (seconds)</label>
                  <span className="text-white">{status?.alert_active ? 'Active!' : '30s'}</span>
                </div>
                <input
                  type="range"
                  min="15"
                  max="120"
                  step="5"
                  defaultValue={30}
                  onChange={(e) => updateConfig({ alert_after_seconds: Number(e.target.value) })}
                  className="w-full accent-blue-500"
                />
              </div>

              {/* Confidence Threshold */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <label className="text-gray-400">Confidence threshold</label>
                  <span className="text-white">60%</span>
                </div>
                <input
                  type="range"
                  min="0.3"
                  max="0.9"
                  step="0.1"
                  defaultValue={0.6}
                  onChange={(e) => updateConfig({ confidence_threshold: Number(e.target.value) })}
                  className="w-full accent-blue-500"
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
