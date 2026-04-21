document.addEventListener('click', function (e) {
    var addBtn = e.target.closest('[data-action="add-med-row"]');
    if (addBtn) {
        addMedRow();
        return;
    }
    var removeBtn = e.target.closest('[data-action="remove-med-row"]');
    if (removeBtn) {
        var row = removeBtn.closest('.med-row');
        if (row) row.remove();
    }
});

function addMedRow() {
    const list = document.getElementById('med-list');
    if (!list) return;

    const first = list.querySelector('.med-row');
    if (!first) return;

    const clone = first.cloneNode(true);
    clone.querySelectorAll('input').forEach(i => i.value = '');

    const removeGroup = document.createElement('div');
    removeGroup.className = 'form-group';
    removeGroup.style.alignSelf = 'end';
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-danger btn-sm';
    removeBtn.dataset.action = 'remove-med-row';
    removeBtn.textContent = 'Remove';
    removeGroup.appendChild(removeBtn);
    clone.appendChild(removeGroup);

    list.appendChild(clone);
}

(function setTimezoneCookie() {
    try {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (!tz) return;
        if (document.cookie.split('; ').some(c => c.startsWith('tz=' + tz))) return;
        document.cookie = 'tz=' + tz + '; path=/; max-age=31536000; samesite=lax';
    } catch (e) {}
})();

document.addEventListener('input', function (e) {
    const el = e.target;
    if (!(el instanceof HTMLInputElement) || el.type !== 'tel') return;

    const digits = el.value.replace(/\D/g, '').slice(0, 10);
    let formatted = digits;
    if (digits.length > 6)      formatted = `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
    else if (digits.length > 3) formatted = `(${digits.slice(0,3)}) ${digits.slice(3)}`;
    else if (digits.length > 0) formatted = `(${digits}`;
    el.value = formatted;
});

// auto dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity .4s';
            setTimeout(function () { alert.remove(); }, 400);
        }, 4000);
    });
});