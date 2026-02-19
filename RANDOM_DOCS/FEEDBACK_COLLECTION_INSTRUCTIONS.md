# AIRRVie Field Test - Feedback Collection System
## Instructions for Test Coordinator

---

## OVERVIEW

You have **3 feedback collection tools** to use with your 10 extension officer testers:

1. **📊 Excel Spreadsheet** - For structured ratings and quick bug logging
2. **📝 Google Form** - For online submission with automatic aggregation
3. **📄 Word Document** - For detailed bug reports with screenshots

---

## RECOMMENDED APPROACH

### **Option A: Google Form (Easiest)** ⭐ RECOMMENDED

**Best for:**
- Remote testing (testers in different locations)
- Quick deployment
- Automatic data aggregation
- Real-time monitoring

**Steps:**
1. Create Google Form using `GOOGLE_FORM_STRUCTURE.md`
2. Send form link to all 10 testers
3. Testers fill form after testing (15-20 mins)
4. Responses auto-save to Google Sheets
5. Export to Excel for analysis

**Advantages:**
- ✅ No file distribution
- ✅ Real-time responses
- ✅ Automatic charts
- ✅ Mobile-friendly
- ✅ Can accept image uploads

---

### **Option B: Excel Spreadsheet (Traditional)**

**Best for:**
- Offline testing
- When testers prefer spreadsheets
- More control over format

**Steps:**
1. Create Excel file using `EXCEL_TEMPLATE_STRUCTURE.md`
2. Save 10 copies, one per tester
3. Email/share files with testers
4. Testers fill and return files
5. Manually consolidate into master file

**Advantages:**
- ✅ Works offline
- ✅ Familiar format
- ✅ Flexible editing
- ✅ Multiple sheets for organization

---

### **Option C: Hybrid Approach** (Most Comprehensive)

**Use all three:**

**Google Form:** For quick ratings and feedback
- All testers fill this out (required)
- Takes 15-20 minutes
- Provides quantitative data

**Excel Spreadsheet:** For bug tracking
- Used by coordinator to consolidate bugs
- Aggregates data from all sources

**Word Document:** For critical bugs only
- Testers create detailed bug reports for S1/S2 issues
- Include multiple screenshots
- Send separately via email

---

## DETAILED SETUP INSTRUCTIONS

### 1. GOOGLE FORM SETUP (45 minutes)

**Step 1: Create Form**
1. Go to https://forms.google.com
2. Click "+" to create blank form
3. Title: "AIRRVie Field Test Feedback - Extension Officers"
4. Open `GOOGLE_FORM_STRUCTURE.md`
5. Copy questions one by one into form
6. Follow exact structure (47 questions total)

**Step 2: Configure Settings**
1. Click gear icon (Settings)
2. General tab:
   - ☑ Limit to 1 response
   - ☑ Collect email addresses
   - Response receipts: Optional
3. Presentation tab:
   - ☑ Show progress bar
   - ☐ Shuffle questions (keep order)
4. Click "Save"

**Step 3: Customize Confirmation**
1. Settings → Presentation
2. Confirmation message: Copy from template
3. Click "Save"

**Step 4: Test the Form**
1. Click "Preview" (eye icon)
2. Fill out form yourself
3. Check all questions display properly
4. Verify responses save to Sheets

**Step 5: Get Shareable Link**
1. Click "Send" button (top right)
2. Click link icon (🔗)
3. Copy link
4. Shorten with bit.ly if needed

**Step 6: Monitor Responses**
1. Click "Responses" tab
2. View summary statistics
3. Click green Sheets icon to open response spreadsheet
4. Bookmark for easy access

---

### 2. EXCEL SETUP (60 minutes)

**Step 1: Create Master File**
1. Open Microsoft Excel or Google Sheets
2. Create new workbook
3. Name: "AIRRVie_Field_Test_Master.xlsx"

**Step 2: Create Sheet 1 - Ratings**
1. Rename sheet to "Tester Information & Ratings"
2. Open `EXCEL_TEMPLATE_STRUCTURE.md`
3. Copy headers from "SHEET 1" section
4. Paste into Row 1 (columns A through AE)
5. Format header row:
   - Bold text
   - Blue background (#4472C4)
   - White text
   - Freeze row: View → Freeze Panes → Freeze Top Row

**Step 3: Create Sheet 2 - Bug Tracker**
1. Create new sheet, name: "Bug Tracker"
2. Copy headers from "SHEET 2" section
3. Add data validation dropdowns:
   - Column B (Severity): S1,S2,S3,S4
   - Column E (Feature): List all feature areas
   - Column K (Status): Open,In Progress,Fixed,Won't Fix,Duplicate
4. Apply conditional formatting:
   - S1 rows: Red background
   - S2 rows: Orange background
   - S3 rows: Yellow background
   - S4 rows: Light blue background

**Step 4: Create Sheet 3 - Detailed Feedback**
1. Create new sheet, name: "Detailed Feedback"
2. Copy structure from "SHEET 3" section
3. Pre-fill questions (rows 2-11)
4. Leave response column blank for testers

**Step 5: Create Sheet 4 - Summary**
1. Create new sheet, name: "Summary Statistics"
2. Add formulas from "SHEET 4" section
3. These auto-calculate when data is entered
4. Leave for now (will populate after testing)

**Step 6: Save Template**
1. Save As: "AIRRVie_Field_Test_TEMPLATE.xlsx"
2. Keep this as master copy

**Step 7: Create Individual Files**
1. Save 10 copies with tester names:
   - `AIRRVie_Test_NguyenVanA.xlsx`
   - `AIRRVie_Test_TranThiB.xlsx`
   - etc.
2. Or: Save one template, testers make their own copies

---

### 3. WORD TEMPLATE SETUP (30 minutes)

**Step 1: Create Document**
1. Open Microsoft Word
2. New blank document
3. Open `BUG_REPORT_TEMPLATE.md`
4. Copy entire content into Word

**Step 2: Apply Formatting**
1. Follow formatting instructions in `WORD_BUG_REPORT_TEMPLATE_CONTENT.md`
2. Main title: Arial 18pt, Bold, Blue
3. Section headers: Arial 14pt, Bold, Red background
4. Body text: Calibri 11pt
5. Add checkboxes: Insert → Symbol → ☐

**Step 3: Create Screenshot Placeholders**
1. For each "[PASTE SCREENSHOT HERE]":
   - Insert → Table (1 cell)
   - Size: 6" wide x 4" tall
   - Border: Dashed gray
   - Background: Light gray
2. Center text: "[PASTE SCREENSHOT HERE]"

**Step 4: Add Page Setup**
1. Layout → Margins → Normal (1")
2. Insert → Page Number → Bottom Center
3. Format: "Page X of Y"

**Step 5: Save Template**
1. Save As: "AIRRVie_Bug_Report_TEMPLATE.docx"
2. File Type: Word Document (.docx)
3. Keep as master template

**Step 6: Create Instructions**
1. Save copy as: "How_to_Use_Bug_Report_Template.docx"
2. Add example filled-in bug report
3. Show how to insert screenshots
4. Provide file naming examples

---

## DISTRIBUTING TO TESTERS

### Email Template to Send Testers:

```
Subject: AIRRVie Field Test - Testing Materials

Xin chào [Tester Name],

Thank you for participating in the AIRRVie field testing program!

TESTING INSTRUCTIONS:
📖 Field Test Guide: [Attach VIETNAM_EXTENSION_OFFICER_APP_TEST_GUIDE_FIRST_DRAFT.md]
📱 Test Website: https://rice-app3.pepeshanty.store/
🎯 Demo Login: demo@airrvie.app / demo123

FEEDBACK SUBMISSION OPTIONS:

Option 1 (REQUIRED): Google Form (15-20 minutes)
📋 Form Link: [Insert Google Form link]
Please complete by: [Date]

Option 2 (Optional): Excel File
📊 Excel Template: [Attach AIRRVie_Test_[YourName].xlsx]
Fill and return if you prefer spreadsheets

Option 3 (For critical bugs only): Word Document
📄 Bug Report Template: [Attach AIRRVie_Bug_Report_TEMPLATE.docx]
Use for S1/S2 bugs with many screenshots

TESTING TIMELINE:
- Start Date: [Date]
- Testing Duration: At least 1-2 hours
- Feedback Due: [Date]

SUPPORT:
If you encounter issues or have questions:
📞 Phone: [Your Phone]
📧 Email: [Your Email]

Thank you for your valuable contribution!

Best regards,
[Your Name]
[Your Title]
[Organization]
```

---

### WhatsApp/Telegram Message Template:

```
🌾 AIRRVie Field Test Instructions

📱 App: https://rice-app3.pepeshanty.store/
🎯 Demo: demo@airrvie.app / demo123

📋 Feedback Form: [Google Form link]

📖 Full instructions sent via email

⏰ Due: [Date]

Questions? Reply here or call [Phone]

Thank you! 🙏
```

---

## COLLECTING & ANALYZING RESPONSES

### From Google Form:

**Real-time Monitoring:**
1. Open form → Responses tab
2. See number of responses
3. View summary charts
4. Check individual responses

**Export to Sheets:**
1. Responses → Green Sheets icon
2. Opens linked Google Sheet
3. All responses in spreadsheet format
4. Auto-updates as new submissions come in

**Export to Excel:**
1. Open linked Google Sheet
2. File → Download → Microsoft Excel (.xlsx)
3. Save as: "AIRRVie_Form_Responses_[Date].xlsx"

**Create Charts:**
1. In Google Sheets, select rating data
2. Insert → Chart
3. Chart type: Bar chart for ratings
4. Chart type: Pie chart for Yes/No questions

---

### From Excel Files:

**Collecting Files:**
1. Receive files via email
2. Rename: "RECEIVED_[TesterName]_[Date].xlsx"
3. Store in folder: "Tester_Responses"

**Consolidating Data:**
1. Open your master Excel file
2. Open each tester's file
3. Copy their data row from Sheet 1
4. Paste into master Sheet 1
5. Copy their bugs from Sheet 2
6. Paste into master Sheet 2
7. Repeat for all 10 testers

**Analyzing Aggregate Data:**
1. Sheet 4 (Summary) auto-calculates:
   - Average ratings per feature
   - Highest/lowest ratings
   - Number of Yes/No/Maybe responses
   - Bug count by severity
2. Create pivot tables for deeper analysis
3. Create charts for presentation

---

### From Word Bug Reports:

**Organizing:**
1. Create folder: "Critical_Bug_Reports"
2. Receive Word files via email
3. Save with consistent naming
4. Log in Excel Sheet 2 (Bug Tracker)

**Prioritizing:**
1. Read all S1 bugs first
2. Verify reproducibility
3. Group similar bugs
4. Create action plan for fixes

---

## CREATING FINAL REPORT

### Summary Report Structure:

**1. Executive Summary** (1 page)
- Number of testers
- Testing dates
- Overall ratings (averages)
- Top 3 strengths
- Top 3 issues
- Recommendation (ready/not ready)

**2. Detailed Findings** (5-10 pages)

**2.1 Quantitative Results**
- Feature ratings (charts)
- Farmer adoption likelihood (pie chart)
- Bug severity distribution (chart)

**2.2 Qualitative Feedback**
- Common themes from open-ended responses
- Direct quotes from testers
- Examples of good/bad experiences

**2.3 Critical Issues**
- All S1/S2 bugs listed
- Screenshots included
- Reproduction steps
- Recommended fixes

**2.4 Language Quality**
- Translation errors found
- Natural phrasing suggestions
- Terminology improvements

**2.5 AI Assistant Quality**
- Example questions and responses
- Accuracy assessment
- Safety assessment
- Recommendations for improvement

**3. Recommendations** (2-3 pages)
- Must-fix issues before launch
- Should-fix issues for better experience
- Nice-to-have improvements
- Timeline for fixes

**4. Appendices**
- Full data tables
- All bug reports
- Tester demographics
- Raw feedback

---

### Creating Charts for Report:

**From Excel/Google Sheets:**

**Chart 1: Average Feature Ratings**
- Type: Horizontal bar chart
- Data: Sheet 4, average ratings
- X-axis: Rating (1-5)
- Y-axis: Features
- Show data labels

**Chart 2: Farmer Adoption**
- Type: Pie chart
- Data: Yes/No/Maybe counts
- Show percentages
- Color code: Green (Yes), Red (No), Yellow (Maybe)

**Chart 3: Bug Severity**
- Type: Donut chart
- Data: S1/S2/S3/S4 counts
- Color code: Red/Orange/Yellow/Blue

**Export Charts:**
1. Right-click chart → Save as Image
2. Insert into Word report
3. Add descriptive captions

---

## TIMELINE EXAMPLE

### Week 1: Setup (You)
- **Day 1-2:** Create Google Form (45 min)
- **Day 1-2:** Create Excel template (60 min)
- **Day 1-2:** Create Word template (30 min)
- **Day 3:** Test all templates yourself
- **Day 4:** Prepare tester materials
- **Day 5:** Send materials to 10 testers

### Week 2-3: Testing (Testers)
- **Day 1:** Testers receive materials
- **Day 2-10:** Testers test app (1-2 hours each)
- **Day 11-14:** Testers submit feedback
- **Day 14:** Follow up with late testers

### Week 4: Analysis (You)
- **Day 1-2:** Collect all responses
- **Day 3-4:** Consolidate data in Excel
- **Day 5-7:** Analyze findings
- **Day 8-10:** Create summary report
- **Day 11:** Share report with supervisor/team
- **Day 12-14:** Present findings, discuss next steps

---

## TROUBLESHOOTING

### Common Issues:

**Issue:** Tester can't access Google Form
- **Solution:** Check if link is correct, try incognito mode, check internet connection

**Issue:** Excel file won't open
- **Solution:** Save as .xlsx (not .xls), check Excel version compatibility, try Google Sheets

**Issue:** Testers don't understand what to do
- **Solution:** Create video tutorial, hold kickoff meeting, provide examples

**Issue:** Low response rate
- **Solution:** Send reminders, offer incentive, extend deadline, follow up individually

**Issue:** Inconsistent data quality
- **Solution:** Provide clearer instructions, show examples, reject incomplete submissions

---

## CHECKLIST

### Before Starting:
- [ ] Read all template files
- [ ] Create Google Form (45 min)
- [ ] Create Excel template (60 min)
- [ ] Create Word template (30 min)
- [ ] Test all templates yourself
- [ ] Prepare tester list (names, emails, phones)
- [ ] Set testing dates and deadline
- [ ] Draft email/message to testers

### During Testing:
- [ ] Send materials to all testers
- [ ] Monitor Google Form responses
- [ ] Send reminder 1 week before deadline
- [ ] Send reminder 2 days before deadline
- [ ] Follow up with non-responders
- [ ] Answer tester questions promptly

### After Testing:
- [ ] Collect all Excel files
- [ ] Collect all Word bug reports
- [ ] Export Google Form responses
- [ ] Consolidate all data in master Excel
- [ ] Review all bugs and feedback
- [ ] Calculate summary statistics
- [ ] Create charts and visualizations
- [ ] Write summary report
- [ ] Present findings to team
- [ ] Plan bug fixes and improvements

---

## SUPPORT CONTACTS

**Technical Issues:**
[Your Name]: [Email] / [Phone]

**Project Lead:**
[Supervisor Name]: [Email] / [Phone]

**App Development Team:**
[Developer Contact]: [Email]

---

## FILES CREATED

You should have these files ready:

1. ✅ `EXCEL_TEMPLATE_STRUCTURE.md` - Instructions for Excel
2. ✅ `GOOGLE_FORM_STRUCTURE.md` - Instructions for Google Form
3. ✅ `BUG_REPORT_TEMPLATE.md` - Content for Word bug report
4. ✅ `WORD_BUG_REPORT_TEMPLATE_CONTENT.md` - Word formatting guide
5. ✅ `FEEDBACK_COLLECTION_INSTRUCTIONS.md` - This file

**To Create:**
- `AIRRVie_Field_Test_Master.xlsx` (using #1)
- Google Form at forms.google.com (using #2)
- `AIRRVie_Bug_Report_TEMPLATE.docx` (using #3 and #4)

---

**Good luck with your field testing!**

**Questions? Refer to this guide or contact the project team.**
