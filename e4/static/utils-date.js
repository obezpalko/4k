
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
    return dateformatted(new Date(d.setDate(diff)));
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
    return dateformatted(d);
    }