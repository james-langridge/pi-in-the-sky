import { useState, useEffect } from 'react';
import { useSwipeable } from 'react-swipeable';
import { CameraControls } from './CameraControls';
import { MotionDetection } from './MotionDetection';
import { AudioDetection } from './AudioDetection';
import { OptimizedLogViewer } from './OptimizedLogViewer';
import { ErrorBoundary } from './ErrorBoundary';
import { useCameraPresets } from '../api/hooks';
import { toast } from 'react-toastify';
import type { CameraPreset } from '../types';

interface ControlPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  onMotionDetected?: () => void;
  onAudioDetected?: () => void;
  motionVisualAlertsEnabled: boolean;
  onMotionVisualAlertsToggle: (enabled: boolean) => void;
  audioVisualAlertsEnabled: boolean;
  onAudioVisualAlertsToggle: (enabled: boolean) => void;
  motionSoundAlertsEnabled: boolean;
  onMotionSoundAlertsToggle: (enabled: boolean) => void;
  audioSoundAlertsEnabled: boolean;
  onAudioSoundAlertsToggle: (enabled: boolean) => void;
}

export function ControlPanel({
  isOpen,
  onToggle,
  onMotionDetected,
  onAudioDetected,
  motionVisualAlertsEnabled,
  onMotionVisualAlertsToggle,
  audioVisualAlertsEnabled,
  onAudioVisualAlertsToggle,
  motionSoundAlertsEnabled,
  onMotionSoundAlertsToggle,
  audioSoundAlertsEnabled,
  onAudioSoundAlertsToggle
}: ControlPanelProps) {
  const [activeTab, setActiveTab] = useState<'presets' | 'controls' | 'motion' | 'audio' | 'logs'>('presets');
  const { applyPreset } = useCameraPresets();
  const [applyingPreset, setApplyingPreset] = useState<CameraPreset | null>(null);
  const [activePreset, setActivePreset] = useState<CameraPreset | null>('default');

  // Close panel with Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onToggle();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onToggle]);

  const handlePresetClick = async (preset: CameraPreset) => {
    setApplyingPreset(preset);
    const success = await applyPreset(preset);
    if (success) {
      const presetName = preset === 'default' ? 'Default' : 
                        preset === 'low_light' ? 'Low Light' : 
                        preset === 'bright' ? 'Bright' : preset;
      toast.success(`Applied ${presetName} preset`);
      setActivePreset(preset);
      setTimeout(() => setApplyingPreset(null), 1000);
    } else {
      toast.error(`Failed to apply preset`);
      setApplyingPreset(null);
    }
  };

  // Setup swipe handlers
  const swipeHandlers = useSwipeable({
    onSwipedDown: () => {
      if (isOpen) {
        onToggle();
      }
    },
    trackMouse: false,
    delta: 50,
    swipeDuration: 500
  });

  return (
    <>
      {/* Backdrop - click outside to close */}
      {isOpen && (
        <div
          className="absolute inset-0 bg-black/50 z-[9] transition-opacity duration-300"
          onClick={onToggle}
          aria-label="Close control panel"
        />
      )}

      {/* Control panel */}
      <div
        className={`absolute bottom-0 left-0 right-0 bg-gray-800 rounded-t-2xl shadow-2xl
                    transform transition-transform duration-300 ease-out z-10 ${
                      isOpen ? 'translate-y-0' : 'translate-y-full'
                    }`}
        style={{ maxHeight: '70vh' }}
      >
        {/* Handle bar - swipe down here to close */}
        <div {...swipeHandlers} className="flex justify-center py-3 cursor-grab active:cursor-grabbing">
          <div className="w-12 h-1.5 bg-gray-600 rounded-full"></div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setActiveTab('presets')}
            className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
              activeTab === 'presets'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Presets
          </button>
          <button
            onClick={() => setActiveTab('controls')}
            className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
              activeTab === 'controls'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Controls
          </button>
          <button
            onClick={() => setActiveTab('motion')}
            className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
              activeTab === 'motion'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Motion
          </button>
          <button
            onClick={() => setActiveTab('audio')}
            className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
              activeTab === 'audio'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Audio
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
              activeTab === 'logs'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Logs
          </button>
        </div>

        {/* Tab content */}
        <div className="p-4 overflow-y-auto" style={{ maxHeight: 'calc(70vh - 100px)' }}>
          {activeTab === 'presets' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Camera Presets</h3>
              
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => handlePresetClick('default')}
                  disabled={applyingPreset !== null}
                  className={`p-4 rounded-lg border transition-all ${
                    activePreset === 'default'
                      ? 'bg-green-600 border-green-500 text-white'
                      : applyingPreset === 'default'
                      ? 'bg-blue-500 border-blue-400 text-white'
                      : 'bg-gray-700 border-gray-600 text-gray-200 hover:bg-gray-600'
                  } disabled:opacity-50`}
                >
                  <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                  </svg>
                  <span className="text-sm font-medium">Default</span>
                  <p className="text-xs opacity-75 mt-1">Standard settings</p>
                </button>

                <button
                  onClick={() => handlePresetClick('low_light')}
                  disabled={applyingPreset !== null}
                  className={`p-4 rounded-lg border transition-all ${
                    activePreset === 'low_light'
                      ? 'bg-green-600 border-green-500 text-white'
                      : applyingPreset === 'low_light'
                      ? 'bg-blue-500 border-blue-400 text-white'
                      : 'bg-gray-700 border-gray-600 text-gray-200 hover:bg-gray-600'
                  } disabled:opacity-50`}
                >
                  <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span className="text-sm font-medium">Low Light</span>
                  <p className="text-xs opacity-75 mt-1">Night vision</p>
                </button>

                <button
                  onClick={() => handlePresetClick('bright')}
                  disabled={applyingPreset !== null}
                  className={`p-4 rounded-lg border transition-all ${
                    activePreset === 'bright'
                      ? 'bg-green-600 border-green-500 text-white'
                      : applyingPreset === 'bright'
                      ? 'bg-blue-500 border-blue-400 text-white'
                      : 'bg-gray-700 border-gray-600 text-gray-200 hover:bg-gray-600'
                  } disabled:opacity-50`}
                >
                  <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                  </svg>
                  <span className="text-sm font-medium">Bright</span>
                  <p className="text-xs opacity-75 mt-1">Outdoor daylight</p>
                </button>

                <button
                  onClick={() => {
                    // Reset all controls to default
                    handlePresetClick('default');
                  }}
                  disabled={applyingPreset !== null}
                  className="p-4 rounded-lg border bg-gray-700 border-gray-600 text-gray-200 
                           hover:bg-gray-600 transition-all disabled:opacity-50"
                >
                  <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="text-sm font-medium">Reset All</span>
                  <p className="text-xs opacity-75 mt-1">Factory defaults</p>
                </button>
              </div>
            </div>
          )}

          {activeTab === 'controls' && (
            <ErrorBoundary>
              <CameraControls />
            </ErrorBoundary>
          )}
          
          {activeTab === 'motion' && (
            <ErrorBoundary>
              <MotionDetection 
                onMotionDetected={onMotionDetected}
                visualAlertsEnabled={motionVisualAlertsEnabled}
                onVisualAlertsToggle={onMotionVisualAlertsToggle}
                soundAlertsEnabled={motionSoundAlertsEnabled}
                onSoundAlertsToggle={onMotionSoundAlertsToggle}
              />
            </ErrorBoundary>
          )}
          
          {activeTab === 'audio' && (
            <ErrorBoundary>
              <AudioDetection
                onAudioDetected={onAudioDetected}
                visualAlertsEnabled={audioVisualAlertsEnabled}
                onVisualAlertsToggle={onAudioVisualAlertsToggle}
                soundAlertsEnabled={audioSoundAlertsEnabled}
                onSoundAlertsToggle={onAudioSoundAlertsToggle}
              />
            </ErrorBoundary>
          )}

          {activeTab === 'logs' && (
            <ErrorBoundary>
              <OptimizedLogViewer isVisible={activeTab === 'logs' && isOpen} />
            </ErrorBoundary>
          )}
        </div>
      </div>
    </>
  );
}