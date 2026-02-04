/** @odoo-module **/

import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * Live clock component for Operations Board
 * Updates every second to show current UTC time
 */
export class OperationsBoardClock extends Component {
    static template = "fs_flights.OperationsBoardClock";
    static props = {};

    setup() {
        this.intervalId = null;

        onMounted(() => {
            this.updateClock();
            this.intervalId = setInterval(() => this.updateClock(), 1000);
        });

        onWillUnmount(() => {
            if (this.intervalId) {
                clearInterval(this.intervalId);
            }
        });
    }

    updateClock() {
        const clockElement = document.getElementById('live_clock');
        if (clockElement) {
            const now = new Date();
            const hours = String(now.getUTCHours()).padStart(2, '0');
            const minutes = String(now.getUTCMinutes()).padStart(2, '0');
            clockElement.textContent = `${hours}:${minutes} Z`;
        }
    }
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

// Initialize clock when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const updateClock = () => {
        const clockElement = document.getElementById('live_clock');
        if (clockElement) {
            const now = new Date();
            const hours = String(now.getUTCHours()).padStart(2, '0');
            const minutes = String(now.getUTCMinutes()).padStart(2, '0');
            clockElement.textContent = `${hours}:${minutes} Z`;
        }
    };

    // Update immediately and then every second
    updateClock();
    setInterval(updateClock, 1000);
});

// Handle manual clock updates for non-OWL context
if (typeof owl !== 'undefined') {
    owl.whenReady(() => {
        const updateClock = () => {
            const clockElement = document.getElementById('live_clock');
            if (clockElement) {
                const now = new Date();
                const hours = String(now.getUTCHours()).padStart(2, '0');
                const minutes = String(now.getUTCMinutes()).padStart(2, '0');
                clockElement.textContent = `${hours}:${minutes} Z`;
            }
        };
        updateClock();
        setInterval(updateClock, 1000);
    });
}



