PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS cafe_order;
DROP TABLE IF EXISTS menu_item;
DROP TABLE IF EXISTS menu_category;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS customer;

CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    joined_at DATE NOT NULL,
    city TEXT NOT NULL,
    membership_level TEXT NOT NULL CHECK (membership_level IN ('regular', 'silver', 'gold'))
);

CREATE TABLE staff (
    staff_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    hired_at DATE NOT NULL
);

CREATE TABLE menu_category (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_order INTEGER NOT NULL CHECK (display_order > 0)
);

CREATE TABLE menu_item (
    menu_item_id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    price INTEGER NOT NULL CHECK (price > 0),
    is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    created_at DATE NOT NULL,
    FOREIGN KEY (category_id) REFERENCES menu_category(category_id)
);

CREATE TABLE cafe_order (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    ordered_at DATETIME NOT NULL,
    order_type TEXT NOT NULL CHECK (order_type IN ('takeout', 'dine_in', 'delivery')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'cancelled')),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
);

CREATE TABLE order_item (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price > 0),
    FOREIGN KEY (order_id) REFERENCES cafe_order(order_id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id)
);
