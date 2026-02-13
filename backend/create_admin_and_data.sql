-- Create superuser (password: admin123)
-- Password hash for 'admin123' using Django's PBKDF2
INSERT INTO auth_user (username, email, password, is_superuser, is_staff, is_active, date_joined, first_name, last_name)
VALUES ('admin', 'toby@nbnesigns.com', 'pbkdf2_sha256$870000$YourSaltHere$hash', true, true, true, NOW(), '', '');

-- Create services
INSERT INTO bookings_service (name, description, duration_minutes, price, active, created_at, updated_at)
VALUES 
('Haircut', 'Professional haircut and styling', 60, 45.00, true, NOW(), NOW()),
('Color', 'Full color treatment', 90, 85.00, true, NOW(), NOW()),
('Highlights', 'Partial highlights', 120, 95.00, true, NOW(), NOW()),
('Styling', 'Special occasion styling', 45, 35.00, true, NOW(), NOW());

-- Create staff
INSERT INTO bookings_staff (name, email, phone, active, created_at, updated_at)
VALUES 
('Sarah Johnson', 'sarah@houseofhair.co.uk', '01665 123456', true, NOW(), NOW()),
('Mike Chen', 'mike@houseofhair.co.uk', '01665 123457', true, NOW(), NOW()),
('Dr. Emily Smith', 'emily@houseofhair.co.uk', '01665 123458', true, NOW(), NOW());

-- Link services to staff (all staff can do all services)
INSERT INTO bookings_staff_services (staff_id, service_id)
SELECT s.id, sv.id 
FROM bookings_staff s
CROSS JOIN bookings_service sv;
