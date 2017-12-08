function json_api_call(method, url, data, func_success, func_error) {
    $.ajax({
        type: method,
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        dataType: 'json',
        url: url,
        data: JSON.stringify(data),
        success: func_success,
        error: func_error

    });
}

function load_currencies(url) {
    var r = '';
    $.ajax({
        dataType: "json",
        url: url,
        success: function(data) {
            $.each(data, function(key, val) {
                r += '<option value="' + val.id + '">' + val.symbol + ' ' + val.title +
                    '</option>\n';
            });
            $("select[name='currency.id']").html(r);
        }
    });
}

$(function() {
    $(":input.account_visible").change(function() {
        var c = $(this).val();
        json_api_call(
            'POST',
            "/api/account/" + c, {
                'visible': $(this).prop('checked')
            },
            function(data) {
                // console.log('data +' + JSON.stringify(data));
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
        if (accountid === '0') {
            // new account
            buttons = [{
                text: 'Insert',
                click: function() {
                    var data = {
                        title: $("#accounts [name='title']").val(),
                        currency: $("#accounts [name='currency.id']").val(),
                        visible: $("#accounts [name='visible']").prop('checked'),
                        balance: $("#accounts [name='balance']").val()
                    };
                    //console.log('insert' + JSON.stringify(data));
                    json_api_call('PUT', '/api/account', data,
                        function() {
                            location.reload();
                            $('#accounts').dialog("close");
                            return false;
                        },
                        function(data) {
                            alert('error on \n' + JSON.stringify(data));
                            $('#accounts').dialog("close");
                            return false;
                        }
                    );
                }
            }];
        } else {
            // modify account

            buttons = [{
                text: 'Change',
                click: function() {
                    json_api_call('POST', '/api/account/' + accountid, {
                            title: $("#accounts [name='title']").val(),
                            currency: $("#accounts [name='currency.id']").val(),
                            visible: $("#accounts [name='visible']").prop('checked'),
                            balance: $("#accounts [name='balance']").val()
                        },
                        function() {
                            location.reload();
                            $('#accounts').dialog("close");
                            return false;
                        },
                        function(data) {
                            alert('error on \n' + JSON.stringify(data));
                            $('#accounts').dialog("close");
                            return false;
                        }
                    );

                }
            }, {
                text: 'Delete',
                click: function() {
                    json_api_call('DELETE', '/api/account/' + accountid, {
                            delete: accountid
                        },
                        function() {
                            location.reload();
                            $('#accounts').dialog("close");
                            return false;
                        },
                        function(data) {
                            alert('error on \n' + JSON.stringify(data));
                            $('#accounts').dialog("close");
                            return false;
                        }
                    );
                }
            }];
        }
        json_api_call('GET', '/api/account/' + accountid, '',
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
    load_currencies('/api/currency');
});