/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Soft Refresh Field Widget
 * 
 * Refreshes the form view without a full page reload,
 * thereby preserving the fullscreen state.
 */
export class SoftRefreshField extends Component {
    static template = "fs_flights.SoftRefreshField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({ isRefreshing: false });
    }

    /**
     * Trigger a soft reload of the current record.
     * This refreshes the data without exiting fullscreen.
     */
    async softRefresh() {
        if (this.state.isRefreshing) {
            return; // Prevent double-clicks
        }

        this.state.isRefreshing = true;

        try {
            // Get the root model and reload it
            // This will refresh all computed fields and related data
            const record = this.props.record;
            if (record && record.model) {
                // Use the model's root to reload
                await record.model.root.load();
            }
        } catch (error) {
            console.warn("Soft refresh error:", error);
        } finally {
            // Only update state if component is still mounted
            if (this.state) {
                this.state.isRefreshing = false;
            }
        }
    }
}

export const softRefreshField = {
    component: SoftRefreshField,
    supportedTypes: ["boolean"],
};

registry.category("fields").add("soft_refresh", softRefreshField);
