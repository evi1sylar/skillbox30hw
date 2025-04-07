CREATE TABLE client (
    id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    credit_card VARCHAR(50),
    car_number VARCHAR(10),
    PRIMARY KEY (id)
);

CREATE TABLE parking (
    id INTEGER NOT NULL,
    address VARCHAR(100) NOT NULL,
    opened BOOLEAN,
    count_places INTEGER NOT NULL,
    count_available_places INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE client_parking (
    id INTEGER NOT NULL,
    client_id INTEGER,
    parking_id INTEGER,
    time_in DATETIME,
    time_out DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT unique_client_parking UNIQUE (client_id, parking_id),
    FOREIGN KEY(client_id) REFERENCES client (id),
    FOREIGN KEY(parking_id) REFERENCES parking (id)
);