\c clinic_management;

INSERT INTO "USER" (first_name, last_name, email, phone, password_hash, role) VALUES
('Alex',     'Johnson',  'alex.johnson@email.com',  '4031111111', 'pbkdf2_sha256$1200000$4JplPP9B5xOdH3PEUeO0yQ$BHE6jQg8QyXT/sZK8rQc215ERPX1dew713j5jyLePCg=', 'patient'),
('Sarah',    'Lee',      'sarah.lee@email.com',     '4032222222', 'pbkdf2_sha256$1200000$4JplPP9B5xOdH3PEUeO0yQ$BHE6jQg8QyXT/sZK8rQc215ERPX1dew713j5jyLePCg=', 'patient'),
('Michael',  'Brown',    'michael.brown@email.com', '4033333333', 'pbkdf2_sha256$1200000$4JplPP9B5xOdH3PEUeO0yQ$BHE6jQg8QyXT/sZK8rQc215ERPX1dew713j5jyLePCg=', 'patient'),
('Rose',     'Smith',    'rose.smith@email.com',    '4034444444', 'pbkdf2_sha256$1200000$4JplPP9B5xOdH3PEUeO0yQ$BHE6jQg8QyXT/sZK8rQc215ERPX1dew713j5jyLePCg=', 'doctor'),
('James',    'Wilson',   'james.wilson@email.com',  '4035555555', 'pbkdf2_sha256$1200000$4JplPP9B5xOdH3PEUeO0yQ$BHE6jQg8QyXT/sZK8rQc215ERPX1dew713j5jyLePCg=', 'doctor'),
('Sara',     'Admin',    'sara.admin@email.com',    '4036666666', 'pbkdf2_sha256$1200000$4JplPP9B5xOdH3PEUeO0yQ$BHE6jQg8QyXT/sZK8rQc215ERPX1dew713j5jyLePCg=', 'admin');



INSERT INTO patient (patient_id, date_of_birth, gender, address, emergency_contact_name, emergency_contact_phone) VALUES
(1, '1995-03-10', 'Male',   '123 Main St, Calgary',   'Mary Johnson', '4039991111'),
(2, '1988-07-22', 'Female', '456 Oak Ave, Calgary',   'Tom Lee',      '4039992222'),
(3, '2000-11-05', 'Male',   '789 Pine Rd, Calgary',   'Lisa Brown',   '4039993333');

INSERT INTO doctor (doctor_id, specialty, license_number) VALUES
(4, 'Family Medicine', 'LIC10001'),
(5, 'Cardiology',      'LIC10002');

INSERT INTO admin (admin_id) VALUES (6);

INSERT INTO medical_record (patient_id, record_number) VALUES
(1, 1), (2, 1), (3, 1);

INSERT INTO availability (doctor_id, availability_date, start_time, end_time) VALUES
(4, '2026-04-14', '09:00:00', '12:00:00'),
(4, '2026-04-16', '13:00:00', '17:00:00'),
(4, '2026-04-18', '09:00:00', '12:00:00'),
(4, '2026-04-21', '09:00:00', '12:00:00'),
(4, '2026-04-23', '13:00:00', '17:00:00'),
(4, '2026-04-25', '09:00:00', '12:00:00'),
(5, '2026-04-15', '10:00:00', '14:00:00'),
(5, '2026-04-17', '13:00:00', '17:00:00'),
(5, '2026-04-22', '10:00:00', '14:00:00'),
(5, '2026-04-24', '13:00:00', '17:00:00');

INSERT INTO appointment (appointment_date, appointment_time, status, reason, patient_id, doctor_id, admin_id) VALUES
('2026-04-14', '09:00:00', 'Scheduled',  'Routine checkup',    1, 4, 6),
('2026-04-14', '10:00:00', 'Scheduled',  'Chest pain',         2, 5, 6),
('2026-03-20', '09:30:00', 'Completed',  'Flu symptoms',       3, 4, 6),
('2026-03-15', '11:00:00', 'Cancelled',  'Back pain',          1, 5, 6);

INSERT INTO visit (appointment_id, patient_id, record_number, diagnosis, vitals, visit_notes, visit_date) VALUES
(3, 3, 1, 'Influenza', 'BP 118/76, Temp 38.5C', 'Prescribed rest and fluids.', '2026-03-20');

INSERT INTO medication (medication_name, description, dosage_form) VALUES
('Acetaminophen', 'Pain reliever and fever reducer', '500mg tablet'),
('Amoxicillin',   'Antibiotic for bacterial infections', '250mg capsule'),
('Cough Syrup',   'Relief for cough symptoms', '50ml syrup'),
('Ibuprofen',     'Anti-inflammatory pain reliever', '400mg tablet');

INSERT INTO prescription (visit_id, doctor_id, issue_date) VALUES
(3, 4, '2026-03-20');

INSERT INTO contains (prescription_id, medication_id, frequency, duration) VALUES
(1, 1, 'Twice daily', '5 days'),
(1, 3, 'Once daily',  '3 days');