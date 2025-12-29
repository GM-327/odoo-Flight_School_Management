/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { ListView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FsDocumentListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    /**
     * Open the Document Upload Wizard
     */
    async onClickUploadDocument() {
        await this.actionService.doAction("fs_documents.action_fs_document_upload_wizard", {
            additionalContext: this.props.context,
        });
    }
}

export const FsDocumentListView = {
    ...ListView,
    Controller: FsDocumentListController,
    buttonTemplate: "fs_documents.ListButtons",
};

registry.category("views").add("fs_document_list", FsDocumentListView);
