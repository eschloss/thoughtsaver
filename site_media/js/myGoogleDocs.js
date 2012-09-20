$(document).ready(function() {
  $('.donotimport_checkbox').click(function() {
    var id = $(this).attr('id');
    if ($(this).attr('checked')) {
      $('option#row_' +id).attr("selected", false);
    } else {
      $('option#row_' +id).attr("selected", true);
    }
  });
});