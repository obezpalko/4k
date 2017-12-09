function jsonapicall(method, url, data, funcSuccess = function() {
    location.reload();
    $("#accounts").dialog("close");
    return false;
}, funcError = function(data) {
    alert("error on \n" + JSON.stringify(data));
    $("#accounts").dialog("close");
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
        data: JSON.stringify(data),
        success: funcSuccess,
        error: funcError

    });
}

function getFormData() {
    return {
        title: $("#accounts [name='title']").val(),
        currency: $("#accounts [name='currency.id']").val(),
        visible: $("#accounts [name='visible']").prop("checked"),
        balance: $("#accounts [name='balance']").val()
    };
}


$(function() {
    $(":input.account_visible").change(function() {
        var c = $(this).val();
        jsonapicall(
            "POST",
            "/api/account/" + c, {
                "visible": $(this).prop("checked")
            },
            function(data) {
                if (data.result !== "Ok") {
                    $(this).prop("checked", false);
                }
            },
            function() {
                $(this).prop("checked", !$(this).prop("checked"));
            }

        );
    });
    $(".account_edit").click(function() {
        var accountid = $(this).attr("href").substring(1);
        var buttons = [];
        if (accountid === '0') {
            // new account
            buttons = [{
                text: "Insert",
                click() {

                    //console.log('insert' + JSON.stringify(data));
                    jsonapicall("PUT", "/api/account", getFormData());
                }
            }];
        } else {
            // modify account

            buttons = [{
                text: "Change",
                click() {
                    jsonapicall("POST", "/api/account/" + accountid, getFormData());

                }
            }, {
                text: "Delete",
                click() {
                    jsonapicall("DELETE", "/api/account/" + accountid, {
                        delete: accountid
                    });
                }
            }];
        }
        jsonapicall("GET", "/api/account/" + accountid, null,
            function(data) {
                $("#accounts [name='id']").val(data.id);
                $("#accounts [name='title']").val(data.title);
                $("#accounts [name='currency.id']").val(data.currency.id);
                $("#accounts [name='visible']").prop("checked", data.visible);

                $("#accounts [name='balance']").val(data.balance);
                $("#accounts").dialog({
                    buttons: buttons
                }).focus();
            },
            function() {}
        );



    });
});