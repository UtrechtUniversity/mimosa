// Run with: node --test tests/javascript/plotly-resize.test.cjs
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { test } = require("node:test");
const vm = require("node:vm");

const source = readFileSync(`${__dirname}/../../docs/assets/plotly-resize.js`, "utf8");

function page(plots) {
    let change;
    const frames = [];
    const resized = [];
    const context = {
        document: { addEventListener(type, handler) {
            assert.equal(type, "change");
            change = handler;
        } },
        requestAnimationFrame(callback) { frames.push(callback); },
        window: { Plotly: { Plots: { resize(plot) { resized.push(plot); } } } },
    };
    vm.runInNewContext(source, context);
    return {
        context, frames, resized,
        change(isTab = true) {
            change({ target: {
                matches: selector => {
                    assert.equal(selector, '.tabbed-set > input[type="radio"]');
                    return isTab;
                },
                parentElement: { querySelectorAll: () => plots },
            } });
        },
    };
}

test("a tab switch resizes plots after layout and skips hidden or unloaded plots", () => {
    const visible = { _fullLayout: {}, clientWidth: 300, clientHeight: 250 };
    const nestedHidden = { _fullLayout: {}, clientWidth: 0, clientHeight: 0 };
    const unloaded = { clientWidth: 300, clientHeight: 250 };
    const current = page([visible, nestedHidden, unloaded]);

    current.change();
    assert.deepEqual(current.resized, []);
    current.frames.shift()();
    assert.deepEqual(current.resized, [visible]);

    // Switching to a nested tab makes its plot eligible too.
    visible.clientWidth = 0;
    Object.assign(nestedHidden, { clientWidth: 300, clientHeight: 250 });
    current.change();
    current.frames.shift()();
    assert.deepEqual(current.resized, [visible, nestedHidden]);
});

test("other form changes do not resize plots", () => {
    const current = page([]);
    current.change(false);
    assert.deepEqual(current.frames, []);
});

test("tabs remain usable when Plotly has not loaded", () => {
    const current = page([]);
    delete current.context.window.Plotly;
    current.change();
    assert.doesNotThrow(() => current.frames.shift()());
});
