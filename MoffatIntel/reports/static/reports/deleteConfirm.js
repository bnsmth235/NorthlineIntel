function deleteConfirmation(button) {
  var confirmed = confirm('Are you sure you want to delete this item?');
  if (confirmed) {
    var username = prompt('Enter your username:');

    if (username) {
      // Submit the form with the username
      var form = button.parentNode;
      form.username.value = username;
      form.action = form.getAttribute('data-delete-url');
      form.submit();
    } else {
      // User cancelled the username input
      alert('Username confirmation is required.');
    }
  } else {
    //ignore
  }
}
