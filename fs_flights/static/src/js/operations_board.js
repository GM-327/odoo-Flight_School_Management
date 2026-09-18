/** @odoo-module **/

let clockIntervalId = null;
let clockObserver = null;

function updateClocks() {
    const now = new Date();
    const value = `${String(now.getUTCHours()).padStart(2, '0')}:` +
        `${String(now.getUTCMinutes()).padStart(2, '0')} Z`;
    document.querySelectorAll('.fs_operations_board #live_clock').forEach((element) => {
        element.textContent = value;
    });
}

function syncClockTimer() {
    const boardIsMounted = document.querySelector('.fs_operations_board #live_clock');
    if (boardIsMounted && !clockIntervalId) {
        updateClocks();
        clockIntervalId = setInterval(updateClocks, 1000);
    } else if (!boardIsMounted && clockIntervalId) {
        clearInterval(clockIntervalId);
        clockIntervalId = null;
    }
}

function setupClockTimer() {
    syncClockTimer();
    if (clockObserver || !document.body) {
        return;
    }
    clockObserver = new MutationObserver(syncClockTimer);
    clockObserver.observe(document.body, { childList: true, subtree: true });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupClockTimer, { once: true });
} else {
    setupClockTimer();
}

/**
 * Toggle browser fullscreen mode (like pressing F11)
 * Updates button icon and text based on current state
 */
window.toggleFullScreen = function () {
    console.log('fs_flights: toggleFullScreen called');
    const doc = document;
    const docEl = doc.documentElement;
    const btn = doc.getElementById('btn_fullscreen');

    // Check if we're currently in fullscreen
    const isFullscreen = doc.fullscreenElement ||
        doc.webkitFullscreenElement ||
        doc.mozFullScreenElement ||
        doc.msFullscreenElement;

    if (!isFullscreen) {
        // Enter fullscreen
        if (docEl.requestFullscreen) {
            docEl.requestFullscreen();
        } else if (docEl.webkitRequestFullscreen) { // Safari
            docEl.webkitRequestFullscreen();
        } else if (docEl.mozRequestFullScreen) { // Firefox
            docEl.mozRequestFullScreen();
        } else if (docEl.msRequestFullscreen) { // IE/Edge
            docEl.msRequestFullscreen();
        }
        // Update button
        if (btn) {
            btn.innerHTML = '<i class="fa fa-compress"></i> Exit Fullscreen';
            btn.classList.remove('btn-dark');
            btn.classList.add('btn-warning');
        }
    } else {
        // Exit fullscreen
        if (doc.exitFullscreen) {
            doc.exitFullscreen();
        } else if (doc.webkitExitFullscreen) { // Safari
            doc.webkitExitFullscreen();
        } else if (doc.mozCancelFullScreen) { // Firefox
            doc.mozCancelFullScreen();
        } else if (doc.msExitFullscreen) { // IE/Edge
            doc.msExitFullscreen();
        }
        // Update button
        if (btn) {
            btn.innerHTML = '<i class="fa fa-expand"></i> Fullscreen';
            btn.classList.remove('btn-warning');
            btn.classList.add('btn-dark');
        }
    }
};

// Listen for fullscreen change events to update button state
document.addEventListener('fullscreenchange', updateFullscreenButton);
document.addEventListener('webkitfullscreenchange', updateFullscreenButton);
document.addEventListener('mozfullscreenchange', updateFullscreenButton);
document.addEventListener('MSFullscreenChange', updateFullscreenButton);

function updateFullscreenButton() {
    const doc = document;
    const btn = doc.getElementById('btn_fullscreen');
    const isFullscreen = doc.fullscreenElement ||
        doc.webkitFullscreenElement ||
        doc.mozFullScreenElement ||
        doc.msFullscreenElement;

    if (btn) {
        if (isFullscreen) {
            btn.innerHTML = '<i class="fa fa-compress"></i> Exit Fullscreen';
            btn.classList.remove('btn-dark');
            btn.classList.add('btn-warning');
        } else {
            btn.innerHTML = '<i class="fa fa-expand"></i> Fullscreen';
            btn.classList.remove('btn-warning');
            btn.classList.add('btn-dark');
        }
    }
}


