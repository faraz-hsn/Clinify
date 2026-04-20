(function () {
    document.addEventListener('click', function (e) {
        if (e.target.closest('a, button, input, select, textarea, label')) return;
        var row = e.target.closest('[data-href]');
        if (!row) return;
        window.location = row.dataset.href;
    });
})();
