#!/usr/bin/env python3
"""Hermes Memory Compaction — deduplicate + summarize MEMORY.md and USER.md"""
import re, sys, os
from datetime import datetime

def compact_memories(profile_path: str):
    memory_file = os.path.join(profile_path, "memories", "MEMORY.md")
    user_file = os.path.join(profile_path, "memories", "USER.md")
    
    results = {}
    
    for path, label in [(memory_file, "MEMORY"), (user_file, "USER")]:
        if not os.path.exists(path):
            results[label] = "not found"
            continue
            
        with open(path) as f:
            content = f.read()
        
        # Split into entries (separated by double newline or §)
        entries = [e.strip() for e in re.split(r'\n\n|\n§\n', content) if e.strip()]
        
        # Remove duplicates (by first 50 chars similarity)
        seen = set()
        deduped = []
        for entry in entries:
            key = entry[:80].lower().strip()
            if key not in seen:
                seen.add(key)
                deduped.append(entry)
                if len(deduped) >= 30:  # max 30 entries
                    break
        
        new_content = "\n§\n".join(deduped)
        
        # Write back only if changed
        if new_content != content:
            backup = path + f".bak.{datetime.now().strftime('%Y%m%d')}"
            os.rename(path, backup)
            with open(path, 'w') as f:
                f.write(new_content)
            results[label] = f"compacted: {len(entries)} → {len(deduped)} entries (backup: {os.path.basename(backup)})"
        else:
            results[label] = f"unchanged ({len(entries)} entries)"
    
    return results

if __name__ == "__main__":
    default_path = os.path.expanduser("~/.hermes/profiles/tech_and_ai_architect")
    path = sys.argv[1] if len(sys.argv) > 1 else default_path
    results = compact_memories(path)
    for label, status in results.items():
        print(f"  {label}: {status}")
