drop schema if exists public cascade;

create schema public;

create extension hstore;

create table public.notices(
  id serial primary key,
  channel text,
  payload text
);

create table public.users(
  id serial primary key,
  name text,
  email text unique,
  balance numeric,
  flags hstore
);

insert into public.users (name, email, balance, flags) values
    ('Elaina Dach', 'hane.ebba@wolf.com', 7.10, '"extra_feature"=>"true"'::hstore),
    ('Lucas Jaskolski', 'chad.cummings@hotmail.com', 46.35, null),
    ('Ms. Agustin Walter', 'johnnie.jast@hotmail.com', 81.0, null),
    ('Mr. Agustina Ward IV', 'guiseppe85@metz.info', 11.50, null),
    ('Dr. Brock Sanford IV', 'hilpert.beryl@langworthryan.com', 44.47, null),
    ('Itzel Schimmel', 'myost@hagenesklein.com', 94.50, null),
    ('Ms. Desiree Simonis', 'liliana23@beer.net', 81.98, null),
    ('Gabe Kling', 'jordyn.lynch@yahoo.com', 19.99, null),
    ('Raheem Kreiger', 'lindgren.tanya@yahoo.com', 20.10, null),
    ('Maximilian Kulas', 'tomas45@hotmail.com', 11.67, null);


drop schema if exists other cascade;

create schema other;

create table other.users(
  id serial primary key,
  name text
);

insert into other.users (name) values ('Mr. John Piere');

create function other.after_insert() returns trigger as $$
  begin
    raise notice 'New user inserted';
    return null;
  end;
$$ language plpgsql;

create trigger after_insert after insert on other.users for each row execute procedure other.after_insert();