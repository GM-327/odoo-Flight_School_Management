/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FsDocumentKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    async onClickUploadDocument() {
        await this.actionService.doAction("fs_documents.action_fs_document_upload_wizard", {
            additionalContext: this.props.context,
        });
    }
}

export const FsDocumentKanbanView = {
    ...KanbanView,
    Controller: FsDocumentKanbanController,
    buttonTemplate: "fs_documents.KanbanButtons",
};

registry.category("views").add("fs_document_kanban", FsDocumentKanbanView);
