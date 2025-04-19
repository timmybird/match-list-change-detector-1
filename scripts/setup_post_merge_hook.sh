#!/bin/bash

# Script to set up a post-merge hook that reminds users to update their hooks
# after pulling changes

echo "Setting up post-merge hook..."

# Create the post-merge hook
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash

# Check if any hook scripts have changed
changed_files=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD scripts/)

if [ -n "$changed_files" ]; then
    echo ""
    echo "⚠️  IMPORTANT: Hook scripts have changed in this pull/merge! ⚠️"
    echo "The following files were updated:"
    echo "$changed_files"
    echo ""
    echo "Please run the following commands to update your hooks:"
    echo "  ./scripts/install_hooks.sh"
    echo ""
    echo "Or run this command to update everything:"
    echo "  ./scripts/update_environment.sh"
    echo ""
fi
EOF

# Make the hook executable
chmod +x .git/hooks/post-merge

echo "Post-merge hook installed successfully!"
echo "Now, whenever you pull changes that modify scripts, you'll be reminded to update your hooks."
