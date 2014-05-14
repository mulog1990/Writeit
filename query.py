def get_neighbor_entries(db, entry_id):
    entries = dict()
    newer = db.get("SELECT * from entry_v WHERE entry_id>%s\
            ORDER BY entry_id ASC LIMIT 1", entry_id)
    older = db.get("SELECT * from entry_v WHERE entry_id<%s\
            ORDER BY entry_id DESC LIMIT 1", entry_id)


    if newer:
        entries["next"] = dict()
        entries["next"]["title"] = newer["title"]
        entries["next"]["slug"] = newer["slug"]
    if older: 
        entries["prev"] = dict()
        entries["prev"]["title"] = older["title"]
        entries["prev"]["slug"] = older["slug"]

    return entries
    
def check_slug(db, slug):
    existed = db.get("SELECT entry_id from entry_v WHERE slug=%s", slug)
    print "query " + str(existed)
    if existed:
        return False
    else:
        return True

def update_entry(db, title, markdown_id, new_slug, slug):

    return db.update("UPDATE entries SET title=%s,markdown_id=%d,slug=%s \
            WHERE slug=%s", title, markdown_id, new_slug, slug)

def create_entry(db, title, markdown_id, slug, user_email):
    return db.insert("INSERT INTO entries SET title=%s, markdown_id=%s,\
            slug=%s, author_id=(SELECT id FROM users WHERE email=%s)",\
            title, markdown_id, slug, user_email)

def get_tags(db, entry_id):
    tags = db.query("SELECT tag FROM tag_v WHERE entry_id=%s", entry_id)
    return tags

def update_tags(db, slug, tags):
    entry_id = db.get("SELECT entry_id from entry_v where slug=%s", slug)["entry_id"]
    old_tags = db.query("SELECT tag FROM tag_v WHERE entry_id=%s", int(entry_id))
    old_tags = [tag["tag"] for tag in old_tags]
    new_tags = set(tags) - set(old_tags)
    deprec_tags = set(old_tags) - set(tags)

    for tag in deprec_tags:
        tag_id=db.get("SELECT id from tags WHERE tag=%s", tag)["id"]
        db.execute("DELETE FROM tagged where entry_id=%s AND tag_id=%s", \
                int(entry_id), int(tag_id))
    for tag in new_tags:
        tag_id = db.get("SELECT id FROM tags WHERE tag=%s", tag)
        if not tag_id:
            db.execute("INSERT INTO tags SET tag=%s", tag)
            tag_id = db.get("SELECT id FROM tags WHERE tag=%s", tag)
        tag_id = tag_id["id"]
        db.execute("INSERT INTO tagged SET entry_id=%s,tag_id=%s", entry_id, tag_id)

def get_all_tags(db):
    return db.query("SELECT COUNT(*) as count,tag FROM tagged,tags\
            WHERE tagged.tag_id=tags.id GROUP BY tagged.tag_id")
        

def get_entries_by_tag(db, tag):
    return db.query("SELECT * FROM entry_v,tag_v WHERE tag_v.tag=%s AND\
            tag_v.entry_id=entry_v.entry_id", tag)

def save_markdown(db, markdown, slug):
    entry_id = db.get("SELECT id FROM entries WHERE slug=%s LIMIT 1", slug)
    if entry_id:
        entry_id = entry_id["id"]
    else:
        entry_id = -1

    return db.execute("INSERT INTO markdowns SET markdown=%s,entry_id=%s",\
            markdown, entry_id)


def get_earliest_year(db):
    entry = db.get("SELECT published FROM entries ORDER BY published ASC LIMIT 1")
    if entry:
        return entry["published"]
    else:
        return -1

def get_entries_by_year(db, year):
    entries = db.query("SELECT * FROM entry_v WHERE published BETWEEN\
            '%s-01-01' AND '%s-12-31' ORDER BY published DESC", year, year)
    return entries

def get_year_range(db):
    oldest = db.query("SELECT published from entry_v ORDER by published\
            ASC LIMIT 1")
    newest = db.query("SELECT published from entry_v ORDER by published\
            DESC LIMIT 1")

    oldest_year = oldest["published"].split("-")[0]
    newest_year = newest["published"].spili("-")[0]

    return (oldest_year, oldest_year)

def get_entry_by_slug(db, slug):
    return db.get("SELECT * FROM entry_v WHERE slug=%s", slug)

def get_last_insert_id(db):
    return db.execute("SELECT LAST_INSERT_ID()")

def get_fresh_entries(db, num_of_entries):
    return db.query("SELECT * FROM entry_v ORDER BY entry_id DESC LIMIT %s",\
            num_of_entries)
    
def remove_entry(db, slug):
    db.execute("DELETE FROM entries WHERE slug=%s", slug)
    return

