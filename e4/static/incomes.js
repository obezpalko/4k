/*global
jsonApiCall

*/

/*eslint no-console: 0*/
function getFormData() {
    return {
        title: $("#incomes [name='title']").val(),
        currency: $("#incomes [name='currency.id']").val(),
        "start_date": $("#incomes [name='start_date']").val(),
        "end_date": $("#incomes [name='end_date']").val(),
        period: $("#incomes [name='period']").val(),
        summ: $("#incomes [name='summ']").val()
    };
}
$(function() {

    $(".income_edit").click(function() {
        var incomeid = $(this).attr("href").substring(1);
        var buttons = [{
            text: "Insert",
            click() {
                jsonApiCall("PUT", "/api/income", getFormData(), $("#incomes"));
            }
        }];
        if (incomeid !== "0") {
            buttons = [{
                text: "Change",
                click() {
                    jsonApiCall("POST", "/api/income/" + incomeid, getFormData(), $("#incomes"));
                }
            }, {
                text: "Delete",
                click() {
                    jsonApiCall("DELETE", "/api/income/" + incomeid, {
                        delete: incomeid
                    }, $("#incomes"));
                }
            }];
        }

        jsonApiCall("GET", "/api/income/" + incomeid, null, $("incomes"),
            function(data) {
                $("#incomes [name='id']").val(data.id);
                $("#incomes [name='title']").val(data.title);
                $("#incomes [name='currency.id']").val(data.currency.id);
                $("#incomes [name='period']").val(data.period.id);
                $("#incomes [name='start_date']").val(data.start_date);
                $("#incomes [name='end_date']").val(data.end_date);
                $("#incomes [name='summ']").val(data.summ);
                $("#incomes").dialog({
                    buttons
                }).focus();
            },
            function() {}
        );
    });
});