$(function() {
    // When we're using HTTPS, use WSS too.
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var chatsock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + "/chat" + window.location.pathname);

    chatsock.onmessage = function(message) {
        var data = JSON.parse(message.data);
        var chat = $("#chat")
        var ele = $('<tr></tr>')

        ele.append(
            $("<td></td>").text(data.timestamp)
        )
        ele.append(
            $("<td></td>").text(data.handle)
        )
        ele.append(
            $("<td></td>").text(data.message)
        )

        chat.append(ele)
        var boundary = document.getElementById("chatboundary");
        boundary.scrollTop = boundary.scrollHeight;
    };

    $("#chatform").on("submit", function(event) {
        if($('#message').val().replace(/ /g , '') === ''){
        $("#message").val('').focus();
        return false;
        };
        //else:
        //alert('bbbb');
        var usnm = document.getElementById("user").innerHTML;
        var message = {
            handle: usnm,
            message: $('#message').val(),
        }
        chatsock.send(JSON.stringify(message));
        $("#message").val('').focus();
        //$("#chatboundary").scrollTop = $("#chatboundary").scrollHeight;

        return false;
    });
});

$(function () {
    var acc = document.getElementsByClassName("accordion");
        var i;
        for (i = 0; i < acc.length; i++) {
        acc[i].onclick = function() {
        this.classList.toggle("active");
        var panel = this.nextElementSibling;
        if (panel.style.maxHeight){
          panel.style.maxHeight = null;
        } else {
          panel.style.maxHeight = panel.scrollHeight + "px";
        }
      }
    }
})
