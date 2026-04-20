(function () {
    var modal = document.getElementById('confirm-modal');
    if (!modal) return;

    var titleEl = document.getElementById('confirm-title');
    var bodyEl = document.getElementById('confirm-body');
    var actionInput = document.getElementById('confirm-action');
    var submitBtn = document.getElementById('confirm-submit');

    var CONFIRM_COPY = {
        no_show: {
            title: 'Mark as No-Show?',
            body: 'The patient did not attend this appointment. This cannot be undone.',
            submit: 'Mark No-Show',
            submitClass: 'btn btn-outline',
        },
        cancel: {
            title: 'Cancel Appointment?',
            body: 'The appointment will be cancelled and the patient will be notified. This cannot be undone.',
            submit: 'Cancel Appointment',
            submitClass: 'btn btn-danger',
        },
    };

    document.addEventListener('click', function (e) {
        var opener = e.target.closest('[data-confirm]');
        if (opener) {
            var copy = CONFIRM_COPY[opener.dataset.confirm];
            if (!copy) return;
            titleEl.textContent = copy.title;
            bodyEl.textContent = copy.body;
            actionInput.value = opener.dataset.confirm;
            submitBtn.textContent = copy.submit;
            submitBtn.className = copy.submitClass;
            modal.classList.add('open');
            return;
        }

        var closer = e.target.closest('[data-close-modal]');
        if (closer) {
            document.getElementById(closer.dataset.closeModal).classList.remove('open');
        }
    });

    modal.addEventListener('click', function (e) {
        if (e.target === modal) modal.classList.remove('open');
    });
})();
