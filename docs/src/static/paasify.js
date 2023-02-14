// Sorry, but this is awful, but I'm not a js dev ... at all XD

window.onload = function() {
  console.log("Yoo")
  // Make title clickable
  document.getElementsByClassName('md-header__topic')[0].addEventListener('click', function() {
      location.href = '/paasify'
  }, false);
  console.log(document.getElementsByClassName('md-header__topic')[0])
};


