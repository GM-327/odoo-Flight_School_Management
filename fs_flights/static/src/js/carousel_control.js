/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CarouselControl extends Component {
    static template = "fs_flights.CarouselControl";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.isUnmounted = false;
        this.state = useState({
            isPlaying: true, // Default to playing
            interval: 10,
            timerId: null,
            progress: 0,
        });

        onMounted(async () => {
            let interval = 10;
            try {
                const result = await this.orm.call(
                    this.props.record.resModel,
                    "get_carousel_interval",
                    [],
                );
                const configuredInterval = Number.parseInt(result, 10);
                if (Number.isInteger(configuredInterval) && configuredInterval >= 0) {
                    interval = configuredInterval;
                }
            } catch (error) {
                console.warn("CarouselControl: failed to read interval; using default", error);
            }

            if (this.isUnmounted) return;
            this.state.interval = interval;

            if (this.state.interval > 0) {
                this.startTimer();
            } else {
                this.state.isPlaying = false; // Disable if interval is 0
            }
        });

        onWillUnmount(() => {
            this.isUnmounted = true;
            this.stopTimer();
        });
    }

    startTimer() {
        if (this.state.timerId || this.state.interval <= 0) return;

        // Use a simple Interval to trigger next page
        this.state.timerId = setInterval(() => {
            this.triggerNextPage();
        }, this.state.interval * 1000);

        this.state.isPlaying = true;
    }

    stopTimer() {
        if (this.state.timerId) {
            clearInterval(this.state.timerId);
            this.state.timerId = null;
        }
        this.state.isPlaying = false;
    }

    togglePlay() {
        if (this.state.interval <= 0) return;
        if (this.state.isPlaying) {
            this.stopTimer();
        } else {
            this.startTimer();
        }
    }

    async triggerNextPage() {
        // Trigger the backend action_next_page
        // Ensure we have a valid ID
        const resId = this.props.record.resId;

        if (!resId) {
            console.warn("CarouselControl: No valid record ID found, skipping auto-advance");
            return;
        }

        try {
            await this.orm.call(
                this.props.record.resModel,
                'action_next_page',
                [resId]
            );
            // Force view reload to reflect changes
            await this.props.record.model.load();
        } catch (e) {
            console.error("Carousel auto-advance failed:", e);
            this.stopTimer(); // Stop on error
        }
    }
}

export const carouselControl = {
    component: CarouselControl,
    supportedTypes: ["boolean"],
};

registry.category("fields").add("carousel_control", carouselControl);
