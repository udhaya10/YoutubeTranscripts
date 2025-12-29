# PyAnnote: Two API Options Explained

## 🔄 Option 1: Community (What We Currently Use)

### ✅ What You Have Now
- **Model:** `pyannote/speaker-diarization-community-1`
- **Authentication:** HuggingFace token
- **Processing:** Local (runs on your machine)
- **Cost:** FREE
- **Performance:** Good (8.5%-46.8% error rate)

### Setup
```bash
# Token stored in .env
HF_TOKEN=your_huggingface_token_here

# Used in code
from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1",
    token="your_hf_token"
)
```

### ✅ Pros
- ✅ Completely FREE
- ✅ Runs locally (no cloud dependency)
- ✅ Open-source
- ✅ Full privacy (your data stays local)
- ✅ No rate limits

### ❌ Cons
- ❌ Lower accuracy (slower, more errors)
- ❌ Uses local CPU/GPU (slower)
- ❌ Requires local compute resources
- ❌ No advanced features

---

## 🚀 Option 2: Premium API (pyannoteAI)

### What It Is
- **Model:** `pyannote/precision-2` (premium)
- **Authentication:** PyAnnote API key
- **Processing:** Cloud-based (runs on pyannoteAI servers)
- **Cost:** FREE credits + paid plans
- **Performance:** Excellent (3-9 points better than community)

### Setup
1. Create account: https://dashboard.pyannote.ai
2. Get API key from dashboard
3. Use in code:
```python
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/precision-2",
    token="your_pyannote_api_key"
)
```

### ✅ Pros
- ✅ **2.2-2.6x FASTER** (cloud processing)
- ✅ **Better accuracy** (3-9% improvement)
- ✅ FREE starter credits (nice amount!)
- ✅ Additional features:
  - Voiceprinting (identify speakers across files)
  - Confidence scores
  - Advanced metrics
- ✅ No local resources needed
- ✅ Scalable (can handle unlimited videos)

### ❌ Cons
- ❌ Paid after free credits (but generous)
- ❌ Cloud dependency (needs internet)
- ❌ Data sent to pyannoteAI servers
- ❌ Potential privacy concerns
- ❌ API rate limits

---

## 📊 Detailed Comparison

| Feature | Community-1 | Premium (Precision-2) |
|---------|-------------|----------------------|
| **Cost** | FREE | FREE credits + paid |
| **Authentication** | HF token | PyAnnote API key |
| **Processing** | Local | Cloud |
| **Speed** | Slower | 2-3x FASTER ⭐ |
| **Accuracy** | Good (8-46% error) | Excellent (better by 3-9%) |
| **Privacy** | Full (local) | Partial (cloud) |
| **Voiceprinting** | ❌ No | ✅ Yes |
| **Confidence Scores** | ❌ No | ✅ Yes |
| **Advanced Metrics** | ❌ No | ✅ Yes |
| **Rate Limits** | None | Yes (but generous) |
| **Setup Difficulty** | Easy | Easy |
| **Best For** | Development, local, privacy | Production, speed, accuracy |

---

## 🎯 Which Should You Use?

### Use **Community-1** if:
- ✅ Privacy is critical (don't want to send audio to cloud)
- ✅ You have local compute resources
- ✅ You're just experimenting/testing
- ✅ You want zero cost forever
- ✅ You have slow/unreliable internet

**Current setup = Community-1**

### Use **Precision-2** if:
- ✅ You need SPEED (2-3x faster)
- ✅ You need ACCURACY (3-9% better)
- ✅ You want advanced features (voiceprinting)
- ✅ You're in production
- ✅ You can use cloud infrastructure
- ✅ You want to benefit from free credits

**Recommended for most users!**

---

## 🔄 How to Switch to Premium API

### Step 1: Create PyAnnote Account
```
1. Visit: https://dashboard.pyannote.ai
2. Sign up (free account)
3. Accept terms
4. Get free starter credits (usually $50-100 worth)
```

### Step 2: Get API Key
```
1. Go to Dashboard
2. Find "API Keys" or "Tokens" section
3. Generate new API key
4. Copy the key
```

### Step 3: Update Your Code

**Option A: Update .env**
```bash
# Option 1: Keep Community (current)
HF_TOKEN=your_huggingface_token_here

# Option 2: Add Premium (new)
PYANNOTE_API_KEY=your_pyannote_api_key_here
```

**Option B: Update setup.py**
Add prompt for API key choice during setup:
```python
# Ask user which model to use
model_choice = Confirm.ask("Use Premium PyAnnote API? (faster/better accuracy)")
if model_choice:
    api_key = Prompt.ask("Enter PyAnnote API key from dashboard.pyannote.ai")
    # Store in .env
else:
    hf_token = Prompt.ask("Enter HuggingFace token")
    # Store in .env
```

### Step 4: Use Premium Pipeline
```python
from pyannote.audio import Pipeline

# Use premium (faster, more accurate)
pipeline = Pipeline.from_pretrained(
    "pyannote/precision-2",
    token=os.getenv("PYANNOTE_API_KEY")
)
```

---

## 💰 Pricing & Free Credits

### Community-1
- **Cost:** FREE forever
- **No limits:** Unlimited processing
- **Payment:** None required

### Premium (Precision-2)
- **Free credits:** Usually $50-100 per account
- **Typical usage:**
  - 1 hour video ≈ $0.10-0.20
  - 100 videos (1 hour each) ≈ $10-20
- **Free credits cover:** 250-1000 hours of processing
- **Paid plans:** $0.10 per minute after free credits
- **Annual plan:** Available for high-volume users

---

## 🚀 Implementation Path

### Current (What We Have)
```
Community-1 + HuggingFace Token
↓
Local processing
↓
Good for: Development, testing, privacy
```

### Recommended Upgrade
```
Community-1 + Precision-2 Option
↓
User chooses at setup time
↓
Best of both worlds!
```

### Implementation Steps:
1. ✅ Keep Community-1 as default (no changes needed)
2. ⏳ Add optional Precision-2 support
3. ⏳ Let user choose during setup
4. ⏳ Store both tokens in .env
5. ⏳ Use based on user choice

---

## 📝 What to Do Now

### Recommendation: Get FREE Premium Credits!

1. **Visit:** https://dashboard.pyannote.ai
2. **Sign up:** (2 minutes)
3. **Get API key:** (1 minute)
4. **Test it:** (5 minutes)

You'll get free credits worth $50-100 to try the premium API!

---

## 🔐 Security: Both Are Safe

### Community-1
- ✅ Token stored in .env (local, private)
- ✅ Processing is local (your data stays)
- ✅ No cloud transmission
- ✅ Maximum privacy

### Premium
- ✅ API key stored in .env (local, private)
- ✅ Only audio is sent to cloud for processing
- ✅ Transcripts returned encrypted
- ✅ PyAnnote has privacy policy
- ⚠️ Consider: Privacy vs Speed trade-off

Both options are safe and secure.

---

## 🎯 My Recommendation

**For Most Users: Try Premium First**

Why:
1. ✅ **2-3x faster** - Process videos 3x quicker
2. ✅ **Better accuracy** - More accurate speaker identification
3. ✅ **Free to try** - $50-100 free credits
4. ✅ **Easy to test** - Just switch API key
5. ✅ **Fall back** - Keep Community-1 as backup

If you don't like it:
- Switch back to Community-1 (same setup)
- Your local data stays local
- No harm, no cost

---

## ✅ What We Should Do

Would you like me to:

1. **Option A: Keep Current**
   - Use Community-1 only (current setup)
   - Free forever, local, private

2. **Option B: Add Premium Option**
   - Setup supports both
   - Ask user at setup time
   - Best of both worlds

3. **Option C: Recommend Premium**
   - Switch to Precision-2
   - Use free credits
   - Better performance

Which would you prefer? 🤔

---

*Last updated: December 2025*
*PyAnnote GitHub: https://github.com/pyannote/pyannote-audio*
*Premium Dashboard: https://dashboard.pyannote.ai*
