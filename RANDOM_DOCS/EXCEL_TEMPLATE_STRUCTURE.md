# AIRRVie Field Test - Excel Template Structure

## Instructions for Creating the Excel File

Copy this structure into Microsoft Excel or Google Sheets. Create 4 separate sheets (tabs) as shown below.

---

## SHEET 1: "Tester Information & Ratings"

### Row 1 - Headers:
| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T | U |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tester Name | Organization | Province | District | Phone | Email | Device Model | OS Version | Browser | Network | Test Date | Start Time | End Time | Duration (min) | Onboarding (1-5) | Navigation (1-5) | Assistant Usefulness (1-5) | Assistant Safety (1-5) | Voice (1-5) | Disease Detection (1-5) | Weather (1-5) |

### Continue Headers (Row 1):
| V | W | X | Y | Z | AA | AB | AC | AD |
|---|---|---|---|---|---|---|---|---|
| Tasks/Journal (1-5) | Vietnamese (1-5) | Mobile Experience (1-5) | Overall (1-5) | Would Farmers Use? | Top Strength 1 | Top Strength 2 | Top Issue 1 | Top Issue 2 |

### Row 2 onwards:
Leave blank for testers to fill in their responses.

### Example Row 2:
```
Nguyen Van A | Extension Office An Giang | An Giang | Châu Đốc | 0901234567 | nguyenvana@example.com | iPhone 13 | iOS 17 | Safari | 4G | 2024-02-14 | 10:00 | 10:45 | 45 | 4 | 5 | 4 | 5 | 3 | 4 | 5 | 4 | 5 | 4 | 4 | Yes | Easy to use AI assistant | Good Vietnamese translations | Voice not accurate in field | Weather location wrong sometimes
```

### Color Coding (Optional):
- Header Row: Blue background, white text, bold
- Rating columns (O-X): Light yellow background
- Issues columns (AD-AE): Light red background

---

## SHEET 2: "Bug Tracker"

### Row 1 - Headers:
| A | B | C | D | E | F | G | H | I | J | K |
|---|---|---|---|---|---|---|---|---|---|---|
| Bug ID | Severity | Tester Name | Date Reported | Feature Area | Bug Title | Description | Steps to Reproduce | Expected Behavior | Actual Behavior | Status |

### Row 2 - Example:
```
BUG-001 | S1 | Nguyen Van A | 2024-02-14 | Login | Cannot verify OTP | User enters correct OTP but gets error | 1. Enter email 2. Request OTP 3. Enter correct OTP 4. Click Verify | Should login successfully | Shows "Invalid OTP" error | Open
```

### Severity Levels Dropdown:
- S1 - Critical
- S2 - Major
- S3 - Minor
- S4 - Suggestion

### Feature Area Dropdown:
- Authentication
- Dashboard
- Weather
- Tasks
- Journal
- AI Assistant - Text
- AI Assistant - Voice
- AI Assistant - Disease Detection
- Profile/Settings
- Farm/Plot Management

### Status Dropdown:
- Open
- In Progress
- Fixed
- Won't Fix
- Duplicate

### Color Coding:
- S1 rows: Red background
- S2 rows: Orange background
- S3 rows: Yellow background
- S4 rows: Light blue background

---

## SHEET 3: "Detailed Feedback"

### Row 1 - Headers:
| A | B | C | D | E | F |
|---|---|---|---|---|---|
| Tester Name | Question | Response | Category | Priority | Notes |

### Pre-filled Questions (one per row):

**Row 2:** 
```
[Blank] | What are the top 3 strengths of the app? | [Blank for tester] | Strengths | High | [Blank]
```

**Row 3:**
```
[Blank] | What are the top 3 issues or concerns? | [Blank] | Issues | High | [Blank]
```

**Row 4:**
```
[Blank] | Would farmers in your area use this app? Why or why not? | [Blank] | Adoption | High | [Blank]
```

**Row 5:**
```
[Blank] | Which feature is most useful for rice farmers? | [Blank] | Features | Medium | [Blank]
```

**Row 6:**
```
[Blank] | Which feature is least useful or confusing? | [Blank] | Features | Medium | [Blank]
```

**Row 7:**
```
[Blank] | Is the Vietnamese translation accurate and natural? Provide examples of issues. | [Blank] | Language | High | [Blank]
```

**Row 8:**
```
[Blank] | Are AI Assistant responses accurate and safe? Provide examples. | [Blank] | AI Quality | High | [Blank]
```

**Row 9:**
```
[Blank] | Can the app be used effectively in field conditions (sunlight, dirty hands, etc.)? | [Blank] | Usability | High | [Blank]
```

**Row 10:**
```
[Blank] | What improvements would make this app more useful for farmers? | [Blank] | Suggestions | Medium | [Blank]
```

**Row 11:**
```
[Blank] | Any other comments, observations, or feedback? | [Blank] | General | Low | [Blank]
```

---

## SHEET 4: "Summary Statistics"

### Automatic Calculations Section:

**Row 1-2: Total Responses**
```
A1: Total Testers
B1: =COUNTA('Tester Information & Ratings'!A2:A100)
```

**Row 4: Average Ratings Header**
```
A4: Feature
B4: Average Rating (out of 5)
C4: Highest Rating
D4: Lowest Rating
```

**Row 5-14: Feature Averages**
```
A5: Onboarding/Login
B5: =AVERAGE('Tester Information & Ratings'!O2:O100)
C5: =MAX('Tester Information & Ratings'!O2:O100)
D5: =MIN('Tester Information & Ratings'!O2:O100)

A6: Navigation Clarity
B6: =AVERAGE('Tester Information & Ratings'!P2:P100)
...continue for all features
```

**Row 16: Farmer Adoption Analysis**
```
A16: Would Farmers Use?
A17: Yes
B17: =COUNTIF('Tester Information & Ratings'!Y2:Y100,"Yes")
A18: No
B18: =COUNTIF('Tester Information & Ratings'!Y2:Y100,"No")
A19: Maybe
B19: =COUNTIF('Tester Information & Ratings'!Y2:Y100,"Maybe")
```

**Row 21: Bug Severity Count**
```
A21: Bug Severity Distribution
A22: Critical (S1)
B22: =COUNTIF('Bug Tracker'!B2:B100,"S1")
A23: Major (S2)
B23: =COUNTIF('Bug Tracker'!B2:B100,"S2")
A24: Minor (S3)
B24: =COUNTIF('Bug Tracker'!B2:B100,"S3")
A25: Suggestion (S4)
B25: =COUNTIF('Bug Tracker'!B2:B100,"S4")
```

**Row 27: Charts Recommendation**
```
Create charts for:
1. Average ratings bar chart (columns A5:B14)
2. Farmer adoption pie chart (B17:B19)
3. Bug severity pie chart (B22:B25)
```

---

## How to Use This Template

### For You (Test Coordinator):
1. Create a new Excel file named "AIRRVie_Field_Test_Master.xlsx"
2. Create 4 sheets with the names above
3. Copy the headers and formulas into each sheet
4. Format with colors as suggested
5. Save a copy as "AIRRVie_Field_Test_[TesterName].xlsx" for each tester
6. Distribute to 10 testers

### For Testers:
1. Receive their personalized copy
2. Fill in Sheet 1 (ratings) during/after testing
3. Fill in Sheet 2 (bug reports) as issues are found
4. Fill in Sheet 3 (detailed feedback) at end of testing
5. Sheet 4 auto-calculates (no manual entry)
6. Save and return file to coordinator

### For Analysis:
1. Collect all 10 tester files
2. Copy/paste all data into your master file
3. Sheet 4 automatically calculates aggregated statistics
4. Create charts for presentation
5. Export summary for reports

---

## File Naming Convention

**Master file:** `AIRRVie_Field_Test_Master.xlsx`

**Individual tester files:** 
- `AIRRVie_Test_NguyenVanA_AnGiang.xlsx`
- `AIRRVie_Test_TranThiB_DongThap.xlsx`
- etc.

**Completed files:** 
- `COMPLETED_AIRRVie_Test_NguyenVanA_AnGiang_2024-02-14.xlsx`

---

## Tips for Excel Setup

### Data Validation (Dropdowns):
For Sheet 2 (Bug Tracker):
- Select column B (Severity) → Data → Validation → List: S1,S2,S3,S4
- Select column E (Feature Area) → Data → Validation → List: (copy from Feature Area list)
- Select column K (Status) → Data → Validation → List: Open,In Progress,Fixed,Won't Fix,Duplicate

For Sheet 1 (Would Farmers Use):
- Select column Y → Data → Validation → List: Yes,No,Maybe

### Conditional Formatting:
For Sheet 2 (Bug Tracker) - Auto-color by severity:
1. Select range A2:K100
2. Conditional Formatting → New Rule → Formula
3. For S1: `=$B2="S1"` → Red fill
4. For S2: `=$B2="S2"` → Orange fill
5. For S3: `=$B2="S3"` → Yellow fill
6. For S4: `=$B2="S4"` → Light blue fill

### Freeze Panes:
- Select cell A2 on each sheet
- View → Freeze Panes → Freeze Top Row
- This keeps headers visible while scrolling

---

## Google Sheets Alternative

You can also create this in Google Sheets:
1. Go to sheets.google.com
2. Create new spreadsheet
3. Follow same structure as above
4. Share with testers (edit access)
5. Real-time collaboration
6. Automatic saving

**Advantages of Google Sheets:**
- No file distribution needed
- Real-time updates
- Automatic backup
- Mobile friendly
- Can link to Google Forms (see separate Google Form template)
