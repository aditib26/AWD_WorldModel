# AIRRVie Bug Report Template
## Detailed Issue Documentation

---

**Use this template for documenting detailed bugs with multiple screenshots**

**File Naming:** `BUG_[Severity]_[ShortDescription]_[YourName]_[Date].docx`

Example: `BUG_S1_LoginOTPFails_NguyenVanA_2024-02-14.docx`

---

## BUG REPORT #_____

---

### CLASSIFICATION

**Bug ID:** BUG-___ *(Leave blank if you don't have a tracking system)*

**Severity Level:** *(Select one and DELETE the others)*
- **S1 - CRITICAL:** App crashes, data loss, cannot login, security issue
- **S2 - MAJOR:** Core feature broken (Assistant, Weather, Tasks completely non-functional)
- **S3 - MINOR:** UI issues, typos, layout problems, slow loading
- **S4 - SUGGESTION:** Feature improvement ideas, enhancements

**Feature Area:** *(Select one)*
- [ ] Authentication (Login, Signup, OTP)
- [ ] Dashboard
- [ ] Weather
- [ ] Tasks
- [ ] Journal
- [ ] AI Assistant - Text Chat
- [ ] AI Assistant - Voice Input
- [ ] AI Assistant - Disease Detection
- [ ] Profile & Settings
- [ ] Farm/Plot Management
- [ ] Other: _________________

**Date Reported:** __________________

**Reported By:** __________________

---

### BUG SUMMARY

**Title:** *(One-line description of the issue)*

Example: "OTP verification fails with correct code"

---

**Brief Description:** *(2-3 sentences summarizing the problem)*

Example: "When user enters the correct OTP code received via email, the app displays 'Invalid OTP' error and does not allow login. This happens consistently with multiple email addresses tested."

---

---

### DETAILED DESCRIPTION

**What were you trying to do?**

*(Describe your goal)*

Example: "I was trying to create a new account and login to the app for the first time."

---

**What exactly happened?**

*(Describe what went wrong, step by step)*

Example: 
"I entered my email address and requested a verification code. The code arrived in my email inbox within 1 minute. I copied the exact 6-digit code (123456) and pasted it into the OTP field. When I clicked 'Verify,' the button showed a loading spinner for 2-3 seconds, then displayed a red error message saying 'Invalid OTP. Please try again.' I tried typing the code manually instead of pasting - same error. I requested a new OTP code and tried again - still the same error."

---

**Expected Behavior:**

*(What should have happened?)*

Example: "The app should verify the OTP code, create my account, and take me to the Dashboard."

---

**Actual Behavior:**

*(What actually happened?)*

Example: "The app rejected the correct OTP code and showed an error message. I cannot proceed with account creation."

---

---

### STEPS TO REPRODUCE

*(Numbered list of exact steps that trigger the bug)*

**Prerequisites:** *(If any - e.g., "Must have an existing account")*

**Steps:**

1. 
2. 
3. 
4. 
5. 

**Example:**
1. Open app at https://rice-app3.pepeshanty.store/
2. Tap "Get Started" button
3. Tap "Sign Up"
4. Enter email: test@example.com
5. Tap "Send Verification Code"
6. Check email and copy the 6-digit OTP
7. Paste OTP into verification field
8. Tap "Verify" button
9. **BUG OCCURS:** Error message appears

---

**Frequency:** *(How often does this happen?)*
- [ ] Always (100% of the time)
- [ ] Often (75% of attempts)
- [ ] Sometimes (50% of attempts)
- [ ] Rarely (25% or less)
- [ ] Once (cannot reproduce)

---

---

### SCREENSHOTS & EVIDENCE

*(Paste screenshots below each description. Use Print Screen or phone screenshot, then paste here)*

**Screenshot 1: [Description]**

*(Example: "OTP email showing code 123456")*

[PASTE SCREENSHOT HERE]

---

**Screenshot 2: [Description]**

*(Example: "OTP entry screen with code entered")*

[PASTE SCREENSHOT HERE]

---

**Screenshot 3: [Description]**

*(Example: "Error message displayed after clicking Verify")*

[PASTE SCREENSHOT HERE]

---

**Screenshot 4: [Description]**

*(Example: "Browser console showing error logs" - if technical)*

[PASTE SCREENSHOT HERE]

---

**Video Recording:** *(If you have a screen recording showing the bug)*

File name: _________________.mp4
Duration: _____ seconds

*(Attach video file or provide link)*

---

---

### DEVICE & ENVIRONMENT INFORMATION

**Device Model:** ___________________
*(Example: iPhone 13, Samsung Galaxy A52, HP Laptop)*

**Operating System:** ___________________
*(Example: iOS 17.2, Android 12, Windows 11, macOS Sonoma)*

**Browser:** ___________________
*(Example: Safari 17, Chrome 120, Firefox 121)*

**Screen Resolution:** ___________________
*(Example: 1170 x 2532, 1920 x 1080)*

**Network Connection:** ___________________
*(Example: 4G mobile data - good signal, Wi-Fi - fast connection)*

**Location/Region:** ___________________
*(Example: An Giang Province, Vietnam)*

**Language Setting:** ___________________
- [ ] English
- [ ] Vietnamese

**Font Size Setting:** ___________________
- [ ] Normal
- [ ] Large
- [ ] Extra Large

---

---

### IMPACT ASSESSMENT

**Who is affected by this bug?**
- [ ] All users
- [ ] New users only
- [ ] Existing users only
- [ ] Users in specific regions: _____________
- [ ] Users on specific devices: _____________

**How severe is the impact?**
- [ ] Blocks user completely (cannot use app at all)
- [ ] Blocks core functionality (major feature unusable)
- [ ] Degraded experience (feature works but poorly)
- [ ] Minor annoyance (cosmetic issue)

**Estimated number of users affected:**
- [ ] All farmers/extension officers (~100%)
- [ ] Many users (~50-75%)
- [ ] Some users (~25-50%)
- [ ] Few users (~10-25%)
- [ ] Very few (~5-10%)

**Business impact:**
- [ ] Critical - prevents app launch/adoption
- [ ] High - significantly reduces value
- [ ] Medium - noticeable but workaroundable
- [ ] Low - minor issue

---

---

### WORKAROUND

**Have you found a way to avoid or work around this issue?**
- [ ] Yes (describe below)
- [ ] No

**Workaround description:**

*(If you found an alternative way to accomplish the task, describe it here)*

Example: "Instead of pasting the OTP, if I manually type it very slowly (one digit at a time with 1-second pauses), it sometimes works. However, this is inconsistent and frustrating."

---

---

### ADDITIONAL CONTEXT

**Did this work before?**
- [ ] Yes, it worked previously but broke recently
- [ ] No, it never worked
- [ ] Don't know / First time testing

**Similar issues observed:**

*(Are there related bugs in other features?)*

Example: "Password reset OTP also fails in the same way."

---

**Browser Console Errors:** *(For technical testers)*

*(If you opened browser DevTools and saw error messages, copy them here)*

```
Example:
Error: Failed to verify OTP
  at verifyOTP (auth.js:45)
  at handleSubmit (AuthPage.tsx:120)
Status: 400 Bad Request
```

---

**Network Request Details:** *(For technical testers)*

*(If you captured the API request/response in Network tab)*

```
POST https://rice-app3-backend.pepeshanty.store/api/auth/verify-otp
Request body: {"email": "test@example.com", "otp": "123456"}
Response: {"error": "Invalid OTP"}
Status: 400
```

---

---

### TESTER NOTES

**Your assessment:**

*(What do you think is causing this? Any theories?)*

Example: "The OTP might be expiring too quickly (less than the advertised 10 minutes). Or there might be a timezone issue causing the OTP to be generated with the wrong time."

---

**Priority recommendation:**

*(How urgently should this be fixed?)*
- [ ] Fix immediately - blocking all users
- [ ] Fix in next release - major issue
- [ ] Fix when possible - minor issue
- [ ] Low priority - suggestion/enhancement

---

**Additional observations:**

*(Any other relevant information)*

---

---

### FOR DEVELOPER USE (Leave blank - team will fill this out)

**Assigned To:** _________________

**Status:** 
- [ ] New
- [ ] In Progress
- [ ] Fixed
- [ ] Cannot Reproduce
- [ ] Won't Fix
- [ ] Duplicate of #____

**Root Cause:** _________________

**Fix Description:** _________________

**Fixed In Version:** _________________

**Verification Date:** _________________

**Verified By:** _________________

---

---

## APPENDIX: SUPPORTING INFORMATION

### Email Logs (if relevant)

*(Copy/paste relevant email headers or content)*

```
From: riceai.otp@gmail.com
To: test@example.com
Subject: Your AIRRVie Verification Code
Date: Feb 14, 2024, 10:32 AM
Body: Your verification code is: 123456
This code expires in 10 minutes.
```

---

### Related Test Data

**Account used:** _________________
**Farm/Plot IDs:** _________________
**Task/Journal IDs:** _________________
**Conversation IDs:** _________________

---

---

## SUBMISSION CHECKLIST

Before submitting this bug report, ensure:

- [ ] Bug summary is clear and concise
- [ ] Steps to reproduce are complete and numbered
- [ ] At least 2-3 screenshots are included
- [ ] Device and environment info is filled out
- [ ] Severity level is accurately assessed
- [ ] Frequency is documented
- [ ] Impact on users is described
- [ ] Expected vs actual behavior is clearly stated
- [ ] File is named correctly
- [ ] Sensitive information (real passwords, personal data) is removed

---

**Report submitted by:** ___________________

**Date submitted:** ___________________

**Contact email:** ___________________

**Contact phone:** ___________________

---

## END OF BUG REPORT

---

# Tips for Writing Effective Bug Reports

1. **Be Specific:** "Login doesn't work" → "OTP verification fails with error 'Invalid OTP'"

2. **Include Context:** Describe what you were trying to accomplish

3. **Reproduce Consistently:** Try to trigger the bug multiple times

4. **One Bug Per Report:** Don't combine multiple unrelated issues

5. **Use Screenshots Liberally:** Visual evidence is invaluable

6. **Describe, Don't Diagnose:** Focus on what happened, not why (unless you're technical)

7. **Check for Duplicates:** Has someone else reported this already?

8. **Update If Needed:** If you discover more information later, add it

---

# Common Mistakes to Avoid

❌ "The app is broken" → Too vague
✅ "Weather page shows 'Location not found' error in An Giang province"

❌ "AI is bad" → Not actionable
✅ "AI assistant recommended wrong fertilizer amount: said 100kg for 1 công when standard is 30-40kg"

❌ No screenshots → Hard to understand
✅ 3-4 screenshots showing the issue step by step

❌ Missing device info → Cannot reproduce
✅ Complete device, OS, browser, and network details

❌ "Tried once, didn't work" → Cannot confirm
✅ "Tried 5 times on 2 different devices - same error every time"

---

**Thank you for taking the time to document bugs thoroughly!**

**Your detailed reports help the development team fix issues quickly and improve the app for all users.**
