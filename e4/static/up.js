

function update_option(element, url, title_fields=['title']){
  $.getJSON(url, function(data){
    var options = [];
    var titles;
    $.each(data, function(key, val){
      if (val['show'] != 'n' ) { 
      titles = []
      title_fields.forEach( function(t){ titles.push( (t=='title') ? val[t] : val[t]['title'])});
      options.push('<option value="'+ val['id'] +'"'+ ((val['default']==1) ? " selected" : "") +'>'+ titles.join(' ') +'</option>')
      }
    });
  
    $(element).html(options.join(''));
  })
}

function getSunday(d) {
  d = new Date(d);
  var day = d.getDay(),
      diff = d.getDate() - day; // adjust when day is sunday
  return new Date(d.setDate(diff));
}

function getDialogButton( dialog_selector, button_name ) {
  var buttons = dialog_selector.find(' .ui-dialog-buttonpane button' );
  for ( var i = 0; i < buttons.length; ++i ) {
     var jButton = $( buttons[i] );
     if ( jButton.text() == button_name )
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
      if (val["default"] == "0") {
        items.push( "<li title='" + val["rate_date"] + "' id='currency_" + key + "'>" + val["title"] + ":" + val["rate"] + "</li>" );
      }
    });
    $("#currencies").html(items.join( "" ));
    $("#currency_refresh").show();
  })
}

function json_names(name, obj){
  // name=a.b.c returns obj {a: {b: {c: value}}}
  var r = name.split('.');
  var n = r.shift();
  if (! n ) {
    return obj;
  } else {
    if (! obj) return null;
    return json_names(r.join('.'), obj[n])
  };
}
