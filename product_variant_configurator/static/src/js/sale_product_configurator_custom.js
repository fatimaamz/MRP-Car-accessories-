/** @odoo-module **/

import { registry } from "@web/core/registry";
import { SaleProductConfigurator } from "sale_product_configurator.SaleProductConfigurator";

class CustomSaleProductConfigurator extends SaleProductConfigurator {
    setup() {
        super.setup();
        if (!this.state.color_option) {
            this.state.color_option = 'paint_match';
        }
    }

    getPayload() {
        const payload = super.getPayload();
        payload.color_option = this.state.color_option;
        return payload;
    }

    onColorOptionChange(event) {
        this.state.color_option = event.target.value;
        // Re-render to apply the filter
        this.render();
    }

    getFilteredProducts() {
        return this.props.products.filter(product => 
            product.product_tmpl_id.color_option === this.state.color_option);
    }
}

registry.category("actionHandlers").add("sale_product_configurator_custom", CustomSaleProductConfigurator);
