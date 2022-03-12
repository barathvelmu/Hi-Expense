// Username, Password, and Email Fields
const usernameField = document.querySelector("#usernameField");
const passwordField = document.querySelector("#passwordField");
const emailField = document.querySelector("#emailField");

// Correct and Incorrect Username & Password Entries
const usernameFeedbackArea = document.querySelector(".invalid_feedback");
const emailFeedbackArea = document.querySelector(".emailFeedbackArea");

// Real Time Validation 
const usernameSuccessOutput = document.querySelector(".usernameSuccessOutput");
const emailSuccessOutput = document.querySelector(".emailSuccessOutput");

// Show Password
const showPasswordToggle = document.querySelector(".showPasswordToggle");

// Submit Button
const submitButton = document.querySelector(".submit-btn");


const handleToggleInput = (e) => {
    if (showPasswordToggle.textContent === 'SHOW') {
        showPasswordToggle.textContent = 'HIDE';
        passwordField.setAttribute("type", "text");
    } else {
        showPasswordToggle.textContent = 'SHOW';
        passwordField.setAttribute("type", "password");
    }
};


showPasswordToggle.addEventListener('click', handleToggleInput);


emailField.addEventListener("keyup", (e) => {
  // Obtain email value entered
  const emailVal = e.target.value;
  emailSuccessOutput.style.display = "block";
  emailSuccessOutput.textContent = `Checking ${emailVal}`;

  emailField.classList.remove("is-invalid");
  emailFeedbackArea.style.display = "none";

  if (emailVal.length > 0) {
    // API Call to Endpoint (e.g. Postman Call but through JS)
    fetch("/authentication/validate-email", {
      body: JSON.stringify({ email: emailVal }),
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        emailSuccessOutput.style.display = "none";
        if (data.email_error) {
          submitButton.disabled = true;
          emailField.classList.add("is-invalid");
          emailFeedbackArea.style.display = "block";
          emailFeedbackArea.innerHTML = `<p>${data.email_error}</p>`;
        } else {
          submitButton.removeAttribute("disabled");
        }
      });
  } else {
    emailSuccessOutput.style.display = "none";
  }
});


usernameField.addEventListener("keyup", (e) => {
  // Obtain username value entered
  const usernameVal = e.target.value;
  usernameSuccessOutput.style.display = "block";
  usernameSuccessOutput.textContent = `Checking ${usernameVal}`;

  usernameField.classList.remove("is-invalid");
  usernameFeedbackArea.style.display = "none";

  if (usernameVal.length > 0) {
    // API Call to Endpoint (e.g. Postman Call but in JS)
    fetch("/authentication/validate-username", {
      body: JSON.stringify({ username: usernameVal }),
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        usernameSuccessOutput.style.display = "none";
        if (data.username_error) {
          submitButton.disabled = true;
          usernameField.classList.add("is-invalid");
          usernameFeedbackArea.style.display = "block";
          usernameFeedbackArea.innerHTML = `<p>${data.username_error}</p>`;
        } else {
          submitButton.removeAttribute("disabled");
        }
        
      });
  } else {
    usernameSuccessOutput.style.display = "none";
  }
});
