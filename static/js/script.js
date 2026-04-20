// add medication row in doctor prescriptions
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
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = () => clone.remove();
    removeGroup.appendChild(removeBtn);
    clone.appendChild(removeGroup);

    list.appendChild(clone);
}

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