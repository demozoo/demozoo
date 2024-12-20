function(modal) {
    modal.ajaxifyForm($('[data-edit-form]', modal.body));
    modal.ajaxifyLink($('a.delete_credit', modal.body));
}
