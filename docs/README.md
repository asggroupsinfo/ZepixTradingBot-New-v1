# Zepix Trading Bot Documentation

Welcome to the Zepix Trading Bot documentation. This folder contains all documentation, guides, and reports for the trading bot.

## Documentation Index

### Main Documentation

#### Deployment Guides
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide for all platforms
- **[WINDOWS_DEPLOYMENT_GUIDE.md](WINDOWS_DEPLOYMENT_GUIDE.md)** - Windows-specific deployment instructions

#### Feature Documentation
- **[COMPLETE_FEATURES_SUMMARY.md](COMPLETE_FEATURES_SUMMARY.md)** - Complete list of all bot features and capabilities
- **[RE-ENTRY_SYSTEMS_DEGIN_AND_IMPLEMENTIOM.MD](RE-ENTRY_SYSTEMS_DEGIN_AND_IMPLEMENTIOM.MD)** - Design and implementation of re-entry systems
- **[PRODUCTION_READY_SUMMARY.md](PRODUCTION_READY_SUMMARY.md)** - Production readiness checklist and summary

## Quick Navigation

### Getting Started
1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for general deployment
2. Read [WINDOWS_DEPLOYMENT_GUIDE.md](WINDOWS_DEPLOYMENT_GUIDE.md) for Windows-specific steps
3. Review [COMPLETE_FEATURES_SUMMARY.md](COMPLETE_FEATURES_SUMMARY.md) to understand all features

### Understanding Features
- **Dual Order System**: See [COMPLETE_FEATURES_SUMMARY.md](COMPLETE_FEATURES_SUMMARY.md#dual-order-system)
- **Profit Booking Chains**: See [COMPLETE_FEATURES_SUMMARY.md](COMPLETE_FEATURES_SUMMARY.md#profit-booking-system)
- **Re-entry Systems**: See [RE-ENTRY_SYSTEMS_DEGIN_AND_IMPLEMENTIOM.MD](RE-ENTRY_SYSTEMS_DEGIN_AND_IMPLEMENTIOM.MD)
- **Risk Management**: See [COMPLETE_FEATURES_SUMMARY.md](COMPLETE_FEATURES_SUMMARY.md#risk-management)

### Production Deployment
- Review [PRODUCTION_READY_SUMMARY.md](PRODUCTION_READY_SUMMARY.md) before going live
- Follow [WINDOWS_DEPLOYMENT_GUIDE.md](WINDOWS_DEPLOYMENT_GUIDE.md) for Windows deployment

## Reports Folder

The `reports/` folder contains historical test reports, deployment notes, and diagnostic reports. These are kept for reference but are not essential for day-to-day operation.

### Report Categories
- **Test Reports**: Results from various test suites
- **Deployment Reports**: Notes from deployment processes
- **Fix Reports**: Documentation of bug fixes and improvements
- **Verification Reports**: System verification and validation reports

## Documentation Structure

```
docs/
├── README.md                          # This file
├── DEPLOYMENT_GUIDE.md                # Main deployment guide
├── WINDOWS_DEPLOYMENT_GUIDE.md        # Windows deployment
├── COMPLETE_FEATURES_SUMMARY.md       # All features
├── RE-ENTRY_SYSTEMS_DEGIN_AND_IMPLEMENTIOM.MD  # Re-entry design
├── PRODUCTION_READY_SUMMARY.md        # Production checklist
└── reports/                           # Historical reports
    ├── BOT_TEST_REPORT.md
    ├── COMPLETE_BOT_TEST_REPORT.md
    ├── FINAL_BOT_TEST_REPORT.md
    └── [other reports...]
```

## Key Topics

### Configuration
- Configuration files are in `config/` folder
- Main config: `config/config.json`
- Environment variables: `.env` (root level)

### Database
- Database file: `data/trading_bot.db`
- Stats file: `data/stats.json`

### Testing
- Test files: `tests/` folder
- Run all tests: `python scripts/run_all_tests.py`

### Scripts
- Deployment scripts: `scripts/` folder
- Windows setup: `scripts/windows_setup.bat`
- Windows admin setup: `scripts/windows_setup_admin.bat`

## Important Notes

- **Main Documentation**: Keep main guides in `docs/` root
- **Old Reports**: Move old test/deployment reports to `docs/reports/`
- **Structure**: Maintain folder structure as specified in root README.md

## Support

For questions or issues:
1. Check the relevant documentation file
2. Review test reports in `reports/` folder
3. Check deployment guides for setup issues

## Version

Documentation for Zepix Trading Bot v2.0

