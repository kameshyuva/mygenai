-- Enable foreign key support (required in SQLite)
PRAGMA foreign_keys = ON;

-- 1. Create Departments Table
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL UNIQUE
);

-- 2. Create Roles Table
CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments (department_id) ON DELETE SET NULL
);

-- 3. Create Grades Table
CREATE TABLE grades (
    grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade_level TEXT NOT NULL UNIQUE,
    description TEXT
);

-- 4. Create Employees Table
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role_id INTEGER,
    grade_id INTEGER,
    hire_date DATE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE SET NULL,
    FOREIGN KEY (grade_id) REFERENCES grades (grade_id) ON DELETE SET NULL
);

-- ==========================================
-- INSERT SAMPLE DATA
-- ==========================================

-- Insert Departments
INSERT INTO departments (department_name) VALUES 
('Engineering'),
('Human Resources'),
('Sales');

-- Insert Roles
INSERT INTO roles (title, department_id) VALUES 
('Software Engineer', 1),
('Senior Software Engineer', 1),
('Engineering Manager', 1),
('HR Specialist', 2),
('Account Executive', 3);

-- Insert Grades
INSERT INTO grades (grade_level, description) VALUES 
('L1', 'Entry Level'),
('L2', 'Mid Level'),
('L3', 'Senior Level'),
('L4', 'Management');

-- Insert Employees
INSERT INTO employees (first_name, last_name, role_id, grade_id, hire_date) VALUES 
('Alice', 'Smith', 1, 1, '2024-01-15'),      -- Software Engineer, L1
('Bob', 'Jones', 2, 3, '2021-06-01'),        -- Senior Software Engineer, L3
('Charlie', 'Brown', 3, 4, '2019-03-10'),    -- Engineering Manager, L4
('Diana', 'Prince', 4, 2, '2023-11-20'),     -- HR Specialist, L2
('Evan', 'Wright', 5, 2, '2022-08-05');      -- Account Executive, L2
