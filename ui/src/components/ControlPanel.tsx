import { useState, useEffect, useCallback } from 'react';
import { useSwipeable } from 'react-swipeable';
import { CameraControls } from './CameraControls';
import { MotionDetection } from './MotionDetection';
import { AudioDetection } from './AudioDetection';
import { BreathingDetection } from './BreathingDetection';
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
  onStartZoneSelection?: () => void;
  motionVisualAlertsEnabled: boolean;
  onMotionVisualAlertsToggle: (enabled: boolean) => void;
  audioVisualAlertsEnabled: boolean;
  onAudioVisualAlertsToggle: (enabled: boolean) => void;
  motionSoundAlertsEnabled: boolean;
  onMotionSoundAlertsToggle: (enabled: boolean) => void;
  audioSoundAlertsEnabled: boolean;
  onAudioSoundAlertsToggle: (enabled: boolean) => void;
  showZoneOverlay?: boolean;
  onZoneOverlayToggle?: (enabled: boolean) => void;
}

type TabId = 'presets' | 'controls' | 'motion' | 'breathing' | 'audio' | 'logs';

interface TabConfig {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const TABS: TabConfig[] = [
  {
    id: 'presets',
    label: 'Presets',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
  },
  {
    id: 'controls',
    label: 'Controls',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
      </svg>
    ),
  },
  {
    id: 'motion',
    label: 'Motion',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
  },
  {
    id: 'breathing',
    label: 'Breathing',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
  },
  {
    id: 'audio',
    label: 'Audio',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    ),
  },
  {
    id: 'logs',
    label: 'Logs',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

type LayoutMode = 'mobile' | 'tablet' | 'desktop';

function useLayoutMode(): LayoutMode {
  const [mode, setMode] = useState<LayoutMode>(() => {
    if (typeof window === 'undefined') return 'mobile';
    if (window.innerWidth >= 1024) return 'desktop';
    if (window.innerWidth >= 768) return 'tablet';
    return 'mobile';
  });

  useEffect(() => {
    let timeoutId: number;
    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        if (window.innerWidth >= 1024) {
          setMode('desktop');
        } else if (window.innerWidth >= 768) {
          setMode('tablet');
        } else {
          setMode('mobile');
        }
      }, 100);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return mode;
}

export function ControlPanel({
  isOpen,
  onToggle,
  onMotionDetected,
  onAudioDetected,
  onStartZoneSelection,
  motionVisualAlertsEnabled,
  onMotionVisualAlertsToggle,
  audioVisualAlertsEnabled,
  onAudioVisualAlertsToggle,
  motionSoundAlertsEnabled,
  onMotionSoundAlertsToggle,
  audioSoundAlertsEnabled,
  onAudioSoundAlertsToggle,
  showZoneOverlay,
  onZoneOverlayToggle,
}: ControlPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>('presets');
  const { applyPreset } = useCameraPresets();
  const [applyingPreset, setApplyingPreset] = useState<CameraPreset | null>(null);
  const [activePreset, setActivePreset] = useState<CameraPreset | null>('default');
  const layoutMode = useLayoutMode();

  const isBottomSheet = layoutMode === 'mobile' || layoutMode === 'tablet';

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

  const handlePresetClick = useCallback(async (preset: CameraPreset) => {
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
  }, [applyPreset]);

  // Setup swipe handlers (only for bottom sheet mode)
  const swipeHandlers = useSwipeable({
    onSwipedDown: () => {
      if (isOpen && isBottomSheet) {
        onToggle();
      }
    },
    trackMouse: false,
    delta: 50,
    swipeDuration: 500
  });

  const renderTabContent = useCallback(() => {
    switch (activeTab) {
      case 'presets':
        return (
          <div className="flex-1 overflow-y-auto space-y-4">
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
        );
      case 'controls':
        return (
          <div className="flex-1 overflow-y-auto">
            <ErrorBoundary>
              <CameraControls />
            </ErrorBoundary>
          </div>
        );
      case 'motion':
        return (
          <div className="flex-1 overflow-y-auto">
            <ErrorBoundary>
              <MotionDetection
                onMotionDetected={onMotionDetected}
                visualAlertsEnabled={motionVisualAlertsEnabled}
                onVisualAlertsToggle={onMotionVisualAlertsToggle}
                soundAlertsEnabled={motionSoundAlertsEnabled}
                onSoundAlertsToggle={onMotionSoundAlertsToggle}
              />
            </ErrorBoundary>
          </div>
        );
      case 'breathing':
        return (
          <div className="flex-1 overflow-y-auto">
            <ErrorBoundary>
              <BreathingDetection
                onStartZoneSelection={() => {
                  onToggle(); // Close panel first
                  onStartZoneSelection?.();
                }}
                showZoneOverlay={showZoneOverlay}
                onZoneOverlayToggle={onZoneOverlayToggle}
              />
            </ErrorBoundary>
          </div>
        );
      case 'audio':
        return (
          <div className="flex-1 overflow-y-auto">
            <ErrorBoundary>
              <AudioDetection
                onAudioDetected={onAudioDetected}
                visualAlertsEnabled={audioVisualAlertsEnabled}
                onVisualAlertsToggle={onAudioVisualAlertsToggle}
                soundAlertsEnabled={audioSoundAlertsEnabled}
                onSoundAlertsToggle={onAudioSoundAlertsToggle}
              />
            </ErrorBoundary>
          </div>
        );
      case 'logs':
        return (
          <ErrorBoundary>
            <OptimizedLogViewer isVisible={activeTab === 'logs' && isOpen} />
          </ErrorBoundary>
        );
    }
  }, [
    activeTab,
    activePreset,
    applyingPreset,
    handlePresetClick,
    isOpen,
    onToggle,
    onMotionDetected,
    onAudioDetected,
    onStartZoneSelection,
    motionVisualAlertsEnabled,
    onMotionVisualAlertsToggle,
    audioVisualAlertsEnabled,
    onAudioVisualAlertsToggle,
    motionSoundAlertsEnabled,
    onMotionSoundAlertsToggle,
    audioSoundAlertsEnabled,
    onAudioSoundAlertsToggle,
    showZoneOverlay,
    onZoneOverlayToggle,
  ]);

  // Desktop sidebar layout
  if (!isBottomSheet) {
    return (
      <>
        {/* Backdrop - click outside to close */}
        {isOpen && (
          <div
            className="absolute inset-0 bg-black/30 z-[9] transition-opacity duration-300"
            onClick={onToggle}
            aria-label="Close control panel"
          />
        )}

        {/* Desktop sidebar */}
        <div
          className={`absolute top-0 right-0 bottom-0 w-[400px] bg-gray-800 shadow-2xl
                      transform transition-transform duration-300 ease-out z-10 flex ${
                        isOpen ? 'translate-x-0' : 'translate-x-full'
                      }`}
        >
          {/* Vertical tabs on left edge */}
          <div className="flex flex-col border-r border-gray-700 bg-gray-900 py-4">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex flex-col items-center justify-center px-3 py-4 text-xs font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'text-blue-400 bg-gray-800'
                    : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/50'
                }`}
              >
                {tab.icon}
                <span className="mt-1.5">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Main content area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Header with close button */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-gray-200">
                {TABS.find(t => t.id === activeTab)?.label}
              </h2>
              <button
                onClick={onToggle}
                className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Close panel"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Tab content */}
            <div className="flex-1 p-4 overflow-hidden flex flex-col">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </>
    );
  }

  // Mobile/Tablet bottom sheet layout
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

      {/* Bottom sheet panel */}
      <div
        className={`absolute bottom-0 left-0 right-0 bg-gray-800 rounded-t-2xl shadow-2xl
                    transform transition-transform duration-300 ease-out z-10 ${
                      isOpen ? 'translate-y-0' : 'translate-y-full'
                    }`}
        style={{ maxHeight: '85vh' }}
      >
        {/* Handle bar - swipe down here to close */}
        <div {...swipeHandlers} className="flex justify-center py-3 cursor-grab active:cursor-grabbing">
          <div className="w-12 h-1.5 bg-gray-600 rounded-full"></div>
        </div>

        {/* Horizontal tabs with icon + label stacked */}
        <div className="flex border-b border-gray-700">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex flex-col items-center py-3 px-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab.icon}
              <span className="mt-1">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="p-4 overflow-y-auto" style={{ maxHeight: 'calc(85vh - 120px)' }}>
          {renderTabContent()}
        </div>
      </div>
    </>
  );
}
