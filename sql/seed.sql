PRAGMA foreign_keys = ON;

INSERT INTO customer (customer_id, name, email, phone, joined_at, city, membership_level) VALUES
(1, '김민준', 'minjun.kim@example.com', '010-1000-0001', '2025-01-05', '서울 강남구', 'gold'),
(2, '이서연', 'seoyeon.lee@example.com', '010-1000-0002', '2025-01-14', '서울 마포구', 'silver'),
(3, '박지호', 'jiho.park@example.com', '010-1000-0003', '2025-02-02', '경기 성남시', 'regular'),
(4, '최하윤', 'hayoon.choi@example.com', '010-1000-0004', '2025-02-18', '서울 송파구', 'gold'),
(5, '정도윤', 'doyoon.jung@example.com', '010-1000-0005', '2025-03-03', '인천 연수구', 'regular'),
(6, '강지민', 'jimin.kang@example.com', '010-1000-0006', '2025-03-11', '서울 강남구', 'silver'),
(7, '윤서준', 'seojun.yoon@example.com', '010-1000-0007', '2025-03-25', '경기 고양시', 'regular'),
(8, '장수아', 'sua.jang@example.com', '010-1000-0008', '2025-04-07', '서울 용산구', 'gold'),
(9, '임현우', 'hyunwoo.lim@example.com', '010-1000-0009', '2025-04-16', '경기 수원시', 'silver'),
(10, '한예린', 'yerin.han@example.com', '010-1000-0010', '2025-05-01', '서울 마포구', 'regular');

INSERT INTO staff (staff_id, name, email, role, hired_at) VALUES
(1, '오지훈', 'jihun.oh@cafe.example', 'manager', '2024-05-01'),
(2, '신나연', 'nayeon.shin@cafe.example', 'barista', '2024-06-15'),
(3, '백현서', 'hyunseo.baek@cafe.example', 'barista', '2024-07-20'),
(4, '문태오', 'taeo.moon@cafe.example', 'cashier', '2024-08-03'),
(5, '서유진', 'yujin.seo@cafe.example', 'cashier', '2024-09-09'),
(6, '권도현', 'dohyun.kwon@cafe.example', 'barista', '2024-10-12'),
(7, '남소율', 'soyul.nam@cafe.example', 'barista', '2024-11-04'),
(8, '유건우', 'geonwoo.yu@cafe.example', 'cashier', '2024-12-01'),
(9, '홍아린', 'arin.hong@cafe.example', 'barista', '2025-01-10'),
(10, '조민재', 'minjae.cho@cafe.example', 'cashier', '2025-02-14');

INSERT INTO menu_category (category_id, name, display_order) VALUES
(1, '커피', 1),
(2, '라떼', 2),
(3, '티', 3),
(4, '에이드', 4),
(5, '스무디', 5),
(6, '디저트', 6),
(7, '샌드위치', 7),
(8, '브런치', 8),
(9, '시즌 메뉴', 9),
(10, '병음료', 10);

INSERT INTO menu_item (menu_item_id, category_id, name, price, is_available, created_at) VALUES
(1, 1, '아메리카노', 4500, 1, '2025-01-01'),
(2, 1, '콜드브루', 5200, 1, '2025-01-01'),
(3, 2, '카페라떼', 5500, 1, '2025-01-01'),
(4, 2, '바닐라라떼', 6100, 1, '2025-01-01'),
(5, 3, '얼그레이 티', 5000, 1, '2025-01-03'),
(6, 3, '유자차', 5300, 1, '2025-01-03'),
(7, 4, '레몬 에이드', 6200, 1, '2025-01-05'),
(8, 5, '딸기 스무디', 6800, 1, '2025-01-05'),
(9, 6, '치즈 케이크', 7200, 1, '2025-01-07'),
(10, 6, '초코 브라우니', 4800, 1, '2025-01-07'),
(11, 7, '햄치즈 샌드위치', 7900, 1, '2025-01-10'),
(12, 8, '아보카도 토스트', 9800, 1, '2025-01-10');

INSERT INTO cafe_order (order_id, customer_id, staff_id, ordered_at, order_type, status) VALUES
(101, 1, 2, '2026-05-01 08:15:00', 'takeout', 'paid'),
(102, 2, 4, '2026-05-01 09:05:00', 'dine_in', 'paid'),
(103, 3, 3, '2026-05-02 12:20:00', 'delivery', 'paid'),
(104, 4, 5, '2026-05-02 13:10:00', 'takeout', 'paid'),
(105, 5, 6, '2026-05-03 10:40:00', 'dine_in', 'cancelled'),
(106, 6, 7, '2026-05-03 18:25:00', 'delivery', 'paid'),
(107, 7, 8, '2026-05-04 08:55:00', 'takeout', 'paid'),
(108, 8, 9, '2026-05-04 14:30:00', 'dine_in', 'paid'),
(109, 9, 10, '2026-05-05 11:45:00', 'delivery', 'paid'),
(110, 1, 2, '2026-05-05 15:10:00', 'takeout', 'pending'),
(111, 2, 3, '2026-05-06 09:20:00', 'dine_in', 'paid'),
(112, 10, 5, '2026-05-06 19:05:00', 'delivery', 'cancelled');

INSERT INTO order_item (order_item_id, order_id, menu_item_id, quantity, unit_price) VALUES
(1001, 101, 1, 2, 4500),
(1002, 101, 10, 1, 4800),
(1003, 102, 3, 1, 5500),
(1004, 102, 9, 2, 7200),
(1005, 103, 11, 2, 7900),
(1006, 103, 7, 1, 6200),
(1007, 104, 4, 1, 6100),
(1008, 104, 8, 1, 6800),
(1009, 105, 5, 1, 5000),
(1010, 105, 10, 1, 4800),
(1011, 106, 12, 1, 9800),
(1012, 106, 2, 2, 5200),
(1013, 107, 1, 1, 4500),
(1014, 107, 6, 1, 5300),
(1015, 108, 9, 1, 7200),
(1016, 108, 3, 2, 5500),
(1017, 109, 7, 2, 6200),
(1018, 109, 11, 1, 7900),
(1019, 110, 4, 2, 6100),
(1020, 111, 1, 1, 4500),
(1021, 111, 12, 1, 9800),
(1022, 112, 8, 1, 6800);
