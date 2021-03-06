/*g lobal
loadCurrencies
*/

/*
var balance_url;
var d = new Date();
balance_url = '/api/balance/0/' + getFirstWeek(d) + '/' + addMonths(getFirstWeek(d), 6);

function load_table(table_name, url) {
    $('#' + table_name + ' tr').not('.template').not('.table_header').remove();
    var template = $('#' + table_name).find('tr.template');
    var new_row, n;
    $.getJSON(url, function(data) {
        $.each(data, function(k, v) {
            if (v['deleted'] == 'y') { return false; }
            new_row = template.clone(true).removeClass('template');
            new_row.find('.row_update').each(function() {
                $(this).text(jsonnames($(this).attr('name'), v));
            });
            template.after(new_row);
            new_row.show();
        });
    });
}

function prepare_transfer(event) {
    var source_account = $(event.target).parents('form').find('[name="account.id"]').val();
    var already_set = false;
    var parent_form = $(event.target).parents('form');
    parent_form.find('.transfer').show().addClass('form_save').prop('disabled', true);
    $('#transfer-dialog').find('[name="account.name"]').val(source_account).prop('disabled', true);
    $('#transfer-dialog').find('[name="transfer.account"]').val((source_account + 1) % $('#transfer-dialog').find('[name="transfer.account"]').children('option').length);
    $('#transfer-dialog').find('[name="transfer.account"]').children('option').each(function() {
        if (!already_set && $(this).val() != source_account) {
            $(this).parent().val($(this).val());
            already_set = true;
        }
        $(this).prop('disabled', $(this).val() == source_account);
    });

    $('#transfer-dialog').dialog({
        buttons: [{
            text: 'Ok',
            click: function() {
                parent_form.find('[name="new_account.id"]').val($(this).dialog().find('[name="transfer.account"]').val());
                parent_form.find('[name="new_sum"]').val($(this).dialog().find('[name="transfer.sum"]').val());
                $(this).dialog("close");
            }
        }]
    }).focus();
}

function get_balance(url) {
    $.getJSON('/api/currency', function(data) {
        var c = [];
        $.each(data, function(c_index, currency) {
            c.push('<dt>' + currency['title'] + '</dt>');
        });
        c.push('<dt>TOTAL</dt>');
        c.push('<dt>weeks</dt>');
        c.push('<dt>weekly</dt>');
        $('#balance dl.balance').html(c.join(''));

        $.getJSON(url, function(data) {
            $.each(data, function(key, val) {
                $('#balance dt').each(function() {
                    if ($(this).text() == key) {
                        $(this).after('<dd>' + val + '</dd>');
                    }
                });
                if (['start_date', 'end_date'].indexOf(key) > -1) {
                    $('#balance input.' + key).val(val);
                }
            });
            $.getJSON('/api/accounts', function(data) {
                var c = [];
                $.each(data, function(k, v) {
                    if (v['show'] == 'y') {
                        c.push('<dt>' + v['title'] + ' ' + v['currency']['title'] + '</dt><dd>' + v['sum'] + '</dd>');
                    }
                });
                $('#balance dl.accounts').html(c.join(''));
            });
        });
    });
    $('#balance').show();
}


function get_accounts(url, titlefields = ["title", "currency.title"]) {
    $.getJSON(url, function(data) {
        var options = [];
        $.each(data, function(key, val) {
            titles = [];
            titlefields.forEach(function(t) {
                titles.push((t == "title") ? val[t] : val[t]["title"]);
            });
            options.push("<li>" + titles.join(" ") + "</li>");
        });
        $("#accounts").html(options.join("")).show();
    });
}


function update_row(event, to_update, clean = false) {
    var id = $(event.target).parents('tr').find("[name=id]").text();
    var row = $(event.target).parents('tr');
    var template = $(event.target).parents('table').find('tr.template');
    // var first_row = $(event.target).parents('tr').siblings().first();
    var buttons = [];
    if (clean) {
        $('form#' + to_update)[0].reset();
        $('#' + to_update).find('input.set_today.datepicker').datepicker('setDate', new Date());
    }
    var transfer_id = 0;
    row.find('.row_update').each(function() {
        var n, v;
        n = $(this).attr('name');
        v = $(this).text().trim();
        $("#" + to_update).find("[name='" + n + "']").each(function() {
            $(this).val(v);
        });
        if (n == "transfer" && v > 0) {
            transfer_id = v;
        }
    });

    // check transfer
    if (transfer_id > 0) {
        console.log('do transfer');
        var j = $.getJSON('/api/transactions/' + transfer_id, function(data) {
            $('#' + to_update).find('[name=new_sum]').val(data['sum']).prop('disabled', true).show();
            $('#' + to_update).find('[name="new_account.id"]').val(data['account']['id']).prop('disabled', true).show();
            $('#' + to_update).find('.transfer-button').hide();
            console.log(data);
        });
        $('#' + to_update).find('.transfer-button').show();
    } else {

    }

    if (!clean) {
        buttons = [{
                text: 'Delete',
                click: function() {
                    var data = {};
                    $(this).dialog().find(".form_save").each(function(f, k) {
                        data[k.name] = k.value.replace(/^\s+|\s+$/g, '');
                    });
                    $.ajax({
                        type: "DELETE",
                        url: "/api/" + to_update + "/" + id,
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        },
                        dataType: 'json',
                        //data: "id=" + id,
                        data: JSON.stringify(data),
                        success: function(msg) {
                            row.remove();
                            get_balance(balance_url);
                            // reload_all();

                        }
                    });
                    $(this).dialog("close");
                }
            },
            {
                text: 'Ok',
                click: function() {
                    var data_ = {};
                    $(this).dialog().find(".form_save").each(function(f, k) {
                        data_[k.name] = k.value.replace(/^\s+|\s+$/g, '');
                    });
                    $.ajax({
                        type: "PUT",
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        },
                        dataType: 'json',
                        url: "/api/" + to_update + "/" + id,
                        data: JSON.stringify(data_),
                        success: function(data) {
                            updated = data['updated'];
                            row.find('.row_update').each(function() {
                                $(this).text(jsonnames($(this).attr('name'), updated));
                            });

                            get_balance(balance_url);
                            // reload_all();

                        }
                    });
                    $(this).dialog("close");
                }
            }
        ];

    } else {
        buttons = [{
            text: 'Insert',
            click: function() {
                var data = {};
                $(this).dialog().find(".form_save").each(function(f, k) {
                    data[k.name] = k.value.replace(/^\s+|\s+$/g, '');
                });
                $.ajax({
                    type: "POST",
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    dataType: 'json',
                    url: "/api/" + to_update,
                    data: JSON.stringify(data),
                    success: function(data) {
                        var new_row = template.clone(true).removeClass('template');
                        new_row.find('.row_update').each(function() {
                            $(this).text(jsonnames($(this).attr('name'), data));
                        });
                        template.after(new_row);
                        new_row.show();
                        get_balance(balance_url);
                        // reload_all();
                    }
                });
                $(this).dialog("close");

            }
        }];
    }

    $('#' + to_update).find('.transfer').hide().addClass('hidden').removeClass('form_save');
    $('#' + to_update).find('.transfer-button').show();
    $('#' + to_update).dialog({ buttons: buttons }).focus();

}

function reload_all() {
    load_table('backlogs_table', '/api/backlogs');
    load_table('incomes_table', '/api/incomes');
    load_table('transactions_table', '/api/transactions');
    load_table('accounts_table', '/api/accounts');
    get_balance(balance_url);
}

$(function() {
    
    $("#tabs").tabs();
    $('.ui-tabs-anchor').click(function() {
        load_table($(this).text() + '_table', '/api/' + $(this).text());
        //alert($(this).text());
    });
    get_balance(balance_url);
    //reload_all();
    updateoption('.account_selector', '/api/accounts', ['title', 'currency']);
    updateoption('.period_selector', '/api/intervals');
    updateoption('.currency_selector', '/api/currency');
    updatecurrency('/api/currency');
    $('#balance input').change(function(event) {
        var a = { 'start_date': '', 'end_date': '' };
        a[$(this).attr('name')] = $(this).val();
        a[$(this).siblings('input').attr('name')] = $(this).siblings('input').val();
        balance_url = '/api/balance/0/' + a['start_date'] + '/' + a['end_date'];
        get_balance(balance_url);
    });

});
*/