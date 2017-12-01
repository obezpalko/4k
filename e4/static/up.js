/*
function updateoption(element, url, titlefields=["title"]){
  $.getJSON(url, function(data){
    var options = "";
    var titles;
    $.each(data, function(key, val){
      if (val["show"] !== "n" ) { 
      titles = "";
      titlefields.forEach( function(t){
        titles = titles + " " + ( (t==="title") ? val[t] : val[t]["title"]);
        });
        options = options + "<option value='" + val["id"] + "'" + ((val["default"] === 1) ? " selected" : "") + ">" + titles + "</option>";
      }
    });
    $(element).html(options);
  });
}



function getDialogButton(dialogselector, buttonname) {
    var buttons = dialogselector.find(" .ui-dialog-buttonpane button");
    for (var i = 0; i < buttons.length; ++i) {
        var jButton = $(buttons[i]);
        if (jButton.text() === buttonname) {
            return jButton;
        }
    }
    return null;
}

function updatecurrency(url) {
    if ($("#currency_refresh_img")) {
        $("#currency_refresh").hide();
    }
    $.getJSON(url, function(data) {
        var items = [];
        items.push("<li><span id='currency_refresh' class='ui-icon ui-icon-refresh' onClick='updatecurrency(\"/update_rates\")'></span></li>");
        $.each(data, function(key, val) {
            if (val["default"] === 0) {
                items.push("<li title='" + val["rate_date"] + "' id='currency_" + key + "'>" + val["title"] + ":" + val["rate"] + "</li>");
            }
        });
        $("#currencies").html(items.join(""));
        $("#currency_refresh").show();
    });
}
*/