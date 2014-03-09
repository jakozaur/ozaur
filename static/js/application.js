$(function() {
    $("#interested-in button").click(function() {
        var userId = $("#interested-in input").val();
        $.post("/account/" + userId + "/interested_in", {
            "interested_in": $("#interested-in textarea").val()
        }, function() {
            $("#interested-in > #alert").show();
        });
    });
});