function deleteConfirmation() {
        var confirmed = confirm('Are you sure you want to delete this project?');
        if (confirmed) {
            var username = prompt('Enter your username:');

            if (username && password) {
                // Submit the form with the username and password
                var form = document.getElementById('delete-form');
                form.username.value = username;
                form.submit();
            } else {
                // User cancelled the username or password input
                alert('Username confirmation is required.');
            }
        } else {
            // User cancelled the delete operation
            window.location.href = '/reports/home/';
        }
    }