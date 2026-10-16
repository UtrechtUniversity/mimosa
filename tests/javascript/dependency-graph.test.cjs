// Run with: node --test tests/javascript/dependency-graph.test.cjs
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { test } = require("node:test");
const vm = require("node:vm");

const source = readFileSync(`${__dirname}/../../docs/assets/dependency-graph.js`, "utf8");

// Small DOM stand-ins let us exercise the viewer's events without a browser.
function element(children = {}) {
    const classes = new Set();
    return Object.assign(new EventTarget(), {
        dataset: {},
        style: {},
        attributes: {},
        isConnected: true,
        classList: {
            add: name => classes.add(name),
            remove: name => classes.delete(name),
            toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name),
            contains: name => classes.has(name),
        },
        querySelector: selector => children[selector],
        closest: () => null,
        setAttribute(name, value) { this.attributes[name] = value; },
        removeAttribute(name) { delete this.attributes[name]; },
        removeAttributeNS() {},
        append(...children) { this.children = [...(this.children || []), ...children]; },
        replaceChildren(...children) { this.children = children; },
        getBoundingClientRect: () => ({ left: 0, top: 0, right: 100, bottom: 40, width: 100, height: 40 }),
    });
}

async function viewer(reference) {
    const links = [element(), element()];
    const nodes = ["input", "output"].map((name, index) => element({
        title: { textContent: name, remove() {} }, a: links[index],
    }));
    const edge = element({ title: { textContent: "input->output" } });
    const svg = element();
    svg.viewBox = { baseVal: { width: 1000, height: 1000 } };
    svg.querySelectorAll = selector => selector === "g.node" ? nodes : [edge];
    const viewport = element();
    Object.assign(viewport, {
        clientWidth: 500, clientHeight: 400, scrollLeft: 0, scrollTop: 0,
        closest: selector => selector === "svg" ? svg : null,
        setPointerCapture(id) { this.capturedPointer = id; },
        replaceChildren() {},
        scrollTo(left, top) { this.scrollLeft = left; this.scrollTop = top; },
    });
    const select = element();
    select.add = () => {};
    const output = {};
    const controls = Object.fromEntries(["focus", "fit", "zoom-in", "zoom-out"].map(
        action => [`[data-action="${action}"]`, element()]
    ));
    const panel = element({
        ".dependency-graph-viewport": viewport, select, output, ...controls,
    });
    const dialog = element();
    dialog.getBoundingClientRect = () => ({ left: 0, top: 0, right: 800, bottom: 600 });
    panel.closest = () => dialog;
    panel.dataset.variableContext = "accreu_sectoral";
    const tooltip = element();
    tooltip.offsetWidth = 300;
    tooltip.offsetHeight = 200;
    let historyWrites = 0;
    const context = {
        document$: { subscribe() {} },
        document: {
            activeElement: null,
            currentScript: { src: "https://example.org/mimosa/assets/dependency-graph.js" },
            createElement: () => tooltip,
            getElementById: () => null,
        },
        window: { innerWidth: 800, innerHeight: 600 },
        setTimeout, clearTimeout,
        requestAnimationFrame: callback => callback(),
        URL,
        AbortController,
        fetch: async () => ({ ok: true, text: async () => "graph" }),
        DOMParser: class { parseFromString() { return { documentElement: svg }; } },
        Option: class {},
        history: { replaceState() { historyWrites++; } },
        console,
    };
    vm.createContext(context);
    vm.runInContext(source, context);
    links.forEach(link => link.addEventListener("focus", () => { context.document.activeElement = link; }));
    const graph = await context.initializeDependencyGraph(panel, "graph.svg", dialog, reference || context.document);
    return { graph, dialog, nodes, links, viewport, output, controls, tooltip, historyWrites: () => historyWrites };
}

test("Escape clears the selection before allowing the modal to close", async () => {
    const { graph, dialog, nodes } = await viewer();
    graph.focusVariable("input");
    const firstEscape = new Event("cancel", { cancelable: true });
    dialog.dispatchEvent(firstEscape);
    assert.equal(firstEscape.defaultPrevented, true);
    assert.equal(nodes.some(node => node.classList.contains("is-selected")), false);

    const secondEscape = new Event("cancel", { cancelable: true });
    dialog.dispatchEvent(secondEscape);
    assert.equal(secondEscape.defaultPrevented, false);
});

test("modal selections preserve history and an already focused view", async () => {
    const { links, nodes, viewport, output, historyWrites } = await viewer();
    links[0].dispatchEvent(new Event("click", { cancelable: true }));
    assert.equal(output.textContent, "85%");
    assert.equal(nodes[0].classList.contains("is-selected"), true);
    const position = [viewport.scrollLeft, viewport.scrollTop];

    links[1].dispatchEvent(new Event("click", { cancelable: true }));
    assert.equal(nodes[1].classList.contains("is-selected"), true);
    assert.equal(output.textContent, "85%");
    assert.deepEqual([viewport.scrollLeft, viewport.scrollTop], position);
    assert.equal(historyWrites(), 0);
});

test("reopening can focus a different variable and fit still resets the zoom", async () => {
    const { graph, nodes, output, controls } = await viewer();
    graph.focusVariable("input");
    graph.focusVariable("output");
    assert.equal(nodes[0].classList.contains("is-selected"), false);
    assert.equal(nodes[1].classList.contains("is-selected"), true);
    controls['[data-action="fit"]'].dispatchEvent(new Event("click"));
    assert.equal(output.textContent, "40%");
});

function pointerEvent(type, properties = {}) {
    return Object.assign(new Event(type, { cancelable: true }), {
        button: 0, pointerId: 1, pointerType: "mouse", clientX: 100, clientY: 100,
        ...properties,
    });
}

test("dragging pans both axes and preserves zoom and selection on release", async () => {
    const { graph, viewport, nodes, output } = await viewer();
    graph.focusVariable("input");
    viewport.scrollLeft = 200;
    viewport.scrollTop = 300;
    viewport.dispatchEvent(pointerEvent("pointerdown"));
    viewport.dispatchEvent(pointerEvent("pointermove", { clientX: 130, clientY: 80 }));
    assert.deepEqual([viewport.scrollLeft, viewport.scrollTop], [170, 320]);
    assert.equal(viewport.capturedPointer, 1);
    assert.equal(viewport.classList.contains("is-panning"), true);

    viewport.dispatchEvent(pointerEvent("pointerup"));
    const releaseClick = Object.assign(new Event("click", { cancelable: true }), { detail: 1 });
    viewport.dispatchEvent(releaseClick);
    assert.equal(releaseClick.defaultPrevented, true);
    assert.equal(viewport.classList.contains("is-panning"), false);
    assert.equal(nodes[0].classList.contains("is-selected"), true);
    assert.equal(output.textContent, "85%");

    // A subsequent background click must still clear the selection.
    viewport.dispatchEvent(Object.assign(new Event("click"), { detail: 1 }));
    assert.equal(nodes[0].classList.contains("is-selected"), false);
});

test("small pointer movements remain clicks, and cancelled drags stop moving", async () => {
    const { viewport } = await viewer();
    viewport.dispatchEvent(pointerEvent("pointerdown"));
    viewport.dispatchEvent(pointerEvent("pointermove", { clientX: 102, clientY: 101 }));
    assert.deepEqual([viewport.scrollLeft, viewport.scrollTop], [0, 0]);
    assert.equal(viewport.classList.contains("is-panning"), false);
    viewport.dispatchEvent(pointerEvent("pointermove", { clientX: 90, clientY: 80 }));
    viewport.dispatchEvent(pointerEvent("pointercancel"));
    viewport.dispatchEvent(pointerEvent("pointermove", { clientX: 50, clientY: 40 }));
    assert.deepEqual([viewport.scrollLeft, viewport.scrollTop], [10, 20]);
    assert.equal(viewport.classList.contains("is-panning"), false);
});

test("touch gestures and secondary mouse buttons retain native behaviour", async () => {
    const { viewport } = await viewer();
    for (const properties of [{ pointerType: "touch" }, { button: 2 }]) {
        viewport.dispatchEvent(pointerEvent("pointerdown", properties));
        const move = pointerEvent("pointermove", { ...properties, clientX: 50 });
        viewport.dispatchEvent(move);
        assert.equal(move.defaultPrevented, false);
        assert.equal(viewport.scrollLeft, 0);
    }
});

test("node information reuses the matching reference entry without duplicate IDs", async () => {
    const copiedAnchor = element();
    copiedAnchor.setAttribute("id", "variable-accreu_sectoral--input");
    const card = element();
    card.querySelectorAll = selector => selector === "[id]" ? [copiedAnchor] : [];
    const reference = {
        getElementById(id) {
            assert.equal(id, "variable-accreu_sectoral--input");
            return { closest: () => ({ cloneNode: () => card }) };
        },
    };
    const { links, nodes, tooltip, viewport } = await viewer(reference);
    links[0].dispatchEvent(new Event("focus"));
    assert.equal(tooltip.hidden, false);
    assert.equal(tooltip.children[0], card);
    assert.equal(copiedAnchor.attributes.id, undefined);
    assert.equal(links[0].attributes["aria-describedby"], tooltip.id);
    assert.equal(nodes.some(node => node.classList.contains("is-selected")), false);
    assert.equal(tooltip.style.left, "108px");
    nodes[0].getBoundingClientRect = () => ({ left: 690, right: 790, top: 580 });
    links[0].dispatchEvent(new Event("focus"));
    assert.equal(tooltip.style.left, "382px");
    assert.equal(tooltip.style.top, "392px");
    nodes[0].getBoundingClientRect = () => ({ left: 290, right: 510, top: 400, bottom: 440 });
    links[0].dispatchEvent(new Event("focus"));
    assert.equal(tooltip.style.left, "290px");
    assert.equal(tooltip.style.top, "192px");
    viewport.dispatchEvent(new Event("scroll"));
    assert.equal(tooltip.hidden, true);
    assert.equal(links[0].attributes["aria-describedby"], undefined);
});

test("hover information stays open while moving from the node into the card", async () => {
    const card = element();
    card.querySelectorAll = () => [];
    const reference = { getElementById: () => ({ closest: () => ({ cloneNode: () => card }) }) };
    const { nodes, tooltip, dialog } = await viewer(reference);
    nodes[0].dispatchEvent(new Event("pointerenter"));
    assert.equal(tooltip.hidden, true);
    await new Promise(resolve => setTimeout(resolve, 280));
    assert.equal(tooltip.hidden, false);
    nodes[0].dispatchEvent(new Event("pointerleave"));
    tooltip.dispatchEvent(new Event("pointerenter"));
    await new Promise(resolve => setTimeout(resolve, 180));
    assert.equal(tooltip.hidden, false);
    dialog.dispatchEvent(new Event("close"));
    assert.equal(tooltip.hidden, true);
});

test("opening a variable link selects the node without opening its information", async () => {
    const card = element();
    card.querySelectorAll = () => [];
    const reference = { getElementById: () => ({ closest: () => ({ cloneNode: () => card }) }) };
    const { graph, nodes, tooltip, dialog } = await viewer(reference);
    graph.focusVariable("input");
    assert.equal(nodes[0].classList.contains("is-selected"), true);
    assert.equal(tooltip.hidden, true);
    nodes[0].dispatchEvent(new Event("pointerenter"));
    await new Promise(resolve => setTimeout(resolve, 280));
    assert.equal(tooltip.hidden, false);
    dialog.dispatchEvent(new Event("cancel", { cancelable: true }));
    assert.equal(tooltip.hidden, true);
    graph.destroy();
    const afterDestroy = new Event("cancel", { cancelable: true });
    dialog.dispatchEvent(afterDestroy);
    assert.equal(afterDestroy.defaultPrevented, false);
});

test("context changes replace the graph, preserve its settings, and offer valid alternatives", async () => {
    const panels = [];
    function graphPanel() {
        const panel = element({
            ".dependency-graph-configuration": element(),
            ".dependency-graph-message": element(),
            ".dependency-graph-viewport": element(),
        });
        panel.cloneNode = graphPanel;
        panel.replaceWith = next => { panel.isConnected = false; panels.push(next); };
        return panel;
    }
    const manifest = { default_context: "coacch", contexts: {
        coacch: { label: "damage module: COACCH", configuration_html: "<pre>params = load_params()</pre>", source: "coacch.svg", variables: ["shared"] },
        accreu_sectoral: { label: "damage module: ACCREU · adaptation: sectoral", configuration_html: "<pre>ACCREU parameters</pre>", source: "accreu_sectoral.svg", variables: ["shared", "sectoral"] },
    } };
    const initialized = [];
    const focused = [];
    let destroyed = 0;
    const context = {
        URL, console,
        document$: { subscribe() {} },
        location: { href: "https://example.org/variables/" },
        history: { replaceState(state, title, url) { context.location.href = String(url); } },
        document: {
            currentScript: { src: "https://example.org/assets/dependency-graph.js" },
            createElement() {
                const node = element();
                node.add = option => { node.value ||= option.value; };
                return node;
            },
        },
        Option: class { constructor(label, value) { this.value = value; } },
        fetch: async () => ({ ok: true, json: async () => manifest }),
    };
    vm.createContext(context);
    vm.runInContext(source, context);
    context.initializeDependencyGraph = async panel => {
        initialized.push(panel.dataset.variableContext);
        return {
            focusVariable: name => focused.push(name),
            destroy: () => destroyed++,
        };
    };
    const download = {};
    const controller = await context.createDependencyGraphController(graphPanel(), {}, null, download);
    await controller.open("accreu_sectoral", "sectoral");
    await controller.open("accreu_sectoral", "shared");
    assert.deepEqual(initialized, ["accreu_sectoral"]);
    await controller.open("coacch", "shared");
    assert.equal(destroyed, 1);
    assert.deepEqual(initialized, ["accreu_sectoral", "coacch"]);
    assert.equal(download.href, "https://example.org/assets/dependency-graphs/coacch.svg");
    assert.equal(panels.at(-1).querySelector(".dependency-graph-configuration").innerHTML, manifest.contexts.coacch.configuration_html);
    assert.equal(focused.at(-1), "shared");

    await controller.open("coacch", "sectoral");
    const message = panels.at(-1).querySelector(".dependency-graph-message");
    assert.equal(message.hidden, false);
    const [, select, button] = message.children;
    assert.equal(select.value, "accreu_sectoral");
    button.dispatchEvent(new Event("click"));
    await new Promise(setImmediate);
    assert.deepEqual(initialized, ["accreu_sectoral", "coacch", "accreu_sectoral"]);
    assert.equal(focused.at(-1), "sectoral");
    await controller.open("unknown", "shared");
    assert.match(panels.at(-1).querySelector(".dependency-graph-viewport").textContent, /no documented graph/);
});

for (const prefix of ["", "/mimosa"]) {
    test(`links created after page setup resolve from the site root ${prefix || "/"}`, async () => {
        let onPage;
        let opens = 0;
        const requests = [];
        const selections = [];
        const graphPanel = { cloneNode() { return this; } };
        const content = element();
        const dialog = element({ button: element(), p: { replaceWith() {} } });
        dialog.showModal = () => { dialog.open = true; opens++; };
        const context = {
            URL, console,
            location: { hash: "" },
            window: new EventTarget(),
            document$: { subscribe(callback) { onPage = callback; } },
            document: {
                currentScript: { src: `https://example.org${prefix}/assets/dependency-graph.js` },
                querySelector: selector => selector === ".md-content" ? content : selector === "[data-documentation-context]"
                    ? { dataset: { documentationContext: "accreu_sectoral" } } : null,
                createElement: () => dialog,
                body: { append() {} },
            },
            fetch: async url => {
                requests.push(String(url));
                return { ok: true, text: async () => "reference page" };
            },
            DOMParser: class {
                parseFromString() {
                    return { querySelector: selector => selector === "#dependency-graph-viewer" ? graphPanel : null };
                }
            },
        };
        vm.createContext(context);
        vm.runInContext(source, context);
        context.createDependencyGraphController = async (panel, reference, modal) => {
            assert.equal(panel, graphPanel);
            assert.equal(modal, dialog);
            return { open: (configuration, name) => selections.push([configuration, name]) };
        };
        context.initializeVariableLinkTooltips = () => ({ destroy() {} });
        onPage();

        for (const name of ["damage_costs", "coacch::riverine_adaptation_costs_abs"]) {
            // A click on a nested MathJax element bubbles to the page container.
            const link = { hash: `#var__${name}` };
            const click = Object.assign(new Event("click", { cancelable: true }), { button: 0 });
            Object.defineProperty(click, "target", { value: {
                closest(selector) {
                    assert.equal(selector, 'a[href*="#var__"]');
                    return link;
                },
            } });
            content.dispatchEvent(click);
            await new Promise(setImmediate);
            assert.equal(click.defaultPrevented, true);
        }
        assert.deepEqual(selections, [["accreu_sectoral", "damage_costs"], ["coacch", "riverine_adaptation_costs_abs"]]);
        assert.deepEqual(requests, [`https://example.org${prefix}/variables/`]);
        assert.equal(opens, 2);
        context.location.hash = "#var__coacch::damage_costs";
        context.window.dispatchEvent(new Event("hashchange"));
        await new Promise(setImmediate);
        assert.deepEqual(selections.at(-1), ["coacch", "damage_costs"]);
        assert.equal(opens, 3);
    });
}

function documentationTooltips({ waitForReference, localReference = false } = {}) {
    const content = element();
    const tooltip = element();
    tooltip.offsetWidth = 300;
    tooltip.offsetHeight = 200;
    tooltip.contains = node => node === tooltip;
    tooltip.remove = () => { tooltip.isConnected = false; };
    const requestedEntries = [];
    const requests = [];
    let parsed = 0;
    const reference = { getElementById(id) {
        requestedEntries.push(id);
        if (id.endsWith("--missing")) return null;
        return { closest: () => ({ cloneNode: () => ({ entry: id, querySelectorAll: () => [] }) }) };
    } };
    const timers = new Map();
    let now = 0;
    let timerId = 0;
    const context = {
        URL, AbortController, console,
        document$: { subscribe() {} },
        document: {
            ...reference,
            activeElement: null,
            currentScript: { src: "https://example.org/mimosa/assets/dependency-graph.js" },
            createElement: () => tooltip,
            getElementById: id => id === "variable-link-tooltip" ? tooltip : reference.getElementById(id),
        },
        window: Object.assign(new EventTarget(), { innerWidth: 800, innerHeight: 600 }),
        setTimeout(callback, delay) { timers.set(++timerId, { callback, due: now + delay }); return timerId; },
        clearTimeout(id) { timers.delete(id); },
        requestAnimationFrame: callback => callback(),
        fetch: async url => {
            requests.push(String(url));
            await waitForReference;
            return { ok: true, text: async () => "reference page" };
        },
        DOMParser: class { parseFromString() { parsed++; return reference; } },
    };
    if (localReference) content.querySelector = () => ({});
    vm.createContext(context);
    vm.runInContext(source, context);
    const controller = context.initializeVariableLinkTooltips(content, "accreu_sectoral");
    function link(hash) {
        const anchor = Object.assign(element(), { hash });
        anchor.contains = node => node === anchor || node?.parentLink === anchor;
        return anchor;
    }
    function event(type, anchor, relatedTarget = null, pointerType = "mouse") {
        const event = new Event(type);
        Object.defineProperties(event, {
            target: { value: { closest: () => anchor } },
            relatedTarget: { value: relatedTarget },
            pointerType: { value: pointerType },
        });
        content.dispatchEvent(event);
    }
    return {
        context, content, tooltip, controller, link, event, requests, requestedEntries,
        parsed: () => parsed,
        async tick(milliseconds) {
            now += milliseconds;
            for (const [id, timer] of [...timers]) {
                if (timer.due <= now) { timers.delete(id); timer.callback(); }
            }
            await new Promise(setImmediate);
        },
    };
}

test("late equation links inherit context, respect overrides, and share cached reference HTML", async () => {
    const page = documentationTooltips();
    const equationLink = page.link("#var__damage_costs");
    page.event("pointerover", equationLink);
    await page.tick(249);
    assert.equal(page.tooltip.hidden, true);
    assert.deepEqual(page.requests, []);
    await page.tick(1);
    assert.equal(page.tooltip.hidden, false);
    assert.equal(page.tooltip.children[0].entry, "variable-accreu_sectoral--damage_costs");
    assert.equal(equationLink.attributes["aria-describedby"], "variable-link-tooltip");

    // Moving between MathJax children inside the same link must not dismiss it.
    page.event("pointerout", equationLink, { parentLink: equationLink });
    await page.tick(200);
    assert.equal(page.tooltip.hidden, false);
    const override = page.link("#var__coacch::damage_costs");
    page.event("pointerover", override);
    await page.tick(250);
    assert.equal(page.tooltip.children[0].entry, "variable-coacch--damage_costs");
    assert.deepEqual(page.requests, ["https://example.org/mimosa/variables/"]);
    assert.equal(page.parsed(), 1);
    assert.equal(equationLink.attributes["aria-describedby"], undefined);
    page.controller.destroy();
});

test("leaving before the delay or during a request prevents a stale hover card", async () => {
    let release;
    const waitForReference = new Promise(resolve => { release = resolve; });
    const page = documentationTooltips({ waitForReference });
    const link = page.link("#var__damage_costs");
    page.event("pointerover", link);
    page.event("pointerout", link);
    await page.tick(250);
    assert.deepEqual(page.requests, []);
    page.event("pointerover", link);
    await page.tick(250);
    assert.equal(page.requests.length, 1);
    page.event("pointerout", link);
    release();
    await page.tick(0);
    assert.equal(page.tooltip.hidden, true);
    assert.deepEqual(page.requestedEntries, []);
    page.controller.destroy();
});

test("link cards stay readable and dismiss on page scrolling, Escape, or clicking", async () => {
    const page = documentationTooltips();
    const link = page.link("#var__damage_costs");
    page.event("pointerover", link);
    await page.tick(250);
    page.event("pointerout", link);
    page.tooltip.dispatchEvent(new Event("pointerenter"));
    // Clicking the card moves focus off the link after the pointer enters it.
    page.event("focusout", link, page.tooltip);
    await page.tick(200);
    assert.equal(page.tooltip.hidden, false);
    assert.equal(page.tooltip.tabIndex, -1);
    const internalScroll = new Event("scroll");
    Object.defineProperty(internalScroll, "target", { value: page.tooltip });
    page.context.window.dispatchEvent(internalScroll);
    assert.equal(page.tooltip.hidden, false);
    const internalClick = new Event("click");
    Object.defineProperty(internalClick, "target", { value: page.tooltip });
    page.content.dispatchEvent(internalClick);
    assert.equal(page.tooltip.hidden, false);
    page.context.window.dispatchEvent(new Event("scroll"));
    assert.equal(page.tooltip.hidden, true);

    for (const dismiss of [
        () => page.context.window.dispatchEvent(Object.assign(new Event("keydown"), { key: "Escape" })),
        () => page.event("click", link),
        () => page.context.window.dispatchEvent(new Event("resize")),
    ]) {
        page.context.document.activeElement = link;
        page.event("focusin", link);
        await page.tick(0);
        assert.equal(page.tooltip.hidden, false);
        dismiss();
        assert.equal(page.tooltip.hidden, true);
        assert.equal(link.attributes["aria-describedby"], undefined);
    }
    page.controller.destroy();
});

test("touch, unavailable entries and disposed page listeners do not open link cards", async () => {
    const page = documentationTooltips({ localReference: true });
    const link = page.link("#var__missing");
    page.event("pointerover", link, null, "touch");
    await page.tick(250);
    assert.deepEqual(page.requestedEntries, []);
    page.event("pointerover", link);
    await page.tick(250);
    assert.equal(page.tooltip.hidden, true);
    assert.deepEqual(page.requests, []);
    page.event("pointerover", page.link("#var__damage_costs"));
    page.controller.destroy();
    await page.tick(250);
    page.event("pointerover", page.link("#var__damage_costs"));
    await page.tick(250);
    assert.deepEqual(page.requestedEntries, ["variable-accreu_sectoral--missing"]);
    assert.equal(page.tooltip.isConnected, false);
});
