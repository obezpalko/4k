
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
