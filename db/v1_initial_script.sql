CREATE SCHEMA training;

CREATE TABLE training.provider_branch_employees (
  id serial primary key,
  provider_branch_id integer REFERENCES public.provider_branches (id),
  name varchar(150) NOT NULL,
  phone varchar(50),
  title varchar(50),
  created_at timestamp without time zone DEFAULT now() NOT NULL,
  updated_at timestamp without time zone DEFAULT now() NOT NULL
);

CREATE TABLE training.training_scenarios
(
    id SERIAL PRIMARY KEY NOT NULL,
    description VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE training.training_batches (
  id serial PRIMARY KEY,
  name varchar(100),
  created_at timestamp without time zone DEFAULT now() NOT NULL,
  updated_at timestamp without time zone DEFAULT now() NOT NULL
);

CREATE TABLE training.training_sessions (
  id SERIAL PRIMARY KEY ,
  training_batch_id INTEGER NOT NULL REFERENCES training.training_batches(id),
  provider_branch_id INTEGER NOT NULL,
  teacher_id INTEGER NOT NULL,
  latitude NUMERIC(15,9),
  longitude NUMERIC(15,9),
  comments text,
  signature_url varchar(500),
  created_at timestamp without time zone DEFAULT now() NOT NULL,
  updated_at timestamp without time zone DEFAULT now() NOT NULL

);

CREATE TABLE training.training_session_assistants(
  id SERIAL PRIMARY KEY,
  training_session_id INTEGER NOT NULL REFERENCES training.training_sessions(id),
  provider_branch_employee_id INTEGER NOT NULL,

  created_at timestamp without time zone DEFAULT now() NOT NULL,
  updated_at timestamp without time zone DEFAULT now() NOT NULL
);

CREATE TABLE training.training_session_assistant_scores(
  id SERIAL PRIMARY KEY,
  training_session_assistant_id INTEGER NOT NULL REFERENCES training.training_session_assistants(id),
  training_scenario_id INTEGER NOT NULL REFERENCES training.training_scenarios,
  score numeric not null
);



INSERT INTO training.training_scenarios (description) values ('Agregar Productos');
INSERT INTO training.training_scenarios (description) values ('Validar autorizacion');
INSERT INTO training.training_batches (name) values ('Primera Capacitacion');

select * from training.training_batches;
select * from users;
