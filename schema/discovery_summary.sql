-- Discovery summary table (Azure SQL)
-- Source: superseding indictment discovery list photos (issue #4)

IF OBJECT_ID('dbo.discovery_summary', 'U') IS NOT NULL
    DROP TABLE dbo.discovery_summary;
GO

CREATE TABLE dbo.discovery_summary (
    id                  INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    source_page         NVARCHAR(16) NOT NULL,  -- page_1_main | page_2_supplement
    sort_order          INT NOT NULL,
    case_number         NVARCHAR(32) NOT NULL DEFAULT '5:25-cr-00376',
    superseding_indictment_date NVARCHAR(16) NULL DEFAULT '1/13/26',
    discovery_due_date  NVARCHAR(16) NULL DEFAULT '1/20/26',
    category            NVARCHAR(128) NOT NULL,
    description         NVARCHAR(512) NOT NULL,
    bates_begin         NVARCHAR(32) NULL,
    bates_end           NVARCHAR(32) NULL,
    doc_date            NVARCHAR(16) NULL,
    notes               NVARCHAR(512) NULL,
    created_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX IX_discovery_summary_category ON dbo.discovery_summary (category, sort_order);
GO

-- Reference photos (paths in repo; optional blob URLs after upload)
IF OBJECT_ID('dbo.discovery_summary_photos', 'U') IS NOT NULL
    DROP TABLE dbo.discovery_summary_photos;
GO

CREATE TABLE dbo.discovery_summary_photos (
    id          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    photo_key   NVARCHAR(32) NOT NULL,
    file_name   NVARCHAR(256) NOT NULL,
    repo_path   NVARCHAR(512) NOT NULL,
    md5_hash    NVARCHAR(32) NULL,
    is_duplicate BIT NOT NULL DEFAULT 0,
    notes       NVARCHAR(256) NULL,
    created_at  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
