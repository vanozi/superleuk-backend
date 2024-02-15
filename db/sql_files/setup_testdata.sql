INSERT INTO users (email, hashed_password, is_active, confirmation)
VALUES ('admin@admin.com', '$2b$12$UKv6whbIteBbIsION9igLef5qOS6yzLn1MczUCST7X6RDn18afzZ2', TRUE, NULL),
       ('werknemer@werknemer.com', '$2b$12$X6OGY1eXztIH2rYDwyVFO.nmrPYq98kla4JmweOu4N/oMgoe3yaKK', TRUE, NULL),
       ('monteur@monteur.com', '$2b$12$XE2/M35H39qI7UnDYH9dieI3byg.3VoA3rB0GuEoByvQUt/xTm0y6', TRUE, NULL),
       ('melker@melker.com', '$2b$12$j79tDoaLxk6aGgcukhlX2OGJ2lwkqzahbCvtOylvoIRx6PZv25XUO', TRUE, NULL);
INSERT INTO roles (name, description)
VALUES ('admin', 'User met admin rechten'),
       ('werknemer', 'User met algemene werknemers rechten'),
       ('monteur', 'User met monteurs rechten'),
       ('melker', 'Medewerker waarvoor de melkbeurten apart worden berekend');
INSERT INTO user_roles (users_id, roles_id)
VALUES (1, 1),
       (2, 2),
       (3, 2),
       (3, 3),
       (4, 2),
       (4, 4);
