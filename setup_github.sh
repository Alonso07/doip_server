#!/bin/bash

# GitHub Repository Setup Script for DoIP Server
# This script helps you set up your GitHub repository with the correct configuration

echo "🚀 GitHub Repository Setup for DoIP Server"
echo "=========================================="

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ Username cannot be empty. Exiting."
    exit 1
fi

echo ""
echo "📝 Updating configuration files with your GitHub username..."

# Update README badges
sed -i.bak "s/YOUR_USERNAME/$GITHUB_USERNAME/g" README.md

# Update Dependabot configuration
sed -i.bak "s/YOUR_USERNAME/$GITHUB_USERNAME/g" .github/dependabot.yml

# Update issue templates
sed -i.bak "s/YOUR_USERNAME/$GITHUB_USERNAME/g" .github/ISSUE_TEMPLATE/bug_report.md
sed -i.bak "s/YOUR_USERNAME/$GITHUB_USERNAME/g" .github/ISSUE_TEMPLATE/feature_request.md

# Update PR template
sed -i.bak "s/YOUR_USERNAME/$GITHUB_USERNAME/g" .github/pull_request_template.md

# Remove backup files
rm -f README.md.bak .github/dependabot.yml.bak .github/ISSUE_TEMPLATE/*.bak .github/pull_request_template.md.bak

echo "✅ Configuration files updated!"
echo ""
echo "📋 Next steps:"
echo "1. Create a new repository on GitHub named 'doip_server'"
echo "2. Add the remote origin:"
echo "   git remote add origin https://github.com/$GITHUB_USERNAME/doip_server.git"
echo "3. Push your code:"
echo "   git push -u origin main"
echo ""
echo "🎯 Your GitHub Actions will automatically run on the first push!"
echo ""
echo "🔗 Repository URL will be: https://github.com/$GITHUB_USERNAME/doip_server"
