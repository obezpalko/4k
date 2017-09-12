function update_income(id) {
  document.getElementById('hidden_id').value = id;
  var a = ['title', 'sum', 'currency', 'start', 'end', 'period'];
  var b = null;
  a.forEach(function(element){
    b = document.getElementById(element+'_'+id);
    if (!b) {
      document.getElementById(element).value = '';
    }
    else {
    document.getElementById(element).value = b.textContent;
    }
    
  });
  document.getElementById('submit').value = 'Update';
}

function c_update(url){
  if ($("#currency_refresh_img")) {
    $("#currency_refresh").hide();
  }
  $.getJSON(url, function(data){
    var items = [];
    items.push("<li><a id='currency_refresh' href='#' onClick='c_update(\"/update_rates\")'><img id='currency_refresh_img' width='10' height='10' src='/static/iconmonstr-refresh-2.svg'/></a></li>");
    $.each( data, function( key, val ) {
      if (val["is_default"] == "0") {
        items.push( "<li title='" + val["rate_date"] + "' id='currency_" + key + "'>" + val["currency_index"] + ":" + val["rate"] + "</li>" );
      }
    });
    
    $("#currencies").html(items.join( "" ));
    $("#currency_refresh").show();
  })
}
