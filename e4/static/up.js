

function updateoption(element, url, titlefields=['title']){
  $.getJSON(url, function(data){
    var options = [];
    var titles;
    $.each(data, function(key, val){
      if (val["show"] !== "n" ) { 
      titles = [];
      titlefields.forEach( function(t){ titles.push( (t==="title") ? val[t] : val[t]["title"]);});
      options.push("<option value='"+ val["id"] + "'" + ((val["default"] === 1) ? " selected" : "") + ">" + titles.join(" ") + "</option>");
      }
    });
    $(element).html(options.join(""));
  });
}

function dateformatted (_date) {
  var mm = _date.getMonth() + 1; // getMonth() is zero-based
  var dd = _date.getDate();

  return [_date.getFullYear(),
          (mm>9 ? "" : "0") + mm,
          (dd>9 ? "" : "0") + dd
         ].join("-");
}

function getSunday(_date) {
  var d = new Date(_date);
  var day = d.getDay(),
      diff = d.getDate() - day; // adjust when day is sunday
  return new dateformatted(Date(d.setDate(diff)));
}

function getFirstWeek(_date) {
  var d = new Date(_date);
  d.setDate(1);
  return getSunday(d);
}


function addMonths(_date, _months) {
  var d = new Date(_date);
  d.setMonth(d.getMonth() + _months);
  d.setDate(d.getDate() - 1);
  return d.formatted();
}

function getDialogButton( dialogselector, buttonname ) {
  var buttons = dialogselector.find(' .ui-dialog-buttonpane button' );
  for ( var i = 0; i < buttons.length; ++i ) {
     var jButton = $( buttons[i] );
     if ( jButton.text() === buttonname )
     {
         return jButton;
     }
  }
  return null;
}

function c_update(url){
  if ($("#currency_refresh_img")) {
    $("#currency_refresh").hide();
  }
  $.getJSON(url, function(data){
    var items = [];
    items.push("<li><span id='currency_refresh' class='ui-icon ui-icon-refresh' onClick='c_update(\"/update_rates\")'></span></li>");
    $.each( data, function( key, val ) {
      if (val["default"] === "0") {
        items.push( "<li title='" + val["rate_date"] + "' id='currency_" + key + "'>" + val["title"] + ":" + val["rate"] + "</li>" );
      }
    });
    $("#currencies").html(items.join( "" ));
    $("#currency_refresh").show();
  });
}

function jsonnames(name, obj){
  // name=a.b.c returns obj {a: {b: {c: value}}}
  var r = name.split(".");
  var n = r.shift();
  if (! n ) {
    return obj;
  } else {
    if (! obj) { return null; }
    return jsonnames(r.join("."), obj[n]);
  }
}
