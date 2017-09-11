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