$(function() {
    $(".title-hover-remove").each(function(index) {
        $(this).click(function() {
        $(this).parent().siblings(".alert").
            css("display", "block").alert();
        });
    });

    $(".remove-cancel").each(function(index) {
        $(this).click(function() {
            $(this).parent().fadeOut(200);
        });
    });

    $(".remove-btn").each(function(index) {
        $(this).click(function() {
            //get slug of the entry
            var slug = $(this).parent().parent().
                attr("id").substring("entry-".length)
            //send ajax request to remove it
            removeEntry(slug);
        });
    });

});

function removeEntry(slug) {
    $.ajax({
        url: "/ajax/removeEntry/" + slug
    }).done(                
        function(data) {
            console.log(slug + " removed!");
            $("#" + "entry-" + slug).fadeOut();
    });

}