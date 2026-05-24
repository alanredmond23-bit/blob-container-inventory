-- Homes v2 blob catalog (Azure SQL or PostgreSQL-compatible)
-- One row per blob; powers the migration "sheet" and six home-* containers.

IF OBJECT_ID('blob_catalog', 'U') IS NOT NULL DROP TABLE blob_catalog;
GO

CREATE TABLE blob_catalog (
    id              BIGINT IDENTITY(1,1) PRIMARY KEY,
    source_container NVARCHAR(128) NOT NULL,
    source_path     NVARCHAR(1024) NOT NULL,
    content_length  BIGINT NOT NULL DEFAULT 0,
    creation_time   DATETIME2 NULL,
    last_modified   DATETIME2 NULL,
    content_md5     VARBINARY(16) NULL,
    home_id         NVARCHAR(32) NOT NULL,
    home_container  AS ('home-' + home_id) PERSISTED,
    home_path       NVARCHAR(1024) NOT NULL,
    zone_path       NVARCHAR(256) NULL,
    card_id         NVARCHAR(256) NULL,
    migrate_status  NVARCHAR(32) NOT NULL DEFAULT 'mapped',
    dup_group_id    NVARCHAR(64) NULL,
    updated_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_blob_catalog_source UNIQUE (source_container, source_path)
);
GO

CREATE INDEX IX_blob_catalog_home ON blob_catalog (home_id, migrate_status)
    INCLUDE (content_length, last_modified);
CREATE INDEX IX_blob_catalog_zone ON blob_catalog (zone_path)
    INCLUDE (content_length);
CREATE INDEX IX_blob_catalog_status ON blob_catalog (migrate_status, home_id);
GO

-- Summary per home (the main dashboard "sheet")
CREATE OR ALTER VIEW v_home_summary AS
SELECT
    home_id,
    home_container,
    COUNT(*) AS blob_count,
    SUM(content_length) AS total_bytes,
    CAST(SUM(content_length) / 1099511627776.0 AS DECIMAL(12,3)) AS total_tib,
    MIN(creation_time) AS earliest_created,
    MAX(creation_time) AS latest_created,
    MIN(last_modified) AS earliest_modified,
    MAX(last_modified) AS latest_modified,
    SUM(CASE WHEN migrate_status = 'verified' THEN 1 ELSE 0 END) AS verified_count
FROM blob_catalog
GROUP BY home_id, home_container;
GO

-- Top 10 largest blobs per zone (mirrors SECTION_VIEWS)
CREATE OR ALTER VIEW v_zone_top10 AS
SELECT * FROM (
    SELECT
        zone_path,
        source_container,
        source_path,
        content_length,
        creation_time,
        last_modified,
        home_id,
        ROW_NUMBER() OVER (PARTITION BY zone_path ORDER BY content_length DESC) AS rn
    FROM blob_catalog
    WHERE zone_path IS NOT NULL
) t WHERE rn <= 10;
GO

-- Migration queue for copy jobs
CREATE OR ALTER VIEW v_migration_queue AS
SELECT
    id,
    home_id,
    home_container,
    home_path,
    source_container,
    source_path,
    content_length,
    migrate_status
FROM blob_catalog
WHERE migrate_status IN ('mapped', 'queued')
ORDER BY home_id, content_length DESC;
GO
