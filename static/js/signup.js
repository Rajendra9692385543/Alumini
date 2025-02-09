document.querySelector('form').addEventListener('submit', function(event) {
    const inputs = document.querySelectorAll('input');
    let valid = true;

    inputs.forEach(input => {
        if (!input.value) {
            valid = false;
            alert('Please fill in all fields.');
        }
    });

    if (!valid) {
        event.preventDefault();
    }
});