$(function() {

  // Tooltips init
  $('[data-toggle="tooltip"]').tooltip()

  // Modals init
  $('.modal').modal({show: false})

  // AJAX submit
  $('#job_form').on('submit', function(event){
    event.preventDefault();
    $('#progress_modal').modal('show');

    var formData = new FormData($(this)[0]);
    var file = document.getElementById('id_fasta').files[0];
    formData.append('fasta', file, file.name);

    $.ajax({
      url: $(this).attr('action'),
      type: 'POST',
      data: formData,
      cache: false,
      dataType: 'json',
      processData: false, // Don't process the files
      contentType: false, // Set content type to false as jQuery will tell the server its a query string request

      success: function(json) {
        $('#progress_modal').modal('hide');
        $('#success_modal').modal('show');
        setTimeout(function () {
          window.location.href = json.redirect_url;
        }, 500)
      },

      error: function(xhr,errmsg,err) {
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        var json = JSON.parse(xhr.responseText);
        $('#progress_modal').modal('hide');
        if ('errors' in json) {
          for (var error in json.errors) {
            var id = '#id_' + error;
            var parent = $(id).parents('.form-group');
            parent.addClass('has-error');
            if ($('.help-block', parent).length) {
              $('.help-block', parent).text(json.errors[error]);
            } else {
              parent.append('<span class="help-block">' + json.errors[error] + '</span>');
            }
          }
        }
        if ('messages' in json && json.messages.length > 0) {
          $('#form_error_list').html('')
          var messages = json.messages;
          for (var i = 0; i < messages.length; i++) {
            var m = messages[i];
            $('#form_error_list').append('<li>' + m.message + '</li>');
          }
          $('#errors_modal').modal('show');
        }
      },
    });
  });

});