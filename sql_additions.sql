--   --------------------------------------------------
--   Adds an additional table to provide a place to put
--   the callback-url. This basically squeezes the data
--   into PyBit's data model.
--   --------------------------------------------------

CREATE OR REPLACE FUNCTION make_plpgsql()
RETURNS VOID
LANGUAGE SQL
AS $$
CREATE LANGUAGE plpgsql;
$$;

SELECT
    CASE
    WHEN EXISTS(
        SELECT 1
        FROM pg_catalog.pg_language
        WHERE lanname='plpgsql'
    )
    THEN NULL
    ELSE make_plpgsql() END;

DROP FUNCTION make_plpgsql();

--  Drop Tables, Stored Procedures and Views

DROP TABLE IF EXISTS Callbacks CASCADE
;
;
--  Create Tables - Changed to add NOT NULLs
CREATE TABLE Callbacks (
id SERIAL PRIMARY KEY NOT NULL,
Job_id bigint NOT NULL,
url text NOT NULL
)
;

COMMENT ON TABLE Callbacks
    IS 'A callback is a URL used to notify the originating application when a job has finished.'
;

--  Create Indexes
ALTER TABLE Callbacks
        ADD CONSTRAINT UQ_Callbacks_id UNIQUE (id)
;

--  Create Foreign Key Constraints
ALTER TABLE Callbacks ADD CONSTRAINT FK_Callbacks_Job
        FOREIGN KEY (Job_id) REFERENCES Job (id)
;
