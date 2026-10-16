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
        classList: {
            add: name => classes.add(name),
            remove: name => classes.delete(name),
            toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name),
            contains: name => classes.has(name),
        },
        querySelector: selector => children[selector],
        setAttribute() {},
        getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 40 }),
    });
}

async function viewer() {
    const links = [element(), element()];
    const nodes = ["input", "output"].map((name, index) => element({
        title: { textContent: name }, a: links[index],
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
    let historyWrites = 0;
    const context = {
        document$: { subscribe() {} },
        document: {
            activeElement: null,
            currentScript: { src: "https://example.org/mimosa/assets/dependency-graph.js" },
        },
        URL,
        fetch: async () => ({ ok: true, text: async () => "graph" }),
        DOMParser: class { parseFromString() { return { documentElement: svg }; } },
        Option: class {},
        history: { replaceState() { historyWrites++; } },
        console,
    };
    vm.createContext(context);
    vm.runInContext(source, context);
    const graph = await context.initializeDependencyGraph(panel, "graph.svg", dialog);
    return { graph, dialog, nodes, links, viewport, output, controls, historyWrites: () => historyWrites };
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

for (const prefix of ["", "/mimosa"]) {
    test(`links created after page setup resolve from the site root ${prefix || "/"}`, async () => {
        let onPage;
        let opens = 0;
        const requests = [];
        const selections = [];
        const graphPanel = {};
        const content = element();
        const dialog = element({ button: element(), p: { replaceWith() {} } });
        dialog.showModal = () => { dialog.open = true; opens++; };
        const context = {
            URL, console,
            document$: { subscribe(callback) { onPage = callback; } },
            document: {
                currentScript: { src: `https://example.org${prefix}/assets/dependency-graph.js` },
                querySelector: selector => selector === ".md-content" ? content : null,
                createElement: () => dialog,
                body: { append() {} },
            },
            fetch: async url => {
                requests.push(String(url));
                return { ok: true, text: async () => "reference page" };
            },
            DOMParser: class {
                parseFromString() {
                    return { querySelector: selector => selector === "#dependency-graph-viewer"
                        ? graphPanel : { getAttribute: () => "../assets/dependency-graph.svg" } };
                }
            },
        };
        vm.createContext(context);
        vm.runInContext(source, context);
        context.initializeDependencyGraph = async (panel, source, modal) => {
            assert.equal(panel, graphPanel);
            assert.equal(String(source), `https://example.org${prefix}/assets/dependency-graph.svg`);
            assert.equal(modal, dialog);
            return { focusVariable: name => selections.push(name) };
        };
        onPage();

        for (const name of ["damage_costs", "riverine_adaptation_costs_abs"]) {
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
        assert.deepEqual(selections, ["damage_costs", "riverine_adaptation_costs_abs"]);
        assert.deepEqual(requests, [`https://example.org${prefix}/variables/`]);
        assert.equal(opens, 2);
    });
}
