document.getElementById("login-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent default HTML form submission

    let formData = new FormData(this); // Get form data

    fetch("/login", {
        method: "POST",
        body: formData
    }).then(response => response.text())
    .then(data => {
        console.log("Server response:", data); // Debugging
        if (data.includes("Invalid login")) {
            document.getElementById("login-status").innerText = "Login failed!";
        } else {
            window.location.href = "/dashboard"; // Redirect on success
        }
    }).catch(error => console.error("Login error:", error));
});
