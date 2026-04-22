(function () {
    var availEl = document.getElementById('availability-data');
    var docsEl = document.getElementById('doctors-data');
    if (!availEl || !docsEl) return;

    var availabilityData = JSON.parse(availEl.getAttribute('data-json'));
    var doctors = JSON.parse(docsEl.getAttribute('data-json'));

    var DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
    var MONTHS = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
    var SLOT_MINUTES = 30;
    var MAX_MONTHS_AHEAD = 3;

    // ---- Helpers ----
    function toISODate(d) {
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }
    function parseTime(t) {
        var p = t.split(':').map(Number);
        return p[0] * 60 + p[1];
    }
    function fmtTime(mins) {
        var h = Math.floor(mins / 60), m = mins % 60;
        return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
    }
    function fmtDisplayTime(t) {
        var p = t.split(':').map(Number);
        var period = p[0] >= 12 ? 'PM' : 'AM';
        var h = p[0] % 12 || 12;
        return h + ':' + String(p[1]).padStart(2, '0') + ' ' + period;
    }
    function fmtDisplayDate(iso) {
        var d = new Date(iso + 'T00:00:00');
        return d.toLocaleDateString(undefined, {
            weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
        });
    }
    function startOfToday() {
        var d = new Date();
        d.setHours(0, 0, 0, 0);
        return d;
    }

    // ---- Popover manager ----
    var openPop = null;
    function closeAnyPop() {
        if (openPop) { openPop.hidden = true; openPop = null; }
    }
    document.addEventListener('click', function (e) {
        if (!openPop) return;
        if (!e.target.closest('[data-cp-pop]') && !e.target.closest('[data-cp-trigger]')) {
            closeAnyPop();
        }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeAnyPop();
    });

    function togglePop(pop) {
        if (openPop && openPop !== pop) openPop.hidden = true;
        pop.hidden = !pop.hidden;
        openPop = pop.hidden ? null : pop;
    }

    // ---- Doctor picker ----
    function initDoctorPicker(rootId, onChange) {
        var root = document.getElementById(rootId);
        if (!root) return null;
        var input = root.querySelector('input[type=hidden]');
        var trigger = root.querySelector('[data-cp-trigger]');
        var display = root.querySelector('.cp-display');
        var sub = root.querySelector('.cp-sub');
        var pop = root.querySelector('[data-cp-pop]');
        var list = root.querySelector('.cp-list');

        doctors.forEach(function (d) {
            var opt = document.createElement('button');
            opt.type = 'button';
            opt.className = 'cp-option';
            opt.dataset.value = d.id;
            opt.innerHTML =
                '<div class="cp-option-name">' + d.name + '</div>' +
                '<div class="cp-option-sub">' + d.specialty + '</div>';
            list.appendChild(opt);
        });

        list.addEventListener('click', function (e) {
            var opt = e.target.closest('.cp-option');
            if (!opt) return;
            var doc = doctors.find(function (d) { return d.id === opt.dataset.value; });
            input.value = doc.id;
            display.textContent = doc.name;
            sub.textContent = doc.specialty;
            sub.hidden = false;
            trigger.classList.add('has-value');
            list.querySelectorAll('.cp-option.is-active').forEach(function (b) {
                b.classList.remove('is-active');
            });
            opt.classList.add('is-active');
            closeAnyPop();
            if (onChange) onChange(doc.id);
        });

        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            togglePop(pop);
        });

        return {
            setValue: function (id) {
                var doc = doctors.find(function (d) { return d.id === String(id); });
                if (!doc) return;
                input.value = doc.id;
                display.textContent = doc.name;
                sub.textContent = doc.specialty;
                sub.hidden = false;
                trigger.classList.add('has-value');
                list.querySelectorAll('.cp-option.is-active').forEach(function (b) {
                    b.classList.remove('is-active');
                });
                var opt = list.querySelector('.cp-option[data-value="' + doc.id + '"]');
                if (opt) opt.classList.add('is-active');
            },
        };
    }

    // ---- Date picker ----
    function initDatePicker(rootId) {
        var root = document.getElementById(rootId);
        if (!root) return null;
        var input = root.querySelector('input[type=hidden]');
        var trigger = root.querySelector('[data-cp-trigger]');
        var display = root.querySelector('.cp-display');
        var pop = root.querySelector('[data-cp-pop]');
        var grid = root.querySelector('[data-cal-grid]');
        var label = root.querySelector('[data-cal-label]');
        var prev = root.querySelector('[data-cal-prev]');
        var next = root.querySelector('[data-cal-next]');

        var doctorId = null;
        var keepDate = null; // { date, time } for reschedule current
        var viewDate = new Date();
        viewDate.setDate(1);
        viewDate.setHours(0, 0, 0, 0);

        function hasAnySlot(weekday) {
            var doc = availabilityData[doctorId];
            if (!doc) return false;
            return (doc.slots || []).some(function (s) { return s.day === weekday; });
        }

        function hasOpenSlot(iso, weekday) {
            var doc = availabilityData[doctorId];
            if (!doc) return false;
            var slots = (doc.slots || []).filter(function (s) { return s.day === weekday; });
            if (!slots.length) return false;
            var booked = ((doc.booked || {})[iso] || []).slice();
            if (keepDate && iso === keepDate.date) {
                var idx = booked.indexOf(keepDate.time);
                if (idx !== -1) booked.splice(idx, 1);
            }
            var now = new Date();
            var isToday = iso === toISODate(now);
            var nowMins = now.getHours() * 60 + now.getMinutes();
            for (var i = 0; i < slots.length; i++) {
                var s = parseTime(slots[i].start), e = parseTime(slots[i].end);
                for (var m = s; m < e; m += SLOT_MINUTES) {
                    if (booked.indexOf(fmtTime(m)) !== -1) continue;
                    if (isToday && m <= nowMins) continue;
                    return true;
                }
            }
            return false;
        }

        function render() {
            grid.innerHTML = '';
            label.textContent = MONTHS[viewDate.getMonth()] + ' ' + viewDate.getFullYear();
            var first = new Date(viewDate);
            var startWd = first.getDay();
            var daysInMonth = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0).getDate();
            var today = startOfToday();
            var maxDate = new Date(today);
            maxDate.setMonth(maxDate.getMonth() + MAX_MONTHS_AHEAD);

            // Leading blanks
            for (var i = 0; i < startWd; i++) {
                var pad = document.createElement('span');
                pad.className = 'cal-day cal-day--pad';
                grid.appendChild(pad);
            }

            for (var d = 1; d <= daysInMonth; d++) {
                var date = new Date(viewDate.getFullYear(), viewDate.getMonth(), d);
                var iso = toISODate(date);
                var weekday = DAYS[date.getDay()];
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'cal-day';
                btn.textContent = String(d);
                btn.dataset.date = iso;

                var inPast = date < today;
                var tooFar = date > maxDate;
                var hasSlots = !inPast && !tooFar && doctorId && hasOpenSlot(iso, weekday);

                if (iso === toISODate(new Date())) btn.classList.add('is-today');

                if (!doctorId || inPast || tooFar) {
                    btn.disabled = true;
                    btn.classList.add('is-disabled');
                } else if (!hasSlots) {
                    btn.disabled = true;
                    btn.classList.add('is-off');
                    btn.title = hasAnySlot(weekday) ? 'No open slots' : 'Not available';
                } else {
                    btn.classList.add('is-avail');
                }
                if (input.value === iso) btn.classList.add('is-selected');
                grid.appendChild(btn);
            }
        }

        function canGo(dir) {
            var today = startOfToday();
            var maxMonth = new Date(today.getFullYear(), today.getMonth() + MAX_MONTHS_AHEAD, 1);
            var minMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            var probe = new Date(viewDate);
            probe.setMonth(probe.getMonth() + dir);
            if (probe < minMonth) return false;
            if (probe > maxMonth) return false;
            return true;
        }

        prev.addEventListener('click', function (e) {
            e.stopPropagation();
            if (!canGo(-1)) return;
            viewDate.setMonth(viewDate.getMonth() - 1);
            render();
        });
        next.addEventListener('click', function (e) {
            e.stopPropagation();
            if (!canGo(1)) return;
            viewDate.setMonth(viewDate.getMonth() + 1);
            render();
        });

        grid.addEventListener('click', function (e) {
            var day = e.target.closest('.cal-day');
            if (!day || day.disabled) return;
            input.value = day.dataset.date;
            display.textContent = fmtDisplayDate(day.dataset.date);
            trigger.classList.add('has-value');
            grid.querySelectorAll('.cal-day.is-selected').forEach(function (b) {
                b.classList.remove('is-selected');
            });
            day.classList.add('is-selected');
            closeAnyPop();
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });

        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            if (trigger.disabled) return;
            if (pop.hidden) render();
            togglePop(pop);
        });

        return {
            setDoctor: function (id) {
                doctorId = id ? String(id) : null;
                trigger.disabled = !doctorId;
                if (!doctorId) {
                    display.textContent = 'Select a doctor first';
                    trigger.classList.remove('has-value');
                } else if (!input.value) {
                    display.textContent = 'Select an available date';
                }
                render();
            },
            setKeepDate: function (date, time) {
                keepDate = date ? { date: date, time: time } : null;
            },
            reset: function () {
                input.value = '';
                display.textContent = doctorId ? 'Select an available date' : 'Select a doctor first';
                trigger.classList.remove('has-value');
                viewDate = new Date();
                viewDate.setDate(1);
                viewDate.setHours(0, 0, 0, 0);
                render();
            },
            render: render,
        };
    }

    // ---- Inline booking calendar ----
    function initInlineCalendar(rootId) {
        var root = document.getElementById(rootId);
        if (!root) return null;
        var input = root.querySelector('input[type=hidden]');
        var grid = root.querySelector('[data-cal-grid]');
        var label = root.querySelector('[data-cal-label]');
        var prev = root.querySelector('[data-cal-prev]');
        var next = root.querySelector('[data-cal-next]');
        var note = root.querySelector('[data-cal-note]');

        var doctorId = null;
        var viewDate = new Date();
        viewDate.setDate(1);
        viewDate.setHours(0, 0, 0, 0);

        function hasOpenSlot(iso, weekday) {
            var doc = availabilityData[doctorId];
            if (!doc) return false;
            var slots = (doc.slots || []).filter(function (s) { return s.day === weekday; });
            if (!slots.length) return false;
            var booked = ((doc.booked || {})[iso] || []).slice();
            var now = new Date();
            var isToday = iso === toISODate(now);
            var nowMins = now.getHours() * 60 + now.getMinutes();
            for (var i = 0; i < slots.length; i++) {
                var s = parseTime(slots[i].start), e = parseTime(slots[i].end);
                for (var m = s; m < e; m += SLOT_MINUTES) {
                    if (booked.indexOf(fmtTime(m)) !== -1) continue;
                    if (isToday && m <= nowMins) continue;
                    return true;
                }
            }
            return false;
        }

        function canGo(dir) {
            var today = startOfToday();
            var maxMonth = new Date(today.getFullYear(), today.getMonth() + MAX_MONTHS_AHEAD, 1);
            var minMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            var probe = new Date(viewDate);
            probe.setMonth(probe.getMonth() + dir);
            if (probe < minMonth) return false;
            if (probe > maxMonth) return false;
            return true;
        }

        function render() {
            grid.innerHTML = '';
            label.textContent = MONTHS[viewDate.getMonth()] + ' ' + viewDate.getFullYear();

            if (note) note.hidden = !!doctorId;
            prev.disabled = !doctorId || !canGo(-1);
            next.disabled = !doctorId || !canGo(1);

            var first = new Date(viewDate);
            var startWd = first.getDay();
            var daysInMonth = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0).getDate();
            var today = startOfToday();
            var maxDate = new Date(today);
            maxDate.setMonth(maxDate.getMonth() + MAX_MONTHS_AHEAD);

            for (var i = 0; i < startWd; i++) {
                var pad = document.createElement('span');
                pad.className = 'cal-day cal-day--pad';
                grid.appendChild(pad);
            }

            for (var d = 1; d <= daysInMonth; d++) {
                var date = new Date(viewDate.getFullYear(), viewDate.getMonth(), d);
                var iso = toISODate(date);
                var weekday = DAYS[date.getDay()];
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'cal-day';
                btn.textContent = String(d);
                btn.dataset.date = iso;

                var inPast = date < today;
                var tooFar = date > maxDate;
                var hasSlots = !inPast && !tooFar && doctorId && hasOpenSlot(iso, weekday);

                if (iso === toISODate(new Date())) btn.classList.add('is-today');

                if (!doctorId || inPast || tooFar) {
                    btn.disabled = true;
                    btn.classList.add('is-disabled');
                } else if (!hasSlots) {
                    btn.disabled = true;
                    btn.classList.add('is-off');
                    btn.title = 'Unavailable';
                } else {
                    btn.classList.add('is-avail');
                }
                if (input.value === iso) btn.classList.add('is-selected');
                grid.appendChild(btn);
            }
        }

        prev.addEventListener('click', function (e) {
            e.stopPropagation();
            if (prev.disabled) return;
            viewDate.setMonth(viewDate.getMonth() - 1);
            render();
        });
        next.addEventListener('click', function (e) {
            e.stopPropagation();
            if (next.disabled) return;
            viewDate.setMonth(viewDate.getMonth() + 1);
            render();
        });

        grid.addEventListener('click', function (e) {
            var day = e.target.closest('.cal-day');
            if (!day || day.disabled) return;
            input.value = day.dataset.date;
            grid.querySelectorAll('.cal-day.is-selected').forEach(function (b) {
                b.classList.remove('is-selected');
            });
            day.classList.add('is-selected');
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });

        render();

        return {
            setDoctor: function (id) {
                doctorId = id ? String(id) : null;
                render();
            },
            reset: function () {
                input.value = '';
                viewDate = new Date();
                viewDate.setDate(1);
                viewDate.setHours(0, 0, 0, 0);
                render();
            },
            render: render,
        };
    }

    // ---- Time slot grid ----
    function renderSlotGrid(opts) {
        var grid = opts.grid;
        var hidden = opts.hiddenInput;
        var doctorId = opts.doctorId;
        var dateStr = opts.dateStr;

        hidden.value = '';
        grid.innerHTML = '';

        var fallbackEmpty = grid.getAttribute('data-empty-message') || 'Select a doctor and date first.';
        var emptyDoctor = grid.getAttribute('data-empty-doctor') || fallbackEmpty;
        var emptyDate = grid.getAttribute('data-empty-date') || fallbackEmpty;

        if (!doctorId || !availabilityData[doctorId]) {
            grid.innerHTML = '<div class="time-slot-empty">' + emptyDoctor + '</div>';
            return;
        }
        if (!dateStr) {
            grid.innerHTML = '<div class="time-slot-empty">' + emptyDate + '</div>';
            return;
        }

        var doc = availabilityData[doctorId];
        var dayName = DAYS[new Date(dateStr + 'T00:00:00').getDay()];
        var slots = (doc.slots || []).filter(function (s) { return s.day === dayName; });

        if (slots.length === 0) {
            grid.innerHTML = '<div class="time-slot-empty time-slot-empty--warn">' +
                'Doctor is not available on ' + dayName + '.' + '</div>';
            return;
        }

        var booked = ((doc.booked || {})[dateStr] || []).slice();
        if (opts.keepCurrentTime && dateStr === opts.currentDate) {
            var idx = booked.indexOf(opts.currentTime);
            if (idx !== -1) booked.splice(idx, 1);
        }

        var now = new Date();
        var today = toISODate(now);
        var nowMins = now.getHours() * 60 + now.getMinutes();
        var isToday = (dateStr === today);

        var wrap = document.createElement('div');
        wrap.className = 'time-slot-wrap';
        slots.sort(function (a, b) { return parseTime(a.start) - parseTime(b.start); });

        var totalShown = 0;
        slots.forEach(function (slot) {
            var startM = parseTime(slot.start);
            var endM = parseTime(slot.end);

            var head = document.createElement('div');
            head.className = 'time-slot-range';
            head.textContent = fmtDisplayTime(slot.start) + ' – ' + fmtDisplayTime(slot.end);
            wrap.appendChild(head);

            var row = document.createElement('div');
            row.className = 'time-slot-row';
            for (var m = startM; m < endM; m += SLOT_MINUTES) {
                var value = fmtTime(m);
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'time-slot';
                btn.dataset.value = value;
                btn.textContent = fmtDisplayTime(value);
                if (booked.indexOf(value) !== -1) {
                    btn.classList.add('is-booked');
                    btn.disabled = true;
                    btn.title = 'Already booked';
                } else if (isToday && m <= nowMins) {
                    btn.classList.add('is-past');
                    btn.disabled = true;
                    btn.title = 'Time has passed';
                }
                row.appendChild(btn);
                totalShown++;
            }
            wrap.appendChild(row);
        });

        if (totalShown === 0) {
            grid.innerHTML = '<div class="time-slot-empty time-slot-empty--warn">' +
                'No open times left on this day.' + '</div>';
            return;
        }
        grid.appendChild(wrap);

        var legend = document.createElement('div');
        legend.className = 'time-slot-legend';
        legend.innerHTML =
            '<span class="legend-dot legend-available"></span>Available' +
            '<span class="legend-dot legend-booked"></span>Booked';
        grid.appendChild(legend);
    }

    function wireSlotGrid(grid, hidden) {
        grid.addEventListener('click', function (e) {
            var btn = e.target.closest('.time-slot');
            if (!btn || btn.disabled) return;
            grid.querySelectorAll('.time-slot.is-selected').forEach(function (b) {
                b.classList.remove('is-selected');
            });
            btn.classList.add('is-selected');
            hidden.value = btn.dataset.value;
        });
    }

    function flashHint(el, message) {
        var existing = el.parentNode.querySelector('.inline-hint');
        if (existing) existing.remove();
        var hint = document.createElement('div');
        hint.className = 'inline-hint';
        hint.textContent = message;
        el.parentNode.appendChild(hint);
        setTimeout(function () { hint.remove(); }, 3500);
    }

    // ---- Booking form wiring ----
    var doctorInput = document.getElementById('doctor-input');
    var dateInput = document.getElementById('date-input');
    var timeInput = document.getElementById('time-input');
    var slotGrid = document.getElementById('time-slot-grid');
    var bookingForm = document.getElementById('booking-form');

    var bookingCalendar = initInlineCalendar('booking-calendar');
    initDoctorPicker('doctor-picker', function (doctorId) {
        bookingCalendar.setDoctor(doctorId);
        bookingCalendar.reset();
        renderSlotGrid({
            grid: slotGrid, hiddenInput: timeInput,
            doctorId: doctorInput.value, dateStr: dateInput.value,
        });
    });

    wireSlotGrid(slotGrid, timeInput);

    dateInput.addEventListener('change', function () {
        renderSlotGrid({
            grid: slotGrid, hiddenInput: timeInput,
            doctorId: doctorInput.value, dateStr: dateInput.value,
        });
    });

    bookingForm.addEventListener('submit', function (e) {
        if (!doctorInput.value) {
            e.preventDefault();
            flashHint(document.getElementById('doctor-picker'), 'Please choose a doctor.');
            return;
        }
        if (!dateInput.value) {
            e.preventDefault();
            flashHint(document.getElementById('booking-calendar'), 'Please pick a date.');
            return;
        }
        if (!timeInput.value) {
            e.preventDefault();
            flashHint(slotGrid, 'Please pick an available time slot.');
            return;
        }
    });

    // Reason counter
    var reasonInput = document.getElementById('reason-input');
    var reasonCount = document.getElementById('reason-count');
    if (reasonInput && reasonCount) {
        reasonInput.addEventListener('input', function () {
            reasonCount.textContent = reasonInput.value.length;
        });
    }

    // ---- Reschedule modal ----
    var rescheduleModal = document.getElementById('reschedule-modal');
    var rescheduleForm = document.getElementById('reschedule-form');
    var rescheduleId = document.getElementById('reschedule-id');
    var rescheduleDoctor = document.getElementById('reschedule-doctor-id');
    var rescheduleCurrentDate = document.getElementById('reschedule-current-date');
    var rescheduleCurrentTime = document.getElementById('reschedule-current-time');
    var rescheduleDate = document.getElementById('reschedule-date');
    var rescheduleTimeInput = document.getElementById('reschedule-time-input');
    var rescheduleGrid = document.getElementById('reschedule-slot-grid');
    var rescheduleMeta = document.getElementById('reschedule-meta');

    var reschedDatePicker = initDatePicker('reschedule-date-picker');
    wireSlotGrid(rescheduleGrid, rescheduleTimeInput);

    rescheduleDate.addEventListener('change', function () {
        renderSlotGrid({
            grid: rescheduleGrid,
            hiddenInput: rescheduleTimeInput,
            doctorId: rescheduleDoctor.value,
            dateStr: rescheduleDate.value,
            keepCurrentTime: true,
            currentDate: rescheduleCurrentDate.value,
            currentTime: rescheduleCurrentTime.value,
        });
    });

    rescheduleForm.addEventListener('submit', function (e) {
        if (!rescheduleDate.value) {
            e.preventDefault();
            flashHint(document.getElementById('reschedule-date-picker'),
                'Please pick a new date.');
            return;
        }
        if (!rescheduleTimeInput.value) {
            e.preventDefault();
            flashHint(rescheduleGrid, 'Please pick an available time slot.');
            return;
        }
    });

    // ---- Cancel modal & global click routing ----
    var cancelModal = document.getElementById('cancel-modal');
    var cancelIdInput = document.getElementById('cancel-id');
    var cancelBody = document.getElementById('cancel-body');

    document.addEventListener('click', function (e) {
        var rescheduleBtn = e.target.closest('[data-action="reschedule"]');
        if (rescheduleBtn) {
            rescheduleId.value = rescheduleBtn.dataset.appointmentId;
            rescheduleDoctor.value = rescheduleBtn.dataset.doctorId;
            rescheduleCurrentDate.value = rescheduleBtn.dataset.currentDate || '';
            rescheduleCurrentTime.value = rescheduleBtn.dataset.currentTime || '';
            rescheduleMeta.textContent =
                'Currently: ' + fmtDisplayDate(rescheduleBtn.dataset.currentDate) +
                ' at ' + fmtDisplayTime(rescheduleBtn.dataset.currentTime) +
                ' with ' + (rescheduleBtn.dataset.doctorName || '');
            rescheduleTimeInput.value = '';
            rescheduleGrid.innerHTML =
                '<div class="time-slot-empty">Select a date to see available times.</div>';
            reschedDatePicker.setDoctor(rescheduleDoctor.value);
            reschedDatePicker.setKeepDate(
                rescheduleCurrentDate.value, rescheduleCurrentTime.value,
            );
            reschedDatePicker.reset();
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
