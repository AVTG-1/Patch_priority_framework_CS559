"""
Collaboration CLI

Command-line interface for managing users, systems, and shared vulnerabilities.
Provides easy testing and demonstration of the collaboration framework.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import argparse
import json
from typing import Optional
from datetime import datetime

from collaboration.user import User
from collaboration.user_manager import UserManager
from collaboration.shared_vulnerability import SharedVulnerability
from collaboration.vulnerability_repository import VulnerabilityRepository
from data_model.config_loader import ConfigLoader
from data_model.system import SystemInstance


class CollaborationCLI:
    """
    Command-line interface for collaboration operations.
    
    Manages in-memory user manager and vulnerability repository.
    For production use, these would be backed by a database.
    """
    
    def __init__(self):
        """Initialize CLI with in-memory storage."""
        self.user_manager = UserManager()
        self.repo = VulnerabilityRepository()
        self.systems = {}  # system_id -> SystemInstance
    
    # User Management Commands
    
    def user_create(self, user_id: str, username: str, email: str, system_id: str):
        """Create a new user."""
        try:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                system_id=system_id,
                created_at=datetime.utcnow().isoformat()
            )
            self.user_manager.create_user(user)
            print(f"✓ User created: {username} (ID: {user_id})")
            print(f"  System: {system_id}")
        except ValueError as e:
            print(f"✗ Error: {e}")
            return False
        return True
    
    def user_list(self, pattern: Optional[str] = None):
        """List all users or search by username pattern."""
        if pattern:
            users = self.user_manager.search_users(pattern)
            print(f"Users matching '{pattern}':")
        else:
            users = self.user_manager.list_all()
            print("All users:")
        
        if not users:
            print("  No users found")
            return
        
        for user in users:
            print(f"  • {user.username} ({user.email})")
            print(f"    ID: {user.user_id}, System: {user.system_id}")
    
    def user_info(self, identifier: str):
        """Get user information by ID, username, or email."""
        # Try by ID first
        user = self.user_manager.get(identifier)
        
        # Try by username
        if not user:
            user = self.user_manager.get_by_username(identifier)
        
        # Try by email
        if not user:
            user = self.user_manager.get_by_email(identifier)
        
        if not user:
            print(f"✗ User not found: {identifier}")
            return False
        
        print(f"User: {user.username}")
        print(f"  ID: {user.user_id}")
        print(f"  Email: {user.email}")
        print(f"  System: {user.system_id}")
        print(f"  Created: {user.created_at or 'N/A'}")
        return True
    
    def user_delete(self, user_id: str):
        """Delete a user."""
        if self.user_manager.delete(user_id):
            print(f"✓ User deleted: {user_id}")
            return True
        else:
            print(f"✗ User not found: {user_id}")
            return False
    
    # System Management Commands
    
    def system_load(self, config_file: str, user_id: Optional[str] = None):
        """Load a system from configuration file."""
        try:
            loader = ConfigLoader()
            system = loader.load_system(config_file)
            
            # Override owner if specified
            if user_id:
                system.owner_user_id = user_id
            
            # Determine system_id from owner or file name
            if system.owner_user_id:
                system_id = system.owner_user_id
            else:
                system_id = os.path.splitext(os.path.basename(config_file))[0]
            
            self.systems[system_id] = system
            
            print(f"✓ System loaded: {system.system_class.name}")
            print(f"  System ID: {system_id}")
            print(f"  Owner: {system.owner_user_id or 'None'}")
            print(f"  Subsystems: {len(system.subsystems)}")
            print(f"  Vulnerabilities: {system.get_total_vulnerability_count()}")
            return True
        except Exception as e:
            print(f"✗ Error loading system: {e}")
            return False
    
    def system_list(self):
        """List all loaded systems."""
        if not self.systems:
            print("No systems loaded")
            return
        
        print("Loaded systems:")
        for system_id, system in self.systems.items():
            print(f"  • {system.system_class.name} (ID: {system_id})")
            print(f"    Owner: {system.owner_user_id or 'None'}")
            print(f"    Subsystems: {len(system.subsystems)}")
            print(f"    Vulnerabilities: {system.get_total_vulnerability_count()}")
    
    def system_info(self, system_id: str):
        """Show detailed system information."""
        system = self.systems.get(system_id)
        if not system:
            print(f"✗ System not found: {system_id}")
            return False
        
        print(f"System: {system.system_class.name}")
        print(f"  ID: {system_id}")
        print(f"  Owner: {system.owner_user_id or 'None'}")
        print(f"  Subsystems: {len(system.subsystems)}")
        
        print("\n  Subsystems:")
        for sub in system.subsystems:
            vuln_count = sub.get_vulnerability_count()
            print(f"    • {sub.name} ({sub.id}): {vuln_count} vulnerabilities")
        
        return True
    
    # Vulnerability Sharing Commands
    
    def publish(self, system_id: str, cve_id: str, subsystem_type: str, 
                metrics: Optional[str] = None):
        """Publish a vulnerability from a system to the shared repository."""
        system = self.systems.get(system_id)
        if not system:
            print(f"✗ System not found: {system_id}")
            return False
        
        # Find the vulnerability in the system
        vuln = None
        for v in system.get_all_vulnerabilities():
            if v.cve_id == cve_id:
                vuln = v
                break
        
        if not vuln:
            print(f"✗ Vulnerability not found: {cve_id}")
            return False
        
        # Parse game theory metrics if provided
        game_metrics = {}
        if metrics:
            try:
                game_metrics = json.loads(metrics)
            except json.JSONDecodeError:
                print(f"✗ Invalid JSON for metrics: {metrics}")
                return False
        
        # Convert to shared vulnerability
        if not system.owner_user_id:
            print("✗ System has no owner. Cannot publish.")
            return False
        
        shared_data = vuln.to_shared(
            author_user_id=system.owner_user_id,
            subsystem_type=subsystem_type,
            game_theory_metrics=game_metrics
        )
        shared_vuln = SharedVulnerability.from_dict(shared_data)
        
        try:
            self.repo.add(shared_vuln)
            print(f"✓ Published: {cve_id}")
            print(f"  Shared ID: {shared_vuln.shared_vuln_id}")
            print(f"  Author: {system.owner_user_id}")
            print(f"  Subsystem Type: {subsystem_type}")
            return True
        except ValueError as e:
            print(f"✗ Error: {e}")
            return False
    
    def search(self, author: Optional[str] = None, subsystem_type: Optional[str] = None,
               min_votes: Optional[int] = None, cve_prefix: Optional[str] = None):
        """Search the vulnerability repository."""
        results = self.repo.search(
            author_user_id=author,
            subsystem_type=subsystem_type,
            min_votes=min_votes,
            cve_prefix=cve_prefix
        )
        
        if not results:
            print("No vulnerabilities found")
            return
        
        print(f"Found {len(results)} vulnerabilities:")
        for v in results:
            print(f"\n  • {v.cve_id} (ID: {v.shared_vuln_id})")
            print(f"    Author: {v.author_user_id}")
            print(f"    Type: {v.subsystem_type}")
            print(f"    Impact: {v.cvss_impact}, Exploitability: {v.cvss_exploitability}")
            print(f"    Patch Cost: {v.patch_cost}")
            print(f"    Votes: {v.votes}")
            if v.game_theory_metrics:
                print(f"    Metrics: {json.dumps(v.game_theory_metrics)}")
    
    def import_vuln(self, system_id: str, shared_vuln_id: str, target_subsystem_id: str):
        """Import a shared vulnerability into a system."""
        system = self.systems.get(system_id)
        if not system:
            print(f"✗ System not found: {system_id}")
            return False
        
        shared_vuln = self.repo.get(shared_vuln_id)
        if not shared_vuln:
            print(f"✗ Shared vulnerability not found: {shared_vuln_id}")
            return False
        
        try:
            imported = system.import_shared_vulnerability(shared_vuln, target_subsystem_id)
            print(f"✓ Imported: {imported.cve_id}")
            print(f"  Into: {system.system_class.name} -> {target_subsystem_id}")
            print(f"  Source: SHARED")
            print(f"  Original author: {shared_vuln.author_user_id}")
            return True
        except ValueError as e:
            print(f"✗ Error: {e}")
            return False
    
    def vote(self, shared_vuln_id: str, direction: str):
        """Vote on a shared vulnerability."""
        if direction not in ['up', 'down']:
            print("✗ Direction must be 'up' or 'down'")
            return False
        
        if direction == 'up':
            result = self.repo.upvote(shared_vuln_id)
        else:
            result = self.repo.downvote(shared_vuln_id)
        
        if result:
            print(f"✓ Voted {direction}: {shared_vuln_id}")
            print(f"  New votes: {result.votes}")
            return True
        else:
            print(f"✗ Vulnerability not found: {shared_vuln_id}")
            return False
    
    # Repository Statistics
    
    def stats_repo(self):
        """Show repository statistics."""
        total = self.repo.count()
        print(f"Repository Statistics:")
        print(f"  Total vulnerabilities: {total}")
        
        if total == 0:
            return
        
        all_vulns = self.repo.list_all()
        
        # By source
        sources = {}
        for v in all_vulns:
            prefix = v.cve_id.split('-')[0]
            sources[prefix] = sources.get(prefix, 0) + 1
        
        print(f"  By CVE prefix:")
        for prefix, count in sorted(sources.items()):
            print(f"    {prefix}-*: {count}")
        
        # Top voted
        top_voted = self.repo.get_top_voted(limit=5)
        if top_voted:
            print(f"\n  Top voted:")
            for v in top_voted:
                print(f"    {v.cve_id}: {v.votes} votes")
    
    def stats_user(self, user_id: str):
        """Show user statistics."""
        user = self.user_manager.get(user_id)
        if not user:
            print(f"✗ User not found: {user_id}")
            return False
        
        published = self.repo.get_by_author(user_id)
        
        print(f"User Statistics: {user.username}")
        print(f"  Published vulnerabilities: {len(published)}")
        
        if published:
            total_votes = sum(v.votes for v in published)
            print(f"  Total votes received: {total_votes}")
            print(f"  Average votes: {total_votes / len(published):.1f}")
            
            print(f"\n  Published:")
            for v in published:
                print(f"    • {v.cve_id}: {v.votes} votes")
        
        return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Collaboration CLI for patch prioritization framework'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # User commands
    user_parser = subparsers.add_parser('user', help='User management')
    user_sub = user_parser.add_subparsers(dest='subcommand')
    
    user_create = user_sub.add_parser('create', help='Create a user')
    user_create.add_argument('user_id', help='User ID')
    user_create.add_argument('username', help='Username')
    user_create.add_argument('email', help='Email address')
    user_create.add_argument('system_id', help='System ID')
    
    user_list = user_sub.add_parser('list', help='List users')
    user_list.add_argument('--pattern', help='Search pattern')
    
    user_info = user_sub.add_parser('info', help='Show user info')
    user_info.add_argument('identifier', help='User ID, username, or email')
    
    user_delete = user_sub.add_parser('delete', help='Delete a user')
    user_delete.add_argument('user_id', help='User ID')
    
    # System commands
    system_parser = subparsers.add_parser('system', help='System management')
    system_sub = system_parser.add_subparsers(dest='subcommand')
    
    system_load = system_sub.add_parser('load', help='Load a system')
    system_load.add_argument('config_file', help='Configuration file path')
    system_load.add_argument('--user', help='Override owner user ID')
    
    system_list = system_sub.add_parser('list', help='List systems')
    
    system_info = system_sub.add_parser('info', help='Show system info')
    system_info.add_argument('system_id', help='System ID')
    
    # Vulnerability commands
    publish_parser = subparsers.add_parser('publish', help='Publish a vulnerability')
    publish_parser.add_argument('system_id', help='Source system ID')
    publish_parser.add_argument('cve_id', help='CVE ID to publish')
    publish_parser.add_argument('subsystem_type', help='Generic subsystem type')
    publish_parser.add_argument('--metrics', help='Game theory metrics (JSON)')
    
    search_parser = subparsers.add_parser('search', help='Search vulnerabilities')
    search_parser.add_argument('--author', help='Filter by author user ID')
    search_parser.add_argument('--type', dest='subsystem_type', help='Filter by subsystem type')
    search_parser.add_argument('--min-votes', type=int, help='Minimum votes')
    search_parser.add_argument('--cve-prefix', help='CVE prefix (e.g., CVE-2024)')
    
    import_parser = subparsers.add_parser('import', help='Import a vulnerability')
    import_parser.add_argument('system_id', help='Target system ID')
    import_parser.add_argument('shared_vuln_id', help='Shared vulnerability ID')
    import_parser.add_argument('target_subsystem_id', help='Target subsystem ID')
    
    vote_parser = subparsers.add_parser('vote', help='Vote on a vulnerability')
    vote_parser.add_argument('shared_vuln_id', help='Shared vulnerability ID')
    vote_parser.add_argument('direction', choices=['up', 'down'], help='Vote direction')
    
    # Statistics commands
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_sub = stats_parser.add_subparsers(dest='subcommand')
    
    stats_repo = stats_sub.add_parser('repo', help='Repository statistics')
    
    stats_user = stats_sub.add_parser('user', help='User statistics')
    stats_user.add_argument('user_id', help='User ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = CollaborationCLI()
    
    # Route commands
    if args.command == 'user':
        if args.subcommand == 'create':
            cli.user_create(args.user_id, args.username, args.email, args.system_id)
        elif args.subcommand == 'list':
            cli.user_list(args.pattern)
        elif args.subcommand == 'info':
            cli.user_info(args.identifier)
        elif args.subcommand == 'delete':
            cli.user_delete(args.user_id)
        else:
            user_parser.print_help()
    
    elif args.command == 'system':
        if args.subcommand == 'load':
            cli.system_load(args.config_file, args.user)
        elif args.subcommand == 'list':
            cli.system_list()
        elif args.subcommand == 'info':
            cli.system_info(args.system_id)
        else:
            system_parser.print_help()
    
    elif args.command == 'publish':
        cli.publish(args.system_id, args.cve_id, args.subsystem_type, args.metrics)
    
    elif args.command == 'search':
        cli.search(args.author, args.subsystem_type, args.min_votes, args.cve_prefix)
    
    elif args.command == 'import':
        cli.import_vuln(args.system_id, args.shared_vuln_id, args.target_subsystem_id)
    
    elif args.command == 'vote':
        cli.vote(args.shared_vuln_id, args.direction)
    
    elif args.command == 'stats':
        if args.subcommand == 'repo':
            cli.stats_repo()
        elif args.subcommand == 'user':
            cli.stats_user(args.user_id)
        else:
            stats_parser.print_help()


if __name__ == '__main__':
    main()
