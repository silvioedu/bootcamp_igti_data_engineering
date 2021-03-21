/* Logico_Cliente: */
USE igti_teste;

CREATE TABLE Cliente (
    cod_cliente INT PRIMARY KEY,
    nom_cliente VARCHAR(30)
);

CREATE TABLE Endereco (
    id_endereco INT PRIMARY KEY,
    nom_endereco VARCHAR(10),
    dsc_endereco VARCHAR(60),
    fk_Cliente_cod_cliente INT
);
 
ALTER TABLE Endereco ADD CONSTRAINT FK_Endereco_2
    FOREIGN KEY (fk_Cliente_cod_cliente)
    REFERENCES Cliente (cod_cliente)
    ON DELETE RESTRICT;

INSERT INTO Cliente(cod_cliente, nom_cliente) values
(1, 'Thaddeus'),
(2, 'Alisa'),
(3, 'Leroy'),
(4, 'Melvin'),
(5, 'Marshall'),
(6, 'Winifred'),
(7, 'Ira'),
(8, 'Amal'),
(9, 'Lila'),
(10, 'Damon');

INSERT INTO Endereco(id_endereco, nom_endereco, dsc_endereco, fk_Cliente_cod_cliente) values
(1, 'Endereco 1', 'Rua xxx1, 100 Bairro yyy', 1),
(2, 'Endereco 2', 'Rua xxx2, 100 Bairro yyy', 2),
(3, 'Endereco 3', 'Rua xxx3, 100 Bairro yyy', 3),
(4, 'Endereco 4', 'Rua xxx4, 100 Bairro yyy', 4),
(5, 'Endereco 5', 'Rua xxx5, 100 Bairro yyy', 5);

select *
  from cliente c
  inner join endereco e
     on c.cod_cliente = e.fk_Cliente_cod_cliente