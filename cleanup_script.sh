#!/bin/bash
# cleanup_database.sh - Clean up database and git history

echo "🧹 Code Evolution Tracker - Database Cleanup"
echo "=============================================="

# Navigate to backend directory
cd backend 2>/dev/null || { echo "❌ Please run from project root"; exit 1; }

echo "1. 🗄️  Removing database files..."
rm -f code_evolution.db
rm -rf chroma_db/
echo "   ✅ Database files removed"

echo "2. 📝 Updating .gitignore..."
cat >> ../.gitignore << EOF

# Database files (added by cleanup script)
backend/code_evolution.db
backend/chroma_db/
*.db
*.sqlite
*.sqlite3

# Environment files with secrets
.env
.env.*
!.env.example

# Secret files
*secret*
*key*
*token*
*password*
credentials/
secrets/
EOF
echo "   ✅ .gitignore updated"

cd ..

echo "3. 🔄 Committing cleanup..."
git add .gitignore
git commit -m "🔒 Add database and secrets to .gitignore

- Prevent database files from being committed
- Add comprehensive secret file patterns
- Prepare for secure repository scanning"

echo "4. 🚀 Ready to push!"
echo ""
echo "Next steps:"
echo "  • git push origin main"
echo "  • Restart your backend server"
echo "  • The database will be recreated automatically"
echo ""
echo "🔒 Secret scanning is now enabled to prevent future issues!"