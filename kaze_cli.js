(function () {
    var pages = [];
    document.querySelectorAll('.sidebar-nav a[href]').forEach(function (a) {
        var name = (a.textContent || '').trim().toLowerCase();
        if (name && a.getAttribute('href')) pages.push({ name: name, href: a.getAttribute('href') });
    });
    var box = document.createElement('section');
    box.className = 'kaze-cli';
    box.hidden = true;
    box.innerHTML = '<header><span>KAZE CLI</span><button type="button" id="cliClose">close</button></header><pre id="cliOut">KAZE Traders command line. Type help.</pre><form id="cliForm"><span>kaze></span><input id="cliInput" autocomplete="off" spellcheck="false" placeholder="help"></form>';
    document.body.appendChild(box);
    var fab = document.createElement('button');
    fab.className = 'cli-fab';
    fab.type = 'button';
    fab.textContent = 'CLI';
    document.body.appendChild(fab);
    var out = box.querySelector('#cliOut');
    var input = box.querySelector('#cliInput');
    function print(line) { out.textContent += '\n' + line; out.scrollTop = out.scrollHeight; }
    function open() { box.hidden = false; fab.hidden = true; input.focus(); }
    function close() { box.hidden = true; fab.hidden = false; }
    fab.addEventListener('click', open);
    box.querySelector('#cliClose').addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === '`') { e.preventDefault(); box.hidden ? open() : close(); }
    });
    function go(q) {
        q = (q || '').toLowerCase();
        var hit = pages.find(function (p) { return p.name === q || p.name.indexOf(q) === 0; });
        if (!hit) { print('No page named "' + q + '". Try: ls'); return; }
        print('Opening ' + hit.name + '…');
        window.location = hit.href;
    }
    box.querySelector('#cliForm').addEventListener('submit', function (e) {
        e.preventDefault();
        var raw = input.value.trim();
        input.value = '';
        if (!raw) return;
        print('kaze> ' + raw);
        var parts = raw.split(/\s+/);
        var cmd = parts[0].toLowerCase();
        var arg = parts.slice(1).join(' ');
        if (cmd === 'help') {
            print('help · ls · go <page> · open <page> · theme dark|light · clear · who · version');
        } else if (cmd === 'ls') {
            print(pages.map(function (p) { return p.name; }).join(' · ') || 'No pages in this mode.');
        } else if (cmd === 'go' || cmd === 'open') {
            go(arg);
        } else if (cmd === 'theme') {
            var next = arg === 'light' ? 'light' : 'dark';
            document.documentElement.classList.toggle('theme-light', next === 'light');
            document.documentElement.setAttribute('data-theme-pref', next);
            try { localStorage.setItem('kaze-theme', next); } catch (err) {}
            print('Theme set to ' + next + ' for this browser.');
        } else if (cmd === 'clear') {
            out.textContent = 'Cleared.';
        } else if (cmd === 'who') {
            var user = document.querySelector('.user-menu .dropbtn, .user-name');
            print(user ? user.textContent.trim() : 'Signed-in desk');
        } else if (cmd === 'version') {
            print('KAZE Traders desk · GUI 4.0 · CLI 1.0');
        } else if (cmd === 'back') {
            history.back();
        } else {
            go(raw);
        }
    });
})();
