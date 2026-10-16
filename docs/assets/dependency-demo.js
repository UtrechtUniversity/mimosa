document$.subscribe(async () => {
    const panel = document.querySelector("#dependency-demo");
    if (!panel) return;

    const viewport = panel.querySelector(".dependency-demo-viewport");
    const select = panel.querySelector("select");
    const focusButton = panel.querySelector('[data-action="focus"]');

    try {
        const response = await fetch(document.querySelector("#dependency-demo-source").href);
        if (!response.ok) throw new Error(`Graph request failed: ${response.status}`);
        const graphDocument = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
        const svg = graphDocument.documentElement;
        svg.setAttribute("role", "group");
        svg.setAttribute("aria-label", "ACCREU sectoral variable dependencies");
        viewport.replaceChildren(svg);

        const nodes = Array.from(svg.querySelectorAll("g.node"));
        const edges = Array.from(svg.querySelectorAll("g.edge"));
        const { width, height } = svg.viewBox.baseVal;
        const focusZoom = 0.85;
        let scale = 1;
        let selected = null;

        nodes.forEach(node => {
            const name = node.querySelector("title").textContent;
            node.dataset.variable = name;
            node.classList.add("demo-node");
            const link = node.querySelector("a");
            link.setAttribute("href", `?demo_variable=${encodeURIComponent(name)}#dependency-graph-demo`);
            link.setAttribute("aria-label", `Highlight ${name}`);
            link.addEventListener("click", event => {
                event.preventDefault();
                choose(name);
                if (scale < focusZoom) focusSelected();
            });
        });
        select.add(new Option("No selection", ""));
        nodes.map(node => node.dataset.variable).sort().forEach(name => {
            select.add(new Option(name, name));
        });
        edges.forEach(edge => {
            const [source, target] = edge.querySelector("title").textContent.split("->");
            edge.dataset.source = source;
            edge.dataset.target = target;
        });

        function highlight(name) {
            selected = name;
            select.value = name || "";
            focusButton.disabled = !name;
            const incoming = edges.filter(edge => edge.dataset.target === name).map(edge => edge.dataset.source);
            const outgoing = edges.filter(edge => edge.dataset.source === name).map(edge => edge.dataset.target);
            nodes.forEach(node => {
                const id = node.dataset.variable;
                node.classList.toggle("is-selected", id === name);
                node.classList.toggle("is-incoming", id !== name && incoming.includes(id));
                node.classList.toggle("is-outgoing", id !== name && outgoing.includes(id));
                node.classList.toggle("is-muted", !!name && id !== name && !incoming.includes(id) && !outgoing.includes(id));
                node.querySelector("a").setAttribute("aria-current", id === name ? "true" : "false");
            });
            edges.forEach(edge => {
                const kind = edge.dataset.target === name ? "incoming" : edge.dataset.source === name ? "outgoing" : "normal";
                edge.classList.add("demo-edge");
                edge.classList.toggle("incoming", kind === "incoming");
                edge.classList.toggle("outgoing", kind === "outgoing");
                edge.classList.toggle("normal", kind === "normal");
                edge.classList.toggle("is-muted", !!name && kind === "normal");
            });
        }

        function choose(name) {
            const url = new URL(location.href);
            if (name) url.searchParams.set("demo_variable", name);
            else url.searchParams.delete("demo_variable");
            url.hash = "dependency-graph-demo";
            history.replaceState(history.state, "", url);
            highlight(name);
            if (!name && document.activeElement?.closest(".demo-node")) {
                document.activeElement.blur();
            }
        }

        function setZoom(next) {
            const centerX = (viewport.scrollLeft + viewport.clientWidth / 2) / scale;
            const centerY = (viewport.scrollTop + viewport.clientHeight / 2) / scale;
            scale = Math.max(0.05, Math.min(3, next));
            svg.style.width = `${width * scale}px`;
            svg.style.height = `${height * scale}px`;
            viewport.scrollLeft = centerX * scale - viewport.clientWidth / 2;
            viewport.scrollTop = centerY * scale - viewport.clientHeight / 2;
            panel.querySelector("output").textContent = `${Math.round(scale * 100)}%`;
        }

        function fitGraph() {
            panel.classList.add("is-overview");
            setZoom(Math.min(viewport.clientWidth / width, viewport.clientHeight / height));
            viewport.scrollTo(0, 0);
        }

        function focusSelected() {
            if (!selected) return;
            panel.classList.remove("is-overview");
            setZoom(Math.max(scale, focusZoom));
            const node = nodes.find(node => node.dataset.variable === selected).getBoundingClientRect();
            const frame = viewport.getBoundingClientRect();
            viewport.scrollLeft += node.left - frame.left + node.width / 2 - viewport.clientWidth / 2;
            viewport.scrollTop += node.top - frame.top + node.height / 2 - viewport.clientHeight / 2;
        }

        function selectFromUrl() {
            const requested = new URLSearchParams(location.search).get("demo_variable");
            const exists = nodes.some(node => node.dataset.variable === requested);
            highlight(exists ? requested : null);
            if (exists) focusSelected();
        }

        select.addEventListener("change", () => {
            choose(select.value || null);
            focusSelected();
        });
        viewport.addEventListener("click", event => {
            if (!event.target.closest(".demo-node")) choose(null);
        });
        viewport.addEventListener("dblclick", event => {
            if (!event.target.closest(".demo-node")) {
                choose(null);
                fitGraph();
            }
        });
        window.addEventListener("keydown", event => {
            if (event.key === "Escape") choose(null);
        });
        panel.querySelector('[data-action="zoom-in"]').addEventListener("click", () => setZoom(scale * 1.4));
        panel.querySelector('[data-action="zoom-out"]').addEventListener("click", () => setZoom(scale / 1.4));
        panel.querySelector('[data-action="fit"]').addEventListener("click", fitGraph);
        focusButton.addEventListener("click", focusSelected);
        window.addEventListener("popstate", selectFromUrl);
        fitGraph();
        selectFromUrl();
    } catch (error) {
        viewport.textContent = "The graph could not be loaded. You can download the SVG below.";
        console.error(error);
    }
});
