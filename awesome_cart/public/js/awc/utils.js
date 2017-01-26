frappe.provide("awc");

awc.response = function(r) {
  var msg = r.message;
  if ( !msg.success ) {
    console.error("Server Response Failed");
    if ( msg.exception ) {
      console.error(msg.exception);
    }
    if ( msg.msg ) {
      console.error(msg.msg);
    }
  }

  if ( msg.debug ) {
    console.log("%c"+msg.debug, 'color:green');
  }

  if ( window.awc_debug ) {
    console.log("%cServer Response:", 'color:blue')
    console.log(msg);
  }
  return msg;
}
