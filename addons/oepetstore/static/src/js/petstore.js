odoo.define('oepetstore.service', function (require) {
    var core = require("web.core");
    var utils = require('web.utils');
    var Model = require('web.Model');
    var Widget = require("web.Widget")


    var HomePage = Widget.extend({
        start: function () {
            this.$el.append("<div>Hello dear Odoo user!</div>");
        },
    });

    core.action_registry.add("petstore.homepage", HomePage)

    var MyClass = window.Backbone.Model.extend({
        say_hello: function () {
            console.log("hello");
        },
    });

    var my_object = new MyClass();
    my_object.say_hello();
});