# _*_ coding: utf-8 _*
import openerp.http as http
import string

class PageOneControl(http.Controller):
    @http.route("/page_one",auth="user",methods=["GET", "POST"],csrf =False)
    def page_one_index(self,val1="None"):
        Thing = http.request.env["todo.thing"].sudo()
        things = Thing.search([])

        values = dict()
        values["title"] = things._name
        values["count"] = len(things)
        values["things"] = things
        values["val1"] = val1

        return http.request.render("todo.page_one_template",values)
