function json_post(method, url, data_, obj) {
    $.ajax({
        type: method,
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        dataType: 'json',
        url: url,
        data: JSON.stringify(data_),
        success: function(data) {
            var result = $.parseJSON(data);
            if (result.result != 'Ok') {
                obj.prop('checked', false);
            }
        },
        error: function() {
            obj.prop('checked', !obj.prop('checked'));
        }
    });
}

$(function() {
    $(":input.currency_rb").change(function() {
        var c = $(this).val();
        json_post("PUT", "/api/usercurrency/" + c, {
            "default": true
        }, $(this));
        $(":input.currency_cb[value*=" + c + "]").prop('checked', true);
    });

    $(":input.currency_cb").change(function() {
        var m = 'DELETE';
        var c = $(this).val();
        // console.log("change checkbox val:" + c + " " + $(this).prop('checked'));
        if ($(this).prop('checked')) {
            m = 'PUT';
        } else {
            $(":input.currency_rb[value*=" + c + "]").prop('checked', false);
        }
        json_post(m, "/api/usercurrency/" + c, {}, $(this));
    });
});