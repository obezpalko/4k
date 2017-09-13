function update_income(id) {
  $("#hidden_id").val(id);
  var a = ['title', 'sum', 'currency_id', 'start', 'end', 'period'];
  var b = null;
  $.each(a, function(element){
    console.log(a[element]+" "+$("#" + a[element] + "_" + id).text());
    $(("#" + a[element])).val($(("#" + a[element] + "_" + id)).text());
  });
  $("#submit").val('Update');
}

function c_update(url){
  if ($("#currency_refresh_img")) {
    $("#currency_refresh").hide();
  }
  $.getJSON(url, function(data){
    var items = [];
    items.push("<li><a id='currency_refresh' href='#' onClick='c_update(\"/update_rates\")'><img id='currency_refresh_img' width='10' height='10' src='/static/iconmonstr-refresh-2.svg'/></a></li>");
    $.each( data, function( key, val ) {
      if (val["default"] == "0") {
        items.push( "<li title='" + val["rate_date"] + "' id='currency_" + key + "'>" + val["index"] + ":" + val["rate"] + "</li>" );
      }
    });
    
    $("#currencies").html(items.join( "" ));
    $("#currency_refresh").show();
  })
}
