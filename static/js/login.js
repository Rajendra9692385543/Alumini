document.querySelector('form').addEventListener('submit', function(event) {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        event.preventDefault();
        alert('Please fill in all fields.');
    }
});