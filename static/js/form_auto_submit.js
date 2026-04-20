(function () {
    document.addEventListener('change', function (e) {
        var el = e.target.closest('[data-auto-submit]');
        if (el && el.form) el.form.submit();
    });
})();
