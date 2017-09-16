function update_income(event) {
  var id;
  $('#income').show();
  id = $($(event.target).parents('tr').find('.income_id')[0]).text();
  
  $("#hidden_id").val(id);
  var a = ['title', 'sum', 'currency_id', 'start', 'end', 'period'];
  $.each(a, function(element){
    //console.log(a[element] + '=' + $(("#" + a[element] + "_" + id)).text());
    $(("#" + a[element])).val($(("#" + a[element] + "_" + id)).text());
  });
  $("#submit").val('Update');
}

function get_balance(){
  $.getJSON('/api/balance/2018-01-01', function(data){
    t = [];
    $.each(data, function(key, val){
      t.push('<li>' + key + ': ' + val + '</li>')
    });
    $('#balance').html(t.join("")).show();
  })  

}

function delete_income(event) {
  var id;
  $('#income').hide();
  id = $($(event.target).parents('tr').find('.income_id')[0]).text();

  $.ajax({
    type: "DELETE",
    url: "/api/income",
    data: "id=" + id,
    success: function(msg){
        console.log("Data Deleted: " + msg);
    }
  });
  $($(event.target).parents('tr')).remove();
  get_balance();
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
