INSERT INTO country ("countryID", "name")
VALUES
(1, 'Spain'),
(2, 'France'),
(3, 'Belgium'),
(4, 'United Kingdom'),
(5, 'Denmark'),
(6, 'Germany'),
(7, 'Portugal'),
(8, 'Italy'),
(9, 'Austria'),
(10,'Romania'),
(11,'Netherlands'),
(12,'Ireland'),
(13,'Norway')
;

INSERT INTO "director" ("directorID", "name")
VALUES
(1,'Rhys Shillaber'),
(2,'Meggie Sarjeant'),
(3,'Allard Benzi'),
(4,'Barbie Peak'),
(5,'Judy Noar')
;

INSERT INTO "actor" ("actorID", "name")
VALUES
(1,'Rana Graddell'),
(2,'Jolene Mayoral'),
(3,'Newton Coomer'),
(4,'Bernard Sawtell'),
(5,'Myrlene Sauter'),
(6,'Merle Haysham')
;
 
INSERT INTO "film" ("filmID", "title", "description", "price", "directorID")
VALUES
(1,'Apache', 'nullam orci pede venenatis non sodales sed tincidunt eu felis fusce', 23.70, 4),
(2,'Immortal Sergeant', 'eget tempus vel pede morbi porttitor lorem id ligula suspendisse ornare consequat lectus', 11.90,3),
(3,'Vai~E~Vem', 'id luctus nec molestie sed justo pellentesque viverra pede ac diam cras pellentesque volutpat', 22.50,2),
(4,'Hart of London, The', 'sem mauris laoreet ut rhoncus aliquet pulvinar sed nisl nunc rhoncus dui vel sem', 10.15,1),
(5,'Night Must Fall', 'nulla tempus vivamus in felis eu sapien cursus vestibulum proin eu', 8.88,5),
(6,'Tracers', 'euismod scelerisque quam turpis adipiscing lorem vitae mattis nibh ligula nec sem', 20.52,4),
(7,'The Count of Monte Cristo', 'non mi integer ac neque duis bibendum morbi non quam nec dui luctus rutrum nulla', 4.35,3),
(8,'Kalifornia', 'nascetur ridiculus mus etiam vel augue vestibulum rutrum rutrum neque aenean', 15.30,2),
(9,'Faces of Death 5', 'quis odio consequat varius integer ac leo pellentesque ultrices mattis odio donec vitae nisi nam', 12.41,1),
(10,'Empire of Passion (a.k.a. In the Realm of Passion) (a.k.a. Phantom Love) (Ai No Borei)', 'vel accumsan tellus nisi eu orci mauris lacinia sapien quis libero nullam sit amet turpis', 4.77,1),
(11,'Winter in Wartime', 'turpis eget elit sodales scelerisque mauris sit amet eros suspendisse accumsan', 17.88,2),
(12,'Love Walked In', 'tortor quis turpis sed ante vivamus tortor duis mattis egestas', 7.23,3),
(13,'Lascars', 'eu interdum eu tincidunt in leo maecenas pulvinar lobortis est', 16.33,4),
(14,'Late Autumn (Man-choo)', 'orci pede venenatis non sodales sed tincidunt eu felis fusce posuere felis', 20.67,5),
(15,'Street Fight', 'ac enim in tempor turpis nec euismod scelerisque quam turpis', 16.49,1),
(16,'Umberto D.', 'tortor quis turpis sed ante vivamus tortor duis mattis egestas metus aenean fermentum donec ut', 21.66,2),
(17,'Lethal Weapon 3', 'rhoncus aliquam lacus morbi quis tortor id nulla ultrices aliquet maecenas leo odio condimentum id', 3.78,3),
(18,'Toy Story 2', 'nullam molestie nibh in lectus pellentesque at nulla suspendisse potenti cras in', 13.33,4),
(19,'John Rabe', 'sed justo pellentesque viverra pede ac diam cras pellentesque volutpat dui', 6.75,5),
(20,'No End (Bez konca)', 'est risus auctor sed tristique in tempus sit amet sem', 10.92,2);
;

INSERT INTO "inventory" ("filmID", "amount")
VALUES
(1,2),
(2,3),
(3,0),
(4,0),
(5,4),
(6,1),
(7,5),
(8,3),
(9,10),
(10,2),
(11,0),
(12,5),
(13,2),
(14,3),
(15,4),
(16,1),
(17,0),
(18,0),
(19,7),
(20,9);
INSERT INTO "film_actor" ("filmID", "actorID")
VALUES
(1,1),
(2,5),
(3,6),
(4,2),
(5,5),
(6,4),
(7,1),
(8,3),
(9,2),
(10,3),
(11,6),
(12,2),
(13,4),
(14,1),
(15,5),
(16,3),
(17,1),
(18,6),
(19,3),
(20,5);


--Al parecer, es obligatorio ir sincronizando los valores
--que insertamos a mano de los id para que luego no den problemas
--cuando insertamos nuevas peliculas dinamicamente

SELECT setval(
    pg_get_serial_sequence('"country"', 'countryID'),
    (SELECT MAX("countryID") FROM "country"),
    true
);

SELECT setval(
    pg_get_serial_sequence('"director"', 'directorID'),
    (SELECT MAX("directorID") FROM "director"),
    true
);

SELECT setval(
    pg_get_serial_sequence('"actor"', 'actorID'),
    (SELECT MAX("actorID") FROM "actor"),
    true
);

SELECT setval(
    pg_get_serial_sequence('"film"', 'filmID'),
    (SELECT MAX("filmID") FROM "film"),
    true
);