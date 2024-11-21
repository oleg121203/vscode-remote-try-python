#!/bin/bash

# Check if there are any changes
if [[ -z $(git status -s) ]]; then
    echo "No changes to commit"
    exit 0
fi

# Add all changes
git add .

# Create commit with timestamp
commit_msg="Auto-commit $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$commit_msg"

# Push changes
if git push; then
    echo "Successfully pushed changes"
else
    echo "Failed to push changes"
    exit 1
fi
