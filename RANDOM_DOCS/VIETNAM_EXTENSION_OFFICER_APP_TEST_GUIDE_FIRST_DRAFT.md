# AIRRVie Extension Officer Guide & Test Protocol (First Draft)

**Audience**: Vietnam extension officers (10 field testers)

**Purpose**: This document has two parts:
1. **App Feature Guide** - Learn what AIRRVie does and how each component works
2. **Testing Protocol** - Structured test scenarios to validate functionality and field readiness

---

# PART 1: APP FEATURE GUIDE

## What is AIRRVie?

AIRRVie (AI Rice Research Vietnam) is a **mobile-first web application** designed to help Vietnamese rice farmers and extension officers manage farms, get real-time weather alerts, track tasks, maintain field journals, and receive AI-powered agronomic advice.

**Key technologies**:
- Qwen-32B large language model (Vietnamese + English)
- Rice disease detection (MobileNetV3 trained on Vietnamese pests/diseases)
- Voice interface (Whisper ASR + VieNeu TTS)
- Real-time weather (OpenWeather API with AI-enhanced recommendations)
- Knowledge base (RAG with Qdrant vector search)

---

## App Components Overview

### 1. Authentication & User Management

**What it does**:
- Secure login with JWT tokens
- OTP-based registration and password reset (6-digit code via email)
- **Demo mode**: Pre-filled test account for quick exploration without email verification

**Who uses it**:
- Extension officers creating accounts for themselves or farmers
- Farmers logging in on their own devices

**Key features**:
- Vietnamese + English interface
- Email-based OTP (10-minute expiry)
- Demo login: `demo@airrvie.app` / `demo123`

---

### 2. Dashboard

**What it does**:
- **Central hub** showing overview of all farms, plots, tasks, and journal entries
- Quick navigation to all app features

**What you see**:
- **My Farms & Plots**: Summary cards with farm names, locations, plot counts
- **Upcoming Tasks**: Next 5 tasks with due dates and priorities
- **Recent Journal Entries**: Last 3 entries with dates and types
- **Quick Actions**: Buttons to add journal entry, add task, ask assistant, check weather

**Who uses it**:
- Anyone who needs a quick overview of their farming operations

---

### 3. Weather

**What it does**:
- Fetches **real-time weather** for your current location (GPS or IP-based)
- Displays **5-day forecast**
- Generates **AI-enhanced farming recommendations** based on weather conditions
- Shows **alerts** for extreme conditions (heavy rain, drought, heat stress)

**Data shown**:
- **Current**: Temperature (°C), humidity (%), rainfall (mm), wind speed (km/h), condition
- **Forecast**: Daily high/low, rainfall probability, conditions
- **Visibility, sunrise, sunset** (when available)
- **Province-specific**: Can detect location down to district level for Vietnamese provinces

**How it works**:
- Uses OpenWeather API for real-time data
- Qwen AI analyzes weather patterns and suggests irrigation, fertilization, pest management timing
- Falls back to default Mekong Delta location if GPS/IP detection fails

**Who uses it**:
- Farmers planning irrigation, fertilization, spraying schedules
- Extension officers advising on weather-dependent activities

---

### 4. Tasks

**What it does**:
- **Task management** for farm activities
- Create, update, complete, and delete tasks
- Organize tasks by plot, type, and due date

**Task types**:
- Planting (gieo sạ)
- Fertilizer (bón phân)
- Irrigation (tưới nước)
- Pest control (phòng trừ sâu bệnh)
- Harvest (thu hoạch)
- Other (khác)

**What you can do**:
- Assign task to a specific plot
- Set due date and priority
- Add description/notes
- Mark as complete
- Filter by plot or search by keyword

**Who uses it**:
- Farmers managing daily/weekly farm operations
- Extension officers tracking planned activities with farmers

---

### 5. Journal

**What it does**:
- Digital **field journal** for recording daily observations and activities
- Attach **photos** (field conditions, pests, diseases, growth stages)
- Add **audio notes** (voice memos)
- Organize entries by plot and type

**Journal entry types**:
- Planting
- Fertilizer application
- Irrigation
- Pest/disease observation
- Harvest
- Other

**What you can do**:
- Create entry with date, plot, type, title, and detailed notes
- Upload multiple photos per entry
- Record audio notes (farmer observations in local dialect)
- Search and filter entries
- Edit or delete entries

**Who uses it**:
- Farmers documenting field conditions and activities
- Extension officers keeping records for multiple farmer visits
- Anyone building a historical record for compliance or analysis

---

### 6. AI Assistant

**What it does**:
- **Conversational AI** powered by Qwen-32B language model
- Answers rice farming questions in Vietnamese or English
- Retrieves knowledge from agronomic handbooks (RAG)
- Supports **3 input modes**: text, voice, image

**Key capabilities**:

#### 6a. Text Chat
- Ask questions about rice farming in natural language
- Get advice on:
  - Disease identification and treatment
  - Pest management (rầy nâu, sâu cuốn lá, etc.)
  - Fertilization timing and amounts (NPK, urea)
  - Water management (AWD, continuous flooding, rainfed)
  - Growth stages (đẻ nhánh, làm đòng, trỗ bông)
  - Variety selection (OM 5451, Jasmine 85, IR64)
- **Unit awareness**: Understands Vietnamese area units (công lớn, công nhỏ, sào, m², ha)
- **Safety filter**: Refuses non-farming questions and redirects to rice topics

#### 6b. Voice Chat
- **Speak** questions instead of typing (hands-free)
- Uses **Whisper** (OpenAI) for Vietnamese speech-to-text
- Uses **VieNeu TTS** for natural-sounding Vietnamese audio responses
- Shows transcript for verification

**How it works**:
1. Tap microphone button
2. Speak your question (5–30 seconds)
3. App transcribes your speech
4. AI generates answer
5. Answer is displayed as text + read aloud (optional)

#### 6c. Image Disease Detection
- Upload photo of rice plant (leaf, stem, or full plant)
- AI identifies:
  - **8 conditions**: Healthy, Brown Spot, Rice Blast, Brown Plant Hopper, Rice Borer, Rice Leaf Roller, Rice Gall Midge, Golden Apple Snails
- Returns:
  - Predicted disease/pest name
  - Confidence score (0–100%)
  - Treatment recommendations (cultural, biological, chemical)
  - Prevention tips

**Safety features**:
- Low confidence (<30%) → asks for clearer photo
- Conservative advice (always suggests monitoring before chemical treatment)

**Who uses it**:
- Farmers with specific questions about their fields
- Extension officers demonstrating modern advisory tools
- Anyone needing quick answers in the field

---

### 7. Profile & Settings

**What it does**:
- Manage **personal information** (name, email, phone, language)
- Configure **accessibility** (font size for older farmers or low vision)
- **Add, edit, delete farms and plots**

**Settings**:
- **Language**: Vietnamese (VI) or English (EN)
- **Font scale**: Normal, Large, Extra Large
- **Display name**: How your name appears in the app

**Farms & Plots Management**:

#### Farm details:
- Farm name (e.g., "Trang trại gia đình Nguyễn")
- Province (An Giang, Đồng Tháp, etc.)
- District
- Commune/ward
- Hamlet/village

#### Plot details:
- Plot name (e.g., "Lô lúa chính", "Ruộng sau nhà")
- Soil type: 11 Vietnamese soil types (Đất phù sa, Đất sét, Đất phèn, etc.)
- Rice variety (OM 5451, Jasmine 85, IR64, etc.)
- Sowing date
- Expected harvest date
- Irrigation method (Tưới ngập, AWD, Tự nhiên)
- Area + unit (Công lớn 1,300m², Công nhỏ 1,000m², Sào 500m², Sào 360m², m²)

**Who uses it**:
- Extension officers managing multiple farms
- Farmers updating their farm/plot information as seasons change

---

## Expected User Flows

### Flow 1: New user registration
1. Open app → Auth page
2. Choose language (EN/VI)
3. Enter email → Request OTP
4. Check email inbox → Enter 6-digit code
5. Complete profile (name, password)
6. Land on Dashboard

### Flow 2: Demo login (recommended for testing)
1. Open app → Auth page
2. Click **"Try Demo"**
3. Instantly logged in with sample data (farms, plots, tasks, journal)
4. Land on Dashboard

### Flow 3: Daily farmer workflow
1. Check **Weather** → see rain forecast
2. Go to **Assistant** → ask "Trời mưa lớn 2 ngày, tôi có nên bón phân không?"
3. Get AI advice → decide to delay fertilization
4. Go to **Tasks** → postpone fertilizer task by 3 days
5. Go to **Journal** → add entry "Hoãn bón phân vì mưa"

### Flow 4: Disease diagnosis
1. Notice yellow leaves in field
2. Open **Assistant** → Image tab
3. Take photo of affected leaf
4. Upload → get prediction (e.g., "Rice Blast Disease 87% confidence")
5. Read treatment advice
6. Go to **Tasks** → add task "Phun thuốc trị đạo ôn"

---

# PART 2: TESTING PROTOCOL

## Setup Instructions (10 minutes)

### Test Devices
Use at least one of these:
- **Mobile**: Android Chrome OR iOS Safari (recommended - app is mobile-first)
- **Laptop/Desktop**: Chrome

### Browser Permissions
When prompted, **allow** these permissions:
- **Location** → enables weather based on your current position
- **Microphone** → enables voice assistant
- **Camera / Photo library** → enables disease detection and journal photo uploads

### Test URLs
Ask your test coordinator for the correct URL. Typical options:
- `https://rice-app.pepeshanty.store`
- `https://rice-app2.pepeshanty.store`
- `https://rice-app3.pepeshanty.store`

If you receive a different URL, use that instead.

---

## Test Accounts

### Option 1: Demo Login (Recommended)
**Why**: Instant access with pre-populated sample data (farms, plots, tasks, journal entries)
**How**: On the login screen, click **"Try Demo"** button
**Credentials** (if needed): `demo@airrvie.app` / `demo123`

### Option 2: Create Your Own Account
**When to use**: If you want to test the full registration flow or OTP system
**Steps**:
1. Click "Sign Up"
2. Enter your email → Request OTP
3. Check email inbox for 6-digit code
4. Enter OTP code
5. Complete profile (name, password)
6. Login

**Note**: OTP emails may not work in all test environments. Use Demo Login if you encounter issues.

---

## How to Report Issues

When something fails or looks wrong, capture:
- **What you were trying to do**
- **Steps** (1…2…3…)
- **Expected result** vs **Actual result**
- **Screenshot/video** (phone screen recording is best)
- **Device + browser** (e.g., iPhone 13, iOS 17, Safari)
- **Network** (4G/5G/Wi‑Fi; weak/strong)
- **Time** (approx.)

### Severity levels
- **S1 (Critical)**: app won’t open; can’t login; data not saving
- **S2 (Major)**: key feature broken (assistant/voice/weather/tasks/journal)
- **S3 (Minor)**: confusing UI, translation issues, layout problems
- **S4 (Suggestion)**: improvement ideas

---

## Component-Based Test Scenarios

**Time estimate**: 60–90 minutes for all core components

Below are structured test scenarios organized by app component. Each scenario maps directly to the features described in Part 1 of this guide.

---

### TEST 1: Authentication & First Launch

**What you're testing**: Login system, demo mode, language switching

**Test steps**:
1. [ ] Open the app URL in your browser
2. [ ] Observe the login/auth screen loads correctly
3. [ ] Switch language between EN ↔ VI using the language selector
4. [ ] Verify all labels/buttons update correctly in both languages
5. [ ] Click the **"Try Demo"** button
6. [ ] Confirm you land on the **Dashboard** with sample data visible

**Expected results**:
- App loads in < 5 seconds on 4G/5G connection
- Language switch is instant with no page reload
- Demo login works without requiring email/OTP
- Dashboard displays farms, plots, tasks, and journal entries

**What to verify**:
- [ ] All Vietnamese text is natural and grammatically correct
- [ ] No English text appears when VI language is selected
- [ ] No layout overflow or broken elements on mobile screen
- [ ] Login button is easily tappable on mobile devices

---

### TEST 2: Dashboard Overview

**What you're testing**: Central hub functionality, data display, quick navigation

**Test steps**:
1. [ ] Observe the **My Farms & Plots** section
2. [ ] Count farms and plots shown (demo should have ≥1 of each)
3. [ ] Check the **Upcoming Tasks** section displays tasks with due dates
4. [ ] Check the **Recent Journal Entries** section shows recent entries
5. [ ] Test each **Quick Action** button:
   - [ ] "Add Journal Entry" → navigates to Journal page
   - [ ] "Add Task" → navigates to Tasks page
   - [ ] "Ask Assistant" → navigates to Assistant page
   - [ ] "Check Weather" → navigates to Weather page

**Expected results**:
- All sections display relevant data from the demo account
- Navigation is smooth with no full page reload (React routing)
- Quick action buttons are clearly labeled and responsive

**What to verify**:
- [ ] Farm/plot cards show location information correctly
- [ ] Task due dates are displayed in readable format
- [ ] Journal entry dates are formatted correctly
- [ ] All buttons are large enough for mobile tapping (minimum 44x44px tap target)

---

### TEST 3: Weather Module

**What you're testing**: Location detection, real-time weather, forecasts, AI recommendations

**Test steps**:
1. [ ] Open **Weather** from the main navigation menu
2. [ ] If prompted for location permission, **allow it**
3. [ ] Wait for weather data to load (should be < 10 seconds)
4. [ ] Observe the **Current Weather** section:
   - [ ] Temperature (°C)
   - [ ] Humidity (%)
   - [ ] Rainfall (mm)
   - [ ] Wind speed (km/h)
   - [ ] Weather condition (Clear/Cloudy/Rain/etc.)
5. [ ] Scroll down to view **5-Day Forecast**
6. [ ] Check for **Alerts** section (may be empty if conditions are normal)
7. [ ] Check **AI-Enhanced Recommendations** section
8. [ ] Tap **Refresh Weather** button and verify data updates

**Expected results**:
- Weather data loads successfully
- Location is auto-detected (GPS or IP-based) or defaults to Mekong Delta
- Current conditions and 5-day forecast are displayed
- Recommendations are farming-specific and practical

**What to verify**:
- [ ] Temperature units are Celsius
- [ ] Location name appears in Vietnamese (e.g., "An Giang, Việt Nam")
- [ ] Wind speed is in km/h (not mph)
- [ ] Recommendations mention irrigation, fertilization, or pest timing
- [ ] If location permission denied, app still shows weather (fallback location)

**Error testing**:
- [ ] If weather fails to load, take screenshot of error message
- [ ] Verify fallback behavior works (shows default location data)

---

### TEST 4: Task Management

**What you're testing**: Create, edit, complete, filter, and search tasks

**Test steps**:
1. [ ] Open **Tasks** from the main navigation menu
2. [ ] Tap the **Add Task** or "+" button
3. [ ] Fill in task details:
   - [ ] Select a plot from the dropdown menu
   - [ ] Enter task title: "Bón phân đạm đợt 2" (Second nitrogen fertilization)
   - [ ] Set due date: Tomorrow's date
   - [ ] Select task type: "Fertilizer" (Bón phân)
   - [ ] (Optional) Add description/notes
4. [ ] Save the task
5. [ ] Verify the task appears in the task list
6. [ ] Tap the checkbox to **mark the task as complete**
7. [ ] Verify task is marked done (strikethrough text or moved to completed section)
8. [ ] Test **filtering** by plot or task type
9. [ ] Test **search** functionality (type "phân" and verify it finds your fertilizer task)
10. [ ] Try editing the task (change title or due date)
11. [ ] Try deleting a task

**Expected results**:
- Task creation is smooth with no lag
- Task appears immediately in the list after saving
- Completed tasks are visually distinct from pending tasks
- Filter and search functions work correctly

**What to verify**:
- [ ] Plot dropdown shows all your available plots
- [ ] Task type dropdown displays in Vietnamese
- [ ] Date picker works correctly on mobile devices
- [ ] Tasks persist after page refresh
- [ ] Due dates display in a clear format (e.g., "Ngày mai" for tomorrow)

---

### TEST 5: Journal (Field Diary)

**What you're testing**: Create entries, upload photos/audio, search and edit entries

**Test steps**:
1. [ ] Open **Journal** from the main navigation menu
2. [ ] Tap **Add Entry** or "+" button
3. [ ] Fill in entry details:
   - [ ] Select a plot from dropdown
   - [ ] Select entry type: "Pest" (Sâu bệnh)
   - [ ] Enter title: "Phát hiện rầy nâu" (Brown plant hopper detected)
   - [ ] Enter detailed content describing observations
4. [ ] **Add a photo**:
   - [ ] Tap "Add Photo" button
   - [ ] Either take a new photo OR select from gallery
   - [ ] Verify photo thumbnail appears in the entry
5. [ ] **Add an audio note** (if available on your device):
   - [ ] Tap "Record Audio" or microphone icon
   - [ ] Record 5–10 seconds of voice notes
   - [ ] Stop recording
   - [ ] Verify audio player widget appears
6. [ ] Save the journal entry
7. [ ] Verify entry appears in the journal list
8. [ ] Tap the entry to view full details (photo and audio should be visible)
9. [ ] Test **search/filter** by plot or entry type
10. [ ] **Edit** the entry (change title or add more content)
11. [ ] **Delete** the entry (verify confirmation dialog appears)

**Expected results**:
- Entry creation is smooth
- Photos upload successfully without excessive compression
- Audio recording works on mobile devices
- Entries persist after page refresh and logout/login

**What to verify**:
- [ ] Photo quality is reasonable (can see field details clearly)
- [ ] Audio playback works correctly
- [ ] Vietnamese entry types display properly (Gieo sạ, Bón phân, Tưới nước, etc.)
- [ ] Entries are sorted by date (newest first)
- [ ] Multiple photos can be added to a single entry
- [ ] Entry timestamps are accurate

---

### TEST 6: AI Assistant - Text Chat

**What you're testing**: Vietnamese farming advice, unit awareness, safety filters

**Test steps**:
1. [ ] Open **Assistant** from the main navigation menu
2. [ ] **Test basic farming question**:
   - [ ] Type: "Lúa bị vàng lá, tôi nên làm gì?" (Yellow leaves, what should I do?)
   - [ ] Send the message
   - [ ] Wait for AI response (should be < 10 seconds)
3. [ ] **Evaluate the response**:
   - [ ] Is it relevant to the question?
   - [ ] Is the advice safe and conservative?
   - [ ] Is the Vietnamese natural and grammatically correct?
   - [ ] Does it provide actionable steps?
4. [ ] **Test Vietnamese unit awareness**:
   - [ ] Ask: "Tôi có 7 công ruộng, cần bao nhiêu phân đạm?" (I have 7 công of rice field, how much nitrogen fertilizer?)
   - [ ] Verify response mentions both **công** and converts to **m²** or **ha**
5. [ ] **Test safety filter** (non-farming question):
   - [ ] Ask: "Cách nấu phở bò?" (How to cook beef pho?)
   - [ ] Verify assistant **refuses politely** and redirects to rice farming topics
6. [ ] **Test technical question**:
   - [ ] Ask: "Bệnh đạo ôn xuất hiện khi nào?" (When does rice blast disease appear?)
   - [ ] Check if response cites sources or handbooks

**Expected results**:
- Responses load within 10 seconds
- Advice is practical, field-relevant, and safe
- Assistant refuses off-topic questions appropriately
- Vietnamese text is natural and professional

**What to verify**:
- [ ] No hallucinated facts (fake chemical names, wrong dosages)
- [ ] No dangerous advice (excessive pesticide, untested methods)
- [ ] Citations appear when referencing handbooks or research
- [ ] Response length is reasonable (not too short, not overwhelming)
- [ ] Conversation history is maintained (follow-up questions work)

---

### TEST 7: AI Assistant - Voice Chat

**What you're testing**: Voice input, speech transcription, hands-free usage

**Test steps**:
1. [ ] Stay in the **Assistant** page
2. [ ] Tap the **microphone** button
3. [ ] If prompted, **allow microphone permission**
4. [ ] Speak a short question in Vietnamese (5–15 seconds):
   - Example: "Bệnh đạo ôn xử lý thế nào?" (How to treat rice blast disease?)
5. [ ] Stop recording (tap button again or wait for auto-stop)
6. [ ] Observe the **transcript** that appears on screen
7. [ ] Wait for the AI response to generate
8. [ ] Check if the response is **read aloud** (text-to-speech)
9. [ ] Verify the response matches what you asked

**Expected results**:
- Transcription appears within 5 seconds of stopping recording
- Transcript is mostly accurate (minor errors acceptable for Vietnamese)
- AI response is relevant to your spoken question
- Audio response is clear and natural-sounding (if TTS is enabled)

**What to verify**:
- [ ] Microphone permission dialog appears and works
- [ ] Recording indicator is visible while speaking
- [ ] Transcript displays in Vietnamese
- [ ] Response quality matches text chat quality
- [ ] Volume and clarity of TTS voice is acceptable

**Test in different conditions**:
- [ ] Quiet indoor environment (baseline)
- [ ] Outdoor with moderate background noise (birds, wind)
- [ ] Outdoors with traffic or machinery noise
- [ ] Note which conditions produce accurate transcripts

**If voice fails**:
- [ ] Take screenshot of error message
- [ ] Note whether microphone permission was granted
- [ ] Check if your device/browser supports microphone access

---

### TEST 8: AI Assistant - Image Disease Detection

**What you're testing**: Disease/pest identification, treatment advice, low-confidence handling

**Test steps**:
1. [ ] Stay in the **Assistant** page
2. [ ] Tap the **camera** or **image upload** button
3. [ ] Either:
   - [ ] Take a new photo of a rice plant (leaf, stem, or whole plant)
   - [ ] Upload an existing photo from your gallery
4. [ ] Use **good lighting** and focus on affected areas
5. [ ] Wait for the prediction to complete (should be < 15 seconds)
6. [ ] Observe the results displayed:
   - [ ] Predicted disease/pest name (in Vietnamese)
   - [ ] Confidence percentage (0–100%)
   - [ ] Treatment recommendations
   - [ ] Prevention tips
7. [ ] Read the advice and evaluate:
   - [ ] Is it practical for local conditions?
   - [ ] Is it safe (conservative approach)?
   - [ ] Does it mention cultural, biological, AND chemical options?
8. [ ] **Test low-confidence scenario**:
   - [ ] Upload a blurry, dark, or unclear photo
   - [ ] Verify the app asks for a clearer photo if confidence < 30%

**Expected results**:
- Prediction completes in < 15 seconds
- Disease/pest names are in Vietnamese
- Advice is practical, safe, and multi-option (not just "spray immediately")
- Low confidence triggers helpful guidance to retake photo

**What to verify**:
- [ ] All 8 disease/pest classes are detectable:
   - Healthy (Khỏe mạnh)
   - Brown Spot (Đốm nâu)
   - Rice Blast (Đạo ôn)
   - Brown Plant Hopper (Rầy nâu)
   - Rice Borer (Sâu đục thân)
   - Rice Leaf Roller (Sâu cuốn lá)
   - Rice Gall Midge (Ruồi đục lúa)
   - Golden Apple Snails (Ốc bươu vàng)
- [ ] Confidence score makes sense (high for clear photos, low for unclear)
- [ ] Advice never recommends immediate chemical spray without monitoring
- [ ] Prevention tips are included

**Test with multiple photos** (if possible):
- [ ] Clear, well-lit photo (should have high confidence)
- [ ] Photo with multiple issues visible
- [ ] Photo from different angles (top view vs. side view)

---

### TEST 9: Profile & Settings

**What you're testing**: User preferences, accessibility, farm/plot management

**Test steps**:
1. [ ] Open **Profile** from the main navigation menu
2. [ ] **Test language switching**:
   - [ ] Change language from VI to EN (or vice versa)
   - [ ] Verify the entire app interface updates immediately
   - [ ] Switch back to your preferred language
3. [ ] **Test font size accessibility**:
   - [ ] Change font size to "Large"
   - [ ] Navigate to Dashboard, Tasks, or Journal
   - [ ] Verify text is noticeably larger throughout the app
   - [ ] Return to Profile and try "Extra Large" if available
4. [ ] **Add a new farm**:
   - [ ] Scroll to "My Farms" section
   - [ ] Tap **Add Farm** or "+" button
   - [ ] Fill in farm details:
     - Name: "Trang trại thử nghiệm" (Test farm)
     - Province: Select "An Giang" from dropdown
     - District: Select a district (e.g., "Châu Đốc")
     - (Optional) Commune, hamlet
   - [ ] Save the farm
   - [ ] Verify the new farm appears in the farm list
5. [ ] **Add a new plot** (for the new farm):
   - [ ] Tap **Add Plot** or navigate to the farm and add plot
   - [ ] Fill in plot details:
     - Plot name: "Lô thử nghiệm 1"
     - Soil type: "Đất phù sa" (Alluvial soil)
     - Rice variety: "OM 5451"
     - Sowing date: Today's date
     - Expected harvest date: 120 days from now
     - Irrigation method: "Tưới ngập" (Continuous flooding)
     - Area: 5
     - Area unit: "Công lớn (1,300 m²)"
   - [ ] Save the plot
6. [ ] **Verify data appears elsewhere**:
   - [ ] Navigate to **Dashboard**
   - [ ] Confirm the new farm and plot are visible
   - [ ] Navigate to **Tasks** or **Journal**
   - [ ] Verify the new plot appears in plot selection dropdowns

**Expected results**:
- Language change affects the entire app instantly
- Font size changes are visible and helpful for accessibility
- New farms and plots save successfully and appear across the app

**What to verify**:
- [ ] All Vietnamese provinces are available in dropdown
- [ ] All 11 soil types are in Vietnamese:
   - Đất phù sa, Đất sét, Đất sét pha, Đất pha cát, Đất sét bùn, Đất pha bùn, Đất than bùn, Đất xám, Đất bazan đỏ, Đất mặn, Đất phèn
- [ ] Area units match Vietnamese farming conventions
- [ ] Date pickers work correctly on mobile
- [ ] Farm/plot data persists after page refresh

---

### TEST 10: Data Persistence & Logout

**What you're testing**: Data saves correctly, survives refresh and logout/login cycles

**Test steps**:
1. [ ] Ensure you have created:
   - [ ] At least 1 new task
   - [ ] At least 1 new journal entry
   - [ ] At least 1 new farm (if not using demo)
   - [ ] At least 1 new plot (if not using demo)
2. [ ] **Test page refresh**:
   - [ ] Refresh the browser page (F5 or pull-to-refresh on mobile)
   - [ ] Wait for app to reload
   - [ ] Verify all your data is still visible:
     - [ ] New task appears in Tasks page
     - [ ] New journal entry appears in Journal page
     - [ ] New farm/plot appear in Dashboard and Profile
3. [ ] **Test logout/login cycle**:
   - [ ] Tap **Logout** button (usually in Profile or menu)
   - [ ] Verify you return to the login/auth screen
   - [ ] Log in again:
     - If using demo: Click "Try Demo" again
     - If using your own account: Enter credentials
   - [ ] Verify data persistence:
     - **Demo account**: Should show consistent sample data (not your custom data)
     - **Your own account**: Should show all your custom data (tasks, journal, farms, plots)

**Expected results**:
- Data persists across page refresh (no loss)
- Demo account always shows the same sample data after logout/login
- Custom accounts retain all user-created data after logout/login

**What to verify**:
- [ ] No data is lost after browser refresh
- [ ] No data is lost after closing and reopening the browser
- [ ] Authentication state is maintained (stays logged in on refresh)
- [ ] Logout fully clears session (can't access protected pages without login)
- [ ] Demo mode is consistent (same sample data every time)

---

## 6) Deep-dive assignments (choose 1 module per tester) (30–45 minutes)

### Module A: Authentication / OTP / password reset
- [ ] Request OTP and confirm you received the email
- [ ] Try wrong OTP and confirm error message is clear
- [ ] Complete registration
- [ ] Logout → login again
- [ ] Password reset flow (request reset OTP → set new password)

### Module B: Assistant quality (Vietnamese agronomy)
Ask 8–10 real extension-officer questions and score:
- **Correctness** (1–5)
- **Safety** (1–5)
- **Practicality** (1–5)
- **Vietnamese clarity** (1–5)

Suggested prompts:
- “Bệnh đạo ôn xuất hiện khi nào và xử lý ra sao?”
- “Rầy nâu nhiều thì cần làm gì trước khi phun thuốc?”
- “Bón phân đón đòng thời điểm nào?”
- “Dự báo mưa lớn 2 ngày tới, tôi nên quản lý nước thế nào?”

### Module C: Voice (field conditions)
- [ ] Test voice in quiet indoor environment
- [ ] Test voice outdoors with background noise
- [ ] Record latency (time to get transcript + answer)
- [ ] Check if the answer language matches your UI language

### Module D: Disease detection
- [ ] Test 3 different photos (different lighting/angles)
- [ ] Check if advice seems safe and consistent with local practice
- [ ] If prediction seems wrong, note what you believe it is and why

### Module E: Weather
- [ ] Test with location allowed vs denied
- [ ] Compare forecast/alerts to a trusted local source (roughly)
- [ ] Check if recommendations match rain/heat conditions

### Module F: Usability + accessibility
- [ ] Check readability under sunlight (mobile)
- [ ] Check button sizes (gloved hands / wet hands)
- [ ] Check Vietnamese wording of key actions
- [ ] Identify any confusing steps for farmers

---

## 7) Feedback form (copy/paste)

### Tester info
- Name:
- Province/organization:
- Device + OS:
- Browser:
- Network:
- Test date/time:

### Ratings (1 = poor, 5 = excellent)
- Onboarding/login: 1 2 3 4 5
- Navigation clarity: 1 2 3 4 5
- Assistant usefulness: 1 2 3 4 5
- Assistant safety: 1 2 3 4 5
- Voice usability: 1 2 3 4 5
- Disease detection usefulness: 1 2 3 4 5
- Weather usefulness: 1 2 3 4 5
- Tasks/journal usefulness: 1 2 3 4 5
- Vietnamese language quality: 1 2 3 4 5

### Top 3 positives
1.
2.
3.

### Top 3 issues / risks
1.
2.
3.

### Bug reports (repeat as needed)
- Severity (S1/S2/S3/S4):
- Feature (Auth/Dashboard/Weather/Tasks/Journal/Assistant/Voice/Disease):
- Steps to reproduce:
- Expected:
- Actual:
- Screenshot/video attached:

---

## 8) Notes for coordinators (internal)

- Assistant guest mode uses `/api/assistant/chat` (no auth).
- Logged-in assistant uses `/api/assistant/conversations/*` and stores chat history.
- Voice uses `/api/voice/talk` (token optional; `VOICE_API_PUBLIC=True`).
- Disease detection uses:
  - Auth: `/api/assistant/predict-disease`
  - No-auth: `/api/assistant/predict-disease-no-auth`
- Weather uses `/api/weather` and may fall back to mock data if external API keys are missing.
