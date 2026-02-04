/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class FullscreenToggleField extends Component {
    static template = "fs_flights.FullscreenToggleField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({ isFullscreen: false });
        // Handle external changes to fullscreen state (e.g. Esc key)
        document.addEventListener('fullscreenchange', this.updateState.bind(this));
    }

    updateState() {
        this.state.isFullscreen = !!document.fullscreenElement;
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
}

export const fullscreenToggleField = {
    component: FullscreenToggleField,
    supportedTypes: ["boolean"],
};

registry.category("fields").add("fullscreen_toggle", fullscreenToggleField);
