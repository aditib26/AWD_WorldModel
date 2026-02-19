# 🤖 Enable Conversational LLM

Your system is **ready for conversational AI**, but needs an OpenAI API key to activate it.

## Quick Setup (2 steps)

### 1. Get OpenAI API Key
- Go to: https://platform.openai.com/api-keys
- Create account or sign in
- Click "Create new secret key"
- Copy the key (starts with `sk-`)

### 2. Set Environment Variable

**Option A - Terminal (temporary, this session only):**
```bash
export OPENAI_API_KEY="sk-your-actual-key-here"
python3 -m water_mgmt.api
```

**Option B - .env file (permanent, recommended):**
```bash
# Create .env file in project root
echo 'OPENAI_API_KEY=sk-your-actual-key-here' > .env

# Install python-dotenv
pip3 install python-dotenv

# Then start server
python3 -m water_mgmt.api
```

**Option C - Add to shell profile (permanent):**
```bash
# Add to ~/.zshrc or ~/.bash_profile
echo 'export OPENAI_API_KEY="sk-your-actual-key-here"' >> ~/.zshrc
source ~/.zshrc

# Then start server
python3 -m water_mgmt.api
```

## Verify It's Working

When you start the server, you should see:
```
Extractor: LLM (gpt-4o)
```

Instead of:
```
Warning: No OpenAI API key found, using mock extractor
Extractor: Mock
```

## Test Conversational AI

Once activated, try these in the chat:
- "Should I irrigate today?"
- "What is AWD?"
- "Tell me about rice growth stages"
- "How do I know when to water?"

The AI will give **real conversational responses** powered by GPT-4o! 🎉

## Cost Estimate

- Typical conversation: $0.01 - 0.05 per exchange
- Most farming questions: < $0.02
- Budget: ~$10 = 500+ conversations

## Troubleshooting

**Still seeing "Mock"?**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Should output: sk-proj-...
# If empty, the key isn't set correctly
```

**API Error?**
- Check your OpenAI account has credits
- Verify key is copied correctly (no extra spaces)
- Try creating a new key
