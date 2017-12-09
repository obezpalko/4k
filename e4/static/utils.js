/*eslint no-unused-vars: "off"*/
/*exported jsonApiCall */

// function jsonnames(name, obj){
//     // name=a.b.c returns obj {a: {b: {c: value}}}
//     var r = name.split(".");
//     var n = r.shift();
//     if (! n ) {
//       return obj;
//     } else {
//       if (! obj) { return null; }
//       return jsonnames(r.join("."), obj[n]);
//     }
// }
function jsonApiCall(method, url, data, dialogObj, funcSuccess = function() {
    location.reload();
    dialogObj.dialog("close");
    return false;
}, funcError = function(data) {
    alert("error on \n" + JSON.stringify(data));
    dialogObj.dialog("close");
    return false;
}) {
    $.ajax({
        type: method,
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        dataType: "json",
        url,
        data: ((data != null) ? JSON.stringify(data) : null),
        success: funcSuccess,
        error: funcError

    });
}


function loadCurrencies(url) {
    if ($("select.currency_picker").length === 0) { return false; }
    var r = "";
    $.ajax({
        dataType: "json",
        url,
        success(data) {
            $.each(data, function(key, val) {
                r += "<option value='" + val.id + "'>" + val.symbol + " " + val.title +
                    "</option>\n";
            });
            $("select.currency_picker").html(r);
        }
    });
}

function loadPeriods(url) {
    if ($("select.period_picker").length === 0) { return false; }
    var r = "";
    $.ajax({
        dataType: "json",
        url: url,
        success(data) {
            $.each(data, function(key, val) {
                r += "<option value='" + val.id + "'>" + val.title +
                    "</option>\n";
            });
            $("select.period_picker").html(r);
        }
    });
}


$(function() {
    loadCurrencies("/api/currency");
    loadPeriods("/api/period");
    /* eslint object-curly-spacing: "off" */
    $(".datepicker").datepicker({ dateFormat: $.datepicker.W3C, changeYear: true });
});