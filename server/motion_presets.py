"""Motion detection preset configurations."""

from models import MotionDetectionConfig


# Motion detection presets for different scenarios
MOTION_PRESETS = {
    'sensitive': MotionDetectionConfig(
        enabled=True,
        sensitivity=0.01,  # Very sensitive - detects small movements
        min_area=300,      # Small minimum area
        cooldown_seconds=15,  # Shorter cooldown
        blur_size=15,      # Less blur for finer detail
        threshold=20       # Lower threshold
    ),
    'normal': MotionDetectionConfig(
        enabled=True,
        sensitivity=0.02,  # Default sensitivity
        min_area=500,      # Standard minimum area
        cooldown_seconds=30,  # Standard cooldown
        blur_size=21,      # Standard blur
        threshold=25       # Standard threshold
    ),
    'outdoor': MotionDetectionConfig(
        enabled=True,
        sensitivity=0.05,  # Less sensitive for outdoor conditions
        min_area=1000,     # Larger minimum area to ignore small movements
        cooldown_seconds=60,  # Longer cooldown
        blur_size=31,      # More blur to reduce noise from wind/trees
        threshold=35       # Higher threshold
    ),
    'security': MotionDetectionConfig(
        enabled=True,
        sensitivity=0.015,  # High sensitivity for security
        min_area=400,      # Medium minimum area
        cooldown_seconds=10,  # Quick notifications
        blur_size=17,      # Moderate blur
        threshold=22       # Lower threshold for night vision
    ),
    'disabled': MotionDetectionConfig(
        enabled=False,
        sensitivity=0.02,
        min_area=500,
        cooldown_seconds=30,
        blur_size=21,
        threshold=25
    )
}


def get_motion_preset(name: str) -> MotionDetectionConfig:
    """
    Get a motion detection preset by name.
    
    Args:
        name: Preset name
        
    Returns:
        MotionDetectionConfig for the preset, or 'normal' if not found
    """
    return MOTION_PRESETS.get(name, MOTION_PRESETS['normal'])


def get_preset_descriptions() -> dict:
    """
    Get descriptions for all available presets.
    
    Returns:
        Dictionary of preset names to descriptions
    """
    return {
        'sensitive': 'High sensitivity for indoor monitoring',
        'normal': 'Balanced settings for general use',
        'outdoor': 'Reduced sensitivity for outdoor environments',
        'security': 'Optimized for security monitoring',
        'disabled': 'Motion detection disabled'
    }