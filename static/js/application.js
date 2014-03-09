$(function() {
    $("#interested-in > button").click(function() {
        var userId = $("#interested-in input").val();
        $.post("/account/" + userId + "/interested_in", {
            "interested_in": $("#interested-in textarea").val()
        }, function() {
            $("#interested-in #interested-in-alert").show();
        });
    });

    $("#interested-in-alert button").click(function() {
        $("#interested-in #interested-in-alert").hide();
    })
});