/** @odoo-module **/

import { TimelineRenderer } from "@web_timeline/views/timeline/timeline_renderer.esm";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/**
 * Patch TimelineRenderer to:
 * 1. Show all resources (instructors/aircraft) even without flights
 * 2. Add zoom +/- buttons
 */
patch(TimelineRenderer.prototype, {
    /**
     * Override split_groups to include all resources from expanded groups.
     */
    async split_groups(records) {
        if (this.model.last_group_bys.length === 0) {
            return records;
        }

        const grouped_field = this.model.last_group_bys[0];
        const groups = [];
        groups.push({ id: -1, content: _t("<b>UNASSIGNED</b>"), order: -1 });

        // Try to get expanded groups from server
        let expanded_groups = [];
        try {
            const field = this.fields[grouped_field];
            if (field && field.relation) {
                // Call read_group_expand method if available
                const expansion_result = await this.orm.call(
                    this.model.model_name,
                    "get_timeline_groups",
                    [grouped_field],
                    {}
                );
                if (expansion_result && expansion_result.length > 0) {
                    expanded_groups = expansion_result;
                }
            }
        } catch (e) {
            // Method not available, fall back to default behavior
            console.log("get_timeline_groups not available, using default grouping");
        }

        // If we got expanded groups, use them
        if (expanded_groups.length > 0) {
            var seq = 1;
            for (const g of expanded_groups) {
                groups.push({
                    id: g.id,
                    content: g.display_name || g.name || `ID: ${g.id}`,
                    order: seq,
                });
                seq += 1;
            }
            return groups;
        }

        // Fall back to original behavior
        return super.split_groups(records);
    },

    /**
     * Zoom in the timeline.
     */
    _onZoomIn() {
        if (this.timeline) {
            const window = this.timeline.getWindow();
            const center = new Date((window.start.getTime() + window.end.getTime()) / 2);
            const duration = window.end.getTime() - window.start.getTime();
            const newDuration = duration * 0.5; // Zoom in by 50%
            this.timeline.setWindow(
                new Date(center.getTime() - newDuration / 2),
                new Date(center.getTime() + newDuration / 2)
            );
        }
    },

    /**
     * Zoom out the timeline.
     */
    _onZoomOut() {
        if (this.timeline) {
            const window = this.timeline.getWindow();
            const center = new Date((window.start.getTime() + window.end.getTime()) / 2);
            const duration = window.end.getTime() - window.start.getTime();
            const newDuration = duration * 2; // Zoom out by 200%
            this.timeline.setWindow(
                new Date(center.getTime() - newDuration / 2),
                new Date(center.getTime() + newDuration / 2)
            );
        }
    },
});
