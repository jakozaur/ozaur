$(function() {
    $("#interested-in > button").click(function() {
        var userId = $("#interested-in input").val();
        $.post("/my_profile/interested_in", {
            "interested_in": $("#interested-in textarea").val()
        }, function() {
            $("#interested-in #interested-in-alert").show();
        });
    });

    $("#interested-in-alert button").click(function() {
        $("#interested-in #interested-in-alert").hide();
    });

    $("#sign-up-button").click(function() {
        if ($("#sign-up-agree-checkbox").prop("checked")) {
            console.log("Clicked sign up buton... authorize with LinkedIN");
            IN.User.authorize(function() {
                $("#signup_form input").val(IN.ENV.auth.oauth_token);
                $("#signup_form").submit();
            });
        } else {
            console.log("Clicked sign up buton... agree check box is missing");
            alert("You need to agree with terms by checking the box first.")
        }
    });


    $("#log-in").click(function() {
         IN.User.authorize(function() {
            // Pass OAuth token to backend, which will log in account in backend.
            $("#linkedin-oauth-token").val(IN.ENV.auth.oauth_token);
            $("#login-form").submit();
        });
    })
});
