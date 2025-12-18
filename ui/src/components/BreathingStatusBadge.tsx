/**
 * Compact breathing status indicator badge.
 * Shows breathing detection state with visual indicators.
 */

import type { BreathingStatus } from '../types';

interface BreathingStatusBadgeProps {
  status: BreathingStatus | null;
  compact?: boolean;
}

export function BreathingStatusBadge({ status, compact = false }: BreathingStatusBadgeProps) {
  if (!status || status.status === 'disabled') {
    return null;
  }

  const getStatusConfig = () => {
    switch (status.status) {
      case 'detected':
        return {
          color: 'bg-green-500',
          pulseColor: 'bg-green-400',
          textColor: 'text-green-400',
          label: status.rate_bpm ? `${Math.round(status.rate_bpm)} BPM` : 'Breathing',
          pulse: true,
        };
      case 'monitoring':
        return {
          color: 'bg-yellow-500',
          pulseColor: 'bg-yellow-400',
          textColor: 'text-yellow-400',
          label: 'Monitoring...',
          pulse: false,
        };
      case 'warning':
        return {
          color: 'bg-orange-500',
          pulseColor: 'bg-orange-400',
          textColor: 'text-orange-400',
          label: 'Low signal',
          pulse: false,
        };
      case 'alert':
        return {
          color: 'bg-red-500',
          pulseColor: 'bg-red-400',
          textColor: 'text-red-400',
          label: 'No breathing!',
          pulse: true,
        };
      default:
        return {
          color: 'bg-gray-500',
          pulseColor: 'bg-gray-400',
          textColor: 'text-gray-400',
          label: 'Unknown',
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();

  if (compact) {
    return (
      <div className="flex items-center gap-1.5" title={`Breathing: ${config.label}`}>
        <div className="relative">
          <div className={`w-2 h-2 rounded-full ${config.color}`} />
          {config.pulse && (
            <div className={`absolute inset-0 w-2 h-2 rounded-full ${config.pulseColor} animate-ping`} />
          )}
        </div>
        <span className={`text-xs ${config.textColor}`}>{config.label}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5">
      <div className="relative">
        <div className={`w-3 h-3 rounded-full ${config.color}`} />
        {config.pulse && (
          <div className={`absolute inset-0 w-3 h-3 rounded-full ${config.pulseColor} animate-ping`} />
        )}
      </div>
      <div className="flex flex-col">
        <span className={`text-sm font-medium ${config.textColor}`}>{config.label}</span>
        {status.confidence > 0 && (
          <span className="text-xs text-gray-400">
            {Math.round(status.confidence * 100)}% confidence
          </span>
        )}
      </div>
    </div>
  );
}
