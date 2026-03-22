import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
server = os.environ.get("MSSQL_SERVER")
database = os.environ.get("MSSQL_DATABASE")
username = os.environ.get("MSSQL_USERNAME")
password = os.environ.get("MSSQL_PASSWORD")

if not password:
    print("Error: Set MSSQL_PASSWORD environment variable")
    exit(1)

# Connection string
connection_string = (
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

def load_csv_to_database():
    """Load player data from CSV into the database."""
    
    try:
        # Read CSV file
        csv_path = "transfermarkt_player_values.csv"
        print(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path) #This loads raw structured data into a dataframe, which we will then process and insert into the database.
        
        print(f"Loaded {len(df)} rows from CSV")
        
        # Connect to database
        print("Connecting to database...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Verify connection
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"Connected to database: {db_name}\n")
        
        # Load data into tables
        load_leagues(cursor, df)
        load_clubs(cursor, df)
        load_players(cursor, df)
        
        conn.commit()
        print("\n✓ All data loaded successfully!")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def load_leagues(cursor, df):
    """Load unique leagues into the leagues table."""
    print("Loading leagues...")
    
    # Get unique leagues from CSV
    leagues = df['league_name'].dropna().unique()
    
    # Get existing leagues from DB
    cursor.execute("SELECT name FROM leagues")
    existing_leagues = {row[0] for row in cursor.fetchall()}
    
    inserted = 0
    for league in leagues:
        if league not in existing_leagues:
            try:
                cursor.execute("INSERT INTO leagues (name) VALUES (?)", league)
                inserted += 1
            except Exception as e:
                print(f"  Error inserting league '{league}': {e}")
    
    print(f"  Inserted {inserted} new leagues")

def load_clubs(cursor, df):
    """Load unique clubs into the clubs table."""
    print("Loading clubs...")
    
    # Get unique clubs with their leagues
    clubs_data = df[['current_club', 'league_name']].dropna().drop_duplicates()
    
    # Get existing clubs from DB
    cursor.execute("SELECT name FROM clubs")
    existing_clubs = {row[0] for row in cursor.fetchall()}
    
    inserted = 0
    for _, row in clubs_data.iterrows():
        club_name = row['current_club']
        league_name = row['league_name']
        
        if club_name not in existing_clubs:
            try:
                # Get league_id
                cursor.execute("SELECT id FROM leagues WHERE name = ?", league_name)
                league_result = cursor.fetchone()
                league_id = league_result[0] if league_result else None
                
                if league_id:
                    cursor.execute(
                        "INSERT INTO clubs (name, league_id) VALUES (?, ?)",
                        club_name, league_id
                    )
                    inserted += 1
            except Exception as e:
                print(f"  Error inserting club '{club_name}': {e}")
    
    print(f"  Inserted {inserted} new clubs")

def load_players(cursor, df):
    """Load player data into the players table."""
    print("Loading players...")
    
    # Get club_id mapping
    cursor.execute("SELECT name, id FROM clubs")
    club_mapping = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Map CSV to DB columns
    insert_sql = """
        INSERT INTO players 
        (player_id, player_name, age, nationality, position, position_group,
         current_value_eur, peak_value_eur, first_value_eur, last_value_eur,
         trajectory, cagr, volatility, club_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    inserted = 0
    skipped = 0
    
    for _, row in df.iterrows():
        try:
            # Get club_id
            club_name = row.get('current_club')
            club_id = club_mapping.get(club_name)
            
            # Extract numeric values from currency strings
            current_value = extract_numeric(row.get('current_value_eur'))
            peak_value = extract_numeric(row.get('peak_value_eur'))
            first_value = extract_numeric(row.get('first_value_eur'))
            last_value = extract_numeric(row.get('last_value_eur'))
            
            values = (
                int(row['player_id']),
                row.get('name'),
                int(row['age']) if pd.notna(row.get('age')) else None,
                row.get('nationality'),
                row.get('position'),
                row.get('position_group'),
                current_value,
                peak_value,
                first_value,
                last_value,
                row.get('trajectory'),
                float(row.get('value_cagr')) if pd.notna(row.get('value_cagr')) else None,
                float(row.get('value_volatility')) if pd.notna(row.get('value_volatility')) else None,
                club_id
            )
            
            cursor.execute(insert_sql, values)
            inserted += 1
            
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  Row {inserted + skipped}: {e}")
    
    print(f"  Inserted {inserted} players, skipped {skipped}")

def extract_numeric(value):
    """Extract numeric value from currency string like '€200.00m' or '200000000'."""
    if pd.isna(value):
        return None
    
    value_str = str(value).replace(',', '')
    
    # Handle million suffix
    if 'm' in value_str.lower():
        return int(float(value_str.lower().replace('€', '').replace('m', '').strip()) * 1_000_000)
    
    # Handle billion suffix
    if 'b' in value_str.lower():
        return int(float(value_str.lower().replace('€', '').replace('b', '').strip()) * 1_000_000_000)
    
    # Try to convert directly to integer
    try:
        return int(float(value_str.replace('€', '').replace('.', '').strip()))
    except:
        return None

if __name__ == "__main__":
    load_csv_to_database()
