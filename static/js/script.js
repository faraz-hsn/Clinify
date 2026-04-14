// add medication row in doctor prescriptions
function addMedRow() {
    const list = document.getElementById('med-list');
    if (!list) return;

    const first = list.querySelector('.med-row');
    if (!first) return;

    const clone = first.cloneNode(true);
    clone.querySelectorAll('input').forEach(i => i.value = '');
    list.appendChild(clone);
}

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