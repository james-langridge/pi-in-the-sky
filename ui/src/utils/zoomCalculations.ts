/**
 * Pure functions for zoom calculations
 */

/**
 * Calculate CSS scale transform from zoom level
 * @param zoomLevel - Zoom level from 0 to 100
 * @returns Scale multiplier (1.0 to 3.0)
 */
export function calculateZoomScale(zoomLevel: number): number {
  // 0 = 1x, 50 = 2x, 100 = 3x
  return 1 + (zoomLevel / 50);
}

/**
 * Format zoom level as percentage string for display
 * @param zoomLevel - Zoom level from 0 to 100
 * @returns Formatted string like "100%" or "200%"
 */
export function formatZoomPercentage(zoomLevel: number): string {
  const scale = calculateZoomScale(zoomLevel);
  return `${Math.round(scale * 100)}%`;
}

/**
 * Load zoom level from localStorage with default fallback
 * @param defaultZoom - Default zoom level if not stored
 * @returns Stored zoom level or default
 */
export function loadZoomLevel(defaultZoom: number = 0): number {
  try {
    const stored = localStorage.getItem('videoZoomLevel');
    if (stored !== null) {
      const parsed = parseInt(stored, 10);
      if (!isNaN(parsed) && parsed >= 0 && parsed <= 100) {
        return parsed;
      }
    }
  } catch (e) {
    // localStorage might not be available
  }
  return defaultZoom;
}

/**
 * Save zoom level to localStorage
 * @param zoomLevel - Zoom level to persist
 */
export function saveZoomLevel(zoomLevel: number): void {
  try {
    localStorage.setItem('videoZoomLevel', zoomLevel.toString());
  } catch (e) {
    // localStorage might not be available
  }
}
