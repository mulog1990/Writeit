SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+8:00";
ALTER DATABASE CHARACTER SET "utf8";

DROP TABLE IF EXISTS users;
CREATE TABLE users (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(128) NOT NULL UNIQUE,
        name VARCHAR(128) NOT NULL
);

DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        author_id INT NOT NULL,
        markdown_id INT NOT NULL,
        title varchar(255) NOT NULL,
        slug varchar(512) NOT NULL,
        published DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

);

DROP TABLE IF EXISTS markdowns;
CREATE TABLE markdowns (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        entry_id INT NOT NULL,
        markdown MEDIUMTEXT NOT NULL,
        created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS tags;
CREATE TABLE tags (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        tag varchar(64) UNIQUE NOT NULL
);

DROP TABLE IF EXISTS tagged;
CREATE TABLE tagged (
        entry_id INT NOT NULL, 
        tag_id INT NOT NULL,
        PRIMARY KEY(entry_id,tag_id),
        FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id)
);

DROP VIEW IF EXISTS entry_v;
CREATE VIEW entry_v AS SELECT entries.id AS entry_id, users.name as author, title, slug,published,markdowns.markdown AS markdown, created AS modified from entries,markdowns,users where entries.markdown_id=markdowns.id AND entries.author_id=users.id;

DROP VIEW IF EXISTS tag_v;
CREATE VIEW tag_v AS SELECT entries.id AS entry_id, tags.tag AS tag FROM entries,tags,tagged WHERE entries.id=tagged.entry_id AND tagged.tag_id=tags.id;
