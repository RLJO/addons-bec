odoo.inagro_room = function(instance, local) {
	var instance = odoo;
    let FormView = require('web.FormView');
    
    // override load_record
    FormView.include({
        load_record: function(record) {
        // disable only for cancel and paid account.invoice
        if (record){
            if (this.model == 'room.booking' & _.contains(['confirm', 'cancel'], record.state)){
                    $('button.oe_form_button_edit').hide()
                }else {
                    $('button.oe_form_button_edit').show()
                }
        }
        // call super
        return this._super(record);
        }
    });
}