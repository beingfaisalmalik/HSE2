/* Cookie-independent, per-tab demo transport. No popup or service worker needed. */
(function () {
    "use strict";
    const currentScript = document.currentScript;
    const KEY = "hse-demo-browser-session-v1";
    const TOKEN_HEADER = "X-HSE-Demo-Session";
    const CHALLENGE_HEADER = "X-HSE-Demo-Challenge";
    const original = window.__hseTransportOriginal || {
        fetch: window.fetch.bind(window),
        xhrOpen: XMLHttpRequest.prototype.open,
        xhrSend: XMLHttpRequest.prototype.send,
    };
    window.__hseTransportOriginal = original;
    function token() {
        try { return sessionStorage.getItem(KEY) || ""; } catch (_) { return window.__hseSession || ""; }
    }
    function save(value) {
        window.__hseSession = value || "";
        try { if (value) sessionStorage.setItem(KEY, value); else sessionStorage.removeItem(KEY); } catch (_) {}
        // Same-origin full navigation can recover even if sessionStorage is unavailable.
        if (value) window.name = KEY + ":" + value;
        else if (window.name.startsWith(KEY + ":")) window.name = "";
    }
    if (!token() && window.name.startsWith(KEY + ":")) save(window.name.slice(KEY.length + 1));
    function sameOrigin(value) {
        try { return new URL(value, location.href).origin === location.origin; } catch (_) { return false; }
    }
    function adopt(response) {
        const next = response.headers.get(TOKEN_HEADER);
        if (next) save(next);
    }
    function logOutURL(url) {
        return /\/web\/session\/(?:destroy|logout)(?:\?|$)/.test(url);
    }
    window.fetch = async function (input, options) {
        const url = input instanceof Request ? input.url : String(input);
        const opts = Object.assign({}, options || {});
        if (sameOrigin(url) && token()) {
            opts.headers = new Headers(opts.headers || (input instanceof Request ? input.headers : {}));
            opts.headers.set(TOKEN_HEADER, token());
        }
        const response = await original.fetch(input, opts);
        if (sameOrigin(url)) { adopt(response); if (logOutURL(url)) save(""); }
        return response;
    };
    XMLHttpRequest.prototype.open = function (method, url) {
        this.__hseURL = String(url);
        return original.xhrOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function () {
        if (sameOrigin(this.__hseURL) && token()) this.setRequestHeader(TOKEN_HEADER, token());
        this.addEventListener("load", () => {
            const next = this.getResponseHeader(TOKEN_HEADER);
            if (next) save(next);
            if (logOutURL(this.__hseURL)) save("");
        });
        return original.xhrSend.apply(this, arguments);
    };
    // Prevent Odoo's offline worker caching private recovered documents.
    if (navigator.serviceWorker && !window.__hseWorkerPatched) {
        const register = navigator.serviceWorker.register.bind(navigator.serviceWorker);
        navigator.serviceWorker.register = (url, options) => {
            if (String(url).includes("/web/service-worker.js")) return Promise.reject(new Error("Offline caching is disabled for the preview session."));
            return register(url, options);
        };
        window.__hseWorkerPatched = true;
    }
    function message(text, failed) {
        let box = document.querySelector("[data-hse-auth-message]");
        if (!box) {
            box = document.createElement("p"); box.dataset.hseAuthMessage = "1";
            (document.querySelector("form.oe_login_form") || document.body).prepend(box);
        }
        box.textContent = text;
        box.style.cssText = "padding:12px;border-radius:6px;background:" + (failed ? "#fff0ed;color:#9f3328" : "#edf5ef;color:#245b40") + ";font:14px system-ui;";
    }
    async function recover() {
        if (!token()) { location.replace("/web/login?redirect=" + encodeURIComponent(location.pathname + location.search + location.hash)); return; }
        try {
            const response = await window.fetch(location.pathname + location.search, {cache: "no-store"});
            if (!response.ok || response.headers.get("X-HSE-Demo-Recovery")) throw new Error("Your demo session expired. Please sign in again.");
            const html = await response.text();
            if (!response.headers.get("Content-Type")?.includes("text/html")) throw new Error("This page is not available in the preview.");
            document.open(); document.write(html); document.close();
        } catch (error) {
            save(""); message(error.message, true);
            const link = document.createElement("a"); link.href = "/web/login"; link.textContent = "Return to sign-in"; document.body.append(link);
        }
    }
    if (currentScript && currentScript.dataset.hseRecover) { recover(); return; }
    const challenge = currentScript && currentScript.dataset.hseChallenge;
    document.addEventListener("submit", async event => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || !sameOrigin(form.action)) return;
        const path = new URL(form.action || location.href, location.href).pathname;
        const isLogin = path === "/web/login";
        if (!isLogin && !token()) return;
        if (isLogin && !challenge) return;
        event.preventDefault(); event.stopImmediatePropagation();
        const button = event.submitter || form.querySelector('button[type="submit"]');
        if (button) button.disabled = true;
        try {
            const data = new FormData(form);
            if (event.submitter?.name) data.append(event.submitter.name, event.submitter.value);
            const headers = {};
            if (isLogin) headers[CHALLENGE_HEADER] = challenge;
            else headers[TOKEN_HEADER] = token();
            message(isLogin ? "Signing in securely…" : "Saving your submission…", false);
            const response = await original.fetch(form.action || location.href, {
                method: (form.method || "POST").toUpperCase(), headers, body: data, cache: "no-store",
            });
            adopt(response);
            if (isLogin && response.headers.get("Content-Type")?.includes("application/json")) {
                const result = await response.json();
                if (!response.ok || !result.token) throw new Error(result.error || "Sign-in failed.");
                save(result.token);
                location.assign(result.next); // Fresh context; the GET recovers from this tab's token.
            } else if (isLogin) {
                const page = new DOMParser().parseFromString(await response.text(), "text/html");
                throw new Error(page.querySelector(".alert-danger")?.textContent.trim() || "Sign-in was rejected. Check the demo credentials and try again.");
            } else {
                if (!response.ok) throw new Error("The submission was rejected. Please check the form.");
                location.assign(response.url);
            }
        } catch (error) { message(error.message, true); if (button) button.disabled = false; }
    }, true);
    document.addEventListener("click", async event => {
        const link = event.target.closest("a[href]");
        if (!link || !token() || !sameOrigin(link.href)) return;
        const url = new URL(link.href);
        const download = link.hasAttribute("download") || url.pathname === "/hse/demo/guide" || url.pathname.endsWith(".csv") || url.pathname.startsWith("/report/pdf/");
        if (download) {
            event.preventDefault(); event.stopImmediatePropagation();
            try {
                const response = await window.fetch(url.href);
                if (!response.ok) throw new Error("The download is unavailable for this account.");
                const objectURL = URL.createObjectURL(await response.blob());
                const anchor = document.createElement("a"); anchor.href = objectURL;
                const disposition = response.headers.get("Content-Disposition") || "";
                anchor.download = disposition.match(/filename="?([^";]+)"?/)?.[1] || "HSE-demo-export";
                anchor.click(); setTimeout(() => URL.revokeObjectURL(objectURL), 30000);
            } catch (error) { message(error.message, true); }
        } else if (link.target === "_blank") {
            // The real preview can block popups. All demo navigation remains in this view.
            event.preventDefault(); event.stopImmediatePropagation(); location.assign(url.href);
        }
    }, true);
    // Private image elements cannot attach headers. Resolve same-origin image
    // requests through authenticated fetch and display their object URLs.
    function images(root) {
        const candidates = root instanceof HTMLImageElement ? [root] : root.querySelectorAll?.("img") || [];
        for (const image of candidates) {
            if (!token() || image.dataset.hseFetched || !sameOrigin(image.src) || !new URL(image.src).pathname.startsWith("/web/image")) continue;
            image.dataset.hseFetched = "1";
            window.fetch(image.src).then(response => response.ok ? response.blob() : null).then(blob => {
                if (blob) { const url = URL.createObjectURL(blob); image.src = url; image.addEventListener("load", () => URL.revokeObjectURL(url), {once:true}); }
            }).catch(() => {});
        }
    }
    document.addEventListener("DOMContentLoaded", () => {
        images(document);
        new MutationObserver(records => records.forEach(record => record.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) images(node);
        }))).observe(document.body, {childList:true,subtree:true});
        if (challenge) message("Preview-compatible sign-in: no cookies or new tab required.", false);
    }, {once:true});
})();
