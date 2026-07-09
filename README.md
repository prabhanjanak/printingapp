# 📇 Custom Badge PDF Generator

A lightweight Streamlit application that converts an uploaded Excel attendee list into a single, multi-page PDF optimized for printing custom event badges. 

Each page in the generated PDF is custom-sized to exactly **4 inches by 1 inch**, with text dynamically centered and sized perfectly for labels or badge inserts.

## 🚀 Features

* **Custom Page Layout:** Generates a crisp PDF where each attendee gets their own individual 4" x 1" page.
* **Smart Filtering:** Reads only `Name` and `Organisation Name` from your Excel sheet, completely ignoring other columns like IDs, phone numbers, or emails.
* **Global Role Assignment:** Allows you to type a single role (e.g., *Attendee*, *Exhibitor*, *Crew*) directly in the app UI to apply to all badges instantly.
* **Perfect Alignment:** Name is rendered large, bold, and centered. Organization and Role details are formatted as cleanly spaced subtitles directly underneath.

## 📊 Excel Sheet Format Requirement

The app expects an Excel file (`.xlsx` or `.xls`) containing at least the following column headers (case-sensitive):

| Name | Organisation Name |
| :--- | :--- |
| John Doe | Acme Corporation |
| Jane Smith | Tech Industries |

*Note: Extra columns in your sheet (such as `Reg No.`, `Mob`, `email Id`) are totally fine! The app will automatically ignore them.*

## 🛠️ Local Installation & Setup

If you ever want to run this project locally on your machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
