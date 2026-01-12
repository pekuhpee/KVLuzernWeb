(() => {
  const grid = document.getElementById("meme-grid");
  if (!grid) return;
  const modal = document.getElementById("meme-modal"), modalImage = document.getElementById("meme-modal-image"), modalTitle = document.getElementById("meme-modal-title"), modalLikeButton = document.getElementById("meme-modal-like"), modalCount = document.getElementById("meme-modal-count"), closeTriggers = modal ? modal.querySelectorAll("[data-modal-close]") : [], prevTrigger = modal ? modal.querySelector("[data-modal-prev]") : null, nextTrigger = modal ? modal.querySelector("[data-modal-next]") : null, state = { memes: [], selectedIndex: null };
  const likeLabel = (liked) => (liked ? "❤️ Geliked" : "🤍 Like");
  const setLikeButton = (button, meme) => { button.textContent = likeLabel(meme.liked); button.disabled = meme.liked; };
  const getCookie = (name) => document.cookie.split("; ").find((row) => row.startsWith(`${name}=`))?.split("=")[1] || "";
  const collectMemes = () => {
    state.memes = Array.from(grid.querySelectorAll("[data-meme-id]")).map((card) => {
      const image = card.querySelector(".meme-card__image");
      const imageUrl = card.dataset.memeImage || image?.getAttribute("src") || "";
      if (image && imageUrl && image.getAttribute("src") !== imageUrl) {
        image.setAttribute("src", imageUrl);
      }
      return {
        id: Number(card.dataset.memeId),
        title: card.dataset.memeTitle || "",
        imageUrl,
        likeCount: Number(card.dataset.likeCount || 0),
        liked: card.dataset.liked === "true",
        card,
      };
    });
  };
  const updateCard = (meme) => {
    const likeButton = meme.card.querySelector(".meme-like__button");
    const likeCount = meme.card.querySelector(".meme-like__count");
    if (likeButton) setLikeButton(likeButton, meme);
    if (likeCount) likeCount.textContent = `${meme.likeCount} Likes`;
    meme.card.dataset.likeCount = String(meme.likeCount);
    meme.card.dataset.liked = meme.liked ? "true" : "false";
  };
  const showModal = (index) => {
    const meme = state.memes[index];
    if (!meme || !modal) return;
    state.selectedIndex = index;
    modalImage.src = meme.imageUrl;
    modalImage.alt = meme.title || `Meme ${meme.id}`;
    modalTitle.textContent = meme.title || `Meme #${meme.id}`;
    modalCount.textContent = `${meme.likeCount} Likes`;
    setLikeButton(modalLikeButton, meme);
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
  };
  const closeModal = () => { if (!modal) return; modal.classList.remove("is-open"); modal.setAttribute("aria-hidden", "true"); state.selectedIndex = null; };
  const shiftModal = (delta) => {
    if (state.selectedIndex === null || state.memes.length === 0) return;
    const nextIndex = (state.selectedIndex + delta + state.memes.length) % state.memes.length;
    showModal(nextIndex);
  };
  const handleLike = async (meme) => {
    if (!meme || meme.liked) return;
    try {
      const response = await fetch(`/api/memes/${meme.id}/like/`, { method: "POST", headers: { "X-CSRFToken": getCookie("csrftoken") }, credentials: "same-origin" });
      if (!response.ok) return;
      const data = await response.json();
      meme.likeCount = data.like_count ?? meme.likeCount;
      meme.liked = true;
      updateCard(meme);
      if (state.selectedIndex !== null && state.memes[state.selectedIndex]?.id === meme.id) {
        modalCount.textContent = `${meme.likeCount} Likes`;
        setLikeButton(modalLikeButton, meme);
      }
    } catch (error) {
      console.error(error);
    }
  };
  collectMemes();
  grid.querySelectorAll("[data-meme-open]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const card = trigger.closest("[data-meme-id]");
      const index = state.memes.findIndex((meme) => meme.card === card);
      if (index !== -1) showModal(index);
    });
  });
  grid.querySelectorAll(".meme-like__button").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const card = button.closest("[data-meme-id]");
      const meme = state.memes.find((item) => item.card === card);
      if (meme) handleLike(meme);
    });
  });
  if (modalLikeButton) { modalLikeButton.addEventListener("click", () => { if (state.selectedIndex !== null) handleLike(state.memes[state.selectedIndex]); }); }
  if (prevTrigger) prevTrigger.addEventListener("click", () => shiftModal(-1));
  if (nextTrigger) nextTrigger.addEventListener("click", () => shiftModal(1));
  closeTriggers.forEach((trigger) => trigger.addEventListener("click", closeModal));
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeModal(); if (event.key === "ArrowLeft") shiftModal(-1); if (event.key === "ArrowRight") shiftModal(1); });
})();
