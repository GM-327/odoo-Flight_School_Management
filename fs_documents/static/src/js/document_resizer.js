
/** @odoo-module **/

// Simple resizable splitter logic for Odoo 19
// Finds elements with class .o_document_splitter_handle and enables drag-to-resize

(function () {
    let isResizing = false;

    document.addEventListener('mousedown', function (e) {
        const handle = e.target.closest('.o_document_splitter_handle');
        if (!handle) return;

        isResizing = true;
        const container = handle.closest('.o_document_form_container');
        const leftPane = container.querySelector('.o_document_form_main');

        const startX = e.pageX;
        const startWidth = leftPane.offsetWidth;
        const containerWidth = container.offsetWidth;

        // Add overlay to prevent iframe interference during drag
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100vw';
        overlay.style.height = '100vh';
        overlay.style.zIndex = '9999';
        overlay.style.cursor = 'col-resize';
        document.body.appendChild(overlay);

        function onMouseMove(e) {
            if (!isResizing) return;
            const delta = e.pageX - startX;
            let newWidth = startWidth + delta;

            // Constraints
            if (newWidth < 300) newWidth = 300;
            if (newWidth > containerWidth * 0.8) newWidth = containerWidth * 0.8;

            leftPane.style.flex = `0 0 ${newWidth}px`;
            leftPane.style.width = `${newWidth}px`;
        }

        function onMouseUp() {
            isResizing = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        e.preventDefault();
    });
})();
