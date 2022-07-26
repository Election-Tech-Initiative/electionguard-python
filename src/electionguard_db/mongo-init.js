db.createCollection("guardians");
db.createCollection("key_ceremonies");
db.createCollection("elections");
db.createCollection("ballot_uploads");
db.createCollection("decryptions");
db.createCollection("key_ceremony_deltas", { capped: true, size: 100000 });
db.key_ceremony_deltas.insert({ type: "init" });
