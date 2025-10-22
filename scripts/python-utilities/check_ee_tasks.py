#!/usr/bin/env python3
"""
Check Earth Engine tasks status
"""

import ee
import time
from datetime import datetime

def check_tasks():
    """Check and display Earth Engine tasks"""
    
    print("Checking Earth Engine tasks...\n")
    
    try:
        # Try to initialize - you may need to authenticate first
        try:
            ee.Initialize()
        except:
            print("Trying with project ID...")
            ee.Initialize(project='ee-bbofori90')
            
        # Get all tasks
        tasks = ee.batch.Task.list()
        
        if not tasks:
            print("No tasks found in the task queue.")
            print("\nPossible reasons:")
            print("1. All tasks have completed and been cleared (tasks are removed after 10 days)")
            print("2. Tasks are associated with a different project")
            print("3. You need to authenticate: run 'earthengine authenticate'")
            return
            
        print(f"Total tasks found: {len(tasks)}")
        
        # Count by status
        status_count = {'READY': 0, 'RUNNING': 0, 'COMPLETED': 0, 'FAILED': 0, 'CANCELLED': 0}
        ndwi_tasks = []
        ndmi_tasks = []
        
        for task in tasks:
            status = task.state
            status_count[status] = status_count.get(status, 0) + 1
            
            # Check if it's an NDWI or NDMI task
            desc = task.config.get('description', '')
            if 'NDWI' in desc:
                ndwi_tasks.append((desc, status))
            elif 'NDMI' in desc:
                ndmi_tasks.append((desc, status))
        
        # Display summary
        print("\nTask Status Summary:")
        print("-" * 30)
        for status, count in status_count.items():
            if count > 0:
                print(f"{status}: {count}")
        
        # Display NDWI/NDMI specific tasks
        if ndwi_tasks or ndmi_tasks:
            print("\nNigeria Index Export Tasks:")
            print("-" * 50)
            
            all_index_tasks = [(desc, status, 'NDWI') for desc, status in ndwi_tasks] + \
                             [(desc, status, 'NDMI') for desc, status in ndmi_tasks]
            
            # Sort by description to group by date
            all_index_tasks.sort(key=lambda x: x[0])
            
            for desc, status, index_type in all_index_tasks:
                if status == 'COMPLETED':
                    print(f"✓ {desc}: {status}")
                elif status == 'RUNNING':
                    print(f"⏳ {desc}: {status}")
                elif status == 'FAILED':
                    print(f"❌ {desc}: {status}")
                else:
                    print(f"• {desc}: {status}")
        
        # Show most recent tasks
        print("\nMost Recent Tasks (all types):")
        print("-" * 50)
        for i, task in enumerate(tasks[:10]):
            desc = task.config.get('description', 'No description')
            status = task.state
            task_type = task.task_type
            
            # Try to get creation time
            creation_time = task.config.get('creationTime', 'Unknown')
            
            print(f"{i+1}. {desc}")
            print(f"   Status: {status} | Type: {task_type}")
            
    except Exception as e:
        print(f"Error accessing tasks: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you're authenticated: earthengine authenticate")
        print("2. Check you're using the correct project")
        print("3. Try the web interface: https://code.earthengine.google.com/tasks")

if __name__ == "__main__":
    check_tasks()
    
    print("\n" + "="*50)
    print("Alternative: Check your Google Drive")
    print("="*50)
    print("Your exported files should be in:")
    print("Google Drive > Nigeria_Raster_Indices folder")
    print("\nCompleted exports will appear there even if not shown in task manager.")