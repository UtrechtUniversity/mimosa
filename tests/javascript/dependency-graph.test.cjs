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
        document: { activeElement: null },
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
