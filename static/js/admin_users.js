(function () {
    var editModal = document.getElementById('edit-modal');
    var toggleModal = document.getElementById('toggle-modal');
    if (!editModal) return;

    var editFields = {
        id: document.getElementById('edit-user-id'),
        first: document.getElementById('edit-first'),
        last: document.getElementById('edit-last'),
        phone: document.getElementById('edit-phone'),
    };

    var toggleFields = {
        id: document.getElementById('toggle-user-id'),
        active: document.getElementById('toggle-is-active'),
        title: document.getElementById('toggle-title'),
        body: document.getElementById('toggle-body'),
        submit: document.getElementById('toggle-submit'),
    };

    document.addEventListener('click', function (e) {
        var editBtn = e.target.closest('[data-action="edit-user"]');
        if (editBtn) {
            editFields.id.value = editBtn.dataset.userId;
            editFields.first.value = editBtn.dataset.firstName;
            editFields.last.value = editBtn.dataset.lastName;
            var phone = editBtn.dataset.phone;
            editFields.phone.value = phone === 'None' ? '' : phone;
            editModal.classList.add('open');
            return;
        }

        var toggleBtn = e.target.closest('[data-action="toggle-doctor"]');
        if (toggleBtn) {
            var wasActive = toggleBtn.dataset.isActive === '1';
            var nextActive = wasActive ? '0' : '1';
            toggleFields.id.value = toggleBtn.dataset.userId;
            toggleFields.active.value = nextActive;
            toggleFields.title.textContent = wasActive ? 'Deactivate Doctor?' : 'Activate Doctor?';
            toggleFields.body.textContent =
                (wasActive
                    ? 'Deactivate ' + toggleBtn.dataset.name + '? They will not be able to access the doctor portal.'
                    : 'Activate ' + toggleBtn.dataset.name + '? They will be able to access the doctor portal.');
            toggleFields.submit.textContent = wasActive ? 'Deactivate' : 'Activate';
            toggleModal.classList.add('open');
            return;
        }

        var closer = e.target.closest('[data-close-modal]');
        if (closer) {
            document.getElementById(closer.dataset.closeModal).classList.remove('open');
        }
    });

    [editModal, toggleModal].forEach(function (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.remove('open');
        });
    });
})();
