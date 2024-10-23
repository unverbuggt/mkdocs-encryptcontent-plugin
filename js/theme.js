// Open and close the sidebar on medium and small screens
function w3_open() {
  document.getElementById("mySidebar").style.display = "block";
  document.getElementById("myOverlay").style.display = "block";
}

function w3_close() {
  document.getElementById("mySidebar").style.display = "none";
  document.getElementById("myOverlay").style.display = "none";
}

// Change style of top container on scroll
window.onscroll = function() {myFunction()};
function myFunction() {
  if (document.body.scrollTop > 400 || document.documentElement.scrollTop > 400) {
    document.getElementById("myToTop").classList.remove("w3-hide");
    document.getElementById("myToTop").classList.add("w3-animate-opacity");
    document.getElementById("myThemeToggle").classList.add("w3-hide");
  } else {
    document.getElementById("myToTop").classList.add("w3-hide");
    document.getElementById("myToTop").classList.remove("w3-animate-opacity");
    document.getElementById("myThemeToggle").classList.remove("w3-hide");
  }
}

// Accordions
function myAccordion(id) {
  var x = document.getElementById(id);
  if (x.className.indexOf("w3-show") == -1) {
    x.className += " w3-show";
  } else { 
    x.className = x.className.replace("w3-show", "");
  }
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
  document.body.scrollTop = 0; // For Safari
  document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
} 

function toggleTheme(themeItem) {
  let theme = localStorage.getItem(themeItem);
  let newtheme;
  if (theme) {
    if (theme == 'light') {
      newtheme = 'dark';
    }
    if (theme == 'dark') {
      newtheme = 'light';
    }
  } else {
    if (window.matchMedia) {
      if(window.matchMedia('(prefers-color-scheme: dark)').matches){
        newtheme = 'light';
      } else {
        newtheme = 'dark';
      }
    } else {
      newtheme = 'dark';
    }
  }
  localStorage.setItem(themeItem, newtheme);
  checkTheme();
}

function openSearch() {
  document.getElementById('mkdocs_search_modal').style.display='block';
  document.getElementById('mkdocs-search-query').focus();
}
function closeSearch() {
  document.getElementById('mkdocs_search_modal').style.display='none'
}

function zoomImg(element) {
    document.getElementById('img_modal').src=element.src;
    document.getElementById('zoom_img_modal').style.display='block';
}
