#!/usr/bin/env python3
"""
mod2fix - Minecraft Mod Error Analyzer & Dependency Resolver
Diagnose mod crashes, check dependencies, and get direct download links
"""

import re
import sys
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  'requests' not installed. Online features disabled.")

try:
    import tomli
    TOMLI_AVAILABLE = True
except ImportError:
    TOMLI_AVAILABLE = False
    print("⚠️  'tomli' not installed. Some Forge mods may not be readable.")

__version__ = "1.0.0"

@dataclass
class ModInfo:
    """Store mod information"""
    mod_id: str
    name: str
    version: str
    loader: str
    minecraft_version: List[str]
    dependencies: List[Dict[str, str]]
    file_path: str
    
    def __str__(self):
        return f"{self.name} ({self.mod_id}) v{self.version}"


class ModrinthAPI:
    """Interface with Modrinth API for mod downloads"""
    
    BASE_URL = "https://api.modrinth.com/v2"
    
    @staticmethod
    def search_mod(mod_id: str, limit: int = 1) -> Optional[Dict]:
        """Search for a mod by ID or name"""
        if not REQUESTS_AVAILABLE:
            return None
            
        try:
            url = f"{ModrinthAPI.BASE_URL}/search"
            params = {"query": mod_id, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('hits'):
                    return data['hits'][0]
        except Exception as e:
            print(f"⚠️  Modrinth API error: {e}")
        return None
    
    @staticmethod
    def get_mod_versions(project_id: str, minecraft_version: str = None, loader: str = None) -> List[Dict]:
        """Get mod versions filtered by MC version and loader"""
        if not REQUESTS_AVAILABLE:
            return []
            
        try:
            url = f"{ModrinthAPI.BASE_URL}/project/{project_id}/version"
            params = {}
            
            if minecraft_version:
                params['game_versions'] = f'["{minecraft_version}"]'
            if loader:
                params['loaders'] = f'["{loader.lower()}"]'
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️  Error fetching versions: {e}")
        return []
    
    @staticmethod
    def get_best_version(mod_id: str, minecraft_version: str, loader: str) -> Optional[Dict]:
        """Get the best matching version for a mod"""
        mod_info = ModrinthAPI.search_mod(mod_id)
        if not mod_info:
            return None
        
        project_id = mod_info.get('project_id') or mod_info.get('slug')
        versions = ModrinthAPI.get_mod_versions(project_id, minecraft_version, loader)
        
        if versions:
            # Return the first version (most recent)
            version = versions[0]
            
            # Get primary file
            files = version.get('files', [])
            primary_file = next((f for f in files if f.get('primary')), files[0] if files else None)
            
            return {
                'name': mod_info.get('title'),
                'slug': mod_info.get('slug'),
                'project_id': project_id,
                'version_number': version.get('version_number'),
                'version_id': version.get('id'),
                'minecraft_versions': version.get('game_versions', []),
                'loaders': version.get('loaders', []),
                'download_url': primary_file.get('url') if primary_file else None,
                'page_url': f"https://modrinth.com/mod/{mod_info.get('slug')}",
                'version_url': f"https://modrinth.com/mod/{mod_info.get('slug')}/version/{version.get('id')}"
            }
        
        return {
            'name': mod_info.get('title'),
            'slug': mod_info.get('slug'),
            'page_url': f"https://modrinth.com/mod/{mod_info.get('slug')}"
        }


class CurseForgeAPI:
    """Interface with CurseForge API (requires API key)"""
    
    BASE_URL = "https://api.curseforge.com/v1"
    API_KEY = None  # Users can set this
    
    @staticmethod
    def search_mod(mod_name: str) -> Optional[Dict]:
        """Search CurseForge for a mod"""
        if not REQUESTS_AVAILABLE or not CurseForgeAPI.API_KEY:
            return None
        
        try:
            headers = {"x-api-key": CurseForgeAPI.API_KEY}
            url = f"{CurseForgeAPI.BASE_URL}/mods/search"
            params = {"gameId": 432, "searchFilter": mod_name}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    return data['data'][0]
        except Exception:
            pass
        return None


class DependencyChecker:
    """Check mod dependencies from mod files"""
    
    def __init__(self, mods_folder: Optional[Path] = None):
        self.mods_folder = mods_folder
        self.mod_cache = {}
        self.minecraft_version = None
        self.loader_type = None
        
    def read_fabric_mod(self, jar_path: Path) -> Optional[ModInfo]:
        """Read Fabric mod metadata"""
        try:
            with zipfile.ZipFile(jar_path, 'r') as zip_file:
                if 'fabric.mod.json' not in zip_file.namelist():
                    return None
                    
                with zip_file.open('fabric.mod.json') as f:
                    data = json.load(f)
                
                dependencies = []
                deps_data = data.get('depends', {})
                deps_data.update(data.get('requires', {}))
                
                for dep_id, version in deps_data.items():
                    if dep_id in ['java']:
                        continue
                    dependencies.append({
                        'id': dep_id,
                        'version': version if isinstance(version, str) else str(version),
                        'required': True
                    })
                
                for dep_id, version in data.get('recommends', {}).items():
                    dependencies.append({
                        'id': dep_id,
                        'version': version if isinstance(version, str) else str(version),
                        'required': False
                    })
                
                mc_versions = self._parse_mc_version(deps_data.get('minecraft', '*'))
                
                return ModInfo(
                    mod_id=data.get('id', 'unknown'),
                    name=data.get('name', jar_path.stem),
                    version=data.get('version', 'unknown'),
                    loader='fabric',
                    minecraft_version=mc_versions,
                    dependencies=dependencies,
                    file_path=str(jar_path)
                )
        except Exception as e:
            pass
        return None
    
    def read_forge_mod(self, jar_path: Path) -> Optional[ModInfo]:
        """Read Forge mod metadata"""
        try:
            with zipfile.ZipFile(jar_path, 'r') as zip_file:
                # Modern Forge (1.13+)
                if 'META-INF/mods.toml' in zip_file.namelist():
                    with zip_file.open('META-INF/mods.toml') as f:
                        content = f.read().decode('utf-8')
                        
                    if TOMLI_AVAILABLE:
                        data = tomli.loads(content)
                    else:
                        return self._parse_forge_toml_manual(content, jar_path)
                    
                    mods_list = data.get('mods', [])
                    if not mods_list:
                        return None
                    
                    mod_data = mods_list[0]
                    mod_id = mod_data.get('modId', 'unknown')
                    
                    dependencies = []
                    for dep in data.get('dependencies', {}).get(mod_id, []):
                        if dep.get('modId') in ['forge', 'java']:
                            continue
                        dependencies.append({
                            'id': dep.get('modId', 'unknown'),
                            'version': dep.get('versionRange', '*'),
                            'required': dep.get('mandatory', True)
                        })
                    
                    mc_version = self._get_forge_mc_version(data)
                    
                    return ModInfo(
                        mod_id=mod_id,
                        name=mod_data.get('displayName', jar_path.stem),
                        version=mod_data.get('version', 'unknown'),
                        loader='forge',
                        minecraft_version=self._parse_mc_version(mc_version),
                        dependencies=dependencies,
                        file_path=str(jar_path)
                    )
                
                # Old Forge (1.12.2 and earlier)
                elif 'mcmod.info' in zip_file.namelist():
                    with zip_file.open('mcmod.info') as f:
                        content = f.read().decode('utf-8')
                        # Handle malformed JSON
                        content = re.sub(r',\s*}', '}', content)
                        content = re.sub(r',\s*]', ']', content)
                        data = json.loads(content)
                    
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    elif isinstance(data, dict) and 'modList' in data:
                        data = data['modList'][0] if data['modList'] else {}
                    
                    dependencies = []
                    for dep in data.get('requiredMods', []):
                        if isinstance(dep, str):
                            dependencies.append({
                                'id': dep,
                                'version': '*',
                                'required': True
                            })
                    
                    return ModInfo(
                        mod_id=data.get('modid', 'unknown'),
                        name=data.get('name', jar_path.stem),
                        version=data.get('version', 'unknown'),
                        loader='forge',
                        minecraft_version=self._parse_mc_version(data.get('mcversion', '*')),
                        dependencies=dependencies,
                        file_path=str(jar_path)
                    )
        except Exception as e:
            pass
        return None
    
    def _parse_forge_toml_manual(self, content: str, jar_path: Path) -> Optional[ModInfo]:
        """Fallback TOML parser"""
        try:
            mod_id = re.search(r'modId\s*=\s*["\']([^"\']+)["\']', content)
            name = re.search(r'displayName\s*=\s*["\']([^"\']+)["\']', content)
            version = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            
            return ModInfo(
                mod_id=mod_id.group(1) if mod_id else 'unknown',
                name=name.group(1) if name else jar_path.stem,
                version=version.group(1) if version else 'unknown',
                loader='forge',
                minecraft_version=['*'],
                dependencies=[],
                file_path=str(jar_path)
            )
        except:
            return None
    
    def _get_forge_mc_version(self, data: dict) -> str:
        """Extract MC version from Forge data"""
        deps = data.get('dependencies', {})
        for mod_deps in deps.values():
            for dep in mod_deps:
                if dep.get('modId') == 'minecraft':
                    return dep.get('versionRange', '*')
        return '*'
    
    def _parse_mc_version(self, version_str: str) -> List[str]:
        """Parse Minecraft version string"""
        if not version_str or version_str == '*':
            return ['*']
        versions = re.findall(r'\d+\.\d+(?:\.\d+)?', str(version_str))
        return versions if versions else ['*']
    
    def scan_mods_folder(self, folder_path: Path) -> List[ModInfo]:
        """Scan mods folder"""
        mods = []
        
        if not folder_path.exists():
            print(f"❌ Mods folder not found: {folder_path}")
            return mods
        
        jar_files = list(folder_path.glob("*.jar"))
        print(f"📁 Scanning {len(jar_files)} mod files...")
        
        loader_count = {'fabric': 0, 'forge': 0}
        mc_version_count = defaultdict(int)
        
        for jar_file in jar_files:
            mod_info = self.read_fabric_mod(jar_file) or self.read_forge_mod(jar_file)
            
            if mod_info:
                mods.append(mod_info)
                self.mod_cache[mod_info.mod_id] = mod_info
                loader_count[mod_info.loader] += 1
                
                for v in mod_info.minecraft_version:
                    if v != '*':
                        mc_version_count[v] += 1
        
        # Detect most common loader and MC version
        self.loader_type = max(loader_count, key=loader_count.get) if mods else None
        self.minecraft_version = max(mc_version_count, key=mc_version_count.get) if mc_version_count else None
        
        if self.minecraft_version:
            print(f"🎮 Detected Minecraft version: {self.minecraft_version}")
        if self.loader_type:
            print(f"🔧 Detected loader: {self.loader_type.upper()}")
        
        return mods
    
    def check_dependencies(self, mods: List[ModInfo]) -> Dict[str, List[Dict]]:
        """Check for missing dependencies with download links"""
        installed_ids = {mod.mod_id for mod in mods}
        missing_deps = defaultdict(list)
        
        for mod in mods:
            for dep in mod.dependencies:
                if dep['required'] and dep['id'] not in installed_ids:
                    if dep['id'] not in ['fabricloader', 'fabric', 'forge', 'minecraft']:
                        # Get download info
                        download_info = None
                        if REQUESTS_AVAILABLE and self.minecraft_version and self.loader_type:
                            download_info = ModrinthAPI.get_best_version(
                                dep['id'], 
                                self.minecraft_version, 
                                self.loader_type
                            )
                        
                        missing_deps[mod.mod_id].append({
                            **dep,
                            'download_info': download_info
                        })
        
        return missing_deps
    
    def create_dependency_tree(self, mods: List[ModInfo]) -> str:
        """Create dependency tree"""
        lines = []
        lines.append("\n📦 DEPENDENCY TREE")
        lines.append("=" * 80)
        
        installed_ids = {mod.mod_id for mod in mods}
        
        for mod in sorted(mods, key=lambda m: m.name):
            lines.append(f"\n📘 {mod.name} ({mod.mod_id}) v{mod.version}")
            lines.append(f"   Loader: {mod.loader.upper()} | MC: {', '.join(mod.minecraft_version)}")
            lines.append(f"   File: {Path(mod.file_path).name}")
            
            if mod.dependencies:
                lines.append("   Dependencies:")
                for dep in mod.dependencies:
                    if dep['id'] in ['minecraft', 'fabricloader', 'forge']:
                        continue
                    status = "✅" if dep['id'] in installed_ids else "❌"
                    req = "REQUIRED" if dep['required'] else "optional"
                    lines.append(f"      {status} {dep['id']} {dep['version']} ({req})")
            else:
                lines.append("   Dependencies: None")
        
        return '\n'.join(lines)


class ModErrorAnalyzer:
    """Analyze crash logs for mod errors"""
    
    def __init__(self):
        self.error_patterns = {
            'missing_dependency': {
                'patterns': [
                    r"(?:Mod|mod) (\S+) requires (\S+) (\S+)",
                    r"Missing (?:required )?(?:mod|dependency):? (\S+)",
                    r"requires mod (\S+)",
                    r"Unmet dependency listing.*?Mod (\S+) requires mod (\S+)",
                    r"depends on mod (\S+)",
                ],
                'reason': 'Missing required dependency',
                'solution': 'Install the required dependency mod'
            },
            'wrong_version': {
                'patterns': [
                    r"(\S+) requires (?:Minecraft )?version (\S+)",
                    r"requires Minecraft version[:\s]+(\S+)",
                    r"Mod (\S+) requires (\S+) (\S+)",
                ],
                'reason': 'Version mismatch',
                'solution': 'Update to the correct version'
            },
            'duplicate_mod': {
                'patterns': [
                    r"Duplicate mod[s]?[:\s]+(\S+)",
                    r"Found duplicate.*?(\S+)",
                ],
                'reason': 'Duplicate mod files',
                'solution': 'Remove duplicate mod from mods folder'
            },
            'mixin_error': {
                'patterns': [
                    r"Mixin.*?failed.*?(\S+)",
                    r"ERROR.*?Mixin.*?```math(\S+)```",
                ],
                'reason': 'Mixin conflict',
                'solution': 'Mod incompatibility - check for conflicting mods'
            },
            'class_not_found': {
                'patterns': [
                    r"ClassNotFoundException: (\S+)",
                    r"NoClassDefFoundError: (\S+)",
                ],
                'reason': 'Missing dependency or corrupted mod',
                'solution': 'Reinstall mod or check dependencies'
            },
            'wrong_loader': {
                'patterns': [
                    r"requires (Forge|Fabric|Quilt)",
                ],
                'reason': 'Wrong mod loader',
                'solution': 'Use the correct mod loader version'
            },
        }
    
    def analyze_log(self, log_content: str) -> List[Dict]:
        """Analyze log and find issues"""
        issues = []
        seen = set()
        
        for error_type, data in self.error_patterns.items():
            for pattern in data['patterns']:
                for match in re.finditer(pattern, log_content, re.IGNORECASE | re.MULTILINE):
                    mod_name = self._clean_name(match.groups()[0] if match.groups() else "Unknown")
                    issue_id = f"{error_type}:{mod_name}"
                    
                    if issue_id not in seen:
                        seen.add(issue_id)
                        issues.append({
                            'error_type': error_type,
                            'mod_name': mod_name,
                            'reason': data['reason'],
                            'solution': data['solution'],
                            'context': match.group(0)[:200],
                            'additional': list(match.groups()[1:]) if len(match.groups()) > 1 else []
                        })
        
        return issues
    
    def _clean_name(self, name: str) -> str:
        """Clean mod name"""
        name = re.sub(r'\.(jar|json)$', '', name)
        name = re.sub(r'^.*[\\/]', '', name)
        name = re.sub(r'[^\w\-]', '', name)
        return name or "Unknown"
    
    def format_report(self, issues: List[Dict], missing_deps: Dict = None, 
                     dep_tree: str = None, mc_version: str = None, loader: str = None) -> str:
        """Format full report"""
        report = []
        report.append("=" * 80)
        report.append("mod2fix - Diagnostic Report".center(80))
        report.append("=" * 80)
        
        if mc_version:
            report.append(f"\n🎮 Minecraft Version: {mc_version}")
        if loader:
            report.append(f"🔧 Mod Loader: {loader.upper()}")
        
        # Crash/error analysis
        if issues:
            report.append(f"\n\n🔍 ERRORS DETECTED: {len(issues)}")
            report.append("=" * 80)
            
            for i, issue in enumerate(issues, 1):
                report.append(f"\n❌ Error #{i}: {issue['error_type'].replace('_', ' ').title()}")
                report.append(f"   Mod: {issue['mod_name']}")
                report.append(f"   Reason: {issue['reason']}")
                report.append(f"   Solution: {issue['solution']}")
                if issue['additional']:
                    report.append(f"   Details: {', '.join(issue['additional'])}")
        
        # Missing dependencies
        if missing_deps:
            report.append(f"\n\n📦 MISSING DEPENDENCIES")
            report.append("=" * 80)
            
            for mod_id, deps in missing_deps.items():
                report.append(f"\n❌ {mod_id} is missing:")
                for dep in deps:
                    report.append(f"\n   📌 {dep['id']} {dep['version']}")
                    
                    if dep.get('download_info'):
                        info = dep['download_info']
                        report.append(f"      Mod: {info.get('name', dep['id'])}")
                        report.append(f"      🔗 Mod Page: {info['page_url']}")
                        
                        if info.get('version_number'):
                            report.append(f"      📦 Version: {info['version_number']} (MC: {', '.join(info.get('minecraft_versions', []))})")
                            if info.get('version_url'):
                                report.append(f"      🌐 Version Page: {info['version_url']}")
                            if info.get('download_url'):
                                report.append(f"      📥 Direct Download: {info['download_url']}")
                        else:
                            report.append(f"      ⚠️  No compatible version found for MC {mc_version}")
                    else:
                        report.append(f"      ⚠️  Search manually on Modrinth or CurseForge")
        
        if dep_tree:
            report.append(f"\n{dep_tree}")
        
        if not issues and not missing_deps:
            report.append("\n✅ No errors or missing dependencies detected!")
        
        report.append("\n" + "=" * 80)
        report.append("\n💡 Tips:")
        report.append("   • Always use mods for the same Minecraft version")
        report.append("   • Don't mix Forge and Fabric mods")
        report.append("   • Check Modrinth/CurseForge for mod compatibility")
        report.append("   • Read mod descriptions for required dependencies")
        report.append("=" * 80)
        
        return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(
        description='mod2fix - Minecraft Mod Error Analyzer & Dependency Resolver',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mod2fix.py crash-2024-01-15.txt
  mod2fix.py --mods-folder ~/.minecraft/mods --find-missing
  mod2fix.py latest.log -m ./mods -f
        """
    )
    
    parser.add_argument('log_file', nargs='?', help='Crash log or latest.log file')
    parser.add_argument('-m', '--mods-folder', help='Path to mods folder')
    parser.add_argument('-f', '--find-missing', action='store_true', help='Find missing dependencies')
    parser.add_argument('-d', '--deps-only', action='store_true', help='Show dependency tree only')
    parser.add_argument('-o', '--output', help='Output file for report')
    parser.add_argument('-v', '--version', action='version', version=f'mod2fix {__version__}')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("mod2fix - Minecraft Mod Diagnostic Tool".center(80))
    print(f"Version {__version__}".center(80))
    print("=" * 80)
    
    if not REQUESTS_AVAILABLE:
        print("\n⚠️  Install 'requests' for online features: pip install requests")
    if not TOMLI_AVAILABLE:
        print("\n⚠️  Install 'tomli' for Forge mod support: pip install tomli")
    
    analyzer = ModErrorAnalyzer()
    dep_checker = DependencyChecker()
    
    mods = []
    missing_deps = None
    dep_tree = None
    issues = []
    
    # Scan mods folder
    if args.mods_folder:
        mods = dep_checker.scan_mods_folder(Path(args.mods_folder))
        print(f"✅ Found {len(mods)} mods\n")
        
        if args.find_missing:
            missing_deps = dep_checker.check_dependencies(mods)
        
        if args.deps_only:
            print(dep_checker.create_dependency_tree(mods))
            return
        
        dep_tree = dep_checker.create_dependency_tree(mods)
    
    # Analyze log
    if args.log_file:
        log_path = Path(args.log_file)
        if not log_path.exists():
            print(f"❌ File not found: {log_path}")
            sys.exit(1)
        
        print(f"📂 Analyzing: {log_path}\n")
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        issues = analyzer.analyze_log(log_content)
    
    # Generate report
    report = analyzer.format_report(
        issues, 
        missing_deps, 
        dep_tree,
        dep_checker.minecraft_version,
        dep_checker.loader_type
    )
    
    print(report)
    
    # Save report
    output_file = Path(args.output) if args.output else Path("mod2fix_report.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 Report saved: {output_file}")


if __name__ == "__main__":
    main()