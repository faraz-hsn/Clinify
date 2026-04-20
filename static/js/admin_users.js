(function () {
    var editModal = document.getElementById('edit-modal');
    var deleteModal = document.getElementById('delete-modal');
    if (!editModal) return;

    var editFields = {
        id: document.getElementById('edit-user-id'),
        first: document.getElementById('edit-first'),
        last: document.getElementById('edit-last'),
        phone: document.getElementById('edit-phone'),
        role: document.getElementById('edit-role'),
    };

    var deleteIdInput = document.getElementById('delete-user-id');
    var deleteBody = document.getElementById('delete-body');

    document.addEventListener('click', function (e) {
        var editBtn = e.target.closest('[data-action="edit-user"]');
        if (editBtn) {
            editFields.id.value = editBtn.dataset.userId;
            editFields.first.value = editBtn.dataset.firstName;
            editFields.last.value = editBtn.dataset.lastName;
            var phone = editBtn.dataset.phone;
            editFields.phone.value = phone === 'None' ? '' : phone;
            editFields.role.value = editBtn.dataset.role;
            editModal.classList.add('open');
            return;
        }

        var deleteBtn = e.target.closest('[data-action="delete-user"]');
        if (deleteBtn) {
            deleteIdInput.value = deleteBtn.dataset.userId;
            deleteBody.textContent =
                'Permanently delete ' + deleteBtn.dataset.name + '? This cannot be undone.';
            deleteModal.classList.add('open');
            return;
        }

        var closer = e.target.closest('[data-close-modal]');
        if (closer) {
            document.getElementById(closer.dataset.closeModal).classList.remove('open');
        }
    });

    [editModal, deleteModal].forEach(function (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.remove('open');
        });
    });
})();
