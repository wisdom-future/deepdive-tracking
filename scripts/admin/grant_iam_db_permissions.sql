-- Grant database privileges to IAM service account user
-- Run this SQL using a database admin account

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO "726493701291-compute@developer";

-- Grant table privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "726493701291-compute@developer";

-- Grant sequence privileges
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "726493701291-compute@developer";

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "726493701291-compute@developer";

-- Grant default privileges for future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "726493701291-compute@developer";
