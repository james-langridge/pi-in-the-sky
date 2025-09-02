// Non-module compatibility script for iOS PWA
// iOS PWA has issues with ES6 modules, so critical functionality goes here

(function() {
    'use strict';
    
    // Version display
    var APP_VERSION = '1.1.5';
    
    // Wait for DOM
    document.addEventListener('DOMContentLoaded', function() {
        // Update version
        var versionText = document.getElementById('version-text');
        if (versionText) {
            versionText.textContent = 'v' + APP_VERSION;
        }
        
        // Control panel toggle button
        var toggleBtn = document.getElementById('toggleBtn');
        var controls = document.getElementById('controls');
        var chevron = document.getElementById('chevron');
        var controlsOpen = false;
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                controlsOpen = !controlsOpen;
                
                if (controlsOpen) {
                    controls.classList.add('open');
                    chevron.innerHTML = '<path d="M6 9l6 6 6-6"/>';
                } else {
                    controls.classList.remove('open');
                    chevron.innerHTML = '<path d="M18 15l-6-6-6 6"/>';
                }
            });
        }
        
        // Refresh button
        var refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                window.location.reload(true);
            });
        }
        
        // Stream initialization (basic version)
        var stream = document.getElementById('stream');
        var loading = document.getElementById('loading');
        
        if (stream) {
            // Simple stream setup without modules
            var baseUrl = window.location.origin;
            var timestamp = new Date().getTime();
            stream.src = baseUrl + '/video_feed?t=' + timestamp;
            
            stream.onload = function() {
                loading.style.display = 'none';
                stream.style.display = 'block';
            };
            
            stream.onerror = function() {
                // Handle stream error silently
            };
        }
    });
})();