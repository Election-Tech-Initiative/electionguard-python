db.createCollection("guardians");
db.createCollection("key_ceremonies");
db.createCollection("elections");
db.createCollection("ballot_uploads");
db.createCollection("decryptions");
db.createCollection("db_deltas", { capped: true, size: 100000 });
db.db_deltas.insert({ type: "init" });
