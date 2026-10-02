/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Group } from "@web/model/relational_model/group";

patch(Group.prototype, {
    setup(config, data) {
        super.setup(...arguments);
        this.values = data.values;
    }
});
