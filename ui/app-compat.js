// Non-module compatibility script for iOS PWA
// iOS PWA has issues with ES6 modules, so critical functionality goes here

(function() {
    'use strict';
    
    console.log('APP-COMPAT: Non-module script loading');
    
    // Version display
    var APP_VERSION = '1.1.4';
    
    // Wait for DOM
    document.addEventListener('DOMContentLoaded', function() {
        console.log('APP-COMPAT: DOM ready');
        
        // Visual indicators that JS is working
        document.body.style.borderTop = '5px solid blue';
        
        // Update version
        var versionText = document.getElementById('version-text');
        if (versionText) {
            var buildTime = new Date().toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            versionText.textContent = 'v' + APP_VERSION + ' (compat)';
            versionText.style.color = '#00ff00';
        }
        
        // Update JS status
        var jsStatus = document.getElementById('js-status');
        if (jsStatus) {
            jsStatus.textContent = 'COMPAT MODE';
            jsStatus.style.color = 'blue';
        }
        
        // Control panel toggle button
        var toggleBtn = document.getElementById('toggleBtn');
        var controls = document.getElementById('controls');
        var chevron = document.getElementById('chevron');
        var controlsOpen = false;
        
        if (toggleBtn) {
            console.log('APP-COMPAT: Adding toggle button handler');
            toggleBtn.addEventListener('click', function() {
                console.log('APP-COMPAT: Toggle button clicked');
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
        
        // Test button with counter
        var testCounter = 0;
        var testButton = document.getElementById('test-button');
        var testCounterEl = document.getElementById('test-counter');
        
        if (testButton) {
            console.log('APP-COMPAT: Adding test button handler');
            testButton.addEventListener('click', function() {
                console.log('APP-COMPAT: Test button clicked');
                testCounter++;
                if (testCounterEl) {
                    testCounterEl.textContent = testCounter;
                }
            });
        }
        
        // Refresh button
        var refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            console.log('APP-COMPAT: Adding refresh button handler');
            refreshBtn.addEventListener('click', function() {
                console.log('APP-COMPAT: Refresh requested');
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
                console.log('APP-COMPAT: Stream loaded');
                loading.style.display = 'none';
                stream.style.display = 'block';
            };
            
            stream.onerror = function() {
                console.log('APP-COMPAT: Stream error');
            };
        }
        
        console.log('APP-COMPAT: Setup complete');
    });
})();