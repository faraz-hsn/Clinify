\c clinic_management;

-- =====================================================
-- USERS
-- All accounts use the password 'password'
-- Staff (doctors/admins) use the @clinify.com domain.
-- =====================================================
INSERT INTO "USER" (first_name, last_name, email, phone, password_hash, role) VALUES
-- Patients (IDs 1-6)
('Alex',     'Johnson',   'alex.johnson@email.com',    '4031111111', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'patient'),
('Sarah',    'Lee',       'sarah.lee@email.com',       '4032222222', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'patient'),
('Michael',  'Brown',     'michael.brown@email.com',   '4033333333', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'patient'),
('Emma',     'Davis',     'emma.davis@email.com',      '4037777777', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'patient'),
('Liam',     'Martinez',  'liam.martinez@email.com',   '4038888888', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'patient'),
('Olivia',   'Chen',      'olivia.chen@email.com',     '4039999999', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'patient'),
-- Doctors (IDs 7-10)
('Rose',     'Smith',     'rose.smith@clinify.com',    '4034444444', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'doctor'),
('James',    'Wilson',    'james.wilson@clinify.com',  '4035555555', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'doctor'),
('Priya',    'Patel',     'priya.patel@clinify.com',   '4030101010', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'doctor'),
('Marcus',   'Thompson',  'marcus.thompson@clinify.com','4030202020', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'doctor'),
-- Admins (IDs 11-12)
('Sara',     'Admin',     'sara.admin@clinify.com',    '4036666666', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'admin'),
('David',    'Reyes',     'david.reyes@clinify.com',   '4030303030', 'pbkdf2_sha256$600000$cd7oItCoJRKmEbS3IkjeiF$loeLo0vZjx0mQ2gufUVpD2I9tFmN5ItChrgqi1kkEZ0=', 'admin');

-- =====================================================
-- ROLE-SPECIFIC TABLES
-- =====================================================
INSERT INTO patient (patient_id, date_of_birth, gender, address, emergency_contact_name, emergency_contact_phone) VALUES
(1, '1995-03-10', 'Male',   '123 Main St, Calgary',       'Mary Johnson',   '4039991111'),
(2, '1988-07-22', 'Female', '456 Oak Ave, Calgary',       'Tom Lee',        '4039992222'),
(3, '2000-11-05', 'Male',   '789 Pine Rd, Calgary',       'Lisa Brown',     '4039993333'),
(4, '1978-02-14', 'Female', '321 Birch Blvd, Calgary',    'Robert Davis',   '4039994444'),
(5, '2003-09-30', 'Male',   '654 Cedar Cres, Calgary',    'Elena Martinez', '4039995555'),
(6, '1992-12-18', 'Female', '987 Maple Way, Calgary',     'Wei Chen',       '4039996666');

INSERT INTO doctor (doctor_id, specialty, license_number) VALUES
(7,  'Family Medicine', 'LIC10001'),
(8,  'Cardiology',      'LIC10002'),
(9,  'Pediatrics',      'LIC10003'),
(10, 'Dermatology',     'LIC10004');

INSERT INTO admin (admin_id) VALUES (11), (12);

INSERT INTO medical_record (patient_id, record_number) VALUES
(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1);

-- =====================================================
-- DOCTOR AVAILABILITY
-- =====================================================
INSERT INTO availability (doctor_id, day_of_week, start_time, end_time) VALUES
-- Dr. Rose Smith (Family Medicine)
(7, 'Monday',    '09:00:00', '12:00:00'),
(7, 'Monday',    '13:00:00', '17:00:00'),
(7, 'Wednesday', '09:00:00', '17:00:00'),
(7, 'Friday',    '09:00:00', '13:00:00'),
-- Dr. James Wilson (Cardiology)
(8, 'Tuesday',   '10:00:00', '14:00:00'),
(8, 'Thursday',  '13:00:00', '17:00:00'),
(8, 'Friday',    '09:00:00', '12:00:00'),
-- Dr. Priya Patel (Pediatrics)
(9, 'Monday',    '08:00:00', '12:00:00'),
(9, 'Tuesday',   '08:00:00', '12:00:00'),
(9, 'Thursday',  '08:00:00', '12:00:00'),
-- Dr. Marcus Thompson (Dermatology)
(10, 'Wednesday', '10:00:00', '16:00:00'),
(10, 'Friday',    '13:00:00', '17:00:00');

-- =====================================================
-- MEDICATIONS
-- =====================================================
INSERT INTO medication (medication_name, description, dosage_form) VALUES
('Acetaminophen',  'Pain reliever and fever reducer',          '500mg tablet'),
('Amoxicillin',    'Antibiotic for bacterial infections',      '250mg capsule'),
('Cough Syrup',    'Relief for cough symptoms',                '50ml syrup'),
('Ibuprofen',      'Anti-inflammatory pain reliever',          '400mg tablet'),
('Lisinopril',     'ACE inhibitor for hypertension',           '10mg tablet'),
('Atorvastatin',   'Cholesterol-lowering statin',              '20mg tablet'),
('Metformin',      'Type 2 diabetes medication',               '500mg tablet'),
('Albuterol',      'Bronchodilator inhaler',                   '90mcg inhaler'),
('Cetirizine',     'Antihistamine for allergies',              '10mg tablet'),
('Hydrocortisone', 'Topical anti-inflammatory cream',          '1% cream'),
('Omeprazole',     'Proton pump inhibitor for acid reflux',    '20mg capsule'),
('Azithromycin',   'Antibiotic for respiratory infections',    '250mg tablet');

-- =====================================================
-- APPOINTMENTS
-- Dates relative to 2026-04-20 (assumed "today"):
--   Past months  → Completed / Cancelled / No-Show
--   This week    → mix
--   Upcoming     → Scheduled
-- =====================================================
INSERT INTO appointment (appointment_date, appointment_time, status, reason, patient_id, doctor_id, admin_id) VALUES
-- February (all resolved)
('2026-02-09', '09:00:00', 'Completed', 'Annual physical',                 1, 7,  11),
('2026-02-12', '10:30:00', 'Completed', 'Heart palpitations',              2, 8,  11),
('2026-02-18', '09:00:00', 'Completed', 'Childhood vaccination follow-up', 5, 9,  12),
('2026-02-25', '14:00:00', 'No-Show',   'Acne consultation',               6, 10, 11),
-- March (resolved)
('2026-03-04', '09:00:00', 'Completed', 'Flu symptoms',                    3, 7,  11),
('2026-03-11', '10:00:00', 'Completed', 'Blood pressure check',            4, 8,  12),
('2026-03-16', '11:30:00', 'Cancelled', 'Back pain',                       1, 8,  11),
('2026-03-20', '09:30:00', 'Completed', 'Severe cough',                    3, 7,  11),
('2026-03-25', '15:00:00', 'Completed', 'Eczema flare-up',                 6, 10, 12),
-- Early April (resolved)
('2026-04-06', '09:00:00', 'Completed', 'Follow-up on blood pressure',     4, 8,  11),
('2026-04-13', '13:00:00', 'Completed', 'Chronic migraine review',         2, 7,  12),
('2026-04-15', '10:00:00', 'Cancelled', 'Rash consultation',               5, 10, 11),
-- This week (mix)
('2026-04-20', '09:00:00', 'Completed', 'Routine checkup',                 1, 7,  11),
('2026-04-20', '14:00:00', 'Scheduled', 'Diabetes follow-up',              4, 7,  12),
('2026-04-21', '10:00:00', 'Scheduled', 'Chest pain',                      2, 8,  11),
('2026-04-21', '11:00:00', 'Scheduled', 'Seasonal allergies',              6, 7,  11),
('2026-04-22', '09:00:00', 'Scheduled', 'Child wellness visit',            5, 9,  12),
('2026-04-23', '13:30:00', 'Scheduled', 'Cardiac stress test review',      4, 8,  11),
('2026-04-24', '09:00:00', 'Scheduled', 'Skin cancer screening',           3, 10, 11),
-- Next week and beyond
('2026-04-27', '09:00:00', 'Scheduled', 'Annual physical',                 2, 7,  11),
('2026-04-28', '10:00:00', 'Scheduled', 'Heart murmur evaluation',         1, 8,  12),
('2026-04-29', '08:30:00', 'Scheduled', 'Pediatric follow-up',             5, 9,  11),
('2026-05-04', '09:00:00', 'Scheduled', 'Dermatitis check',                6, 10, 11),
('2026-05-07', '13:00:00', 'Scheduled', 'Post-op follow-up',               3, 7,  12);

-- =====================================================
-- VISITS
-- Each Completed appointment should have a corresponding visit
-- =====================================================
INSERT INTO visit (appointment_id, patient_id, record_number, diagnosis, vitals, visit_notes, visit_date) VALUES
(1,  1, 1, 'Healthy; continue current lifestyle',     'BP 118/76, HR 68, Temp 36.8C',  'Annual physical unremarkable. Recommended annual bloodwork next year.',                 '2026-02-09'),
(2,  2, 1, 'Benign palpitations',                     'BP 122/80, HR 88, Temp 36.9C',  'ECG normal. Reassured patient. Follow up if symptoms persist.',                         '2026-02-12'),
(3,  5, 1, 'Up-to-date on MMR booster',               'BP 100/65, HR 92, Temp 37.0C',  'Vaccination booster administered. Patient tolerated well.',                             '2026-02-18'),
(5,  3, 1, 'Viral upper respiratory infection',       'BP 120/78, HR 84, Temp 38.1C',  'Advised rest and fluids. OTC symptomatic relief.',                                      '2026-03-04'),
(6,  4, 1, 'Stage 1 hypertension',                    'BP 138/88, HR 76, Temp 36.7C',  'Start Lisinopril 10mg daily. Re-check in 4 weeks.',                                     '2026-03-11'),
(8,  3, 1, 'Acute bronchitis',                        'BP 122/80, HR 90, Temp 38.5C',  'Prescribed Amoxicillin and cough syrup. Return if worsening.',                          '2026-03-20'),
(9,  6, 1, 'Atopic dermatitis',                       'BP 115/72, HR 72, Temp 36.8C',  'Prescribed topical hydrocortisone. Moisturize twice daily.',                            '2026-03-25'),
(10, 4, 1, 'Hypertension, well-controlled',           'BP 126/82, HR 74, Temp 36.9C',  'BP improving. Continue Lisinopril. Next follow-up in 3 months.',                        '2026-04-06'),
(11, 2, 1, 'Chronic migraine, stable',                'BP 120/78, HR 70, Temp 36.8C',  'Migraine frequency reduced. Continue current management.',                              '2026-04-13'),
(13, 1, 1, 'Healthy',                                 'BP 116/74, HR 66, Temp 36.7C',  'No concerns today. Routine screening labs ordered.',                                    '2026-04-20');

-- =====================================================
-- PRESCRIPTIONS
-- =====================================================
INSERT INTO prescription (visit_id, doctor_id, issue_date) VALUES
(5,  7, '2026-03-04'),  -- Flu: Acetaminophen + Cough Syrup
(6,  8, '2026-03-11'),  -- Hypertension: Lisinopril
(8,  7, '2026-03-20'),  -- Bronchitis: Amoxicillin + Cough Syrup
(9, 10, '2026-03-25'),  -- Eczema: Hydrocortisone + Cetirizine
(10, 8, '2026-04-06');  -- Hypertension follow-up: Lisinopril refill

INSERT INTO contains (prescription_id, medication_id, frequency, duration) VALUES
-- Rx 1 (flu)
(1, 1, 'Every 6 hours as needed', '5 days'),
(1, 3, 'Twice daily',             '5 days'),
-- Rx 2 (new hypertension)
(2, 5, 'Once daily',              '30 days'),
-- Rx 3 (bronchitis)
(3, 2, 'Three times daily',       '7 days'),
(3, 3, 'Twice daily',             '7 days'),
-- Rx 4 (eczema)
(4, 10, 'Apply twice daily',      '14 days'),
(4,  9, 'Once daily',             '14 days'),
-- Rx 5 (hypertension refill)
(5, 5, 'Once daily',              '90 days');
