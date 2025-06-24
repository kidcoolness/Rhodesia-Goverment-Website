console.log("Hello, World");
const form = document.getElementById('login-form');
const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));

var loginStatus = document.getElementById("login-status");

loginStatus.style.opacity = 0.0;

form.onsubmit = async (event) => {

    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/register', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({username, password})
	});

	if (response.ok) {
		if (loginStatus.textContent === "✗ Account Already Exists") {
			loginStatus.style.opacity = 0.0;
			await sleep(250);
		}
		loginStatus.style.color = 'green';
		loginStatus.textContent = "✓ Account Registered Successfully";
		loginStatus.style.opacity = 1.0;
		await sleep(3000);
		loginStatus.textContent = "✓ Redirecting in 3...";
		await sleep(1000);
		loginStatus.textContent = "✓ Redirecting in 2...";
		await sleep(1000);
		loginStatus.textContent = "✓ Redirecting in 1...";
		await sleep(1000);
		window.location.href = "/";
	} else {
		loginStatus.style.opacity = 1.0;
		loginStatus.style.color = 'red';
		loginStatus.textContent = "✗ Account Already Exists";
		await sleep(250);
	}
};