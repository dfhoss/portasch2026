(() => {
  const instances = new WeakMap();

  function initializeCarousel(root = document.querySelector(".carousel")) {
    if (!root) return null;

    let instance = instances.get(root);
    if (!instance) {
      const track = root.querySelector(".carousel-track");
      const prevBtn = root.parentElement?.querySelector(".carousel-btn.prev");
      const nextBtn = root.parentElement?.querySelector(".carousel-btn.next");
      const dotsContainer = root.parentElement?.parentElement?.querySelector(".carousel-dots");
      if (!track || !prevBtn || !nextBtn || !dotsContainer) return null;
      instance = createInstance(root, track, prevBtn, nextBtn, dotsContainer);
      instances.set(root, instance);
    }
    instance.rebuild();
    return instance;
  }

  function createInstance(root, track, prevBtn, nextBtn, dotsContainer) {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let cards = [];
    let pageStarts = [];
    let currentPage = 0;
    let cloneCount = 0;
    let autoplayTimer;
    let transitionTimer;
    let resumeTimer;
    let autoplayPaused = false;
    let animating = false;
    let pendingNavigation = null;

    function getCardsPerView() {
      if (window.innerWidth <= 600) return 1;
      if (window.innerWidth <= 900) return 2;
      return 3;
    }

    function readCards() {
      return Array.from(track.children).filter(
        (card) => !card.hasAttribute("data-carousel-clone"),
      );
    }

    function positionAt(index, instant = false) {
      if (!cards.length) {
        track.style.removeProperty("transform");
        return;
      }
      const step = cards[0].getBoundingClientRect().width + 20;
      track.classList.toggle("is-resetting", instant);
      track.style.transform = `translateX(-${(cloneCount + index) * step}px)`;
      if (instant) {
        void track.offsetWidth;
        track.classList.remove("is-resetting");
      }
    }

    function setTransitionDuration(visualIndex, fromPage) {
      const referenceDistance = pageStarts.length > 1
        ? Math.max(1, pageStarts[1] - pageStarts[0])
        : 1;
      const distance = Math.abs(visualIndex - pageStarts[fromPage]);
      const duration = 0.45 * Math.max(1, distance / referenceDistance);
      track.style.setProperty("--carousel-transition-duration", `${duration}s`);
      return duration;
    }

    function updateIndicators() {
      Array.from(dotsContainer.children).forEach((dot, index) => {
        const active = index === currentPage;
        dot.classList.toggle("active", active);
        dot.setAttribute("aria-current", String(active));
      });
      const singlePage = pageStarts.length <= 1;
      prevBtn.disabled = singlePage;
      nextBtn.disabled = singlePage;
    }

    function finishTransition() {
      if (!animating) return;
      clearTimeout(transitionTimer);
      animating = false;
      positionAt(pageStarts[currentPage], true);
      track.style.removeProperty("--carousel-transition-duration");
      const pending = pendingNavigation;
      pendingNavigation = null;
      if (pending) pending();
    }

    function navigate(page, visualIndex) {
      if (animating) {
        pendingNavigation = () => navigate(page, visualIndex);
        return;
      }
      const previousPage = currentPage;
      currentPage = page;
      updateIndicators();
      if (reducedMotion.matches) {
        positionAt(pageStarts[currentPage], true);
        return;
      }
      animating = true;
      const transitionDuration = setTransitionDuration(visualIndex, previousPage);
      positionAt(visualIndex);
      transitionTimer = setTimeout(finishTransition, transitionDuration * 1000 + 100);
    }

    function move(direction) {
      if (pageStarts.length <= 1) return;
      if (animating) {
        pendingNavigation = () => move(direction);
        return;
      }
      const nextPage = (currentPage + direction + pageStarts.length) % pageStarts.length;
      let visualIndex = pageStarts[nextPage];
      if (direction > 0 && nextPage === 0) visualIndex = cards.length;
      if (direction < 0 && currentPage === 0) visualIndex -= cards.length;
      navigate(nextPage, visualIndex);
    }

    function resetAutoplay() {
      clearInterval(autoplayTimer);
      if (autoplayPaused) return;
      if (pageStarts.length > 1) autoplayTimer = setInterval(() => move(1), 8000);
    }

    function pauseAutoplayForCard() {
      autoplayPaused = true;
      clearInterval(autoplayTimer);
      clearTimeout(resumeTimer);
      resumeTimer = setTimeout(() => {
        autoplayPaused = false;
        resetAutoplay();
      }, 60000);
    }

    function resumeAutoplay() {
      if (!autoplayPaused) return;
      autoplayPaused = false;
      clearTimeout(resumeTimer);
      resetAutoplay();
    }

    function cloneCard(card) {
      const clone = card.cloneNode(true);
      clone.setAttribute("data-carousel-clone", "");
      clone.setAttribute("aria-hidden", "true");
      clone.inert = true;
      clone.removeAttribute("id");
      clone.querySelectorAll("[id]").forEach((element) => element.removeAttribute("id"));
      return clone;
    }

    function rebuild() {
      const previousStart = pageStarts[currentPage] || 0;
      const focusedDot = Array.from(dotsContainer.children).indexOf(document.activeElement);
      clearTimeout(transitionTimer);
      animating = false;
      pendingNavigation = null;
      track.querySelectorAll("[data-carousel-clone]").forEach((clone) => clone.remove());
      cards = readCards();
      const perView = getCardsPerView();
      const lastStart = Math.max(0, cards.length - perView);
      pageStarts = cards.length
        ? Array.from({length: Math.ceil(cards.length / perView)}, (_, index) =>
            Math.min(index * perView, lastStart))
        : [];
      const matchingPage = pageStarts.findIndex((start) => start >= previousStart);
      currentPage = matchingPage < 0 ? Math.max(0, pageStarts.length - 1) : matchingPage;
      cloneCount = pageStarts.length > 1 ? cards.length : 0;
      if (cloneCount) {
        track.prepend(...cards.map(cloneCard));
        track.append(...cards.map(cloneCard));
      }
      dotsContainer.replaceChildren();
      pageStarts.forEach((start, index) => {
        const dot = document.createElement("button");
        dot.type = "button";
        dot.className = "dot";
        dot.setAttribute("aria-label", `Ir para página ${index + 1}`);
        dot.addEventListener("click", () => {
          navigate(index, start);
          resetAutoplay();
        });
        dotsContainer.appendChild(dot);
      });
      updateIndicators();
      if (pageStarts.length) positionAt(pageStarts[currentPage], true);
      else track.style.removeProperty("transform");
      if (focusedDot >= 0 && dotsContainer.children.length) {
        dotsContainer.children[Math.min(focusedDot, dotsContainer.children.length - 1)].focus();
      }
      resetAutoplay();
    }

    track.addEventListener("transitionend", (event) => {
      if (event.target === track && event.propertyName === "transform") finishTransition();
    });
    track.addEventListener("click", (event) => {
      if (event.target.closest(".activity-card")) pauseAutoplayForCard();
    });
    document.addEventListener("click", (event) => {
      if (!root.contains(event.target)) resumeAutoplay();
    });
    prevBtn.addEventListener("click", () => {
      move(-1);
      resetAutoplay();
    });
    nextBtn.addEventListener("click", () => {
      move(1);
      resetAutoplay();
    });
    root.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
      event.preventDefault();
      move(event.key === "ArrowRight" ? 1 : -1);
      resetAutoplay();
    });

    let startX = null;
    root.addEventListener("touchstart", (event) => {
      startX = event.touches.length === 1 ? event.touches[0].clientX : null;
    }, {passive: true});
    root.addEventListener("touchcancel", () => {
      startX = null;
    }, {passive: true});
    root.addEventListener("touchend", (event) => {
      if (startX === null || !event.changedTouches.length) return;
      const diff = startX - event.changedTouches[0].clientX;
      startX = null;
      if (Math.abs(diff) > 50) {
        move(diff > 0 ? 1 : -1);
        resetAutoplay();
      }
    }, {passive: true});

    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(rebuild, 150);
    });
    if (typeof reducedMotion.addEventListener === "function") {
      reducedMotion.addEventListener("change", finishTransition);
    }

    return {rebuild};
  }

  window.initializeCarousel = initializeCarousel;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initializeCarousel(), {once: true});
  } else {
    initializeCarousel();
  }
})();
