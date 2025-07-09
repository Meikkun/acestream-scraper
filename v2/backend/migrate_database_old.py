"""
Database migration script for Acestream Scraper v1 to v2
"""
import os
import sqlite3
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.config.database import engine, Base
from app.config.settings import settings
from app.models.models import (
    ScrapedURL, 
    AcestreamChannel, 
    EPGSource, 
    TVChannel, 
    EPGChannel, 
    EPGProgram, 
    EPGStringMapping, 
    Setting
)

class DatabaseMigrator:
    def __init__(self):
        self.v1_db_path = settings.LEGACY_DATABASE_URL.replace("sqlite:///", "")
        self.v2_db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        self.v1_migrated_path = self.v1_db_path + ".migrated"
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.v2_db_path), exist_ok=True)
        
        # Track ID mappings for foreign keys
        self.id_mappings = {
            'tv_channels': {},      # old_id -> new_id
            'epg_sources': {},      # old_id -> new_id
            'epg_channels': {},     # old_id -> new_id
            'scraped_urls': {}      # old_id -> new_id
        }
    
    def should_migrate(self) -> bool:
        """Check if migration should run"""
        return os.path.exists(self.v1_db_path) and not os.path.exists(self.v1_migrated_path)
    
    def inspect_v1_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Inspect v1 database structure and return table schemas"""
        if not os.path.exists(self.v1_db_path):
            print(f"V1 database not found at {self.v1_db_path}")
            return {}
        
        schemas = {}
        
        try:
            with sqlite3.connect(self.v1_db_path) as conn:
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                print(f"Found {len(tables)} tables in v1 database:")
                
                for table_name in tables:
                    table_name = table_name[0]
                    print(f"\nTable: {table_name}")
                    
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    
                    table_schema = []
                    for col in columns:
                        col_info = {
                            'name': col[1],
                            'type': col[2],
                            'notnull': col[3],
                            'default': col[4],
                            'pk': col[5]
                        }
                        table_schema.append(col_info)
                        print(f"  - {col_info['name']}: {col_info['type']} (pk={col_info['pk']}, notnull={col_info['notnull']})")
                    
                    schemas[table_name] = table_schema
                    
                    # Show row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"  Rows: {count}")
                
        except Exception as e:
            print(f"Error inspecting v1 database: {e}")
            return {}
        
        return schemas
    
    def create_v2_database(self):
        """Create v2 database tables"""
        print("Creating v2 database tables...")
        Base.metadata.create_all(bind=engine)
        print("V2 database tables created successfully!")
    
    def migrate_epg_sources(self):
        """Migrate EPG sources first (needed for foreign keys)"""
        if not os.path.exists(self.v1_db_path):
            return
        
        print("Migrating EPG sources...")
        
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)
            
            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()
            
            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='epg_sources';")
            if not v1_cursor.fetchone():
                print("epg_sources table not found in v1 database")
                return
            
            v1_cursor.execute("SELECT * FROM epg_sources ORDER BY id;")
            v1_sources = v1_cursor.fetchall()
            
            print(f"Found {len(v1_sources)} EPG sources in v1 database")
            
            migrated_count = 0
            for row in v1_sources:
                try:
                    # Insert and get new ID
                    v2_cursor.execute("""
                        INSERT INTO epg_sources (url, name, enabled, last_updated, error_count, last_error)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['url'],
                        row['name'],
                        row['enabled'],
                        row['last_updated'],
                        row['error_count'],
                        row['last_error']
                    ))
                    
                    new_id = v2_cursor.lastrowid
                    self.id_mappings['epg_sources'][row['id']] = new_id
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"Error migrating EPG source {row['id']}: {e}")
                    continue
            
            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} EPG sources")
            
        except Exception as e:
            print(f"Error during EPG sources migration: {e}")
        finally:
            v1_conn.close()
            v2_conn.close()
    
    def migrate_tv_channels(self):
        """Migrate TV channels with EPG source foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return
        
        print("Migrating TV channels...")
        
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)
            
            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()
            
            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tv_channels';")
            if not v1_cursor.fetchone():
                print("tv_channels table not found in v1 database")
                return
            
            v1_cursor.execute("SELECT * FROM tv_channels ORDER BY id;")
            v1_channels = v1_cursor.fetchall()
            
            print(f"Found {len(v1_channels)} TV channels in v1 database")
            
            migrated_count = 0
            for row in v1_channels:
                try:
                    # Map foreign key
                    epg_source_id = None
                    if row['epg_source_id']:
                        epg_source_id = self.id_mappings['epg_sources'].get(row['epg_source_id'])
                    
                    # Insert and get new ID
                    v2_cursor.execute("""
                        INSERT INTO tv_channels 
                        (name, description, logo_url, category, country, language, website, 
                         epg_id, epg_source_id, created_at, updated_at, is_active, is_favorite, channel_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['name'],
                        row['description'],
                        row['logo_url'],
                        row['category'],
                        row['country'],
                        row['language'],
                        row['website'],
                        row['epg_id'],
                        epg_source_id,
                        row['created_at'],
                        row['updated_at'],
                        row['is_active'],
                        row['is_favorite'],
                        row['channel_number']
                    ))
                    
                    new_id = v2_cursor.lastrowid
                    self.id_mappings['tv_channels'][row['id']] = new_id
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"Error migrating TV channel {row['id']}: {e}")
                    continue
            
            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} TV channels")
            
        except Exception as e:
            print(f"Error during TV channels migration: {e}")
        finally:
            v1_conn.close()
            v2_conn.close()
    
    def migrate_acestream_channels(self):
        """Migrate acestream channels with TV channel foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return
        
        print("Migrating acestream channels...")
        
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)
            
            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()
            
            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acestream_channels';")
            if not v1_cursor.fetchone():
                print("acestream_channels table not found in v1 database")
                return
            
            v1_cursor.execute("SELECT * FROM acestream_channels;")
            v1_channels = v1_cursor.fetchall()
            
            print(f"Found {len(v1_channels)} acestream channels in v1 database")
            
            migrated_count = 0
            for row in v1_channels:
                try:
                    # Map foreign key
                    tv_channel_id = None
                    if row['tv_channel_id']:
                        tv_channel_id = self.id_mappings['tv_channels'].get(row['tv_channel_id'])
                    
                    # Insert into v2 database
                    v2_cursor.execute("""
                        INSERT OR REPLACE INTO acestream_channels 
                        (channel_id, name, "group", logo, tvg_id, tvg_name, source_url, 
                         last_seen, is_active, is_online, last_checked, original_url, epg_update_protected, tv_channel_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],  # v1 uses 'id' as channel_id
                        row['name'],
                        row['group'],
                        row['logo'],
                        row['tvg_id'],
                        row['tvg_name'],
                        row['source_url'],
                        row['added_at'] or row['last_processed'],
                        row['status'] == 'active' if row['status'] else True,
                        row['is_online'],
                        row['last_checked'],
                        row['original_url'],
                        row['epg_update_protected'] or False,
                        tv_channel_id
                    ))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"Error migrating acestream channel {row['id']}: {e}")
                    continue
            
            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} acestream channels")
            
        except Exception as e:
            print(f"Error during acestream channels migration: {e}")
        finally:
            v1_conn.close()
            v2_conn.close()
    
    def migrate_settings(self):
        """Migrate settings from v1 to v2"""
        if not os.path.exists(self.v1_db_path):
            return
        
        print("Migrating settings...")
        
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)
            
            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()
            
            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings';")
            if not v1_cursor.fetchone():
                print("settings table not found in v1 database")
                return
            
            v1_cursor.execute("SELECT * FROM settings;")
            v1_settings = v1_cursor.fetchall()
            
            print(f"Found {len(v1_settings)} settings in v1 database")
            
            migrated_count = 0
            for row in v1_settings:
                try:
                    v2_cursor.execute("""
                        INSERT OR REPLACE INTO settings (key, value, description)
                        VALUES (?, ?, ?)
                    """, (
                        row['key'],
                        row['value'],
                        None  # v1 doesn't have description field
                    ))
                    migrated_count += 1
                except Exception as e:
                    print(f"Error migrating setting {row['key']}: {e}")
                    continue
            
            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} settings")
            
        except Exception as e:
            print(f"Error during settings migration: {e}")
        finally:
            v1_conn.close()
            v2_conn.close()
    
    def finalize_migration(self):
        """Rename old database and cleanup"""
        if os.path.exists(self.v1_db_path):
            print(f"Renaming {self.v1_db_path} to {self.v1_migrated_path}")
            shutil.move(self.v1_db_path, self.v1_migrated_path)
            print("Migration completed and old database archived!")
    
    def run_migration(self):
        """Run complete migration process"""
        if not self.should_migrate():
            print("No migration needed - either v1 database doesn't exist or already migrated")
            return False
        
        print("Starting database migration...")
        print(f"V1 database: {self.v1_db_path}")
        print(f"V2 database: {self.v2_db_path}")
        
        # Inspect v1 database
        schemas = self.inspect_v1_database()
        
        if not schemas:
            print("No v1 database to migrate")
            return False
        
        # Create v2 database
        self.create_v2_database()
        
        # Migrate data in order (respecting foreign keys)
        self.migrate_epg_sources()
        self.migrate_tv_channels()
        self.migrate_acestream_channels()
        self.migrate_settings()
        
        # Finalize migration
        self.finalize_migration()
        
        print("Migration completed successfully!")
        return True

def main():
    """Main migration function"""
    migrator = DatabaseMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()
