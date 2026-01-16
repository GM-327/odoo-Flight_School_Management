/** @odoo-module **/

import { TimelineController } from "@web_timeline/views/timeline/timeline_controller.esm";
import { patch } from "@web/core/utils/patch";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { makeContext } from "@web/core/context";

/**
 * Patch TimelineController to add a "New" button in the control panel,
 * similar to the List view.
 */
patch(TimelineController.prototype, {
    /**
     * Handle click on the "New" button.
     * Opens a new form view dialog to create a new record.
     */
    onClickCreate() {
        const context = {};

        // If there is a group, set the default group field value
        if (this.model.last_group_bys && this.model.last_group_bys.length > 0) {
            // We don't set a default group since we're creating from the button
            // not from clicking on a specific group row in the timeline
        }

        // Open form view dialog for creating a new record
        this.dialogService.add(
            FormViewDialog,
            {
                resId: false,
                context: makeContext([context], this.env.searchModel.context),
                onRecordSaved: async () => {
                    await this.model.load(this.getSearchProps());
                    this.render();
                },
                resModel: this.model.model_name,
            },
            { onClose: () => { } }
        );
    },
});
