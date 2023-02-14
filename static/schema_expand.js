// Sorry, but this is awful, but I'm not a js dev ... at all XD

var last_checkuser_time = new Date();

function resizeIframe(size) {

    var now = new Date();
    var timeout = now.setSeconds(now.getSeconds() - 1);

    if (last_checkuser_time < timeout) {
        size = size + 150;

        var iframe = document.getElementById("schemadoc");
        console.log("Resize iframe to: " + size);
        iframe.style.height = size + 'px';

        last_checkuser_time = new Date();

    }

}


function ATTACH () {
     console.log("ATTACH");
    var $frame = $("#schemadoc");

    //resizeIframe($frame.height());
    $frame.contents().bind(
        "mouseup",
        function () {
            resizeIframe($(this).height());
        }
    );
    $frame.contents().bind(
        "mousemove",
        function () {
            resizeIframe($(this).height());
        }
    );
    $frame.contents().bind(
        "mousewheel",
        function () {
            resizeIframe($(this).height());
        }
    );
}

function INIT () {

    // var test = document.getElementById('md-header__topic');
    // losole.log(test)

    // // Auto resize schema iframes
    // console.log("INIT");
    // var $frame = $("#schemadoc");
    // resizeIframe($frame.contents().height());
    // ATTACH();

}

//$(window).load(INIT);

window.onload = function() {
  // Make title clickable
  document.getElementByClass('md-header__topic').addEventListener('click', function() {
      location.href = '/paasify'
  }, false);
};



//window.onload = function() {
//    if (window.jQuery) {
//        // jQuery is loaded
//
//    } else {
//        // jQuery is not loaded
//        //alert("Doesn't Work");
//    }
//}
