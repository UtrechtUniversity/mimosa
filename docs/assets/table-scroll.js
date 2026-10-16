document$.subscribe(() => {
    document.querySelectorAll(".table_scrollable").forEach(table => {
        const updateFade = () => {
            table.classList.toggle("is-scrolled", table.scrollTop > 0);
        };

        table.addEventListener("scroll", updateFade, { passive: true });
        updateFade();
    });
});
