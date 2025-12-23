/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";

patch(ProgressBarField.prototype, {
    /**
     * Override the progress bar color class based on the percentage value.
     */
    get progressBarColorClass() {
        const value = this.currentValue;
        const max = this.maxValue;

        // Use overflow class if value exceeds max
        if (value > max) {
            return this.props.overflowClass || "bg-success";
        }

        // Calculate percentage (default to 0 if max is 0)
        const percentage = max > 0 ? (value / max) * 100 : 0;

        // Apply color levels
        if (percentage < 30) {
            return "bg-danger";    // Red
        } else if (percentage < 70) {
            return "bg-warning";   // Orange/Yellow
        } else {
            return "bg-success";   // Green
        }
    }
});
