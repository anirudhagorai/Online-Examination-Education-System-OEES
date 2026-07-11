document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('mobile-menu');
  const navLinks = document.getElementById('nav-link');
  const authButtons = document.querySelector('.auth-buttons');
  const navbar = document.querySelector('.navbar');

  const openMenu = () => {
    navLinks.classList.add('open');
    navLinks.appendChild(authButtons);
    authButtons.style.display = 'flex';
    menuToggle.innerHTML = '<i class="fa-solid fa-times"></i>';
  };
  const closeMenu = () => {
    navLinks.classList.remove('open');
    authButtons.style.display = 'none';
    navbar.insertBefore(authButtons, menuToggle);
    menuToggle.innerHTML = '<i class="fa-solid fa-bars"></i>';
  };
  const handleResize = () => {
    if (window.innerWidth > 1200) {
      navLinks.classList.remove('open');
      authButtons.style.display = 'flex';
      navbar.insertBefore(authButtons, menuToggle);
      menuToggle.innerHTML = '<i class="fa-solid fa-bars"></i>';
    
    } else {
      if (navLinks.classList.contains('open')){
        authButtons.style.display = 'flex';
      }
      else {
        authButtons.style.display = "none";
      }
    }
  };

  handleResize();
  window.addEventListener('resize', handleResize);
  
  menuToggle.addEventListener('click', () => {
    const isMenuOpen = navLinks.classList.contains("open");
    if (isMenuOpen) {
      closeMenu();
    }
    else {
      openMenu();
    }
  });
});

