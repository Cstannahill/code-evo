#!/usr/bin/env node

/**
 * Environment Setup Script for Code Evolution Tracker
 * 
 * This script helps you set up the correct environment configuration
 * for local development.
 */

const fs = require('fs');
const path = require('path');

const frontendEnvPath = path.join(__dirname, 'frontend', '.env.local');
const backendEnvPath = path.join(__dirname, 'backend', '.env');

function createEnvironmentFiles() {
  console.log('🔧 Setting up environment configuration...\n');

  // Create frontend .env.local if it doesn't exist
  if (!fs.existsSync(frontendEnvPath)) {
    const frontendEnvContent = `# Local development environment
VITE_API_BASE_URL=http://localhost:8080
VITE_ENVIRONMENT=development
`;
    
    fs.writeFileSync(frontendEnvPath, frontendEnvContent);
    console.log('✅ Created frontend/.env.local');
  } else {
    console.log('ℹ️  frontend/.env.local already exists');
  }

  // Create backend .env if it doesn't exist
  if (!fs.existsSync(backendEnvPath)) {
    const backendEnvContent = `# Backend environment configuration
# Add your API keys here for development

# OpenAI API Key (optional)
# OPENAI_API_KEY=your_openai_key_here

# Anthropic API Key (optional)
# ANTHROPIC_API_KEY=your_anthropic_key_here

# MongoDB connection (optional - will use default if not set)
# MONGODB_URL=mongodb://localhost:27017/code_evolution

# Disable Ollama discovery in Railway environment
DISABLE_OLLAMA_DISCOVERY=1
`;
    
    fs.writeFileSync(backendEnvPath, backendEnvContent);
    console.log('✅ Created backend/.env');
  } else {
    console.log('ℹ️  backend/.env already exists');
  }

  console.log('\n🎯 Environment setup complete!');
  console.log('\n📋 Next steps:');
  console.log('1. Start the backend: cd backend && python -m uvicorn app.main:app --reload');
  console.log('2. Start the frontend: cd frontend && npm run dev');
  console.log('3. Open http://localhost:3001 in your browser');
  console.log('\n💡 The frontend will automatically connect to your local backend.');
  console.log('   For production builds, it will use the Railway backend by default.');
}

// Check if we're in the right directory
if (!fs.existsSync('frontend') || !fs.existsSync('backend')) {
  console.error('❌ Error: Please run this script from the project root directory.');
  console.error('   Make sure you can see both "frontend" and "backend" folders.');
  process.exit(1);
}

createEnvironmentFiles();
