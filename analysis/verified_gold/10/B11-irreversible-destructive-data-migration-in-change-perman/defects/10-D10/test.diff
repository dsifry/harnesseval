# Evidence test for candidate 10-B11 (discourse PR 10):
#   "Irreversible destructive data migration: `change` permanently deletes site settings on rollback"
#
# Instrument: the REAL migration file executed against a REAL Postgres (Docker service), using the
# repository's own Rails generation (ActiveRecord 4.2). A runtime unit test cannot prove this, and a
# stub cannot either: irreversibility is a property of how ActiveRecord inverts `change`.
#
#   RESULT: FAIL  => the claim holds (rollback is irreversible and the settings are destroyed)
#   RESULT: PASS  => rollback is safe (settings restored)
require 'active_record'

ActiveRecord::Base.establish_connection(
  adapter: 'postgresql', host: ENV.fetch('PGHOST', 'verify-postgres'),
  username: ENV.fetch('PGUSER', 'verify'), password: ENV.fetch('PGPASSWORD', 'verify'),
  database: ENV.fetch('PGDATABASE', 'verify_discourse')
)
conn = ActiveRecord::Base.connection

conn.execute("DROP TABLE IF EXISTS embeddable_hosts")
conn.execute("DROP TABLE IF EXISTS site_settings")
conn.execute("DROP TABLE IF EXISTS categories")
conn.execute("CREATE TABLE site_settings (id serial primary key, name varchar(255), value text)")
conn.execute("CREATE TABLE categories (id serial primary key, name varchar(255))")
conn.execute("INSERT INTO categories (name) VALUES ('Embed Category')")
conn.execute("INSERT INTO site_settings (name, value) VALUES ('embed_category', 'Embed Category')")
conn.execute("INSERT INTO site_settings (name, value) VALUES ('embeddable_hosts', E'one.example.com\\ntwo.example.com')")

settings_before = conn.select_value("SELECT count(*) FROM site_settings").to_i

require_relative '../../db/migrate/20150818190757_create_embeddable_hosts'
migration = CreateEmbeddableHosts.new

up_error = begin; migration.migrate(:up); nil; rescue => e; "#{e.class}: #{e.message[0, 120]}"; end
settings_after_up = conn.select_value("SELECT count(*) FROM site_settings").to_i

down_error = begin; migration.migrate(:down); nil; rescue => e; "#{e.class}: #{e.message[0, 160]}"; end
settings_after_down = conn.select_value("SELECT count(*) FROM site_settings").to_i

puts "up_error=#{up_error.inspect} settings_before=#{settings_before} after_up=#{settings_after_up} " \
     "down_error=#{down_error.inspect} after_down=#{settings_after_down}"

if settings_after_up == 0 && settings_after_down < settings_before
  puts "RESULT: FAIL: the migration's `change` block deletes site_settings irreversibly — up removed all " \
       "#{settings_before} rows, rollback #{down_error ? "raised (#{down_error})" : 'did not restore them'} " \
       "and only #{settings_after_down}/#{settings_before} rows survive"
else
  puts "RESULT: PASS: rollback is safe (settings restored: #{settings_after_down}/#{settings_before})"
end
