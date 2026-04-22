-- =====================================================
-- Clinify - Clinic Management System
-- PostgreSQL Schema
-- =====================================================

DROP DATABASE IF EXISTS clinic_management;
CREATE DATABASE clinic_management;
\c clinic_management;

-- =====================================================
-- TABLES
-- =====================================================

CREATE TABLE "USER" (
    User_ID     SERIAL PRIMARY KEY,
    First_Name  VARCHAR(50)  NOT NULL,
    Last_Name   VARCHAR(50)  NOT NULL,
    Email       VARCHAR(100) NOT NULL UNIQUE,
    Phone       VARCHAR(20),
    Password_Hash VARCHAR(255) NOT NULL,
    Is_Active   BOOLEAN      NOT NULL DEFAULT TRUE,
    Role        VARCHAR(10)  NOT NULL,
    CONSTRAINT chk_role CHECK (Role IN ('patient', 'doctor', 'admin'))
);

CREATE TABLE PATIENT (
    Patient_ID              INT PRIMARY KEY,
    Date_Of_Birth           DATE,
    Gender                  VARCHAR(20),
    Address                 VARCHAR(255),
    Emergency_Contact_Name  VARCHAR(100),
    Emergency_Contact_Phone VARCHAR(20),
    CONSTRAINT fk_patient_user
        FOREIGN KEY (Patient_ID) REFERENCES "USER"(User_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE DOCTOR (
    Doctor_ID      INT PRIMARY KEY,
    Specialty      VARCHAR(100),
    License_Number VARCHAR(50) NOT NULL UNIQUE,
    CONSTRAINT fk_doctor_user
        FOREIGN KEY (Doctor_ID) REFERENCES "USER"(User_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE ADMIN (
    Admin_ID INT PRIMARY KEY,
    CONSTRAINT fk_admin_user
        FOREIGN KEY (Admin_ID) REFERENCES "USER"(User_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE MEDICAL_RECORD (
    Patient_ID    INT NOT NULL,
    Record_Number INT NOT NULL,
    PRIMARY KEY (Patient_ID, Record_Number),
    CONSTRAINT fk_medicalrecord_patient
        FOREIGN KEY (Patient_ID) REFERENCES PATIENT(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE APPOINTMENT (
    Appointment_ID   SERIAL PRIMARY KEY,
    Appointment_Date DATE        NOT NULL,
    Appointment_Time TIME        NOT NULL,
    Status           VARCHAR(20) NOT NULL DEFAULT 'Scheduled',
    Reason           TEXT,
    Patient_ID       INT NOT NULL,
    Doctor_ID        INT NOT NULL,
    Admin_ID         INT,
    CONSTRAINT chk_appointment_status
        CHECK (Status IN ('Scheduled', 'Completed', 'Cancelled', 'No-Show')),
    CONSTRAINT fk_appointment_patient
        FOREIGN KEY (Patient_ID) REFERENCES PATIENT(Patient_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_doctor
        FOREIGN KEY (Doctor_ID) REFERENCES DOCTOR(Doctor_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_admin
        FOREIGN KEY (Admin_ID) REFERENCES ADMIN(Admin_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE VISIT (
    Appointment_ID INT NOT NULL PRIMARY KEY,
    Patient_ID     INT NOT NULL,
    Record_Number  INT NOT NULL,
    Diagnosis      TEXT,
    Vitals         TEXT,
    Visit_Notes    TEXT,
    Visit_Date     DATE NOT NULL,
    CONSTRAINT fk_visit_appointment
        FOREIGN KEY (Appointment_ID) REFERENCES APPOINTMENT(Appointment_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_visit_medicalrecord
        FOREIGN KEY (Patient_ID, Record_Number)
        REFERENCES MEDICAL_RECORD(Patient_ID, Record_Number)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE MEDICATION (
    Medication_ID   SERIAL PRIMARY KEY,
    Medication_Name VARCHAR(100) NOT NULL,
    Description     TEXT,
    Dosage_Form     VARCHAR(50)
);

CREATE TABLE PRESCRIPTION (
    Prescription_ID SERIAL PRIMARY KEY,
    Visit_ID        INT  NOT NULL UNIQUE,
    Doctor_ID       INT  NOT NULL,
    Issue_Date      DATE NOT NULL,
    CONSTRAINT fk_prescription_visit
        FOREIGN KEY (Visit_ID) REFERENCES VISIT(Appointment_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_prescription_doctor
        FOREIGN KEY (Doctor_ID) REFERENCES DOCTOR(Doctor_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE CONTAINS (
    Prescription_ID INT          NOT NULL,
    Medication_ID   INT          NOT NULL,
    Frequency       VARCHAR(100) NOT NULL,
    Duration        VARCHAR(100) NOT NULL,
    PRIMARY KEY (Prescription_ID, Medication_ID),
    CONSTRAINT fk_contains_prescription
        FOREIGN KEY (Prescription_ID) REFERENCES PRESCRIPTION(Prescription_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_contains_medication
        FOREIGN KEY (Medication_ID) REFERENCES MEDICATION(Medication_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE AVAILABILITY (
    Doctor_ID   INT         NOT NULL,
    Day_Of_Week VARCHAR(15) NOT NULL,
    Start_Time  TIME        NOT NULL,
    End_Time    TIME        NOT NULL,
    PRIMARY KEY (Doctor_ID, Day_Of_Week, Start_Time),
    CONSTRAINT chk_day_of_week
        CHECK (Day_Of_Week IN (
            'Monday','Tuesday','Wednesday',
            'Thursday','Friday','Saturday','Sunday'
        )),
    CONSTRAINT chk_time_window
        CHECK (Start_Time < End_Time),
    CONSTRAINT fk_availability_doctor
        FOREIGN KEY (Doctor_ID) REFERENCES DOCTOR(Doctor_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

CREATE OR REPLACE FUNCTION book_appointment(
    p_patient_id INT,
    p_doctor_id  INT,
    p_date       DATE,
    p_time       TIME,
    p_reason     TEXT
) RETURNS VOID AS $$
DECLARE
    v_admin_id INT;
BEGIN
    SELECT Admin_ID INTO v_admin_id FROM ADMIN ORDER BY Admin_ID LIMIT 1;

    INSERT INTO APPOINTMENT (Appointment_Date, Appointment_Time, Status, Reason, Patient_ID, Doctor_ID, Admin_ID)
    VALUES (p_date, p_time, 'Scheduled', p_reason, p_patient_id, p_doctor_id, v_admin_id);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION cancel_appointment(
    p_appointment_id INT
) RETURNS VOID AS $$
BEGIN
    UPDATE APPOINTMENT
    SET Status = 'Cancelled'
    WHERE Appointment_ID = p_appointment_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_visit(
    p_appointment_id INT,
    p_patient_id     INT,
    p_record_number  INT,
    p_diagnosis      TEXT,
    p_vitals         TEXT,
    p_notes          TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO VISIT (Appointment_ID, Patient_ID, Record_Number, Diagnosis, Vitals, Visit_Notes, Visit_Date)
    VALUES (p_appointment_id, p_patient_id, p_record_number, p_diagnosis, p_vitals, p_notes, CURRENT_DATE);

    UPDATE APPOINTMENT
    SET Status = 'Completed'
    WHERE Appointment_ID = p_appointment_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_doctor_schedule(
    p_doctor_id INT,
    p_date      DATE
) RETURNS TABLE (
    appointment_id INT,
    appointment_time TIME,
    status VARCHAR(20),
    reason TEXT,
    patient_name TEXT,
    patient_id INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT a.Appointment_ID, a.Appointment_Time, a.Status, a.Reason,
           (u.First_Name || ' ' || u.Last_Name)::TEXT AS patient_name,
           p.Patient_ID
    FROM APPOINTMENT a
    JOIN PATIENT p ON a.Patient_ID = p.Patient_ID
    JOIN "USER" u ON p.Patient_ID = u.User_ID
    WHERE a.Doctor_ID = p_doctor_id
      AND a.Appointment_Date = p_date
    ORDER BY a.Appointment_Time;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_prescription(
    p_visit_id  INT,
    p_doctor_id INT
) RETURNS INT AS $$
DECLARE
    new_id INT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM VISIT v
        JOIN APPOINTMENT a ON a.Appointment_ID = v.Appointment_ID
        WHERE v.Appointment_ID = p_visit_id
          AND a.Doctor_ID = p_doctor_id
          AND a.Status = 'Completed'
    ) THEN
        RAISE EXCEPTION 'Only the assigned doctor can prescribe for a completed visit.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM PRESCRIPTION
        WHERE Visit_ID = p_visit_id
    ) THEN
        RAISE EXCEPTION 'A prescription already exists for this visit.';
    END IF;

    INSERT INTO PRESCRIPTION (Visit_ID, Doctor_ID, Issue_Date)
    VALUES (p_visit_id, p_doctor_id, CURRENT_DATE)
    RETURNING Prescription_ID INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;
