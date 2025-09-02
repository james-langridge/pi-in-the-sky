import { useState, useEffect } from 'react';
import { useCameraControls } from '../api/hooks';
import type { CameraControl } from '../types';

export function CameraControls() {
  const { controls, loading, updateControl } = useCameraControls();
  const [localValues, setLocalValues] = useState<Record<string, any>>({});
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Image Quality']));

  // Initialize local values when controls load
  useEffect(() => {
    const values: Record<string, any> = {};
    controls.forEach(control => {
      values[control.id] = control.value;
    });
    setLocalValues(values);
  }, [controls]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Group controls by category
  const categories = controls.reduce((acc, control) => {
    if (!acc[control.category]) {
      acc[control.category] = [];
    }
    acc[control.category].push(control);
    return acc;
  }, {} as Record<string, CameraControl[]>);

  const handleSliderChange = (control: CameraControl, value: number) => {
    setLocalValues(prev => ({ ...prev, [control.id]: value }));
  };

  const handleSliderRelease = async (control: CameraControl) => {
    const value = localValues[control.id];
    await updateControl(control.id, value);
  };

  const handleSwitchChange = async (control: CameraControl, checked: boolean) => {
    setLocalValues(prev => ({ ...prev, [control.id]: checked }));
    await updateControl(control.id, checked);
  };

  const handleSelectChange = async (control: CameraControl, value: string) => {
    setLocalValues(prev => ({ ...prev, [control.id]: value }));
    await updateControl(control.id, value);
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const renderControl = (control: CameraControl) => {
    const value = localValues[control.id] ?? control.value;

    switch (control.type) {
      case 'slider':
        return (
          <div key={control.id} className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm text-gray-300">{control.name}</label>
              <span className="text-sm text-gray-400 font-mono">{value}</span>
            </div>
            <input
              type="range"
              min={control.min}
              max={control.max}
              step={control.step}
              value={value}
              onChange={(e) => handleSliderChange(control, parseFloat(e.target.value))}
              onMouseUp={() => handleSliderRelease(control)}
              onTouchEnd={() => handleSliderRelease(control)}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer 
                       [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 
                       [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-blue-500 
                       [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer
                       [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 
                       [&::-moz-range-thumb]:bg-blue-500 [&::-moz-range-thumb]:rounded-full 
                       [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer"
            />
          </div>
        );

      case 'switch':
        return (
          <div key={control.id} className="flex justify-between items-center">
            <label className="text-sm text-gray-300">{control.name}</label>
            <button
              onClick={() => handleSwitchChange(control, !value)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                value ? 'bg-blue-500' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  value ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        );

      case 'select':
        return (
          <div key={control.id} className="space-y-2">
            <label className="text-sm text-gray-300">{control.name}</label>
            <select
              value={value}
              onChange={(e) => handleSelectChange(control, e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 text-gray-200 rounded-lg border border-gray-600 
                       focus:border-blue-500 focus:outline-none"
            >
              {control.options?.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {Object.entries(categories).map(([category, categoryControls]) => (
        <div key={category} className="border border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleCategory(category)}
            className="w-full px-4 py-3 bg-gray-800 hover:bg-gray-750 transition-colors 
                     flex justify-between items-center text-left"
          >
            <span className="font-medium text-gray-200">{category}</span>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${
                expandedCategories.has(category) ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {expandedCategories.has(category) && (
            <div className="p-4 space-y-4 bg-gray-800/50">
              {categoryControls.map(control => renderControl(control))}
            </div>
          )}
        </div>
      ))}

      {Object.keys(categories).length === 0 && (
        <div className="text-center py-8 text-gray-400">
          <p>No camera controls available</p>
          <p className="text-sm mt-2">Camera may not be connected</p>
        </div>
      )}
    </div>
  );
}