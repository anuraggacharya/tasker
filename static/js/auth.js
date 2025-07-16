// static/js/auth.js

$(document).ready(function () {
  // Initialize MDL components
  componentHandler.upgradeDom();

  // Sign In Form Submission
  $("#signin-form").submit(function (e) {
    e.preventDefault();

    const username = $("#signin-username").val();
    const password = $("#signin-password").val();

    $.ajax({
      url: "/api/auth/login",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        username: username,
        password: password,
      }),

      success: function (response) {
        // Store token and user data
        localStorage.setItem("jwt_token", response.token);
        localStorage.setItem("current_user", JSON.stringify(response.user));

        showMessage(
          "#signin-message",
          "Login successful! Loading dashboard...",
          "success",
        );

        // Make authenticated POST to dashboard
        $.ajax({
          url: "/dashboard",
          type: "POST",

          contentType: "application/json",
          xhrFields: {
            withCredentials: true,
          },
          headers: {
            Authorization: "Bearer " + response.token,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          data: JSON.stringify({
            user: response.user,
          }),
          success: function (dashboardResponse) {
            // Replace entire page content with dashboard
            document.open();
            document.write(dashboardResponse);
            document.close();
          },
          error: function (xhr) {
            showMessage(
              "#signin-message",
              "Dashboard load failed: " + xhr.responseText,
              "error",
            );
          },
        });
      },
      error: function (xhr) {
        showMessage(
          "#signin-message",
          "Login failed: " + xhr.responseJSON.message,
          "error",
        );
      },
    });
  });

  // Sign Up Form Submission
  $("#signup-form").submit(function (e) {
    e.preventDefault();

    const username = $("#signup-username").val();
    const email = $("#signup-email").val();
    const password = $("#signup-password").val();
    const confirmPassword = $("#signup-confirm-password").val();

    if (password !== confirmPassword) {
      showMessage("#signup-message", "Passwords do not match!", "error");
      return;
    }

    $.ajax({
      url: "/api/auth/register",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        username: username,
        email: email,
        password: password,
      }),
      success: function (response) {
        showMessage(
          "#signup-message",
          "Registration successful! Please sign in.",
          "success",
        );
        // Switch to sign in tab
        document.querySelector(".mdl-tabs__tab-bar a:nth-child(1)").click();
        // Clear form
        $("#signup-form")[0].reset();
      },
      error: function (xhr) {
        showMessage(
          "#signup-message",
          "Registration failed: " + xhr.responseJSON.message,
          "error",
        );
      },
    });
  });

  function showMessage(selector, message, type) {
    const $message = $(selector);
    $message.text(message).removeClass("hidden");

    // Add appropriate styling based on message type
    $message.removeClass("success error");
    $message.addClass(type);

    // Style the message based on type
    if (type === "success") {
      $message.css("color", "green");
    } else {
      $message.css("color", "red");
    }

    setTimeout(() => {
      $message.addClass("hidden");
    }, 10000);
  }
});
