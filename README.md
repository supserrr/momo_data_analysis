# MoMo Analytics 📊

A comprehensive web application for analyzing Mobile Money (MoMo) transaction data from SMS backups. Transform your cluttered SMS history into actionable financial insights with beautiful visualizations.

## 🚀 Features

- **Automatic XML Detection**: Scans for existing XML files in your data directory
- **Smart SMS Parsing**: Extracts transaction details from 1600+ messages in under 30 seconds
- **Intelligent Categorization**: Automatically categorizes transactions into 12+ types
- **Interactive Dashboard**: Beautiful charts and visualizations using Chart.js
- **Dark/Light Theme**: Toggle between themes for comfortable viewing
- **Data Export**: Download your transactions as CSV for further analysis
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/supserrr/momo-analytics.git
   cd momo-analytics
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Running the Application

### Quick Start (Auto-processes XML files if found)
```bash
python run.py
```

The application will:
- Automatically scan for XML files in the `data/` directory
- Process the first file found (if any)
- Start the web server on an available port
- Open your browser to `http://localhost:5000`

### Manual Database Initialization
```bash
# Initialize empty database
python app/init_database.py

# View database info
python app/init_database.py info

# Reset database (WARNING: deletes all data)
python app/init_database.py reset
```

## 📱 Usage

### Method 1: Automatic File Detection
1. Place your SMS backup XML file in the `data/` directory
2. Run `python run.py`
3. The app will automatically process the file

### Method 2: Web Interface Upload
1. Start the application: `python run.py`
2. Navigate to `http://localhost:5000`
3. Click "Scan for Files" to detect XML files, or
4. Drag and drop your XML file onto the upload area
5. Click "Process File" to analyze your transactions

### Method 3: Manual File Upload
1. Use the web interface to upload your XML file
2. The file will be processed and stored in the database
3. View your analytics on the dashboard

## 📊 Understanding Your Data

The dashboard provides several insights:

- **Summary Cards**: Total transactions, amounts, fees, and averages
- **Category Distribution**: Pie chart showing transaction types
- **Monthly Trends**: Line graph of transaction volume over time
- **Transaction Table**: Detailed view with filtering and pagination
- **Category Breakdown**: Amount totals by transaction type

## 🗂️ Project Structure

```
momo-analytics/
├── app/                    # Application package
│   ├── __init__.py        # Flask app initialization
│   ├── models.py          # Database models
│   ├── routes.py          # API endpoints and views
│   ├── parser.py          # SMS parsing logic
│   └── database.py        # Database operations
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Upload page
│   └── dashboard.html    # Analytics dashboard
├── static/               # Static assets
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── data/                # Data directory
│   ├── uploads/         # Uploaded files
│   └── momo.db         # SQLite database
├── requirements.txt     # Python dependencies
├── run.py              # Application entry point
└── README.md          # This file
```

## 🔧 Configuration

The application uses sensible defaults, but you can modify settings in `app/__init__.py`:

- `MAX_CONTENT_LENGTH`: Maximum upload file size (default: 16MB)
- `UPLOAD_FOLDER`: Directory for uploaded files
- Database location: `data/momo.db`

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'lxml'"**
   ```bash
   pip install lxml
   ```

2. **"Permission denied" errors**
   - Ensure the `data/` directory has write permissions
   - On Unix systems: `chmod 755 data/`

3. **"Port already in use"**
   - The app automatically finds an available port
   - If issues persist, manually specify a port in `run.py`

4. **XML parsing errors**
   - Ensure your XML file is from SMS Backup & Restore app
   - Check that the file isn't corrupted

## 👥 Team

- **Serein Shima** - Backend Development & Database Design
- **Kessy Gaju** - Frontend Development & UI/UX
- **Sheilla Ruvugabigwi** - Data Processing & Analytics
- **Anthony Chinedu Emoh** - Testing & Documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.