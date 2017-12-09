function jsonapicall(method, url, data, func_success = function() {
    location.reload();
    $("#accounts").dialog("close");
    return false;
}, func_error = function(data) {
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
        url: url,
        data: JSON.stringify(data),
        success: func_success,
        error: func_error

    });
}



$(function() {
    $(":input.account_visible").change(function() {
        var c = $(this).val();
        jsonapicall(
            "POST",
            "/api/account/" + c, {
                "visible": $(this).prop('checked')
            },
            function(data) {
                if (data.result != 'Ok') {
                    $(this).prop('checked', false);
                }
            },
            function() {
                $(this).prop('checked', !$(this).prop('checked'));
            }

        );
    });
    $('.account_edit').click(function() {
        var accountid = $(this).attr('href').substring(1);
        var buttons = [];
        var form_data = {
            title: $("#accounts [name='title']").val(),
            currency: $("#accounts [name='currency.id']").val(),
            visible: $("#accounts [name='visible']").prop('checked'),
            balance: $("#accounts [name='balance']").val()
        };
        if (accountid === '0') {
            // new account
            buttons = [{
                text: 'Insert',
                click: function() {

                    //console.log('insert' + JSON.stringify(data));
                    jsonapicall('PUT', '/api/account', form_data);
                }
            }];
        } else {
            // modify account

            buttons = [{
                text: 'Change',
                click: function() {
                    jsonapicall('POST', '/api/account/' + accountid, form_data);

                }
            }, {
                text: 'Delete',
                click: function() {
                    jsonapicall('DELETE', '/api/account/' + accountid, {
                        delete: accountid
                    });
                }
            }];
        }
        jsonapicall('GET', '/api/account/' + accountid, '',
            function(data) {
                $("#accounts [name='id']").val(data.id);
                $("#accounts [name='title']").val(data.title);
                $("#accounts [name='currency.id']").val(data.currency.id);
                $("#accounts [name='visible']").prop('checked', data.visible);

                $("#accounts [name='balance']").val(data.balance);
                $('#accounts').dialog({
                    buttons: buttons
                }).focus();
            },
            function() {}
        );



    });
});