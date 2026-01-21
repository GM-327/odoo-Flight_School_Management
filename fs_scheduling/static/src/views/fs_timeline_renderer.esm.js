/** @odoo-module **/

import { TimelineRenderer } from "@web_timeline/views/timeline/timeline_renderer.esm";
import { TimelineModel } from "@web_timeline/views/timeline/timeline_model.esm";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

import { onMounted, onPatched } from "@odoo/owl";

/**
 * Patch TimelineModel to store the current domain for filtering groups.
 */
patch(TimelineModel.prototype, {
    async load(searchParams) {
        // Store the domain for use by the renderer when fetching groups
        this.domain = searchParams.domain || [];
        return super.load(searchParams);
    },
});

/**
 * Patch TimelineRenderer to:
 * 1. Show all resources (instructors/aircraft) even without flights
 * 2. Add zoom +/- buttons
 * 3. Auto-scroll to first flight for "Tomorrow's Flights"
 */
patch(TimelineRenderer.prototype, {
    setup() {
        super.setup();
        this.hasScrolledToFirst = false;
        onMounted(this.scrollToFirstFlight);
        onPatched(this.scrollToFirstFlight);
    },

    async scrollToFirstFlight(retryCount = 0) {
        // Stop if we've already succeeded
        if (this.hasScrolledToFirst) return;

        // Check context - support both searchModel (standard) and props context
        const context = this.env.searchModel?.context || this.props.context || {};

        // Relaxed check: if search_default_tomorrow is missing, check active filters
        let isTomorrow = context.search_default_tomorrow;

        if (!isTomorrow && this.env.searchModel && typeof this.env.searchModel.getSearchItems === 'function') {
            const filters = this.env.searchModel.getSearchItems((item) => item.name === 'tomorrow');
            // Check if any "tomorrow" filter is active
            if (filters.some(f => f.isActive)) {
                isTomorrow = true;
            }
        }

        if (!isTomorrow) {
            return;
        }

        if (!this.timeline) {
            // If timeline not ready, retry a few times
            if (retryCount < 5) {
                setTimeout(() => this.scrollToFirstFlight(retryCount + 1), 200);
            }
            return;
        }

        // Check for items
        const itemIds = this.timeline.itemsData.getIds();
        if (itemIds.length === 0) {
            // Data might not be loaded yet, retry
            if (retryCount < 10) { // Retry for up to 2 seconds
                setTimeout(() => this.scrollToFirstFlight(retryCount + 1), 200);
            }
            return;
        }

        // Find earliest start time
        const items = this.timeline.itemsData.get(itemIds);
        let minDate = null;

        for (const item of items) {
            if (item.start) {
                const start = new Date(item.start);
                // Simple check: start date must be valid
                if (!isNaN(start.getTime())) {
                    if (!minDate || start < minDate) {
                        minDate = start;
                    }
                }
            }
        }

        if (minDate) {
            // Focus on the flight with a slight offset (e.g. 1 hour before) to make it look nice
            // But centering is also fine.
            this.timeline.moveTo(minDate, { animation: { duration: 1000, easingFunction: 'easeInOutQuad' } });

            this.hasScrolledToFirst = true;
        }
    },

    /**
     * Override split_groups to include all resources from expanded groups.
     * Pass current domain to backend so filters (like "Hide Simulators") also affect groups.
     */
    async split_groups(records) {
        if (this.model.last_group_bys.length === 0) {
            return records;
        }

        const grouped_field = this.model.last_group_bys[0];
        const groups = [];
        groups.push({ id: -1, content: _t("<b>UNASSIGNED</b>"), order: -1 });

        // Get current search domain to pass to backend
        const currentDomain = this.model.domain || [];

        // Try to get expanded groups from server
        let expanded_groups = [];
        try {
            const field = this.fields[grouped_field];
            if (field && field.relation) {
                // Call get_timeline_groups with domain parameter
                const expansion_result = await this.orm.call(
                    this.model.model_name,
                    "get_timeline_groups",
                    [grouped_field, currentDomain],
                    {}
                );
                if (expansion_result && expansion_result.length > 0) {
                    expanded_groups = expansion_result;
                }
            }
        } catch (e) {
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
