# MoMo Analytics - Mobile Money Transaction Analysis Platform

## 📱 Project Overview

MoMo Analytics is a comprehensive web-based platform for analyzing Mobile Money (MoMo) SMS transaction data. The application processes XML backups of SMS messages, extracts mobile money transactions, categorizes them intelligently, and provides interactive visualizations and analytics.

## 🎯 Project Objectives

This project demonstrates the complete data analysis pipeline from raw SMS data to actionable insights:

1. **Data Extraction & Processing**: Parse XML SMS backups and extract MoMo transactions
2. **Data Cleaning & Categorization**: Clean, validate, and categorize transactions automatically
3. **Database Design**: Store structured data using JSON-based storage system
4. **Interactive Dashboard**: Provide comprehensive analytics with charts and tables
5. **Full-Stack Development**: Modern web interface with responsive design

## ✨ Key Features

### 🔍 **Smart File Detection**
- Auto-detect XML files in data directory
- Drag & drop file upload interface
- File validation and size checking

### 🧠 **Intelligent Transaction Processing**
- **12+ Transaction Categories** automatically detected:
  - Incoming Money
  - Payments to Code Holders
  - Transfers to Mobile Numbers
  - Bank Deposits/Transfers
  - Airtime & Cash Power Payments
  - Third Party Initiated Transactions
  - Withdrawals from Agents
  - Internet & Voice Bundle Purchases
  - And more...

### 📊 **Comprehensive Analytics Dashboard**
- **Real-time Statistics**: Total transactions, amounts, fees, averages
- **Interactive Charts**:
  - Category distribution (pie chart)
  - Monthly transaction trends (line chart)
  - Transaction volume by type (bar chart)
  - Category breakdown with counts and amounts
- **Transaction Management**: Paginated table with filtering and search
- **Data Export**: CSV export functionality

### 🎨 **Modern User Experience**
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Dark/Light Theme**: Toggle between themes with smooth transitions
- **Real-time Updates**: Live progress indicators during processing
- **Intuitive Interface**: Clean, modern design with smooth animations

## 🛠️ Technical Architecture

### **Backend (Python/Flask)**
- **Framework**: Flask with modular blueprint architecture
- **Data Storage**: JSON-based storage system (no database setup required)
- **File Processing**: XML parsing with lxml library
- **API Design**: RESTful endpoints for all operations

### **Frontend (HTML/CSS/JavaScript)**
- **Responsive Design**: CSS Grid and Flexbox layouts
- **Interactive Charts**: Chart.js for data visualizations
- **Modern CSS**: CSS custom properties for theming
- **Progressive Enhancement**: Works without JavaScript for basic functionality

### **Data Processing Pipeline**
1. **XML Validation**: Check file structure and format
2. **SMS Extraction**: Parse SMS messages from XML backup
3. **Transaction Detection**: Filter MoMo-specific messages
4. **Data Extraction**: Use regex patterns to extract:
   - Transaction amounts and fees
   - Recipient/sender information
   - Transaction IDs and balances
   - Dates and timestamps
5. **Categorization**: Intelligent categorization using pattern matching
6. **Storage**: JSON-based persistent storage with backup functionality

## 📁 Project Structure

```
momo-analytics/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── routes.py            # API endpoints and web routes
│   ├── models.py            # Data models (SQLAlchemy compatible)
│   ├── parser.py            # SMS parsing and categorization logic
│   └── storage.py           # JSON storage system
├── static/
│   ├── css/
│   │   └── styles.css       # Modern responsive CSS with theming
│   └── js/
│       ├── main.js          # File upload and processing
│       ├── charts.js        # Dashboard charts and analytics
│       └── theme.js         # Theme switching functionality
├── templates/
│   ├── base.html            # Base template with common layout
│   ├── index.html           # Upload page
│   └── dashboard.html       # Analytics dashboard
├── data/                    # Data directory for XML files and storage
├── requirements.txt         # Python dependencies
├── run.py                   # Application runner with auto-setup
├── README.md               # This documentation
├── AUTHORS                 # Project contributors
└── LICENSE                 # MIT License
```

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### **Quick Start**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd momo-analytics
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   - Open your browser to `http://localhost:5000`
   - The application will automatically find an available port if 5000 is busy

### **Alternative Setup Methods**

**Option 1: Auto-detect existing files**
- Place XML files in the `data/` folder
- Use the "Scan for Files" feature on the homepage

**Option 2: Upload through interface**
- Use the drag & drop interface on the homepage
- Select XML files from your computer

## 📝 Usage Guide

### **Step 1: Prepare Your Data**
- Export SMS backup from your Android device as XML
- Ensure the backup includes MoMo/MTN Mobile Money messages
- Supported format: SMS Backup & Restore XML format

### **Step 2: Upload/Process Data**
- **Auto-detection**: Click "Scan for Files" to find XML files in data folder
- **Manual upload**: Drag & drop or select XML file through interface
- Wait for processing to complete (progress indicators provided)

### **Step 3: Analyze Results**
- Navigate to the dashboard automatically after processing
- Explore interactive charts and statistics
- Use pagination and filtering for transaction details
- Export data as CSV for further analysis

### **Step 4: Export & Share**
- Export transaction data as CSV
- Clear data when needed for new analysis
- Upload additional files to merge data

## 🔧 Configuration

### **Environment Variables**
- `FLASK_ENV`: Set to 'development' for debug mode
- `SECRET_KEY`: Custom secret key for session security

### **File Limits**
- Maximum file size: 16MB
- Supported formats: XML only
- Processing timeout: 5 minutes for large files

### **Storage**
- Data stored in JSON files in `data/` directory
- Automatic backup on data updates
- No external database required

## 🧪 Data Processing Details

### **Transaction Categories**
The system automatically categorizes transactions into these types:

1. **Incoming Money**: Received payments from other users
2. **Payment to Code**: Payments to code holders (merchants)
3. **Transfer to Number**: Direct transfers to phone numbers
4. **Bank Deposit**: Bank account deposits
5. **Airtime Payment**: Mobile airtime purchases
6. **Cash Power**: Electricity bill payments
7. **Third Party Initiated**: Transactions initiated by external parties
8. **Withdrawal from Agent**: Cash withdrawals via agents
9. **Bank Transfer**: Bank-to-mobile transfers
10. **Internet Voice Bundle**: Data and voice bundle purchases
11. **Fees and Charges**: Service fees and charges
12. **Balance Inquiry**: Account balance checks

### **Data Extraction**
For each transaction, the system extracts:
- **Amount**: Transaction value in RWF
- **Fee**: Service charges
- **Balance**: Account balance after transaction
- **Date/Time**: Transaction timestamp
- **Recipient**: Name and number of recipient
- **Sender**: Name and number of sender (for incoming)
- **Transaction ID**: Unique transaction reference
- **Message**: Additional transaction details

## 📊 Analytics Features

### **Summary Statistics**
- Total number of transactions
- Total transaction amount
- Total fees paid
- Average transaction amount

### **Visual Analytics**
- **Category Distribution**: Pie chart showing transaction type breakdown
- **Monthly Trends**: Line chart showing transaction volume and amount over time
- **Volume Analysis**: Bar chart showing transaction amounts by category
- **Detailed Breakdown**: Tabular view with category counts and totals

### **Interactive Features**
- **Pagination**: Navigate through large datasets
- **Filtering**: Filter by transaction category
- **Search**: Search across multiple transaction fields
- **Sorting**: Sort by date, amount, category
- **Export**: Download data as CSV

## 🎨 Design Features

### **Theme System**
- **Light Theme**: Clean, bright interface with MoMo-inspired colors
- **Dark Theme**: Modern dark interface for low-light usage
- **Auto-detection**: Respects system theme preference
- **Persistent**: Theme choice saved in browser

### **Responsive Design**
- **Mobile-first**: Optimized for mobile devices
- **Tablet-friendly**: Adapted layouts for medium screens
- **Desktop-enhanced**: Full feature set on large screens
- **Touch-optimized**: Touch-friendly interface elements

### **Animation & Interaction**
- **Smooth transitions**: 300ms CSS transitions throughout
- **Hover effects**: Interactive feedback on all clickable elements
- **Loading states**: Progress indicators during operations
- **Micro-animations**: Subtle animations enhance user experience

## 🔒 Security Considerations

### **File Validation**
- File type checking (XML only)
- File size limits (16MB max)
- Path traversal protection
- XML structure validation

### **Data Privacy**
- Local processing only (no data sent to external servers)
- JSON storage with local file system
- No external API calls for data processing
- User data remains on local machine

## 🚨 Troubleshooting

### **Common Issues**

**File Upload Fails**
- Check file format (must be XML)
- Verify file size (under 16MB)
- Ensure XML structure is valid SMS backup format

**No Transactions Found**
- Verify XML contains MoMo/MTN Mobile Money messages
- Check SMS sender names include "M-Money", "MTN Mobile Money", or "MoMo"
- Ensure messages contain transaction details (amounts, dates)

**Charts Not Loading**
- Refresh the page
- Check browser console for JavaScript errors
- Ensure modern browser with JavaScript enabled

**Port Already in Use**
- Application automatically finds available port
- Check terminal output for actual port number
- Try manually specifying different port

### **Performance Tips**
- For large XML files (>5MB), processing may take 1-2 minutes
- Clear browser cache if experiencing display issues
- Use modern browser for best performance
- Close other resource-intensive applications during processing

## 🤝 Contributing

### **Team Members**
- **Serein Shima** - Project Lead & Backend Development
- **Kessy Gaju** - Frontend Development & UI/UX
- **Sheilla Ruvugabigwi** - Data Processing & Analytics
- **Anthony Chinedu Emoh**

### **Development Guidelines**
1. Follow Python PEP 8 style guidelines
2. Use meaningful variable and function names
3. Add comments for complex logic
4. Test thoroughly before committing
5. Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.