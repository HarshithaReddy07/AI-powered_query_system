USE football_db;
GO

SELECT COUNT(*) AS broken_players
FROM dbo.players
WHERE club_id NOT IN (SELECT id FROM dbo.clubs);