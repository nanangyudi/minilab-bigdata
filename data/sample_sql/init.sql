CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    city VARCHAR(100),
    age INT,
    signup_date DATE
);

INSERT INTO customers (customer_id, customer_name, city, age, signup_date) VALUES
(1, 'Andi', 'Malang', 21, '2024-01-10'),
(2, 'Budi', 'Blitar', 22, '2024-02-11'),
(3, 'Citra', 'Surabaya', 20, '2024-03-12'),
(4, 'Dewi', 'Kediri', 23, '2024-04-13')
ON CONFLICT (customer_id) DO NOTHING;
