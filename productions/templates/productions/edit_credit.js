function(modal) {
    modal.ajaxifyForm($('form.edit_credit_form', modal.body));
    modal.ajaxifyLink($('a.delete_credit', modal.body));
}
