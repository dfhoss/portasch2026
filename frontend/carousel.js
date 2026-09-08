(function () {
  const track = document.querySelector(".carousel-track");
  const cards = Array.from(document.querySelectorAll(".activity-card"));
  const prevBtn = document.querySelector(".carousel-btn.prev");
  const nextBtn = document.querySelector(".carousel-btn.next");
  const dotsContainer = document.querySelector(".carousel-dots");
  const carousel = document.querySelector(".carousel");

  let currentIndex = 0;
  let cardsPerView = getCardsPerView();
  let autoplayTimer = null;

  function getCardsPerView() {
    if (window.innerWidth <= 600) return 1;
    if (window.innerWidth <= 900) return 2;
    return 3;
  }

  function createDots() {
    dotsContainer.innerHTML = "";
    const totalPages = Math.ceil(cards.length / cardsPerView);

    for (let i = 0; i < totalPages; i++) {
      const dot = document.createElement("button");
      dot.classList.add("dot");
      dot.setAttribute("role", "tab");
      dot.setAttribute("aria-label", `Ir para página ${i + 1}`);
      if (i === 0) dot.classList.add("active");
      dot.addEventListener("click", () => goTo(i * cardsPerView));
      dotsContainer.appendChild(dot);
    }
  }

  function updateCarousel() {
    cardsPerView = getCardsPerView();
    const maxIndex = Math.max(0, cards.length - cardsPerView);
    if (currentIndex > maxIndex) currentIndex = maxIndex;

    const cardWidth = cards[0].offsetWidth;
    const gap = 20;
    const offset = currentIndex * (cardWidth + gap);

    track.style.transform = `translateX(-${offset}px)`;

    // Atualiza dots
    const dots = dotsContainer.querySelectorAll(".dot");
    const activePage = Math.floor(currentIndex / cardsPerView);
    dots.forEach((dot, i) => {
      dot.classList.toggle("active", i === activePage);
    });

    // Estado dos botões
    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex >= maxIndex;
  }

  function goTo(index) {
    const maxIndex = Math.max(0, cards.length - cardsPerView);
    currentIndex = Math.max(0, Math.min(index, maxIndex));
    updateCarousel();
    resetAutoplay();
  }

  function next() {
    const maxIndex = Math.max(0, cards.length - cardsPerView);
    if (currentIndex < maxIndex) {
      currentIndex++;
    } else {
      currentIndex = 0; // loop
    }
    updateCarousel();
  }

  function prev() {
    const maxIndex = Math.max(0, cards.length - cardsPerView);
    if (currentIndex > 0) {
      currentIndex--;
    } else {
      currentIndex = maxIndex;
    }
    updateCarousel();
  }

  function startAutoplay() {
    autoplayTimer = setInterval(next, 5000);
  }

  function resetAutoplay() {
    clearInterval(autoplayTimer);
    startAutoplay();
  }

  // Eventos
  nextBtn.addEventListener("click", () => {
    next();
    resetAutoplay();
  });
  prevBtn.addEventListener("click", () => {
    prev();
    resetAutoplay();
  });

  // Teclado
  carousel.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") {
      next();
      resetAutoplay();
    }
    if (e.key === "ArrowLeft") {
      prev();
      resetAutoplay();
    }
  });

  // Touch / swipe simples
  let startX = 0;
  carousel.addEventListener(
    "touchstart",
    (e) => {
      startX = e.touches[0].clientX;
    },
    { passive: true },
  );

  carousel.addEventListener(
    "touchend",
    (e) => {
      const diff = startX - e.changedTouches[0].clientX;
      if (Math.abs(diff) > 50) {
        if (diff > 0) next();
        else prev();
        resetAutoplay();
      }
    },
    { passive: true },
  );

  // Resize
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      cardsPerView = getCardsPerView();
      createDots();
      updateCarousel();
    }, 150);
  });

  // Init
  createDots();
  updateCarousel();
  startAutoplay();
})();
