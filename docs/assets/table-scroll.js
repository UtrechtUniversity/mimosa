document$.subscribe(() => {
    document.querySelectorAll(".table_scrollable").forEach(table => {
        const updateFade = () => {
            table.classList.toggle("is-scrolled", table.scrollTop > 0);
            const remaining = table.scrollHeight - table.clientHeight - table.scrollTop;
            table.classList.toggle("has-more-below", remaining > 1);
        };

        table.addEventListener("scroll", updateFade, { passive: true });
        updateFade();
    });
});
