-- ============================================================
-- Minilab Big Data — Inisialisasi Database
-- Tabel: customers, products, orders
-- Dirancang untuk mendukung teknik data mining di Tahap 2:
--   - Clustering    : segmentasi pelanggan
--   - Klasifikasi   : prediksi pelanggan aktif/tidak
--   - Asosiasi      : produk yang sering dibeli bersamaan
-- ============================================================

-- ------------------------------------------------------------
-- Tabel customers
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id   INT PRIMARY KEY,
    customer_name VARCHAR(100),
    city          VARCHAR(100),
    age           INT,
    signup_date   DATE
);

INSERT INTO customers (customer_id, customer_name, city, age, signup_date) VALUES
(1,  'Andi',   'Malang',     21, '2024-01-10'),
(2,  'Budi',   'Blitar',     22, '2024-02-11'),
(3,  'Citra',  'Surabaya',   20, '2024-03-12'),
(4,  'Dewi',   'Kediri',     23, '2024-04-13'),
(5,  'Eko',    'Jakarta',    25, '2024-01-15'),
(6,  'Fani',   'Bandung',    19, '2024-02-20'),
(7,  'Gilang', 'Yogyakarta', 28, '2024-01-25'),
(8,  'Hana',   'Semarang',   24, '2024-03-05'),
(9,  'Irfan',  'Medan',      30, '2024-02-08'),
(10, 'Julia',  'Makassar',   22, '2024-04-01'),
(11, 'Krisna', 'Surabaya',   27, '2024-01-20'),
(12, 'Linda',  'Jakarta',    31, '2024-03-15'),
(13, 'Mario',  'Bandung',    26, '2024-02-28'),
(14, 'Nina',   'Malang',     29, '2024-01-30'),
(15, 'Oscar',  'Yogyakarta', 23, '2024-04-10'),
(16, 'Putri',  'Semarang',   21, '2024-03-22'),
(17, 'Qadir',  'Medan',      35, '2023-12-15'),
(18, 'Rina',   'Makassar',   28, '2024-01-05'),
(19, 'Sandi',  'Jakarta',    32, '2023-11-20'),
(20, 'Tina',   'Surabaya',   24, '2024-02-14'),
(21, 'Umar',   'Bandung',    26, '2024-03-10'),
(22, 'Vina',   'Malang',     20, '2024-04-18'),
(23, 'Wahyu',  'Yogyakarta', 29, '2023-12-01'),
(24, 'Xena',   'Semarang',   27, '2024-01-12'),
(25, 'Yudi',   'Medan',      33, '2023-10-25'),
(26, 'Zara',   'Makassar',   22, '2024-02-05'),
(27, 'Agus',   'Jakarta',    38, '2023-09-15'),
(28, 'Bela',   'Surabaya',   25, '2024-03-28'),
(29, 'Cepi',   'Bandung',    21, '2024-04-22'),
(30, 'Dian',   'Malang',     34, '2023-11-10')
ON CONFLICT (customer_id) DO NOTHING;

-- ------------------------------------------------------------
-- Tabel products
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id   INT PRIMARY KEY,
    product_name VARCHAR(150),
    category     VARCHAR(100),
    price        INT,
    stock        INT
);

INSERT INTO products (product_id, product_name, category, price, stock) VALUES
(1,  'Laptop ASUS VivoBook',        'Elektronik',       8500000, 15),
(2,  'Smartphone Samsung A54',       'Elektronik',       4200000, 30),
(3,  'Headphone Sony WH-1000XM5',   'Elektronik',       3800000, 20),
(4,  'Kaos Polos Cotton',            'Pakaian',            75000,100),
(5,  'Jaket Hoodie Fleece',          'Pakaian',           250000, 50),
(6,  'Celana Jeans Slim',            'Pakaian',           180000, 75),
(7,  'Kopi Arabika 200g',            'Makanan',            45000,200),
(8,  'Teh Hijau Premium',            'Makanan',            35000,150),
(9,  'Mie Instan Goreng',            'Makanan',             3500,500),
(10, 'Panci Presto 5L',              'Peralatan Rumah',   320000, 25),
(11, 'Blender Philips 600W',         'Peralatan Rumah',   450000, 20),
(12, 'Sepatu Lari Nike',             'Olahraga',          850000, 40),
(13, 'Bola Futsal Mikasa',           'Olahraga',          185000, 35),
(14, 'Mouse Wireless Logitech',      'Elektronik',        380000, 60),
(15, 'Keyboard Mechanical Rexus',    'Elektronik',        620000, 30)
ON CONFLICT (product_id) DO NOTHING;

-- ------------------------------------------------------------
-- Tabel orders
-- Pola yang disengaja untuk latihan association rules:
--   - Laptop  → Mouse + Keyboard (klaster elektronik kerja)
--   - Kopi    → Teh              (klaster minuman)
--   - Jaket   → Celana           (klaster fashion)
--   - Sepatu  → Bola             (klaster olahraga)
--   - Panci   → Blender          (klaster dapur)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id    INT PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    product_id  INT REFERENCES products(product_id),
    quantity    INT,
    order_date  DATE
);

INSERT INTO orders (order_id, customer_id, product_id, quantity, order_date) VALUES
-- Klaster Elektronik Kerja (Laptop + Mouse + Keyboard)
(1,  1,  1,  1, '2024-01-15'),
(2,  1,  14, 1, '2024-01-15'),
(3,  1,  15, 1, '2024-01-15'),
(4,  3,  1,  1, '2024-03-15'),
(5,  3,  14, 1, '2024-03-15'),
(6,  5,  1,  1, '2024-01-20'),
(7,  5,  15, 1, '2024-01-20'),
(8,  17, 1,  1, '2023-12-18'),
(9,  17, 14, 1, '2023-12-18'),
(10, 17, 15, 1, '2023-12-18'),
-- Klaster Elektronik Hiburan (Smartphone + Headphone)
(11, 2,  2,  1, '2024-02-12'),
(12, 2,  3,  1, '2024-02-12'),
(13, 4,  2,  1, '2024-04-15'),
(14, 4,  3,  1, '2024-04-16'),
(15, 19, 2,  1, '2023-11-22'),
(16, 19, 3,  1, '2023-11-23'),
(17, 5,  3,  1, '2024-02-01'),
(18, 10, 2,  1, '2024-04-03'),
-- Klaster Minuman (Kopi + Teh)
(19, 11, 7,  2, '2024-01-22'),
(20, 11, 8,  1, '2024-01-22'),
(21, 12, 7,  3, '2024-03-17'),
(22, 13, 7,  2, '2024-03-01'),
(23, 13, 8,  2, '2024-03-01'),
(24, 14, 8,  1, '2024-02-01'),
(25, 16, 7,  2, '2024-03-24'),
(26, 20, 8,  2, '2024-02-16'),
(27, 28, 7,  2, '2024-04-03'),
(28, 30, 7,  1, '2023-11-12'),
-- Klaster Makanan (Mie + Teh / Kopi)
(29, 12, 9,  5, '2024-03-17'),
(30, 14, 9,  3, '2024-02-01'),
(31, 20, 9,  5, '2024-02-16'),
(32, 15, 7,  1, '2024-04-12'),
-- Klaster Fashion (Jaket + Celana)
(33, 21, 4,  2, '2024-03-12'),
(34, 21, 5,  1, '2024-03-12'),
(35, 22, 4,  3, '2024-04-20'),
(36, 22, 6,  1, '2024-04-20'),
(37, 23, 5,  1, '2023-12-05'),
(38, 23, 6,  2, '2023-12-05'),
(39, 24, 4,  2, '2024-01-15'),
(40, 24, 5,  1, '2024-01-16'),
(41, 18, 5,  1, '2024-01-07'),
(42, 18, 6,  1, '2024-01-07'),
(43, 10, 4,  1, '2024-04-03'),
(44, 16, 4,  1, '2024-03-24'),
(45, 29, 4,  2, '2024-04-25'),
-- Klaster Olahraga (Sepatu + Bola)
(46, 25, 12, 1, '2023-10-30'),
(47, 25, 13, 1, '2023-10-30'),
(48, 26, 12, 1, '2024-02-07'),
(49, 27, 13, 2, '2023-09-20'),
(50, 27, 12, 1, '2023-09-20'),
(51, 28, 12, 1, '2024-04-01'),
(52, 15, 12, 1, '2024-04-14'),
-- Klaster Dapur (Panci + Blender)
(53, 6,  10, 1, '2024-02-22'),
(54, 6,  11, 1, '2024-02-22'),
(55, 7,  10, 1, '2024-01-28'),
(56, 8,  11, 1, '2024-03-07'),
(57, 9,  10, 1, '2024-02-10'),
(58, 9,  11, 1, '2024-02-10'),
(59, 30, 10, 1, '2023-12-10'),
-- Tambahan variasi
(60, 1,  7,  1, '2024-03-01'),
(61, 11, 4,  2, '2024-02-25'),
(62, 26, 8,  1, '2024-02-08'),
(63, 27, 7,  1, '2023-10-01')
ON CONFLICT (order_id) DO NOTHING;
