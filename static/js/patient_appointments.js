(function () {
    var dataEl = document.getElementById('availability-data');
    if (!dataEl) return;
    var availabilityData = JSON.parse(dataEl.getAttribute('data-json'));

    var DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

    function getUpcomingDates(dayName, count) {
        var target = DAYS.indexOf(dayName);
        var dates = [];
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        for (var i = 1; i <= 60 && dates.length < count; i++) {
            var d = new Date(today);
            d.setDate(today.getDate() + i);
            if (d.getDay() === target) dates.push(d);
        }
        return dates;
    }

    function formatDate(d) {
        return d.toLocaleDateString('en-CA', {
            weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
        });
    }

    function toISODate(d) {
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    function buildTimeOptions(doctorId, dateStr, selectEl) {
        selectEl.innerHTML = '<option value="">Select a time</option>';
        if (!doctorId || !dateStr || !availabilityData[doctorId]) return;
        var dayName = DAYS[new Date(dateStr + 'T00:00:00').getDay()];
        var slots = availabilityData[doctorId].filter(function (s) { return s.day === dayName; });
        if (slots.length === 0) {
            selectEl.innerHTML = '<option value="">Doctor not available on this date</option>';
            return;
        }
        slots.forEach(function (slot) {
            var current = slot.start;
            while (current < slot.end) {
                var opt = document.createElement('option');
                opt.value = current;
                opt.textContent = current;
                selectEl.appendChild(opt);
                var parts = current.split(':').map(Number);
                var next = new Date(0, 0, 0, parts[0], parts[1] + 30);
                current = String(next.getHours()).padStart(2, '0') + ':' +
                          String(next.getMinutes()).padStart(2, '0');
            }
        });
    }

    var doctorSelect = document.getElementById('doctor-select');
    var dateInput = document.getElementById('date-input');
    var timeSelect = document.getElementById('time-select');
    var availabilityInfo = document.getElementById('availability-info');
    var availabilityList = document.getElementById('availability-list');

    doctorSelect.addEventListener('change', function () {
        var doctorId = this.value;
        if (!doctorId || !availabilityData[doctorId]) {
            availabilityInfo.style.display = 'none';
            return;
        }
        availabilityList.innerHTML = '';
        availabilityData[doctorId].forEach(function (s) {
            getUpcomingDates(s.day, 2).forEach(function (date) {
                var chip = document.createElement('span');
                chip.className = 'availability-chip';
                chip.dataset.date = toISODate(date);
                chip.textContent = formatDate(date) + '  ' + s.start + '–' + s.end;
                availabilityList.appendChild(chip);
            });
        });
        availabilityInfo.style.display = 'block';
        buildTimeOptions(doctorId, dateInput.value, timeSelect);
    });

    availabilityList.addEventListener('click', function (e) {
        var chip = e.target.closest('.availability-chip');
        if (!chip) return;
        dateInput.value = chip.dataset.date;
        buildTimeOptions(doctorSelect.value, dateInput.value, timeSelect);
    });

    dateInput.addEventListener('change', function () {
        buildTimeOptions(doctorSelect.value, this.value, timeSelect);
    });

    dateInput.min = new Date().toISOString().split('T')[0];

    var reasonInput = document.getElementById('reason-input');
    var reasonCount = document.getElementById('reason-count');
    if (reasonInput && reasonCount) {
        reasonInput.addEventListener('input', function () {
            reasonCount.textContent = reasonInput.value.length;
        });
    }

    var rescheduleModal = document.getElementById('reschedule-modal');
    var rescheduleIdInput = document.getElementById('reschedule-id');
    var rescheduleDoctorInput = document.getElementById('reschedule-doctor-id');
    var rescheduleDate = document.getElementById('reschedule-date');
    var rescheduleTime = document.getElementById('reschedule-time');

    rescheduleDate.addEventListener('change', function () {
        buildTimeOptions(rescheduleDoctorInput.value, this.value, rescheduleTime);
    });

    var cancelModal = document.getElementById('cancel-modal');
    var cancelIdInput = document.getElementById('cancel-id');
    var cancelBody = document.getElementById('cancel-body');

    document.addEventListener('click', function (e) {
        var rescheduleBtn = e.target.closest('[data-action="reschedule"]');
        if (rescheduleBtn) {
            rescheduleIdInput.value = rescheduleBtn.dataset.appointmentId;
            rescheduleDoctorInput.value = rescheduleBtn.dataset.doctorId;
            rescheduleDate.value = '';
            rescheduleDate.min = new Date().toISOString().split('T')[0];
            rescheduleTime.innerHTML = '<option value="">Select a date first</option>';
            rescheduleModal.classList.add('open');
            return;
        }

        var cancelBtn = e.target.closest('[data-action="cancel-appt"]');
        if (cancelBtn) {
            cancelIdInput.value = cancelBtn.dataset.appointmentId;
            cancelBody.textContent =
                'Your appointment on ' + cancelBtn.dataset.date +
                ' at ' + cancelBtn.dataset.time +
                ' will be cancelled. This cannot be undone.';
            cancelModal.classList.add('open');
            return;
        }

        var closer = e.target.closest('[data-close-modal]');
        if (closer) {
            document.getElementById(closer.dataset.closeModal).classList.remove('open');
        }
    });

    [rescheduleModal, cancelModal].forEach(function (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.remove('open');
        });
    });
})();
